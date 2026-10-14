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
