"""Helpers for driving PyBeam QA worksheets from tests, the way a user does: add files, tick them, press Analyze, wait."""
import os
from contextlib import contextmanager
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog

from ui.util_widgets.statusbar import AnalysisInfoLabel

DONE = (AnalysisInfoLabel.COMPLETE, AnalysisInfoLabel.FAILED)
TIMEOUT_MS = 180_000
AS1200_PIXEL_MM = 0.336   # pylinac's AS1200 simulator at SID 1000 mm (magnification 1)
SHOTS = os.environ.get("PYBEAM_SHOTS")  # optional folder for window screenshots


@contextmanager
def file_dialog_returns(paths):
    """Stand in for the file dialog, for worksheets whose add_files() always asks (e.g. Field Analysis)."""
    original = QFileDialog.getOpenFileNames
    QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: ([str(p) for p in paths], ""))
    try:
        yield
    finally:
        QFileDialog.getOpenFileNames = original


def run_worksheet(qtbot, window_cls, files, configure=None, timeout_ms=TIMEOUT_MS):
    """Open a test window, load `files` as the File menu would, tick them, press Analyze and wait for the outcome.
    Returns (window, worksheet)."""
    win = window_cls()
    qtbot.addWidget(win)
    ws = win.ui.tabWidget.currentWidget()
    if configure:
        configure(ws)
    try:
        ws.add_files([str(f) for f in files])
    except TypeError:  # add_files() takes no paths: answer its dialog instead
        with file_dialog_returns(files):
            ws.add_files()
    for i in range(ws.ui.imageListWidget.count()):
        ws.ui.imageListWidget.item(i).setCheckState(Qt.Checked)
    assert ws.ui.analyzeBtn.isEnabled(), "ticking the images should enable Analyze"
    with qtbot.waitSignal(ws.analysis_info_signal, timeout=timeout_ms,
                          check_params_cb=lambda info: info["state"] in DONE):
        qtbot.mouseClick(ws.ui.analyzeBtn, Qt.LeftButton)
    return win, ws


def wl_images(folder, **offsets):
    """Four gantry images (0/90/180/270) from pylinac's generator, BB 5 mm, field 20x20 mm, no noise (deterministic).
    offsets: offset_mm_left / offset_mm_in / offset_mm_up."""
    from pylinac.core.image_generator import AS1200Image, FilteredFieldLayer, GaussianFilterLayer, generate_winstonlutz
    names = generate_winstonlutz(AS1200Image(sid=1000), FilteredFieldLayer, dir_out=str(folder), field_size_mm=(20, 20),
                                 final_layers=[GaussianFilterLayer(sigma_mm=1)], bb_size_mm=5, **offsets)
    return [Path(folder) / n for n in names]  # the generator returns bare file names


def field_image(path, slope_x=0.0, slope_y=0.0, size_mm=100):
    """An open field from pylinac's generator, optionally tilted (non-zero flatness/symmetry); deterministic."""
    from pylinac.core.image_generator import AS1200Image, FilteredFieldLayer, GaussianFilterLayer, SlopeLayer
    sim = AS1200Image(sid=1000)
    sim.add_layer(FilteredFieldLayer(field_size_mm=(size_mm, size_mm)))
    if slope_x or slope_y:
        sim.add_layer(SlopeLayer(slope_x=slope_x, slope_y=slope_y))
    sim.add_layer(GaussianFilterLayer(sigma_mm=2))
    sim.generate_dicom(str(path), gantry_angle=0)
    return Path(path)


def snap_to_pixels(mm, pixel_mm=AS1200_PIXEL_MM):
    """pylinac's image generator places layers on whole pixels, so a planted offset of `mm` is really this."""
    return round(mm / pixel_mm) * pixel_mm


def save_shot(widget, name):
    if SHOTS:
        Path(SHOTS).mkdir(parents=True, exist_ok=True)
        widget.resize(1400, 900)
        widget.grab().save(str(Path(SHOTS) / f"{name}.png"))


def field_metrics(ws):
    """Numbers the Field Analysis worksheet computed (from the pylinac object it holds), with CAX offsets derived
    the way a physicist reads them: +x = beam centre right of CAX, +y = beam centre below CAX (image rows)."""
    r = ws.current_results["field_analysis_obj"].results_data(as_dict=True)
    out = {k: r[k] for k in ("field_size_vertical_mm", "field_size_horizontal_mm", "left_penumbra_mm",
                             "right_penumbra_mm", "top_penumbra_mm", "bottom_penumbra_mm")}
    out["cax_offset_x_mm"] = (r["cax_to_right_mm"] - r["cax_to_left_mm"]) / 2
    out["cax_offset_y_mm"] = (r["cax_to_bottom_mm"] - r["cax_to_top_mm"]) / 2
    for k, v in r["protocol_results"].items():
        out[k] = v
    return out
