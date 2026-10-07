"""
센서 테스트. 투입 초음파 거리와 칸별 IR(여유/참)를 0.4초마다 출력.
- 손을 초음파에 대면 cm 값이 줄어듦
- IR 센서를 가리면 해당 칸이 "참"으로 바뀜
종료: Ctrl+C
"""
from time import sleep
from gpiozero import DistanceSensor, DigitalInputDevice
from config import PIN_TRIG, PIN_ECHO, PIN_IR

ultrasonic = DistanceSensor(echo=PIN_ECHO, trigger=PIN_TRIG, max_distance=1)
# IR 장애물 센서는 물체 감지 시 보통 LOW(0) 출력 → active_state=False 로 "참"을 True 로
ir = {name: DigitalInputDevice(pin, pull_up=None, active_state=False)
      for name, pin in PIN_IR.items()}

print("측정 시작 (Ctrl+C 로 종료)")
try:
    while True:
        dist = ultrasonic.distance * 100
        status = {name: ("참" if dev.value else "여유") for name, dev in ir.items()}
        print(f"투입구 {dist:5.1f}cm | " +
              " ".join(f"{n}:{s}" for n, s in status.items()))
        sleep(0.4)
except KeyboardInterrupt:
    print("\n종료")
