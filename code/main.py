"""
전체 통합. 감지 → 촬영 → 분류 → 회전+기울임 투하 → 원위치 → Supabase 기록(투입·사진·센서·연결 신호).
실행: python main.py   (model_unquant.tflite, labels.txt, .env 가 같은 폴더에 있어야 함)
Supabase 미설정 시 웹 기록만 건너뛰고 분류·투하는 정상 동작 (cloud.py).
IR 센서(가득참)는 config.PIN_IR 이 비어 있으면 자동으로 건너뜀.
"""
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
    kit.servo[C.CH_TILT].angle = tilt         # 앞 또는 뒤로 기울여 투하
    time.sleep(1.0)
    home()                                    # 원위치

# ── 센서 ──
ultrasonic = None
if C.USE_ULTRASONIC:
    ultrasonic = DistanceSensor(echo=C.PIN_ECHO, trigger=C.PIN_TRIG, max_distance=1)
ir = {name: DigitalInputDevice(pin, active_state=False, pull_up=None, bounce_time=0.5)
      for name, pin in C.PIN_IR.items()}

# 센서 값이 바뀔 때만 기록. 켤 때 한 번 현재 값을 남겨 웹이 시작 상태를 알게 한다.
for name, dev in ir.items():
    dev.when_activated = lambda n=name: cloud.sensor(n, True)
    dev.when_deactivated = lambda n=name: cloud.sensor(n, False)
    cloud.sensor(name, dev.value)

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

def classify():
    """(라벨, 확신도, 원본 사진) 반환."""
    photo = cam.capture_image("main").convert("RGB")
    img = photo
    w, h = img.size
    s = min(w, h)
    img = img.crop(((w-s)//2, (h-s)//2, (w+s)//2, (h+s)//2)).resize((224, 224))
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
    prev = None                                # 카메라 모드: 2번 연속 같은 결과일 때만
    while True:
        label, conf, photo = classify()
        if label == "empty" or conf < C.DETECT_CONF:
            prev = None
        elif label == prev:
            return label, conf, photo
        else:
            prev = label
        time.sleep(0.4)

home()
print("준비 완료. 쓰레기를 넣어 주세요. (Ctrl+C 종료)")
try:
    while True:
        label, conf, photo = wait_for_item()
        print(f"분류: {label} ({conf:.0%})")
        if label == "empty" or label not in C.BINS:
            continue
        into = label
        if conf < C.MIN_CONF:
            into = "general"                   # 안전 로직
            print("  → 확신 부족, 일반으로")
        drop(into)
        cloud.deposit(photo, label, conf, into)  # 판정 품목과 실제로 들어간 칸을 따로 기록
except KeyboardInterrupt:
    print("\n종료")
    cloud.flush()
