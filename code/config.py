"""
공통 설정. 핀 번호와 각도는 여기만 바꾸면 모든 코드에 반영됩니다.
※ 각도는 실물 조립 후 팀원(HW)이 실측해서 수정합니다.
"""
import os

# 같은 폴더의 .env 를 읽어 환경변수로 넣는다 (systemd 없이 python main.py 로 실행해도 키가 들어가게)
_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env):
    for _line in open(_env, encoding="utf-8"):
        _k, _sep, _v = _line.strip().partition("=")
        if _sep and not _k.startswith("#"):
            os.environ.setdefault(_k.strip(), _v.strip())

# ── 서보 (PCA9685 채널) ──
CH_PAN = 0          # 회전 서보
CH_TILT = 1         # 기울임 서보

# 3칸을 받침판 앞쪽 반원(180°) 안에 부채꼴로 배치 (칸 중심 15° / 90° / 165°, 서보 끝에 15° 여유)
# MG996R은 0~180°만 돌아가므로 칸을 반원 안에 두고, 기울임은 항상 앞으로 한 방향만 쓴다
TILT_HOME = 90      # 평소 수평
TILT_FWD = 160      # 앞으로 기울임 (10-21 실물 조립 기준 90보다 큰 쪽이 앞. 수평에서 70°)

# 설치 규칙: 서보①을 90°에 둔 상태에서, 받침판의 "앞으로 쏟는 쪽"이 일반 칸(가운데) 한가운데를 보게 혼을 끼움
BINS = {               # 이름: (회전 각도, 기울임 각도)
    "plastic": (15, TILT_FWD),    # 왼쪽 칸
    "general": (90, TILT_FWD),    # 가운데 칸
    "can": (165, TILT_FWD),       # 오른쪽 칸
}
PAN_HOME = 90

# ── 투입 감지 방식 ──
# False: 카메라만으로 감지 (초기 단계, 센서 없음)
# True : 초음파 센서로 감지 (나중에 HC-SR04 추가하면 True로)
USE_ULTRASONIC = False
DETECT_CONF = 0.60      # 카메라 감지: 이 확신 이상으로 2번 연속 같은 결과면 "넣었다"

# ── 핀 (BCM 번호) ──
PIN_TRIG = 23           # 투입 감지 초음파 TRIG
PIN_ECHO = 24           # 투입 감지 초음파 ECHO (저항으로 3.3V 분배)
PIN_IR = {              # 칸별 IR 장애물 센서 (참=가득)
    # 초기 단계에서는 빼고 진행. main.py는 빈 딕셔너리여도 그대로 동작함.
    # 나중에 추가할 때 아래 중 필요한 줄만 주석 해제 (코드 수정 불필요)
    # "general": 22,
    # "plastic": 17,
    # "can": 27,
}

# ── 동작 파라미터 ──
TRIGGER_CM = 12         # 투입구 거리가 이보다 가까우면 "넣었다"로 판단 (빈 상태 거리-3)
MIN_CONF = 0.70         # 확신이 이보다 낮으면 일반쓰레기로 (안전 로직)

# ── Supabase (웹 대시보드용). 환경변수로 주입, 코드에 키 하드코딩 금지 ──
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
BIN_ID = os.environ.get("BIN_ID", "bin-01")    # supabase/schema.sql 의 bins.id
HEARTBEAT_SEC = 30                              # 연결 신호 주기. 웹은 2분 넘게 없으면 "연결 끊김"
