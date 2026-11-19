"""
전체 통합. 감지 → 촬영 → 분류 → 회전+기울임 투하 → 원위치 → Supabase 기록(투입·사진·센서·연결 신호).
실행: python main.py   (model_unquant.tflite, labels.txt, .env 가 같은 폴더에 있어야 함)
Supabase 미설정 시 웹 기록만 건너뛰고 분류·투하는 정상 동작 (cloud.py).
IR 센서(가득참)는 config.PIN_IR 이 비어 있으면 자동으로 건너뜀.
"""
import threading
import time
import numpy as np
from picamera2 import Picamera2
from gpiozero import DistanceSensor, DigitalInputDevice
from adafruit_servokit import ServoKit
try:
    from ai_edge_litert.interpreter import Interpreter
except ImportError:
    from tflite_runtime.interpreter import Interpreter

import config as C
from cloud import Cloud
from logic import ArrivalDetector, SensorFilter, choose_compartment

cloud = Cloud()                               # 연결 신호는 여기서부터 30초마다 나감

# ── 서보 ──
kit = ServoKit(channels=16)
for ch in (C.CH_PAN, C.CH_TILT):
    kit.servo[ch].set_pulse_width_range(500, 2500)

def home():
    kit.servo[C.CH_TILT].angle = C.TILT_HOME
    kit.servo[C.CH_PAN].angle = C.PAN_HOME
    time.sleep(0.7)

def drop(label):
    pan, tilt = C.BINS[label]
    kit.servo[C.CH_PAN].angle = pan           # 방향 조준
    time.sleep(0.8)
    kit.servo[C.CH_TILT].angle = tilt         # 앞으로 기울여 투하
    time.sleep(1.0)
    if label in C.SHAKE_BINS:                 # 가벼운 일반쓰레기(봉지 등)가 붙어 안 떨어지는 것 방지
        for _ in range(C.SHAKE_TIMES):
            kit.servo[C.CH_TILT].angle = tilt - C.SHAKE_BACK
            time.sleep(0.15)
            kit.servo[C.CH_TILT].angle = tilt + C.SHAKE_MORE
            time.sleep(0.2)
    home()                                    # 원위치

# ── 센서 ──
ultrasonic = None
if C.USE_ULTRASONIC:
    ultrasonic = DistanceSensor(echo=C.PIN_ECHO, trigger=C.PIN_TRIG, max_distance=1)
ir = {name: DigitalInputDevice(pin, active_state=False, pull_up=None)
      for name, pin in C.PIN_IR.items()}

# 센서 값이 FULL_HOLD_SEC 이상 유지돼 바뀐 것으로 확정될 때만 기록 (떨어지는 쓰레기 무시).
# 켤 때 한 번 현재 값을 남겨 웹이 시작 상태를 알게 한다.
filters = {name: SensorFilter(C.FULL_HOLD_SEC) for name in ir}
for name, dev in ir.items():
    cloud.sensor(name, filters[name].start(bool(dev.value)))

def watch_sensors():
    while True:
        now = time.monotonic()
        for name, dev in ir.items():
            changed = filters[name].update(bool(dev.value), now)
            if changed is not None:
                cloud.sensor(name, changed)
        time.sleep(0.1)

if ir:
    threading.Thread(target=watch_sensors, daemon=True).start()

# ── AI 모델 ──
model = Interpreter(model_path="model_unquant.tflite")
model.allocate_tensors()
inp = model.get_input_details()[0]
out = model.get_output_details()[0]
labels = [ln.strip().split(" ", 1)[-1] for ln in open("labels.txt", encoding="utf-8")]

# ── 카메라 ──
cam = Picamera2()
cam.configure(cam.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"}))
cam.start()
time.sleep(2)

def probs():
    """(품목별 확률 배열, 원본 사진)."""
    photo = cam.capture_image("main").convert("RGB")
    img = photo
    w, h = img.size
    s = min(w, h)
    left = min(C.CROP_LEFT, w - s)
    img = img.crop((left, (h-s)//2, left + s, (h+s)//2)).resize((224, 224))
    x = np.asarray(img, dtype=np.float32)[None] / 127.5 - 1
    model.set_tensor(inp["index"], x)
    model.invoke()
    return model.get_tensor(out["index"])[0].astype(float), photo


def classify():
    """(라벨, 확신도, 원본 사진) 반환."""
    photo = cam.capture_image("main").convert("RGB")
    img = photo
    w, h = img.size
    s = min(w, h)
    left = min(C.CROP_LEFT, w - s)            # 쓰레기가 멈추는 오른쪽 벽 쪽 정사각형 (학습 사진도 같은 범위)
    img = img.crop((left, (h-s)//2, left + s, (h+s)//2)).resize((224, 224))
    x = np.asarray(img, dtype=np.float32)[None] / 127.5 - 1
    model.set_tensor(inp["index"], x)
    model.invoke()
    p = model.get_tensor(out["index"])[0]
    i = int(np.argmax(p))
    return labels[i], float(p[i]), photo

# ── 메인 루프 ──
def wait_for_item():
    """쓰레기가 올라올 때까지 기다렸다가 (label, conf, photo) 반환."""
    if ultrasonic:                             # 초음파 모드
        while ultrasonic.distance * 100 >= C.TRIGGER_CM:
            time.sleep(0.1)
        time.sleep(1)                          # 흔들림이 멈출 때까지
        return classify()
    # 카메라 모드 (11-18 판단 시간 실험): 빈 받침판 확률이 떨어지면 도착으로 보고,
    # 그때부터 DECIDE_SEC 초 동안 DECIDE_INTERVAL 초마다 찍은 확률의 평균으로 판정.
    # 실험 28회: 2초 평균 89.3%, 예전 규칙(같은 판정 2번 연속) 75.0%
    EMPTY = labels.index("empty")
    while True:                                # 1) 물건이 올라올 때까지
        p, photo = probs()
        if p[EMPTY] < C.ARRIVE_EMPTY_BELOW:
            break
        time.sleep(0.2)
    seen = [p]
    # 웹에 올릴 사진: 첫 장은 떨어지는 중이라 흐리거나 물건이 반쯤만 보임 (11-19 확인).
    # 2초 동안 찍은 것 중 물건이 가장 잘 보이는 장(빈 받침판 확률이 가장 낮은 장)을 고른다.
    best, best_empty = photo, p[EMPTY]
    t0 = time.monotonic()
    while time.monotonic() - t0 < C.DECIDE_SEC:  # 2) 정해진 시간 동안 더 보기
        time.sleep(C.DECIDE_INTERVAL)
        p, photo = probs()
        seen.append(p)
        if p[EMPTY] <= best_empty:
            best, best_empty = photo, p[EMPTY]
    m = np.mean(seen, axis=0)
    m[EMPTY] = 0                               # 빈 받침판은 빼고 품목끼리 비교
    i = int(np.argmax(m))
    return labels[i], float(m[i] / max(1e-9, m.sum())), best


def wait_until_empty():
    """쏟은 뒤 받침판이 빌 때까지 (같은 물건을 두 번 세지 않게)."""
    EMPTY = labels.index("empty")
    run, t0 = 0, time.monotonic()
    while run < 2 and time.monotonic() - t0 < 8:
        p, _ = probs()
        run = run + 1 if p[EMPTY] > C.LEAVE_EMPTY_ABOVE else 0
        time.sleep(0.3)

home()
print("준비 완료. 쓰레기를 넣어 주세요. (Ctrl+C 종료)")
try:
    while True:
        label, conf, photo = wait_for_item()
        print(f"분류: {label} ({conf:.0%})")
        into = choose_compartment(label, conf)
        if into is None:
            continue
        if into != label:
            print("  → 확신 부족, 일반으로")      # 안전 로직
        drop(into)
        cloud.deposit(photo, label, conf, into)  # 판정 품목과 실제로 들어간 칸을 따로 기록
        if not ultrasonic:
            wait_until_empty()
except KeyboardInterrupt:
    print("\n종료")
    cloud.flush()
