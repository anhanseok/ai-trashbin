"""
부품 점검. main.py 를 돌리기 전에 무엇이 준비됐고 무엇이 빠졌는지 한 번에 본다.
실행: python check.py
"""
import os

import config as C

ok_all = True


def report(name, ok, detail=""):
    global ok_all
    ok_all &= ok
    print(f"{'✅' if ok else '❌'} {name}" + (f" — {detail}" if detail else ""))


# 1. 카메라
try:
    from picamera2 import Picamera2
    cams = Picamera2.global_camera_info()
    report("카메라", bool(cams), cams[0]["Model"] if cams else "인식 안 됨: 리본 케이블 방향·연결 확인 (전원 끄고)")
except Exception as e:
    report("카메라", False, str(e))

# 2. 서보 보드 PCA9685 (I2C 0x40)
try:
    from smbus2 import SMBus
    with SMBus(1) as bus:
        bus.read_byte(0x40)
    report("서보 보드 PCA9685", True, "I2C 0x40")
except Exception:
    report("서보 보드 PCA9685", False, "I2C 0x40 응답 없음: SDA(3번)·SCL(5번)·3.3V(1번)·GND 배선 확인")

# 3. AI 모델
have_model = os.path.exists("model_unquant.tflite") and os.path.exists("labels.txt")
if have_model:
    labels = [ln.strip().split(" ", 1)[-1] for ln in open("labels.txt", encoding="utf-8")]
    missing = [c for c in [*C.BINS, "empty"] if c not in labels]
    report("AI 모델", not missing, f"라벨 {labels}" + (f", 빠진 라벨 {missing}" if missing else ""))
else:
    report("AI 모델", False, "model_unquant.tflite, labels.txt 가 code/ 에 없음 (Teachable Machine 또는 Colab 에서 내보내기)")

# 4. IR 센서 (가득참)
if C.PIN_IR:
    from gpiozero import DigitalInputDevice
    for name, pin in C.PIN_IR.items():
        dev = DigitalInputDevice(pin, active_state=False, pull_up=None)
        report(f"IR 센서 {name} (GPIO {pin})", True, "감지 중" if dev.value else "비어 있음")
        dev.close()
else:
    print("➖ IR 센서 — config.PIN_IR 비어 있음 (가득참 감지 안 함)")

# 5. 초음파 (투입 감지)
print("➖ 초음파 — 사용 안 함 (카메라로 투입 감지)" if not C.USE_ULTRASONIC else "ℹ 초음파 사용: test_sensors.py 로 확인")

# 6. 클라우드
try:
    from supabase import create_client
    sb = create_client(C.SUPABASE_URL, C.SUPABASE_KEY)
    b = sb.table("bins").select("id,name").eq("id", C.BIN_ID).execute().data
    report("Supabase", bool(b), b[0]["name"] if b else f"bins 에 {C.BIN_ID} 없음")
except Exception as e:
    report("Supabase", False, f"code/.env 확인 ({e})")

print("\n모두 준비됨: python main.py" if ok_all else "\n❌ 항목을 해결한 뒤 다시 실행하세요.")
