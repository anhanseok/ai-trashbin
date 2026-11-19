"""
IR 센서 재질별 감지 실험. 재질 하나를 정해 10번 "대기 → 치우기"를 반복하고,
센서 3개가 감지했는지 기록한다. 기획서 위험 요소 1번(투명 페트를 못 볼 수 있음) 확인용.

사용법:  python ir_material.py <재질 이름> [횟수=10] [센서=plastic]
         예) python ir_material.py 투명페트 10 plastic
진행:   받침판이 좌우로 한 번 흔들리면 → 물건을 센서 앞(칸이 가득 찼을 때 높이)에 댄다
        받침판이 좌우로 두 번 흔들리면 → 치운다
결과:   exp_ir/ir_<날짜>.csv 에 한 줄씩 추가 (재질, 회차, 센서, 댔을 때, 치웠을 때)
"""
import csv, os, sys, time
from datetime import datetime
from gpiozero import DigitalInputDevice
from adafruit_servokit import ServoKit
import config as C

MATERIAL = sys.argv[1] if len(sys.argv) > 1 else "test"
TRIALS = int(sys.argv[2]) if len(sys.argv) > 2 else 10
TARGET = sys.argv[3] if len(sys.argv) > 3 else "plastic"
PINS = {"plastic": 17, "can": 27, "general": 22}   # 물리 핀 11·13·15
PLACE_SEC, MEASURE_SEC, REMOVE_SEC = 3.0, 1.0, 2.5

# IR 장애물 센서: 물체가 있으면 LOW → active_state=False 로 감지=True
ir = {n: DigitalInputDevice(p, pull_up=None, active_state=False) for n, p in PINS.items()}
kit = ServoKit(channels=16)
kit.servo[C.CH_PAN].set_pulse_width_range(500, 2500)


def wiggle(times):
    for _ in range(times):
        kit.servo[C.CH_PAN].angle = C.PAN_HOME - 8; time.sleep(0.2)
        kit.servo[C.CH_PAN].angle = C.PAN_HOME + 8; time.sleep(0.2)
    kit.servo[C.CH_PAN].angle = C.PAN_HOME
    time.sleep(0.3)


def sample(sec):
    """sec 초 동안 20번/초로 읽어 센서별 감지 비율."""
    hits = {n: 0 for n in ir}
    n = 0
    end = time.time() + sec
    while time.time() < end:
        for k, d in ir.items():
            hits[k] += d.value
        n += 1
        time.sleep(0.05)
    return {k: v / n for k, v in hits.items()}


os.makedirs("exp_ir", exist_ok=True)
path = f"exp_ir/ir_{datetime.now():%Y%m%d}.csv"
new = not os.path.exists(path)
f = open(path, "a", newline="", encoding="utf-8")
w = csv.writer(f)
if new:
    w.writerow(["시각", "재질", "회차", "센서", "댔을때_감지비율", "치웠을때_감지비율"])

base = sample(1.0)
print("시작 전 (아무것도 없을 때):", {k: f"{v:.0%}" for k, v in base.items()}, flush=True)
print(f"[{MATERIAL}] {TRIALS}회, 기준 센서 {TARGET}. 5초 뒤 시작", flush=True)
time.sleep(5)
ok = 0
for t in range(1, TRIALS + 1):
    wiggle(1)                         # 대세요
    time.sleep(PLACE_SEC - MEASURE_SEC)
    on = sample(MEASURE_SEC)
    wiggle(2)                         # 치우세요
    time.sleep(REMOVE_SEC)
    off = sample(0.5)
    hit = on[TARGET] >= 0.5
    ok += hit
    for k in ir:
        w.writerow([datetime.now().isoformat(timespec="seconds"), MATERIAL, t, k, f"{on[k]:.2f}", f"{off[k]:.2f}"])
    f.flush()
    print(f"{t:2d}회  {TARGET}: {'감지' if hit else '못 봄'} ({on[TARGET]:.0%})  치운 뒤 {off[TARGET]:.0%}", flush=True)
print(f"결과 [{MATERIAL}] {ok}/{TRIALS} 감지", flush=True)
