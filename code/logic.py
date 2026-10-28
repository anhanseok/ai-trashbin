"""
수거함 판단 규칙 (하드웨어 없음 → tests/ 에서 그대로 시험).
용어는 CONTEXT.md 기준: 품목, 칸, 확신도.
"""
import config as C


def choose_compartment(label, confidence):
    """판정 결과로 넣을 칸을 고른다. 넣지 않을 때(빈 받침판, 모르는 라벨)는 None.
    확신도가 MIN_CONF 미만이면 판정과 상관없이 일반 칸 (재활용 칸 오염 방지)."""
    if label not in C.BINS:
        return None
    if confidence < C.MIN_CONF:
        return "general"
    return label


class ArrivalDetector:
    """카메라만으로 투입 감지: empty 가 아닌 같은 판정이 DETECT_CONF 이상으로 2번 연속 나오면 투입."""

    def __init__(self):
        self.prev = None

    def update(self, label, confidence):
        """새 판정 하나를 넣는다. 투입으로 확정되면 True."""
        if label == "empty" or confidence < C.DETECT_CONF:
            self.prev = None
            return False
        if label == self.prev:
            self.prev = None                  # 같은 물건으로 두 번 확정되지 않게 초기화
            return True
        self.prev = label
        return False


class SensorFilter:
    """가득참 IR 센서 하나의 값을 거른다. 같은 값이 hold 초 이상 유지돼야 바뀐 것으로 본다.
    떨어지는 쓰레기가 센서 앞을 잠깐 지나가거나, 쌓인 쓰레기가 흔들려 깜빡이는 것을 무시한다."""

    def __init__(self, hold):
        self.hold = hold
        self.reported = None      # 마지막으로 기록한 값
        self.pending = None       # 바뀌는 중인 값
        self.since = None         # pending 이 시작된 시각

    def start(self, raw):
        """켤 때 현재 값. 웹이 시작 상태를 알도록 바로 기록할 값을 돌려준다."""
        self.reported = raw
        return raw

    def update(self, raw, now):
        """새로 읽은 값. 기록해야 할 변화가 확정되면 그 값을, 아니면 None."""
        if raw == self.reported:
            self.pending = None
            return None
        if raw != self.pending:
            self.pending, self.since = raw, now
        if now - self.since >= self.hold:
            self.reported, self.pending = raw, None
            return raw
        return None
