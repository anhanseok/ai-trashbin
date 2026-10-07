"""
학습용 사진 수집. 반드시 조립 완료 후 상자 안 카메라로, LED 켜고 촬영.
사용법:  python capture.py plastic
클래스: plastic / can / general / empty
각 클래스 100장 (80 학습 + 20 평가), 서로 다른 제품 5종 이상 섞기.
"""
import os, sys, time
from picamera2 import Picamera2

if len(sys.argv) < 2:
    print("사용법: python capture.py <plastic|can|general|empty>")
    sys.exit(1)

label = sys.argv[1]
folder = f"data/{label}"
os.makedirs(folder, exist_ok=True)

cam = Picamera2()
cam.configure(cam.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"}))
cam.start()
time.sleep(2)

n = len(os.listdir(folder))
print(f"[{label}] 시작 (현재 {n}장). Enter=촬영, q+Enter=끝")
while input() != "q":
    path = f"{folder}/{n:03d}.jpg"
    cam.capture_image("main").convert("RGB").save(path)
    n += 1
    print(f"  저장 {path}  (총 {n}장)")
print("완료")
