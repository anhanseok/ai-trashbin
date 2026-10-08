"""
전체 통합. 감지 → 촬영 → 분류 → 회전+기울임 투하 → 원위치 → (있으면) 칸 상태 Supabase 기록.
실행: python main.py   (model_unquant.tflite, labels.txt 가 같은 폴더에 있어야 함)
Supabase 미설정 시 웹 기록만 건너뛰고 분류·투하는 정상 동작.
IR 센서(칸 여유/참)는 초기 단계에서 뺌 — config.PIN_IR이 비어 있으면 자동으로 건너뜀.
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

# ── 서보 ──
kit = ServoKit(channels=16)
for ch in (C.CH_PAN, C.CH_TILT):
    kit.servo[ch].set_pulse_width_range(500, 2500)

def home():
    kit.servo[C.CH_TILT].angle = C.TILT_HOME
    kit.servo[C.CH_PAN].angle = C.PAN["can"]  # 가운데 칸 방향을 기본으로
    time.sleep(0.7)

def drop(label):
    kit.servo[C.CH_PAN].angle = C.PAN[label]  # 방향 조준
    time.sleep(0.8)
    kit.servo[C.CH_TILT].angle = C.TILT_DUMP  # 기울여 투하
    time.sleep(1.0)
    home()                                    # 원위치

# ── 센서 ──
ultrasonic = DistanceSensor(echo=C.PIN_ECHO, trigger=C.PIN_TRIG, max_distance=1)
ir = {name: DigitalInputDevice(pin, active_state=False, pull_up=None)
      for name, pin in C.PIN_IR.items()}

def bin_status():
    return {name: bool(dev.value) for name, dev in ir.items()}  # True = 참

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
    img = cam.capture_image("main").convert("RGB")
    w, h = img.size
    s = min(w, h)
    img = img.crop(((w-s)//2, (h-s)//2, (w+s)//2, (h+s)//2)).resize((224, 224))
    x = np.asarray(img, dtype=np.float32)[None] / 127.5 - 1
    model.set_tensor(inp["index"], x)
    model.invoke()
    p = model.get_tensor(out["index"])[0]
    i = int(np.argmax(p))
    return labels[i], float(p[i])

# ── Supabase (선택) ──
sb = None
if C.SUPABASE_URL and C.SUPABASE_KEY:
    try:
        from supabase import create_client
        sb = create_client(C.SUPABASE_URL, C.SUPABASE_KEY)
        print("Supabase 연결됨")
    except Exception as e:
        print("Supabase 연결 실패(무시하고 진행):", e)

def log_event(label, conf, status):
    if not sb:
        return
    try:
        sb.table("events").insert({
            "label": label, "confidence": round(conf, 3), "status": status
        }).execute()
    except Exception as e:
        print("기록 실패(무시):", e)

# ── 메인 루프 ──
home()
print("준비 완료. 쓰레기를 넣어 주세요. (Ctrl+C 종료)")
try:
    while True:
        if ultrasonic.distance * 100 < C.TRIGGER_CM:
            time.sleep(1)                      # 흔들림이 멈출 때까지
            label, conf = classify()
            print(f"분류: {label} ({conf:.0%})")
            if label == "empty":
                continue
            if conf < C.MIN_CONF or label not in C.PAN:
                label = "general"              # 안전 로직
                print("  → 확신 부족, 일반으로")
            drop(label)
            status = bin_status()           # IR 미설치 시 {} (정상)
            log_event(label, conf, status)
            if status:
                print("  칸 상태:", status)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n종료")
