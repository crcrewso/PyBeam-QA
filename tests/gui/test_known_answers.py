"""Truth tests: synthetic images with a known answer are pushed through real PyBeam QA worksheets (files added, boxes
ticked, Analyze clicked) and what the worksheet computed and shows is checked against the planted truth.

Tolerances are the input's own uncertainty: pylinac's generator places layers on whole pixels (0.336 mm on the AS1200
simulator), so planted offsets are compared after snapping to the pixel grid. See docs/gui-testing-and-validation.md.

Two sources of images:
- pylinac's own generators (always available): Winston-Lutz BB offsets and a picket fence;
- linac-dicom-image-suite (package FauxPID; optional): CAX offset, field size, penumbra, symmetry and Winston-Lutz sets.
  Only sets whose stated truth matches PyBeam's definitions are used here; the others are in test_known_bugs.py or
  covered by parity and baseline tests instead.
"""
import pytest
from pylinac.core.image_generator import AS1200Image, FilteredFieldLayer, GaussianFilterLayer, generate_picketfence

from helpers import field_metrics, run_worksheet, save_shot, snap_to_pixels, wl_images
from ui.util_widgets.statusbar import AnalysisInfoLabel


def wl_config(bb_mm=5.0, tolerance_mm=1.0):
    def configure(ws):
        ws.ui.toleranceDSB.setValue(tolerance_mm)
        ws.ui.bb_size_dsb.setValue(bb_mm)
    return configure


# --- pylinac's generators -----------------------------------------------------------------------------------------

@pytest.mark.parametrize("bb_left_mm, expected", [(0.0, "PASS"), (0.5, "PASS"), (1.5, "FAIL")])
def test_winston_lutz_reports_a_known_bb_offset(qtbot, tmp_path, bb_left_mm, expected):
    from ui.linac_qa.winston_lutz_widgets import WinstonLutzMainWindow
    win, ws = run_worksheet(qtbot, WinstonLutzMainWindow, wl_images(tmp_path, offset_mm_left=bb_left_mm), wl_config())
    save_shot(win, f"wl-left-{bb_left_mm}mm")
    assert ws.analysis_state == AnalysisInfoLabel.COMPLETE, ws.analysis_message
    # A pure left/right shift is seen in full at gantry 0 and 180, so the largest 2D CAX-to-BB distance is the shift.
    assert ws.current_results["max_2d_cax_to_bb_mm"] == pytest.approx(bb_left_mm, abs=0.15)
    assert ws.ui.outcomeLE.text() == expected


def test_winston_lutz_shift_vector_follows_pylinac_axes(qtbot, tmp_path):
    """BB planted 2 mm left, 3 mm in, 6 mm up: the shift to bring it to isocentre is (+2, -3, -6) in pylinac's
    reporting (measured with pylinac 3.49: left -> +x, in -> -y, up -> -z)."""
    from ui.linac_qa.winston_lutz_widgets import WinstonLutzMainWindow
    files = wl_images(tmp_path, offset_mm_left=2, offset_mm_in=3, offset_mm_up=6)
    _, ws = run_worksheet(qtbot, WinstonLutzMainWindow, files, wl_config())
    shift = ws.current_results["bb_shift_vector"]
    assert (shift["x"], shift["y"], shift["z"]) == (pytest.approx(2, abs=0.15), pytest.approx(-3, abs=0.15),
                                                    pytest.approx(-6, abs=0.15))


def test_picket_fence_passes_a_perfect_fence(qtbot, tmp_path):
    """pylinac's generator can only shift whole pickets, and PicketFence fits each picket on its own, so a deliberate
    leaf error cannot be planted this way; the known answer here is 'no error'."""
    from ui.linac_qa.picket_fence_widgets import PicketFenceMainWindow
    image = tmp_path / "pf.dcm"
    generate_picketfence(AS1200Image(sid=1500), FilteredFieldLayer, file_out=str(image),
                         final_layers=[GaussianFilterLayer(sigma_mm=1)])
    win, ws = run_worksheet(qtbot, PicketFenceMainWindow, [image], lambda ws: ws.ui.toleranceDSB.setValue(0.5))
    save_shot(win, "pf-perfect")
    assert ws.analysis_state == AnalysisInfoLabel.COMPLETE, ws.analysis_message
    assert ws.current_results["picket_fence_obj"].max_error < 0.1
    assert ws.ui.outcomeLE.text() == "PASS"


# --- linac-dicom-image-suite (FauxPID) ------------------------------------------------------------------------------

CAX_TRUTHS = {  # image stem: (planted x offset, planted y offset) in mm; +x = right, +y = down (image rows)
    "cax_offset_10_mm_10x10": (10, 0), "cax_offset_5_mm_10x10": (5, 0), "cax_offset_1_mm_10x10": (1, 0),
    "cax_offset_minus_3_mm_x_10x10": (-3, 0), "cax_offset_minus_1_mm_y_10x10": (0, -1),
    "cax_offset_5_mm_y_10x10": (0, 5), "cax_offset_7_mm_x_and_y_10x10": (7, 7),
}


@pytest.mark.parametrize("stem", sorted(CAX_TRUTHS))
def test_field_analysis_reports_known_cax_offset(qtbot, fauxpid_images, stem):
    from ui.linac_qa.field_analysis_widgets import FieldAnalysisMainWindow
    _, ws = run_worksheet(qtbot, FieldAnalysisMainWindow, [fauxpid_images / "CAX Offset" / f"{stem}.dcm"])
    assert ws.analysis_state == AnalysisInfoLabel.COMPLETE, ws.analysis_message
    m = field_metrics(ws)
    x, y = CAX_TRUTHS[stem]
    assert m["cax_offset_x_mm"] == pytest.approx(snap_to_pixels(x), abs=0.05)
    assert m["cax_offset_y_mm"] == pytest.approx(snap_to_pixels(y), abs=0.05)


@pytest.mark.parametrize("stem, size_mm", [("field_size_perfect_10x10", 100), ("field_size_realistic_10x10", 100),
                                            ("field_size_realistic_20x20", 200)])
def test_field_analysis_reports_known_field_size(qtbot, fauxpid_images, stem, size_mm):
    from ui.linac_qa.field_analysis_widgets import FieldAnalysisMainWindow
    _, ws = run_worksheet(qtbot, FieldAnalysisMainWindow, [fauxpid_images / "Field Size" / f"{stem}.dcm"])
    m = field_metrics(ws)
    assert m["field_size_horizontal_mm"] == pytest.approx(size_mm, abs=0.4)
    assert m["field_size_vertical_mm"] == pytest.approx(size_mm, abs=0.4)


@pytest.mark.parametrize("stem, penumbra_mm", [("penumbra_1_mm", 1.0), ("penumbra_2_mm", 2.0), ("penumbra_10_mm", 10.0)])
def test_field_analysis_reports_known_penumbra(qtbot, fauxpid_images, stem, penumbra_mm):
    """The set's names are 20-80 % penumbra widths (Gaussian edge sigma x 1.68), which is pylinac's default penumbra."""
    from ui.linac_qa.field_analysis_widgets import FieldAnalysisMainWindow
    _, ws = run_worksheet(qtbot, FieldAnalysisMainWindow, [fauxpid_images / "Penumbra" / f"{stem}.dcm"])
    m = field_metrics(ws)
    for side in ("left", "right", "top", "bottom"):
        assert m[f"{side}_penumbra_mm"] == pytest.approx(penumbra_mm, abs=0.2), side


def test_field_analysis_reports_known_point_difference_symmetry(qtbot, fauxpid_images):
    """The one 'two percent' image whose definition matches PyBeam's default (Varian) protocol: point-difference
    symmetry. The suite's other 'two percent' images use other definitions (see docs/gui-testing-and-validation.md)."""
    from ui.linac_qa.field_analysis_widgets import FieldAnalysisMainWindow
    image = fauxpid_images / "Symmetry" / "symmetry_two_percent_x_cax_point_difference_10x10.dcm"
    _, ws = run_worksheet(qtbot, FieldAnalysisMainWindow, [image])
    m = field_metrics(ws)
    assert m["symmetry_horizontal"] == pytest.approx(2.0, abs=0.1)
    assert m["symmetry_vertical"] == pytest.approx(0.0, abs=0.05)


def test_winston_lutz_perfect_set_passes(qtbot, fauxpid_images):
    from ui.linac_qa.winston_lutz_widgets import WinstonLutzMainWindow
    files = sorted((fauxpid_images / "Winston-Lutz" / "perfect").glob("*.dcm"))
    _, ws = run_worksheet(qtbot, WinstonLutzMainWindow, files, wl_config(bb_mm=6.0))
    assert ws.current_results["max_2d_cax_to_bb_mm"] < 0.1
    assert ws.ui.outcomeLE.text() == "PASS"


def test_winston_lutz_one_mm_out(qtbot, fauxpid_images):
    """BB 1 mm out (away from the gantry): pylinac's shift brings it back in, +1 mm in y."""
    from ui.linac_qa.winston_lutz_widgets import WinstonLutzMainWindow
    files = sorted((fauxpid_images / "Winston-Lutz" / "1mm_out").glob("*.dcm"))
    _, ws = run_worksheet(qtbot, WinstonLutzMainWindow, files, wl_config(bb_mm=6.0))
    shift = ws.current_results["bb_shift_vector"]
    assert shift["y"] == pytest.approx(1.0, abs=0.1)
    assert abs(shift["x"]) < 0.1 and abs(shift["z"]) < 0.1


def test_winston_lutz_outlier_image_inflates_gantry_isocentre(qtbot, fauxpid_images):
    """'outlier' is 'complex (2, 3, 6)' with one gantry image 5 mm off: the gantry isocentre size jumps by about 5 mm."""
    from ui.linac_qa.winston_lutz_widgets import WinstonLutzMainWindow
    sizes = {}
    for name in ("complex (2, 3, 6)", "outlier"):
        files = sorted((fauxpid_images / "Winston-Lutz" / name).glob("*.dcm"))
        _, ws = run_worksheet(qtbot, WinstonLutzMainWindow, files, wl_config(bb_mm=6.0))
        sizes[name] = ws.current_results["gantry_3d_iso_diameter_mm"]
    assert sizes["complex (2, 3, 6)"] < 0.2
    assert sizes["outlier"] == pytest.approx(5.0, abs=0.3)
