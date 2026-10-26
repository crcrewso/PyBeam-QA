"""The CatPhan (CT/CBCT) tool, driven like a user would, on pylinac's public CatPhan demo series.

pylinac downloads its demo files on first use (pylinac.core.io.retrieve_demo_file) and caches them in its package;
without network access and without a cached copy these tests skip.
"""
import zipfile

import pytest
from PySide6.QtCore import Qt

from helpers import DONE, TIMEOUT_MS, run_worksheet, save_shot
from ui.util_widgets.statusbar import AnalysisInfoLabel


def demo(name):
    from pylinac.core.io import retrieve_demo_file
    try:
        return retrieve_demo_file(name)
    except Exception as err:  # offline and not cached
        pytest.skip(f"pylinac demo file {name} unavailable: {err}")


def catphan_config(phantom, hu_tolerance=40.0):
    def configure(ws):
        ws.ui.phantomCB.setCurrentText(phantom)
        ws.ui.huToleranceDSB.setValue(hu_tolerance)
    return configure


def run_catphan(qtbot, source, phantom, hu_tolerance=40.0):
    from ui.linac_qa.catphan_widgets import CatPhanMainWindow
    return run_worksheet(qtbot, CatPhanMainWindow, [source], catphan_config(phantom, hu_tolerance), timeout_ms=TIMEOUT_MS)


# --- truth: pylinac's documented demo outcome ---------------------------------------------------------------------

def test_catphan604_demo_fails_hu_linearity_on_bone_and_teflon(qtbot):
    win, ws = run_catphan(qtbot, demo("CatPhan604.zip"), "CatPhan 604")
    save_shot(win, "catphan604-hu40")
    assert ws.analysis_state == AnalysisInfoLabel.COMPLETE, ws.analysis_message
    result = ws.analysis_data["result"]
    assert {m.name for m in result.hu_materials if not m.passed} == {"50% Bone", "Teflon"}
    assert [c.name for c in result.failed_checks] == ["HU linearity"]
    assert ws.ui.outcomeLE.text() == "FAIL"
    assert ws.hu_table.rowCount() == 9


def test_catphan604_hu_tolerance_setting_is_honoured(qtbot):
    _, ws = run_catphan(qtbot, demo("CatPhan604.zip"), "CatPhan 604", hu_tolerance=60.0)
    assert ws.analysis_data["result"].hu_tolerance == 60.0
    assert ws.ui.outcomeLE.text() == "PASS"


# --- parity: the worksheet equals a direct pylinac call with its settings ------------------------------------------

@pytest.mark.parametrize("zip_name, phantom", [("CatPhan503.zip", "CatPhan 503"), ("CatPhan600.zip", "CatPhan 600"),
                                               ("CatPhan604.zip", "CatPhan 604")])
def test_catphan_matches_pylinac(qtbot, zip_name, phantom):
    from core.analysis.catphan import PHANTOMS, result_from
    source = demo(zip_name)
    _, ws = run_catphan(qtbot, source, phantom)
    assert ws.analysis_state == AnalysisInfoLabel.COMPLETE, ws.analysis_message
    params = ws.analysis_parameters()
    direct = PHANTOMS[phantom].from_zip(str(source))
    direct.analyze(**params, origin_slice=ws.origin_slice())
    expected = result_from(direct, params)
    assert ws.analysis_data["result"] == expected
    assert expected.disagreements_with_pylinac == ()   # no demo value sits at a tolerance
    assert ws.ui.outcomeLE.text() == expected.outcome


# --- input forms and failure paths ------------------------------------------------------------------------------

def test_catphan_folder_input_gives_the_same_result_as_the_zip(qtbot, tmp_path):
    from ui.linac_qa.catphan_widgets import CatPhanMainWindow
    source = demo("CatPhan604.zip")
    zipfile.ZipFile(source).extractall(tmp_path / "series")
    _, from_zip = run_catphan(qtbot, source, "CatPhan 604")

    win = CatPhanMainWindow()
    qtbot.addWidget(win)
    ws = win.ui.tabWidget.currentWidget()
    catphan_config("CatPhan 604")(ws)
    ws.add_folder(str(tmp_path / "series"))
    ws.ui.imageListWidget.item(0).setCheckState(Qt.Checked)
    with qtbot.waitSignal(ws.analysis_info_signal, timeout=TIMEOUT_MS, check_params_cb=lambda d: d["state"] in DONE):
        qtbot.mouseClick(ws.ui.analyzeBtn, Qt.LeftButton)
    assert ws.analysis_state == AnalysisInfoLabel.COMPLETE, ws.analysis_message
    assert ws.analysis_data["result"] == from_zip.analysis_data["result"]


def test_catphan_wrong_phantom_fails_cleanly(qtbot):
    """604 data analysed as a 503: pylinac refuses, and the worksheet must say so - FAILED with the reason - rather than
    hang (contrast with the Winston-Lutz bug in test_known_bugs.py)."""
    _, ws = run_catphan(qtbot, demo("CatPhan604.zip"), "CatPhan 503")
    assert ws.analysis_state == AnalysisInfoLabel.FAILED
    assert "scan extent does not match" in ws.analysis_message
    assert ws.ui.analyzeBtn.isEnabled() and ws.ui.outcomeLE.text() == ""


def test_catphan_missing_input_fails_cleanly(qtbot, tmp_path):
    _, ws = run_catphan(qtbot, tmp_path / "missing.zip", "CatPhan 604")
    assert ws.analysis_state == AnalysisInfoLabel.FAILED
    assert "missing.zip" in ws.analysis_message


def test_catphan_report_is_written(qtbot, tmp_path):
    _, ws = run_catphan(qtbot, demo("CatPhan604.zip"), "CatPhan 604")
    pdf = tmp_path / "catphan604.pdf"
    ws.write_report(str(pdf), author="Test", institution="Test", treatment_unit="Test", comments="test")
    data = pdf.read_bytes()
    assert data.startswith(b"%PDF") and len(data) > 20_000
    pypdf = pytest.importorskip("pypdf")
    text = "".join(page.extract_text() for page in pypdf.PdfReader(str(pdf)).pages)
    for expected in ("CatPhan 604", "HU linearity", "Teflon", "pylinac version", ws.analysis_data["input_sha256"][:16]):
        assert expected in text, expected
