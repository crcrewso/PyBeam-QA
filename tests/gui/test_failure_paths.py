"""A failed analysis must reach the worksheet as FAILED, with the UI usable again, never as a worksheet stuck at
"Analysis in progress…". The CatPhan tool's failure paths are in test_catphan.py."""
import pytest

from helpers import DONE
from ui.util_widgets.statusbar import AnalysisInfoLabel


@pytest.mark.qt_no_exception_capture  # QWinstonLutzWorker re-raises after emitting analysis_failed
def test_winston_lutz_unreadable_file_is_reported_as_failed(qtbot, tmp_path):
    """Was a known bug: the worker loaded the images in __init__, on the GUI thread and outside its try, so an
    unreadable file raised in the Analyze click handler and the worksheet stayed 'in progress'."""
    from PySide6.QtCore import Qt
    from ui.linac_qa.winston_lutz_widgets import WinstonLutzMainWindow
    win = WinstonLutzMainWindow()
    qtbot.addWidget(win)
    ws = win.ui.tabWidget.currentWidget()
    ws.add_files([str(tmp_path / "missing_G0.dcm"), str(tmp_path / "missing_G90.dcm")])
    for i in range(ws.ui.imageListWidget.count()):
        ws.ui.imageListWidget.item(i).setCheckState(Qt.Checked)
    with qtbot.waitSignal(ws.analysis_info_signal, timeout=10_000,
                          check_params_cb=lambda info: info["state"] in DONE):
        qtbot.mouseClick(ws.ui.analyzeBtn, Qt.LeftButton)
    assert ws.analysis_state == AnalysisInfoLabel.FAILED
    assert ws.ui.addImgBtn.isEnabled(), "the worksheet should be usable again after a failure"
    # let the worker thread end before the window is torn down (the thread deletes itself when it finishes)
    from shiboken6 import isValid
    qtbot.waitUntil(lambda: not isValid(ws.qthread) or ws.qthread.isFinished(), timeout=10_000)
