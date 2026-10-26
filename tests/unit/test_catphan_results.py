"""The CatPhan result adapter against stored pylinac results (docs/results-stability.md, "adapter layer").

data/catphan*_pylinac-<version>.json are pylinac's own results_data(as_json=True) for its public CatPhan demo series.
When a new pylinac version is supported, add its samples here: if pylinac reshaped its results, these tests fail at unit
level with a clear message, instead of the worksheet silently showing nothing.
"""
import copy
import json
from pathlib import Path

import pytest

from core.results import ResultShapeError
from core.results.catphan import SCHEMA_VERSION, from_pylinac

DATA = Path(__file__).parent / "data"
SAMPLES = sorted(DATA.glob("catphan*_pylinac-*.json"))

# What results_data() does not carry: pylinac's default tolerances, and each demo series' nominal slice thickness
# (pylinac's ctp404.slice_thickness, measured on the VM with pylinac 3.49.0).
NOMINAL_THICKNESS_MM = {"catphan503": 1.0, "catphan604": 1.98972451686859}


def convert(name_or_data, sample="catphan604", low_contrast_required=1, scaling=1.0, thickness=0.2):
    data = load(name_or_data) if isinstance(name_or_data, str) else name_or_data
    return from_pylinac(data, low_contrast_required=low_contrast_required, scaling_tolerance_mm=scaling,
                        thickness_tolerance_mm=thickness, nominal_slice_thickness_mm=NOMINAL_THICKNESS_MM[sample])


def load(name):
    return json.loads((DATA / name).read_text())


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda p: p.stem)
def test_every_stored_sample_converts(sample):
    result = convert(json.loads(sample.read_text()), sample=sample.stem.split("_")[0])
    assert result.schema_version == SCHEMA_VERSION
    assert result.hu_materials and result.uniformity_rois and result.mtf_lp_mm
    assert {c.name for c in result.checks} >= {"HU linearity", "Geometry (scaling)", "Slice thickness", "Uniformity"}


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda p: p.stem)
def test_decisions_agree_with_pylinac_away_from_the_boundary(sample):
    """On pylinac's demo series no value sits at a tolerance, so PyBeam's decisions and pylinac's flags must agree."""
    result = convert(json.loads(sample.read_text()), sample=sample.stem.split("_")[0])
    assert result.disagreements_with_pylinac == ()


def test_catphan604_demo():
    r = convert("catphan604_pylinac-3.49.0.json")
    assert r.phantom_model == "604" and r.num_images == 93 and r.origin_slice == 47
    assert len(r.hu_materials) == 9
    assert {m.name for m in r.hu_materials if not m.passed} == {"50% Bone", "Teflon"}
    assert [c.name for c in r.failed_checks] == ["HU linearity"]
    assert r.passed is False and r.outcome == "FAIL"   # +44 and -55 HU against 40: clear failures, not borderline
    assert r.low_contrast_available and r.low_contrast_rois_seen == 1 and r.low_contrast_passed is True
    assert r.thickness_decision.decided_value == pytest.approx(0.18)   # 1.81 measured, 1.99 nominal
    assert r.mtf(50) == pytest.approx(0.43706628770310424)


def test_low_contrast_requirement_is_applied():
    assert convert("catphan604_pylinac-3.49.0.json", low_contrast_required=2).low_contrast_passed is False  # 1 seen


def test_catphan503_demo_has_no_low_contrast_and_partial_mtf():
    r = convert("catphan503_pylinac-3.49.0.json", sample="catphan503")
    assert r.phantom_model == "503"
    assert r.low_contrast_available is False and r.low_contrast_passed is None
    assert "Low contrast" not in {c.name for c in r.checks}
    assert r.mtf(50) is None and r.mtf(90) is not None   # pylinac 3.49 resolves only 70-90 % on this series


def test_a_value_at_the_hu_tolerance_passes_as_borderline():
    """Teflon is -55 HU from nominal: at a 55 HU tolerance it passes (the tolerance itself passes), flagged borderline."""
    data = copy.deepcopy(load("catphan604_pylinac-3.49.0.json"))
    data["ctp404"]["hu_tolerance"] = 55
    r = convert(data)
    teflon = next(m for m in r.hu_materials if m.name == "Teflon")
    assert teflon.decision.outcome == "PASS (borderline)"
    assert r.outcome == "PASS (borderline)"


@pytest.mark.parametrize("distance_mm, outcome", [(51.0, "PASS (borderline)"), (51.004, "PASS (borderline)"),
                                                  (51.006, "FAIL (borderline)"), (51.2, "FAIL"), (50.5, "PASS")])
def test_geometry_is_decided_at_0_01_mm_with_the_tolerance_passing(distance_mm, outcome):
    """pylinac fails a node distance of exactly 50 +/- 1 mm (strict <); PyBeam decides at 0.01 mm and passes the
    tolerance itself, flagging it borderline (core/criteria.py)."""
    data = copy.deepcopy(load("catphan604_pylinac-3.49.0.json"))
    data["ctp404"]["line_distances_mm"] = [distance_mm, 50.0, 50.0, 50.0]
    check = next(c for c in convert(data).checks if c.name == "Geometry (scaling)")
    assert check.outcome == outcome


def test_reshaped_results_fail_loudly():
    data = copy.deepcopy(load("catphan604_pylinac-3.49.0.json"))
    del data["ctp404"]["hu_rois"]
    with pytest.raises(ResultShapeError, match=r"ctp404\.hu_rois"):
        convert(data)
