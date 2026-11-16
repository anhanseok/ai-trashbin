"""
판단 시간 ↔ 정확도 실험. 물건마다 받침판에 올라온 순간부터 RECORD_SEC 초 동안
INTERVAL 초마다 사진을 찍고 AI 확률을 기록한 뒤, 평균으로 판정한 칸에 쏟는다.
나중에 analyze_experiment.py 가 "t초까지만 보고 판단했다면" 정확도를 계산한다.

사용법:  python experiment.py [측정 횟수=30] [기록 초=10]
         (11-16 1차 실험: 13개 모두 5초 안에 판정이 굳어 기록은 10초면 충분)
진행:   받침판이 좌우로 살짝 두 번 흔들리면 → 투입구로 물건 하나 넣기 → 기다리기 → 쏟고 나면 다음
결과:   exp/<날짜시각>/item_01.jsonl (사진마다 시간·확률), item_01_00.jpg … (사진)
Supabase 에는 기록하지 않는다 (실험 데이터라 웹 투입 기록과 섞지 않음).
"""
import json, os, sys, time
import numpy as np
from picamera2 import Picamera2
from adafruit_servokit import ServoKit
try:
    from ai_edge_litert.interpreter import Interpreter
except ImportError:
    from tflite_runtime.interpreter import Interpreter

import config as C
from logic import choose_compartment

N_ITEMS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
RECORD_SEC = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
INTERVAL = 0.5
ARRIVE_EMPTY_BELOW = 0.5     # 빈 받침판 확률이 이보다 낮아지면 "물건이 올라왔다"
LEAVE_EMPTY_ABOVE = 0.6      # 쏟은 뒤 이보다 높게 2번 연속이면 "비었다"

kit = ServoKit(channels=16)
for ch in (C.CH_PAN, C.CH_TILT):
    kit.servo[ch].set_pulse_width_range(500, 2500)

def home():
    kit.servo[C.CH_TILT].angle = C.TILT_HOME
    kit.servo[C.CH_PAN].angle = C.PAN_HOME
    time.sleep(0.7)

def ready_signal():
    """다음 물건을 넣어도 된다는 신호: 좌우로 살짝 두 번."""
    for _ in range(2):
        kit.servo[C.CH_PAN].angle = C.PAN_HOME - 8; time.sleep(0.2)
        kit.servo[C.CH_PAN].angle = C.PAN_HOME + 8; time.sleep(0.2)
    home()

def drop(label):
    pan, tilt = C.BINS[label]
    kit.servo[C.CH_PAN].angle = pan; time.sleep(0.8)
    kit.servo[C.CH_TILT].angle = tilt; time.sleep(1.0)
    if label in C.SHAKE_BINS:
        for _ in range(C.SHAKE_TIMES):
            kit.servo[C.CH_TILT].angle = tilt - C.SHAKE_BACK; time.sleep(0.15)
            kit.servo[C.CH_TILT].angle = tilt + C.SHAKE_MORE; time.sleep(0.2)
    home()

model = Interpreter(model_path="model_unquant.tflite")
model.allocate_tensors()
inp = model.get_input_details()[0]; out = model.get_output_details()[0]
labels = [ln.strip().split(" ", 1)[-1] for ln in open("labels.txt", encoding="utf-8")]
EMPTY = labels.index("empty")

cam = Picamera2()
cam.configure(cam.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"}))
cam.start(); time.sleep(2)

def shot():
    """(확률 배열, 원본 사진). main.py 와 같은 전처리."""
    photo = cam.capture_image("main").convert("RGB")
    w, h = photo.size; s = min(w, h); left = min(C.CROP_LEFT, w - s)
    img = photo.crop((left, (h - s) // 2, left + s, (h + s) // 2)).resize((224, 224))
    x = np.asarray(img, dtype=np.float32)[None] / 127.5 - 1
    model.set_tensor(inp["index"], x); model.invoke()
    return model.get_tensor(out["index"])[0].astype(float), photo

folder = os.path.join("exp", time.strftime("%Y%m%d_%H%M%S"))
os.makedirs(folder, exist_ok=True)
json.dump({"labels": labels, "interval": INTERVAL, "record_sec": RECORD_SEC,
           "crop_left": C.CROP_LEFT}, open(os.path.join(folder, "meta.json"), "w"))
print(f"실험 시작: 물건 {N_ITEMS}개, 물건당 {RECORD_SEC:g}초 기록 → {folder}", flush=True)

home()
try:
    for n in range(1, N_ITEMS + 1):
        ready_signal()
        print(f"[{n}/{N_ITEMS}] 물건을 넣어 주세요", flush=True)
        while True:                                   # 물건이 올라올 때까지
            p, photo = shot()
            if p[EMPTY] < ARRIVE_EMPTY_BELOW:
                break
            time.sleep(0.2)
        t0 = time.monotonic(); rows = []; k = 0
        with open(os.path.join(folder, f"item_{n:02d}.jsonl"), "w") as f:
            while True:
                t = time.monotonic() - t0
                row = {"t": round(t, 3), "p": [round(v, 5) for v in p]}
                f.write(json.dumps(row) + "\n"); rows.append(row)
                photo.save(os.path.join(folder, f"item_{n:02d}_{k:02d}.jpg")); k += 1
                if t >= RECORD_SEC:
                    break
                time.sleep(max(0.0, INTERVAL - ((time.monotonic() - t0) - t)))
                p, photo = shot()
        mean = np.mean([r["p"] for r in rows], axis=0); mean[EMPTY] = 0
        label = labels[int(np.argmax(mean))]; conf = float(mean.max() / max(1e-9, mean.sum()))
        into = choose_compartment(label, conf) or "general"
        print(f"  {len(rows)}장 기록, 평균 판정 {label} ({conf:.0%}) → {into} 칸", flush=True)
        drop(into)
        empty_run = 0
        while empty_run < 2:                          # 받침판이 빌 때까지 (안 떨어졌으면 다시 쏟음)
            p, _ = shot()
            empty_run = empty_run + 1 if p[EMPTY] > LEAVE_EMPTY_ABOVE else 0
            if empty_run == 0 and time.monotonic() - t0 > RECORD_SEC + 8:
                drop(into); t0 = time.monotonic() - RECORD_SEC
            time.sleep(0.3)
except KeyboardInterrupt:
    print("중단", flush=True)
finally:
    home(); cam.stop()
    print(f"끝: {folder}", flush=True)
