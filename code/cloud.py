"""
수거함 → Supabase 기록. 용어는 CONTEXT.md 기준 (투입, 칸, 확신도, 가득참).
- 투입: 사진을 Storage 'photos' 에 올리고 deposits 에 한 줄
- 센서 기록: IR 값이 바뀔 때 sensor_readings 에 한 줄
- 연결 신호: HEARTBEAT_SEC 마다 bins.last_seen_at 갱신

모든 전송은 백그라운드 스레드에서 한다. 인터넷이 느리거나 끊겨도 분류·투하는 멈추지 않는다.
3번 시도해도 못 보낸 기록은 outbox/ 폴더에 저장했다가, 인터넷이 돌아오면 순서대로 다시 보낸다.
Supabase 키가 없으면 아무것도 보내지 않고 조용히 넘어간다.
"""
import io
import json
import os
import queue
import threading
import time
from datetime import datetime, timezone

import config as C

OUTBOX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outbox")
RETRY_OUTBOX_SEC = 60


def _now():
    return datetime.now(timezone.utc).isoformat()


def photo_path(bin_id, at, predicted):
    """Storage 안 사진 경로: bin-01/2026-10-15/001234-can.jpg (UTC 기준)"""
    return f"{bin_id}/{at[:10]}/{at[11:19].replace(':', '')}-{predicted}.jpg"


class Cloud:
    def __init__(self, client=None, outbox=OUTBOX, start_threads=True):
        """client 를 넘기면 그걸 쓴다 (테스트용). 아니면 config 의 키로 만든다."""
        self.sb = client
        self.outbox = outbox
        self.jobs = queue.Queue()
        self.lock = threading.Lock()              # outbox 재전송과 일반 전송이 겹치지 않게
        if self.sb is None:
            if not (C.SUPABASE_URL and C.SUPABASE_KEY):
                print("Supabase 미설정: 웹 기록 없이 동작")
                return
            try:
                from supabase import create_client
                self.sb = create_client(C.SUPABASE_URL, C.SUPABASE_KEY)
                print("Supabase 연결됨 (수거함", C.BIN_ID + ")")
            except Exception as e:
                print("Supabase 연결 실패(무시하고 진행):", e)
                return
        if start_threads:
            for target in (self._worker, self._heartbeat, self._retry_outbox):
                threading.Thread(target=target, daemon=True).start()

    # ── 밖에서 부르는 함수 (바로 돌아옴) ──
    def deposit(self, image, predicted, confidence, dropped_into):
        """투입 1건. image 는 PIL 이미지 (없으면 None)."""
        if not self.sb:
            return
        jpeg = None
        if image is not None:                     # 사진은 지금 JPEG 로 굳힌다 (outbox 저장 가능하게)
            buf = io.BytesIO()
            image.convert("RGB").save(buf, "JPEG", quality=80)
            jpeg = buf.getvalue()
        self.jobs.put({"kind": "deposit", "at": _now(), "predicted": predicted,
                       "confidence": round(float(confidence), 3), "dropped_into": dropped_into,
                       "jpeg": jpeg})

    def sensor(self, compartment, detected):
        """칸의 IR 센서 값이 바뀜. detected=True 면 칸 높이 80%까지 참."""
        if self.sb:
            self.jobs.put({"kind": "sensor", "at": _now(), "compartment": compartment,
                           "detected": bool(detected)})

    def flush(self, timeout=10):
        """남은 전송을 기다린다 (프로그램 끝낼 때)."""
        end = time.time() + timeout
        while self.sb and self.jobs.unfinished_tasks and time.time() < end:
            time.sleep(0.2)

    # ── 전송 ──
    def send(self, job):
        """기록 1건을 보낸다. 실패하면 예외."""
        with self.lock:
            if job["kind"] == "deposit":
                path = None
                if job.get("jpeg"):
                    path = photo_path(C.BIN_ID, job["at"], job["predicted"])
                    self.sb.storage.from_("photos").upload(
                        path, job["jpeg"], {"content-type": "image/jpeg", "upsert": "true"})
                self.sb.table("deposits").insert({
                    "bin_id": C.BIN_ID, "created_at": job["at"], "photo_path": path,
                    "predicted": job["predicted"], "confidence": job["confidence"],
                    "dropped_into": job["dropped_into"],
                }).execute()
            else:
                self.sb.table("sensor_readings").insert({
                    "bin_id": C.BIN_ID, "compartment": job["compartment"],
                    "detected": job["detected"], "created_at": job["at"],
                }).execute()

    def _worker(self, tries=3, wait=2):
        while True:
            job = self.jobs.get()
            try:
                for attempt in range(tries):
                    try:
                        self.send(job)
                        break
                    except Exception as e:
                        print(f"기록 실패({job['kind']}, {attempt + 1}/{tries}):", e)
                        time.sleep(wait * (attempt + 1))
                else:
                    self.save_to_outbox(job)
            finally:
                self.jobs.task_done()

    # ── outbox: 못 보낸 기록을 파일로 보관 ──
    def save_to_outbox(self, job):
        os.makedirs(self.outbox, exist_ok=True)
        name = job["at"].replace(":", "").replace("+", "_") + "-" + job["kind"]
        meta = {k: v for k, v in job.items() if k != "jpeg"}
        if job.get("jpeg"):
            open(os.path.join(self.outbox, name + ".jpg"), "wb").write(job["jpeg"])
            meta["jpeg_file"] = name + ".jpg"
        json.dump(meta, open(os.path.join(self.outbox, name + ".json"), "w", encoding="utf-8"))
        print("인터넷 문제로 보관함에 저장:", name)

    def outbox_files(self):
        if not os.path.isdir(self.outbox):
            return []
        return sorted(f for f in os.listdir(self.outbox) if f.endswith(".json"))  # 시간순

    def drain_outbox(self):
        """보관함 기록을 오래된 것부터 보낸다. 하나라도 실패하면 멈추고 다음 기회에. 보낸 개수 반환."""
        sent = 0
        for f in self.outbox_files():
            meta_path = os.path.join(self.outbox, f)
            job = json.load(open(meta_path, encoding="utf-8"))
            jpg = job.pop("jpeg_file", None)
            if jpg:
                job["jpeg"] = open(os.path.join(self.outbox, jpg), "rb").read()
            try:
                self.send(job)
            except Exception as e:
                print("보관함 재전송 실패, 나중에 다시:", e)
                break
            os.remove(meta_path)
            if jpg:
                os.remove(os.path.join(self.outbox, jpg))
            sent += 1
        if sent:
            print(f"보관함 기록 {sent}건 전송 완료")
        return sent

    def _retry_outbox(self):
        while True:
            if self.outbox_files():
                self.drain_outbox()
            time.sleep(RETRY_OUTBOX_SEC)

    def _heartbeat(self):
        while True:
            try:
                self.sb.table("bins").update({"last_seen_at": _now()}).eq("id", C.BIN_ID).execute()
            except Exception as e:
                print("연결 신호 실패(무시):", e)
            time.sleep(C.HEARTBEAT_SEC)
