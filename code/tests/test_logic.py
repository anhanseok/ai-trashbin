import pytest

import config as C
from logic import ArrivalDetector, choose_compartment


@pytest.mark.parametrize("label", ["plastic", "can", "general"])
def test_confident_item_goes_to_its_own_compartment(label):
    assert choose_compartment(label, 0.95) == label


@pytest.mark.parametrize("label", ["plastic", "can"])
def test_low_confidence_recyclable_goes_to_general(label):
    assert choose_compartment(label, C.MIN_CONF - 0.01) == "general"


def test_exactly_min_conf_is_trusted():
    assert choose_compartment("can", C.MIN_CONF) == "can"


@pytest.mark.parametrize("label", ["empty", "unknown"])
def test_empty_or_unknown_is_not_dropped(label):
    assert choose_compartment(label, 0.99) is None


def test_arrival_needs_two_same_confident_results_in_a_row():
    d = ArrivalDetector()
    assert d.update("can", 0.9) is False
    assert d.update("can", 0.9) is True


def test_arrival_resets_on_empty_or_weak_or_different():
    d = ArrivalDetector()
    d.update("can", 0.9)
    assert d.update("empty", 0.99) is False
    assert d.update("can", 0.9) is False            # empty 뒤라 다시 처음부터
    assert d.update("can", C.DETECT_CONF - 0.01) is False
    assert d.update("can", 0.9) is False            # 약한 판정 뒤라 다시 처음부터
    assert d.update("plastic", 0.9) is False        # 다른 품목
    assert d.update("plastic", 0.9) is True


def test_arrival_does_not_fire_twice_for_same_item():
    d = ArrivalDetector()
    d.update("can", 0.9)
    assert d.update("can", 0.9) is True
    assert d.update("can", 0.9) is False


# ── 가득참 센서 필터: HOLD 초 이상 같은 값이 유지돼야 기록 ──
from logic import SensorFilter


def test_filter_reports_start_value_immediately():
    f = SensorFilter(hold=3)
    assert f.start(False) is False


def test_falling_trash_passing_sensor_is_ignored():
    f = SensorFilter(hold=3)
    f.start(False)
    assert f.update(True, now=10.0) is None   # 떨어지는 쓰레기가 잠깐 가림
    assert f.update(False, now=10.1) is None  # 바로 지나감
    assert f.update(False, now=20.0) is None  # 기록할 변화 없음


def test_detection_held_for_hold_seconds_is_reported_once():
    f = SensorFilter(hold=3)
    f.start(False)
    assert f.update(True, now=10.0) is None
    assert f.update(True, now=12.9) is None
    assert f.update(True, now=13.0) is True
    assert f.update(True, now=20.0) is None   # 같은 값은 다시 보내지 않음


def test_clearing_also_needs_hold_seconds():
    f = SensorFilter(hold=3)
    f.start(True)
    assert f.update(False, now=5.0) is None   # 쓰레기가 잠깐 흔들려 비어 보임
    assert f.update(True, now=5.5) is None
    assert f.update(False, now=6.0) is None
    assert f.update(False, now=9.0) is False  # 3초 동안 계속 비어 있어야 기록
