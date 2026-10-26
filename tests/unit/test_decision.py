"""The decision module (core/decision.py): one boundary rule, a stated resolution, and a borderline flag."""
import pytest

from core import criteria
from core.decision import Bound, Criterion, at_resolution, combine

WL = criteria.winston_lutz(1.0)
AS1200_PIXEL_MM = 0.336  # one AS1200 pixel at isocentre (SID 1000 mm)


@pytest.mark.parametrize("value, resolution, expected", [
    (1.005, 0.01, 1.01),    # half away from zero, in decimal: binary floating point would give 1.00
    (1.004, 0.01, 1.0),
    (-1.005, 0.01, -1.01),
    (44.5, 1, 45.0),
    (0.25, 0.5, 0.5),
])
def test_values_are_rounded_to_the_resolution_half_away_from_zero(value, resolution, expected):
    assert at_resolution(value, resolution) == expected


@pytest.mark.parametrize("value, passed", [(1.008, False), (1.004, True), (1.0, True), (0.999, True), (1.01, False)])
def test_decided_at_the_stated_resolution_with_the_tolerance_passing(value, passed):
    """docs/results-stability.md: 1.008 mm against 1.0 mm at a 0.01 mm resolution is FAIL; 1.004 mm is PASS."""
    assert WL.decide(value).passed is passed


@pytest.mark.parametrize("value, outcome", [
    (0.0, "PASS"), (0.5, "PASS"),              # more than a pixel inside the tolerance
    (0.7, "PASS (borderline)"), (1.0, "PASS (borderline)"),
    (1.01, "FAIL (borderline)"), (1.3, "FAIL (borderline)"),
    (1.5, "FAIL"),                             # more than a pixel outside
])
def test_winston_lutz_borderline_band_is_one_pixel_at_isocentre(value, outcome):
    assert WL.decide(value, step=AS1200_PIXEL_MM).outcome == outcome


def test_counts_have_no_borderline_band():
    low_contrast = criteria.catphan_low_contrast(2)
    assert low_contrast.bound is Bound.AT_LEAST
    assert low_contrast.decide(2).outcome == "PASS"
    assert low_contrast.decide(1).outcome == "FAIL"
    assert low_contrast.decide(3).outcome == "PASS"


def test_the_default_band_is_one_resolution_step():
    hu = criteria.catphan_hu(40)
    assert hu.decide(39).outcome == "PASS (borderline)"
    assert hu.decide(38).outcome == "PASS"
    assert hu.decide(41).outcome == "FAIL (borderline)"
    assert hu.decide(44).outcome == "FAIL"


def test_combining_decisions():
    c = Criterion("x", 1.0, 0.01, "mm", step=0.1)
    clear_pass, edge_pass, edge_fail, clear_fail = c.decide(0.5), c.decide(0.95), c.decide(1.05), c.decide(2.0)
    assert combine([clear_pass, clear_pass]) == (True, False)
    assert combine([clear_pass, edge_pass]) == (True, True)     # any borderline member makes a pass borderline
    assert combine([edge_fail, clear_pass]) == (False, True)    # every failure borderline: a borderline fail
    assert combine([edge_fail, clear_fail]) == (False, False)   # one clear failure: a clear fail


def test_a_decision_describes_its_rule():
    text = WL.decide(1.008, step=AS1200_PIXEL_MM).describe()
    assert text == "1.01 mm: FAIL (borderline) (at most 1 mm, decided at 0.01 mm)"
