"""
서보 2개 테스트. 각 서보가 움직인 뒤 가운데(90°)에서 멈추면 성공.
그 상태에서 서보 혼(날개)을 끼우면 90°가 정확히 가운데가 됩니다.
"""
import time
from adafruit_servokit import ServoKit
from config import CH_PAN, CH_TILT

kit = ServoKit(channels=16)
for ch in (CH_PAN, CH_TILT):
    kit.servo[ch].set_pulse_width_range(500, 2500)  # MG996R 가동범위

for ch, name in ((CH_PAN, "회전"), (CH_TILT, "기울임")):
    print(f"--- {name} 서보 (CH{ch}) ---")
    for angle in (90, 0, 90, 180, 90):
        kit.servo[ch].angle = angle
        print("  →", angle, "도")
        time.sleep(1)

print("완료. 두 서보 모두 90°(가운데)에서 멈췄으면 성공.")
