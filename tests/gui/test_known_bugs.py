"""Known bugs, written as strict expected failures. Each states the correct behaviour; when the bug is fixed the test
XPASSes, pytest reports it (strict=True turns that into a failure), and the marker should be removed.

Two groups:
- PyBeam QA itself: none open. The two found while writing these tests are fixed on integ/docs-catphan-ci, and
  their tests now pass where they belong (test_failure_paths.py: an unreadable Winston-Lutz file; test_parity.py:
  the Field Analysis interpolation resolution).
- the linac-dicom-image-suite (FauxPID) reference images: these are problems in the *test data*, recorded so nobody
  mistakes them for PyBeam errors.
"""
import pytest

from helpers import field_metrics, run_worksheet


# --- linac-dicom-image-suite reference images -------------------------------------------------------------------

@pytest.mark.xfail(strict=True, reason="suite bug: field_size_plus_* images also carry rotation=5 (create_image.py "
                                       "263/279/295): measured 110.63/105.24/101.88 x 100.5 mm instead of "
                                       "110/105/101 x 100 mm")
@pytest.mark.parametrize("stem, width_mm", [("field_size_plus_10_mm_10x10", 110), ("field_size_plus_5_mm_10x10", 105),
                                             ("field_size_plus_1_mm_10x10", 101)])
def test_suite_plus_field_sizes(qtbot, fauxpid_images, stem, width_mm):
    """Truth: width as named, height 100 mm. The analysis itself is good to about 0.15 mm on this suite's
    unrotated fields (realistic 10x10 measures 100.14 mm), hence the 0.2 mm tolerance."""
    from ui.linac_qa.field_analysis_widgets import FieldAnalysisMainWindow
    _, ws = run_worksheet(qtbot, FieldAnalysisMainWindow, [fauxpid_images / "Field Size" / f"{stem}.dcm"])
    m = field_metrics(ws)
    assert m["field_size_horizontal_mm"] == pytest.approx(width_mm, abs=0.2)
    assert m["field_size_vertical_mm"] == pytest.approx(100, abs=0.2)


@pytest.mark.xfail(strict=True, reason="suite bug: 1mm_right gantry_180 and gantry_225 are tagged gantry_angle=45 "
                                       "(create_image.py 1679/1718), so pylinac reconstructs the wrong 3D position")
def test_suite_wl_one_mm_right(qtbot, fauxpid_images):
    from ui.linac_qa.winston_lutz_widgets import WinstonLutzMainWindow
    files = sorted((fauxpid_images / "Winston-Lutz" / "1mm_right").glob("*.dcm"))
    _, ws = run_worksheet(qtbot, WinstonLutzMainWindow, files,
                          lambda w: (w.ui.bb_size_dsb.setValue(6.0), w.ui.toleranceDSB.setValue(1.0)))
    shift = ws.current_results["bb_shift_vector"]
    assert shift["x"] == pytest.approx(-1.0, abs=0.1) and abs(shift["z"]) < 0.1


@pytest.mark.xfail(strict=True, reason="suite convention: its vertical axis comes back with the opposite sign to "
                                       "pylinac's own generator (z=+6 is reported as shift z=+6, where pylinac's up=+6 "
                                       "gives -6); either the suite's z means 'down' or its gantry projection is flipped")
def test_suite_wl_complex_vertical_sign(qtbot, fauxpid_images):
    from ui.linac_qa.winston_lutz_widgets import WinstonLutzMainWindow
    files = sorted((fauxpid_images / "Winston-Lutz" / "complex (2, 3, 6)").glob("*.dcm"))
    _, ws = run_worksheet(qtbot, WinstonLutzMainWindow, files,
                          lambda w: (w.ui.bb_size_dsb.setValue(6.0), w.ui.toleranceDSB.setValue(1.0)))
    assert ws.current_results["bb_shift_vector"]["z"] == pytest.approx(-6.0, abs=0.2)
