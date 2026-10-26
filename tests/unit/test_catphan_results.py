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


def load(name):
    return json.loads((DATA / name).read_text())


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda p: p.stem)
def test_every_stored_sample_converts(sample):
    result = from_pylinac(json.loads(sample.read_text()), low_contrast_required=1)
    assert result.schema_version == SCHEMA_VERSION
    assert result.hu_materials and result.uniformity_rois and result.mtf_lp_mm
    assert {c.name for c in result.checks} >= {"HU linearity", "Geometry (scaling)", "Slice thickness", "Uniformity"}


def test_catphan604_demo():
    r = from_pylinac(load("catphan604_pylinac-3.49.0.json"), low_contrast_required=1)
    assert r.phantom_model == "604" and r.num_images == 93 and r.origin_slice == 47
    assert len(r.hu_materials) == 9
    assert {m.name for m in r.hu_materials if not m.passed} == {"50% Bone", "Teflon"}
    assert [c.name for c in r.failed_checks] == ["HU linearity"]
    assert r.passed is False
    assert r.low_contrast_available and r.low_contrast_rois_seen == 1 and r.low_contrast_passed is True
    assert r.mtf(50) == pytest.approx(0.43706628770310424)


def test_low_contrast_requirement_is_applied():
    data = load("catphan604_pylinac-3.49.0.json")
    assert from_pylinac(data, low_contrast_required=2).low_contrast_passed is False   # 1 ROI seen, 2 required


def test_catphan503_demo_has_no_low_contrast_and_partial_mtf():
    r = from_pylinac(load("catphan503_pylinac-3.49.0.json"), low_contrast_required=1)
    assert r.phantom_model == "503"
    assert r.low_contrast_available is False and r.low_contrast_passed is None
    assert "Low contrast" not in {c.name for c in r.checks}
    assert r.mtf(50) is None and r.mtf(90) is not None   # pylinac 3.49 resolves only 70-90 % on this series


def test_reshaped_results_fail_loudly():
    data = copy.deepcopy(load("catphan604_pylinac-3.49.0.json"))
    del data["ctp404"]["hu_rois"]
    with pytest.raises(ResultShapeError, match=r"ctp404\.hu_rois"):
        from_pylinac(data, low_contrast_required=1)
