"""
학습 사진 자동 촬영: 실제 사용처럼 투입구로 떨어뜨린 모습을 찍는다.
받침판이 좌우로 두 번 흔들리면 → 물건 하나를 투입구에 넣기 → 받침판에 멈추면 1장 찍고 그 품목 칸에 쏟음.

사용법:  python capture_drop.py <plastic|can|general> [장수=20] [접두어=n1118]
결과:   data/<품목>/<접두어>_000.jpg … (기존 사진과 이름이 안 겹치게 접두어를 붙임)
같은 물건을 여러 번 찍으려면 한 바퀴(물건마다 1번씩) 돈 뒤 통에서 꺼내 다시 넣는다.
"""
import os, sys, time
import numpy as np
from picamera2 import Picamera2
from adafruit_servokit import ServoKit
try:
    from ai_edge_litert.interpreter import Interpreter
except ImportError:
    from tflite_runtime.interpreter import Interpreter
import config as C

LABEL = sys.argv[1]
COUNT = int(sys.argv[2]) if len(sys.argv) > 2 else 20
PREFIX = sys.argv[3] if len(sys.argv) > 3 else "n1118"
SETTLE = 1.0                 # 받침판에 올라온 뒤 멈출 때까지 기다리는 시간
ARRIVE_EMPTY_BELOW = 0.5
LEAVE_EMPTY_ABOVE = 0.6
folder = f"data/{LABEL}"
os.makedirs(folder, exist_ok=True)

kit = ServoKit(channels=16)
for ch in (C.CH_PAN, C.CH_TILT):
    kit.servo[ch].set_pulse_width_range(500, 2500)


def home():
    kit.servo[C.CH_TILT].angle = C.TILT_HOME
    kit.servo[C.CH_PAN].angle = C.PAN_HOME
    time.sleep(0.7)


def ready_signal():
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
    photo = cam.capture_image("main").convert("RGB")
    w, h = photo.size; s = min(w, h); left = min(C.CROP_LEFT, w - s)
    img = photo.crop((left, (h - s) // 2, left + s, (h + s) // 2)).resize((224, 224))
    x = np.asarray(img, dtype=np.float32)[None] / 127.5 - 1
    model.set_tensor(inp["index"], x); model.invoke()
    return model.get_tensor(out["index"])[0].astype(float), photo


start = len([f for f in os.listdir(folder) if f.startswith(PREFIX)])
print(f"[{LABEL}] {COUNT}장 촬영 시작 (이 접두어로 이미 {start}장)", flush=True)
home()
try:
    for n in range(start, start + COUNT):
        ready_signal()
        print(f"  {n - start + 1}/{COUNT} 넣어 주세요", flush=True)
        while True:
            p, _ = shot()
            if p[EMPTY] < ARRIVE_EMPTY_BELOW:
                break
            time.sleep(0.2)
        time.sleep(SETTLE)
        p, photo = shot()
        path = f"{folder}/{PREFIX}_{n:03d}.jpg"
        photo.save(path)
        print(f"  저장 {path}  (지금 모델 판정 {labels[int(np.argmax(p))]} {p.max():.0%})", flush=True)
        drop(LABEL)
        t0 = time.monotonic(); run = 0
        while run < 2:
            p, _ = shot()
            run = run + 1 if p[EMPTY] > LEAVE_EMPTY_ABOVE else 0
            if run == 0 and time.monotonic() - t0 > 6:
                drop(LABEL); t0 = time.monotonic()
            time.sleep(0.3)
except KeyboardInterrupt:
    print("중단", flush=True)
finally:
    home(); cam.stop()
    print("끝", flush=True)
