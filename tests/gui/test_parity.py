"""Parity tests: what a worksheet computed must equal a direct pylinac call on the same file with the settings the
user chose in that worksheet. Version-independent: pylinac drift moves both sides together. A mismatch means PyBeam's
plumbing is wrong (a setting not passed on, the wrong field read, a unit slip). See docs/results-stability.md."""
import math

import pytest

from helpers import field_image, run_worksheet, wl_images

EXACT = dict(rel_tol=1e-9, abs_tol=1e-9)


def numeric_results(results_data: dict) -> dict:
    out = {k: v for k, v in results_data.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
    out.update({f"protocol.{k}": v for k, v in results_data.get("protocol_results", {}).items()})
    return out


def pylinac_field_kwargs(ws) -> dict:
    """The Field Analysis settings exactly as the user set them in the worksheet, in pylinac's terms."""
    u = ws.ui
    return dict(protocol=ws.DEFAULT_PROTOCOLS[u.protocolCB.currentText()],
                centering=ws.CENTERING[u.centeringCB.currentText()],
                vert_position=u.vertPosDSB.value(), horiz_position=u.horPosDSB.value(),
                normalization_method=ws.NORMALIZATION[u.normalizationCB.currentText()],
                edge_detection_method=ws.EDGE_DETECTION[u.edgeDetCB.currentText()],
                edge_smoothing_ratio=u.edgeSmoothDSB.value(), hill_window_ratio=u.hillWinRatioDSB.value(),
                interpolation=ws.INTERPOLATION[u.interpolationCB.currentText()],
                interpolation_resolution_mm=u.interpolationResDSB.value(),
                in_field_ratio=u.inFieldRatioDSB.value(), slope_exclusion_ratio=u.slopeExclRatioDSB.value(),
                is_FFF=u.fffBeamCheckB.isChecked(), invert=u.invertImageCheckB.isChecked(),
                ground=u.groundCheckB.isChecked())


FIELD_SETTINGS = [
    pytest.param(lambda u: None, id="defaults"),
    pytest.param(lambda u: u.protocolCB.setCurrentText("Elekta"), id="protocol-elekta"),
    pytest.param(lambda u: u.protocolCB.setCurrentText("Siemens"), id="protocol-siemens"),
    pytest.param(lambda u: u.centeringCB.setCurrentText("Geometric center"), id="centering-geometric"),
    pytest.param(lambda u: u.edgeDetCB.setCurrentText("Inflection Derivative"), id="edge-inflection-derivative"),
    pytest.param(lambda u: u.normalizationCB.setCurrentText("Max"), id="normalization-max"),
    pytest.param(lambda u: u.interpolationCB.setCurrentText("Spline"), id="interpolation-spline"),
    pytest.param(lambda u: u.inFieldRatioDSB.setValue(0.7), id="in-field-ratio-0.7"),
    pytest.param(lambda u: u.slopeExclRatioDSB.setValue(0.3), id="slope-exclusion-0.3"),
    pytest.param(lambda u: u.interpolationResDSB.setValue(0.5), id="interpolation-resolution-0.5",
                 marks=pytest.mark.xfail(strict=True, reason="the worksheet never passes interpolationResDSB to "
                                                             "QFieldAnalysisWorker (field_analysis_widgets.py "
                                                             "start_analysis), so the setting has no effect")),
]


@pytest.mark.parametrize("change", FIELD_SETTINGS)
def test_field_analysis_matches_pylinac(qtbot, tmp_path, change):
    from pylinac.field_analysis import FieldAnalysis
    from ui.linac_qa.field_analysis_widgets import FieldAnalysisMainWindow
    image = field_image(tmp_path / "field.dcm", slope_x=0.05, slope_y=-0.03)
    _, ws = run_worksheet(qtbot, FieldAnalysisMainWindow, [image], lambda w: change(w.ui))
    gui = numeric_results(ws.current_results["field_analysis_obj"].results_data(as_dict=True))
    direct = FieldAnalysis(str(image))
    direct.analyze(**pylinac_field_kwargs(ws))
    ref = numeric_results(direct.results_data(as_dict=True))
    differ = {k: (gui.get(k), v) for k, v in ref.items() if not math.isclose(gui.get(k, math.nan), v, **EXACT)}
    assert not differ, f"GUI vs direct pylinac (gui, pylinac): {differ}"


def test_winston_lutz_matches_pylinac(qtbot, tmp_path):
    """PyBeam's QWinstonLutz overrides pylinac's analyze() (core/analysis/wlutz.py), so this is a real check."""
    from pylinac import WinstonLutz
    from ui.linac_qa.winston_lutz_widgets import WinstonLutzMainWindow
    files = wl_images(tmp_path, offset_mm_left=1.0, offset_mm_in=0.5, offset_mm_up=-0.5)
    _, ws = run_worksheet(qtbot, WinstonLutzMainWindow, files, lambda w: w.ui.bb_size_dsb.setValue(5.0))
    direct = WinstonLutz([str(f) for f in files])
    direct.analyze(bb_size_mm=5.0)
    ref = direct.results_data(as_dict=True)
    gui = ws.current_results
    for key in ("max_2d_cax_to_bb_mm", "median_2d_cax_to_bb_mm", "gantry_3d_iso_diameter_mm"):
        assert gui[key] == pytest.approx(ref[key], rel=1e-9, abs=1e-9), key
    for axis in "xyz":
        assert gui["bb_shift_vector"][axis] == pytest.approx(ref["bb_shift_vector"][axis], rel=1e-9, abs=1e-9), axis
