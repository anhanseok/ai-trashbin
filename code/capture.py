"""
학습용 사진 수집. 반드시 조립 완료 후 상자 안 카메라로, LED 켜고 촬영.
사용법:
  python capture.py plastic          Enter 칠 때마다 1장 (q+Enter 끝)
  python capture.py plastic 20       Enter 치면 1초 간격으로 20장 연속 → 그동안 물건을 돌리고 옮김
클래스: plastic / can / general / empty
목표: 품목 200장, empty 100장 (스펙 7-1). 물건 10~15개 × 연속 촬영 15~20장이면 됨.
정확도 시험용으로 물건 몇 개는 학습에 쓰지 말고 남겨 둘 것.
"""
import os, sys, time
from picamera2 import Picamera2

if len(sys.argv) < 2:
    print("사용법: python capture.py <plastic|can|general|empty> [연속 장수]")
    sys.exit(1)

label = sys.argv[1]
burst = int(sys.argv[2]) if len(sys.argv) > 2 else 1
INTERVAL = 1.0                                 # 연속 촬영 간격(초): 물건을 돌리고 옮길 시간
folder = f"data/{label}"
os.makedirs(folder, exist_ok=True)

cam = Picamera2()
cam.configure(cam.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"}))
cam.start()
time.sleep(2)

n = len(os.listdir(folder))
how = "1장" if burst == 1 else f"{burst}장 연속 ({INTERVAL:.0f}초 간격, 그동안 물건을 돌리세요)"
print(f"[{label}] 시작 (현재 {n}장). Enter={how}, q+Enter=끝")
while input() != "q":
    for i in range(burst):
        path = f"{folder}/{n:03d}.jpg"
        cam.capture_image("main").convert("RGB").save(path)
        n += 1
        print(f"  저장 {path}  (총 {n}장)")
        if i < burst - 1:
            time.sleep(INTERVAL)
    if burst > 1:
        print("  다음 물건으로 바꾸고 Enter")
print("완료")
