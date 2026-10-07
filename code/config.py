"""
공통 설정. 핀 번호와 각도는 여기만 바꾸면 모든 코드에 반영됩니다.
※ 각도는 실물 조립 후 팀원(HW)이 실측해서 수정합니다.
"""
import os

# ── 서보 (PCA9685 채널) ──
CH_PAN = 0          # 회전 서보
CH_TILT = 1         # 기울임 서보

# 회전 각도: 각 쓰레기 종류가 갈 칸 방향
# MG996R은 0~180°만 돌아가므로 3칸을 반원으로 배치 (0 / 90 / 180)
PAN = {
    "plastic": 0,    # 페트
    "can": 90,       # 캔
    "general": 180,  # 일반
}
# 기울임 각도: 평소 수평(HOME) → 투하(DUMP). 실물 보고 조정
TILT_HOME = 90
TILT_DUMP = 40

# ── 핀 (BCM 번호) ──
PIN_TRIG = 23           # 투입 감지 초음파 TRIG
PIN_ECHO = 24           # 투입 감지 초음파 ECHO (저항으로 3.3V 분배)
PIN_IR = {              # 칸별 IR 장애물 센서 (참=가득)
    "plastic": 17,
    "can": 27,
    "general": 22,
}

# ── 동작 파라미터 ──
TRIGGER_CM = 12         # 투입구 거리가 이보다 가까우면 "넣었다"로 판단 (빈 상태 거리-3)
MIN_CONF = 0.70         # 확신이 이보다 낮으면 일반쓰레기로 (안전 로직)

# ── Supabase (웹 대시보드용). 환경변수로 주입, 코드에 키 하드코딩 금지 ──
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
