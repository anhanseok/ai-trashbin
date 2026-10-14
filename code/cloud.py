"""
수거함 → Supabase 기록. 용어는 CONTEXT.md 기준 (투입, 칸, 확신도, 가득참).
- 투입: 사진을 Storage 'photos' 에 올리고 deposits 에 한 줄
- 센서 기록: IR 값이 바뀔 때 sensor_readings 에 한 줄
- 연결 신호: HEARTBEAT_SEC 마다 bins.last_seen_at 갱신

모든 전송은 백그라운드 스레드에서 한다. 인터넷이 느리거나 끊겨도 분류·투하는 멈추지 않는다.
Supabase 키가 없으면 아무것도 보내지 않고 조용히 넘어간다.
"""
import io
import queue
import threading
import time
from datetime import datetime, timezone

import config as C


def _now():
    return datetime.now(timezone.utc).isoformat()


class Cloud:
    def __init__(self):
        self.sb = None
        self.jobs = queue.Queue()
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
        threading.Thread(target=self._worker, daemon=True).start()
        threading.Thread(target=self._heartbeat, daemon=True).start()

    # ── 밖에서 부르는 함수 (바로 돌아옴) ──
    def deposit(self, image, predicted, confidence, dropped_into):
        """투입 1건. image 는 PIL 이미지 (없으면 None)."""
        if self.sb:
            self.jobs.put(("deposit", (image, predicted, confidence, dropped_into, _now())))

    def sensor(self, compartment, detected):
        """칸의 IR 센서 값이 바뀜. detected=True 면 칸 높이 80%까지 참."""
        if self.sb:
            self.jobs.put(("sensor", (compartment, bool(detected), _now())))

    def flush(self, timeout=10):
        """남은 전송을 기다린다 (프로그램 끝낼 때)."""
        end = time.time() + timeout
        while self.sb and not self.jobs.empty() and time.time() < end:
            time.sleep(0.2)

    # ── 백그라운드 ──
    def _worker(self):
        while True:
            kind, args = self.jobs.get()
            for attempt in range(3):          # 실패하면 2번 더 시도
                try:
                    if kind == "deposit":
                        self._send_deposit(*args)
                    else:
                        self._send_sensor(*args)
                    break
                except Exception as e:
                    print(f"기록 실패({kind}, {attempt + 1}/3):", e)
                    time.sleep(2 * (attempt + 1))

    def _send_deposit(self, image, predicted, confidence, dropped_into, at):
        path = None
        if image is not None:
            buf = io.BytesIO()
            image.convert("RGB").save(buf, "JPEG", quality=80)
            path = f"{C.BIN_ID}/{at[:10]}/{at[11:19].replace(':', '')}-{predicted}.jpg"
            self.sb.storage.from_("photos").upload(
                path, buf.getvalue(), {"content-type": "image/jpeg", "upsert": "true"})
        self.sb.table("deposits").insert({
            "bin_id": C.BIN_ID, "created_at": at, "photo_path": path,
            "predicted": predicted, "confidence": round(float(confidence), 3),
            "dropped_into": dropped_into,
        }).execute()

    def _send_sensor(self, compartment, detected, at):
        self.sb.table("sensor_readings").insert({
            "bin_id": C.BIN_ID, "compartment": compartment, "detected": detected, "created_at": at,
        }).execute()

    def _heartbeat(self):
        while True:
            try:
                self.sb.table("bins").update({"last_seen_at": _now()}).eq("id", C.BIN_ID).execute()
            except Exception as e:
                print("연결 신호 실패(무시):", e)
            time.sleep(C.HEARTBEAT_SEC)
