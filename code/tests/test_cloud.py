"""cloud.py 를 가짜 Supabase 로 시험한다. 인터넷이 끊기면 outbox 에 저장했다가 다시 보내는지."""
from PIL import Image

from cloud import Cloud, photo_path


class FakeSupabase:
    """table().insert().execute(), storage.from_().upload() 만 흉내. online=False 면 예외."""

    def __init__(self):
        self.online = True
        self.rows = {}
        self.files = {}
        self.storage = self

    def _check(self):
        if not self.online:
            raise ConnectionError("인터넷 끊김")

    def table(self, name):
        fake = self

        class Q:
            def insert(self, row):
                self.row = row
                return self

            def update(self, row):
                self.row = None
                return self

            def eq(self, *a):
                return self

            def execute(self):
                fake._check()
                if self.row is not None:
                    fake.rows.setdefault(name, []).append(self.row)

        return Q()

    def from_(self, bucket):
        fake = self

        class B:
            def upload(self, path, data, opts):
                fake._check()
                fake.files[path] = data

        return B()


def make(tmp_path):
    sb = FakeSupabase()
    return sb, Cloud(client=sb, outbox=str(tmp_path / "outbox"), start_threads=False)


def take(cloud):
    job = cloud.jobs.get()
    cloud.jobs.task_done()
    return job


def test_deposit_uploads_photo_and_inserts_row(tmp_path):
    sb, cloud = make(tmp_path)
    cloud.deposit(Image.new("RGB", (64, 48)), "can", 0.934, "can")
    cloud.send(take(cloud))
    row = sb.rows["deposits"][0]
    assert row["predicted"] == "can" and row["dropped_into"] == "can" and row["confidence"] == 0.934
    assert row["photo_path"] in sb.files and sb.files[row["photo_path"]][:2] == b"\xff\xd8"  # JPEG


def test_low_confidence_keeps_predicted_and_dropped_into_separate(tmp_path):
    sb, cloud = make(tmp_path)
    cloud.deposit(None, "plastic", 0.61, "general")
    cloud.send(take(cloud))
    row = sb.rows["deposits"][0]
    assert (row["predicted"], row["dropped_into"], row["photo_path"]) == ("plastic", "general", None)


def test_offline_jobs_go_to_outbox_and_are_sent_later_in_order(tmp_path):
    sb, cloud = make(tmp_path)
    sb.online = False
    cloud.sensor("plastic", True)
    cloud.deposit(Image.new("RGB", (64, 48)), "can", 0.9, "can")
    for _ in range(2):
        cloud.save_to_outbox(take(cloud))      # _worker 가 3번 실패한 뒤 하는 일
    assert len(cloud.outbox_files()) == 2

    assert cloud.drain_outbox() == 0           # 아직 끊김 → 아무것도 안 지움
    assert len(cloud.outbox_files()) == 2

    sb.online = True
    assert cloud.drain_outbox() == 2
    assert cloud.outbox_files() == []
    assert sb.rows["sensor_readings"][0]["compartment"] == "plastic"
    assert sb.rows["deposits"][0]["photo_path"] in sb.files   # 사진도 함께 복구


def test_worker_saves_to_outbox_after_retries(tmp_path, monkeypatch):
    sb, cloud = make(tmp_path)
    sb.online = False
    cloud.sensor("can", True)
    monkeypatch.setattr("time.sleep", lambda s: None)
    import threading
    t = threading.Thread(target=cloud._worker, kwargs={"tries": 3, "wait": 0}, daemon=True)
    t.start()
    cloud.flush(timeout=5)
    assert len(cloud.outbox_files()) == 1


def test_photo_path_is_grouped_by_bin_and_date():
    assert photo_path("bin-01", "2026-10-15T00:12:34.5+00:00", "can") == "bin-01/2026-10-15/001234-can.jpg"
