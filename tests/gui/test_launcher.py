"""The launcher: each card opens its tool, the way a user's click does (AppMainWin.eventFilter → open_window).
A new tool's card, its four registration edits and its window's construction are all exercised by one test row."""
import pytest
from PySide6.QtCore import QPoint, Qt

TOOLS = [  # (card object name in app_main_win.ui, qa_windows key, window class name)
    ("winstonLutzAnalysis", "winston_lutz", "WinstonLutzMainWindow"),
    ("picketFence", "picket_fence", "PicketFenceMainWindow"),
    ("starshotAnalysis", "starshot", "StarshotMainWindow"),
    ("fieldAnalysis", "field_analysis", "FieldAnalysisMainWindow"),
    ("planarImagingAnalysis", "planar_imaging_analysis", "PlanarImagingMainWindow"),
]


@pytest.fixture
def launcher(qtbot):
    from ui.app_main_win import AppMainWin
    win = AppMainWin()
    qtbot.addWidget(win)
    win.show()
    return win


@pytest.mark.parametrize("card, key, window_class", TOOLS)
def test_card_opens_its_tool(qtbot, launcher, card, key, window_class):
    qtbot.mouseClick(getattr(launcher._ui, card), Qt.LeftButton, Qt.NoModifier, QPoint(10, 10))
    window = launcher.qa_windows[key]
    assert window is not None, f"clicking {card} should open {window_class}"
    qtbot.addWidget(window)
    assert type(window).__name__ == window_class
    assert window.ui.tabWidget.count() == 1, "a new tool window starts with one worksheet"
    worksheet = window.ui.tabWidget.currentWidget()
    for attr in ("analysis_info_signal", "analysis_state", "analysis_message"):  # the QAToolsWindow contract
        assert hasattr(worksheet, attr), f"worksheet is missing {attr}"


@pytest.mark.parametrize("card", ["photonCalib", "electronCalib"])
def test_calibration_cards_switch_page(qtbot, launcher, card):
    before = launcher._ui.mainStackWidget.currentIndex()
    qtbot.mouseClick(getattr(launcher._ui, card), Qt.LeftButton, Qt.NoModifier, QPoint(10, 10))
    assert launcher._ui.mainStackWidget.currentIndex() != before
