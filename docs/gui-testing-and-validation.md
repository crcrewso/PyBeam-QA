# Testing and validating the PyBeam QA GUI

This guide is about checking that the GUI gives the right answers. It covers:

- **how** to drive PyBeam QA's real windows automatically, with no display, as a user would;
- **what with**: synthetic images whose answers are known, from pylinac's generators and from
  [linac-dicom-image-suite](https://github.com/crcrewso/linac-dicom-image-suite) (Python package `FauxPID`);
- **what was found** doing so in October 2026.

The runnable tests are in [`tests/gui/`](../tests/gui/README.md). Measured on a Linux VM (Ubuntu 24.04, Python 3.12,
PySide6 6.7.0, pylinac 3.49.0, pytest-qt 4.5.0), `pytest tests` (the GUI tests plus the CatPhan result-model unit
tests) takes about 150 s, most of it the CatPhan series:

| Outcome | Count | What they are |
|---|---|---|
| passed | 65 | |
| expected failures | 7 | each a known bug, kept as strict `xfail` so a fix is noticed |
| skipped | 16 | the described stubs for planned tests |

On a first run, before a baseline exists for the installed pylinac version, the 10 baseline tests skip as well. The
CatPhan tests use pylinac's demo series, which pylinac downloads on first use; they skip if it cannot.

---

## 1. Running the GUI headless

PySide6 runs without a display in two ways:

- **`QT_QPA_PLATFORM=offscreen`**: no X server at all. Widgets are created, laid out and painted into memory, and
  screenshots work (`widget.grab().save("x.png")`). This is what `tests/gui/conftest.py` sets by default.
- **Xvfb**: a virtual X display (`xvfb-run pytest tests/gui`). Use it to test things that need a real window
  system, or to watch via VNC.

Install the app's locked dependencies plus `pytest` and `pytest-qt`, all pinned: `pip install -r
tests/gui/requirements.txt` includes the app's `requirements.txt`. On Ubuntu,
the Qt xcb libraries are also needed (`libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 libxcb-image0
libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libegl1`) when using Xvfb.

PyBeam QA expects to start from the repository root, because of relative paths to `core/tools/list.json` and the
`ui/py_ui` imports. `conftest.py` does `os.chdir(REPO)` before anything imports the app.

## 2. Driving a worksheet the way a user does

Every tool's worksheet follows the same pattern (see `docs/adding-a-pylinac-test.md` §2.2), and that makes it
testable:

```python
win = WinstonLutzMainWindow(); qtbot.addWidget(win)
ws = win.ui.tabWidget.currentWidget()              # the first worksheet tab
ws.ui.toleranceDSB.setValue(1.0)                   # settings, exactly as the user would set them
ws.add_files([str(p) for p in images])             # what File ▸ Add Image(s) does after its dialog
for i in range(ws.ui.imageListWidget.count()):     # tick the images; this enables Analyze
    ws.ui.imageListWidget.item(i).setCheckState(Qt.Checked)
with qtbot.waitSignal(ws.analysis_info_signal, timeout=180_000,
                      check_params_cb=lambda d: d["state"] in (AnalysisInfoLabel.COMPLETE, AnalysisInfoLabel.FAILED)):
    qtbot.mouseClick(ws.ui.analyzeBtn, Qt.LeftButton)   # the real button, the real QThread
assert ws.analysis_state == AnalysisInfoLabel.COMPLETE
assert ws.ui.outcomeLE.text() == "PASS"           # what the user sees
```

`tests/gui/helpers.py::run_worksheet` wraps this. Three practical points:

1. **Wait on `analysis_info_signal`.** It is the one signal every worksheet emits on completion and on failure.
2. **Stub modal dialogs.** A failed analysis opens a modal `MessageDialog`, which would block an unattended run
   forever. `conftest.py` patches `MessageDialog.exec` to return at once. Other modal dialogs need the same treatment;
   the CatPhan branches use `exec_()`, so patch that too.
3. **Answer file dialogs.** Most worksheets take paths as `add_files(files=None)`. Field Analysis' `add_files()`
   always opens `QFileDialog`, so the helper patches `QFileDialog.getOpenFileNames` to return the files. The same
   technique works for any dialog-driven entry point.

**Launcher tests** (`test_launcher.py`) click each card on the main window and check that the right window class
opens with one worksheet meeting the contract. For a new tool, one row there checks the `.ui` card, the four
registration edits and the window's construction.

## 3. Three kinds of test

See [`results-stability.md`](results-stability.md) for why they are kept apart:

| | File | Expected value | Survives a pylinac upgrade? |
|---|---|---|---|
| **Truth** | `test_known_answers.py` | planted in a synthetic image | yes, unless the tool is wrong |
| **Parity** | `test_parity.py` | a direct pylinac call with the worksheet's settings | yes, unless PyBeam's plumbing is wrong |
| **Baseline** | `test_baselines.py` + `baselines/pylinac-<version>.json` | the last reviewed run on that pylinac version | no, by design: it turns drift into a review |

Plus two more:

- **Known bugs** (`test_known_bugs.py`): strict expected failures stating the *correct* behaviour.
- **Planned tests** (`test_planned_tools.py`): described stubs for every tool not yet built and every gap in the
  existing tests.

## 4. Sources of known-answer images

### pylinac's own generators (`pylinac.core.image_generator`)

Always available, with no randomness unless you add noise, and so deterministic.

| Generator | Planted truth | Used in |
|---|---|---|
| `generate_winstonlutz(simulator, field_layer, dir_out, …, offset_mm_left/in/up, image_axes)` | BB offset in 3D | truth, parity, baseline. **Returns bare file names; join them with `dir_out`** |
| `generate_picketfence(…, picket_offset_error=…)` | Whole-picket offsets only. PicketFence fits each picket separately, so a leaf error cannot be planted this way; use the perfect fence as "no error" | truth (PASS), baseline |
| `generate_winstonlutz_multi_bb_*`, `generate_winstonlutz_cone`, `generate_lightrad` | multi-target WL, cone WL, light/rad | planned stubs |
| Simulators `AS500Image`/`AS1000Image`/`AS1200Image` and layers (`FilteredFieldLayer`, `SlopeLayer`, `GaussianFilterLayer`, `PerfectBBLayer`, `RandomNoiseLayer`, …) | anything you can compose | field images for parity and baselines (`helpers.field_image`) |

**Pixel snapping.** Layers are placed on whole pixels: 0.336 mm on `AS1200Image` at SID 1000. A planted 1.0 mm
offset is really 3 px = 1.008 mm, and pylinac (correctly) reports 1.01. Compare against
`helpers.snap_to_pixels(mm)`, or allow ±½ pixel.

### linac-dicom-image-suite (`FauxPID`)

A tkinter app (`python -m FauxPID.app.main`) and a library, built on pylinac's generator (AS1200, SID 1000, RT Image
DICOM with gantry, collimator, couch and jaw tags). It generates seven image families into
`<out>/DICOM_GENERATION_OUTPUT/Images/<family>/`:

- Artifacts, CAX Offset, Field Size, Flatness, Symmetry and Penumbra;
- Winston-Lutz, in six sets: `perfect`, `1mm_right`, `1mm_out`, `complex (2, 3, 6)`, `wobble`, `outlier`.

It can also analyse its own field images with pylinac's `FieldProfileAnalysis` and its own metric definitions
(`FauxPID.algorithms.metrics.run_analysis_on_path`). Generic hook for custom images:
`ImageGenerator.generate_dicom_using_layers(path, layers, **dicom_tags)`.

For tests, install it into the test environment and let the session fixture generate everything once (about 40 s):

```bash
uv pip install "FauxPID @ git+https://github.com/crcrewso/linac-dicom-image-suite.git@1014da2"
```

**What PyBeam QA reports for the suite's images, measured** (Field Analysis worksheet at its defaults: Varian
protocol, beam-centre centring, FWHM edges; Winston-Lutz with BB 6 mm). It also shows which of the suite's truths can
be used as truths:

| Image | Stated truth | PyBeam QA reports | Usable as truth? |
|---|---|---|---|
| CAX offset 10 / 5 / 1 mm right, 3 mm left, 1 mm up, 5 mm down, 7+7 mm | as named | 10.09 / 5.05 / 1.01 / −3.03 / −1.01 / 5.05 / 7.06+7.06 mm | **yes, after pixel snapping** (all within 0.01 mm of the snapped value) |
| Field size perfect / realistic 10×10, realistic 20×20 | 100 / 200 mm | 100.13–100.14 / 200.26 mm | **yes** (±0.4 mm) |
| Field size plus 10 / 5 / 1 mm | 110 / 105 / 101 × 100 mm | 110.63 / 105.24 / 101.88 × 100.5 mm | **no**: the images also carry a 5° rotation (suite bug) |
| Penumbra 1 / 2 / 10 mm (20–80 %) | as named | 1.01 / 2.02 / 9.87 mm | **yes** (±0.2 mm) |
| Symmetry "2 % x, CAX point difference" | 2 % | 2.02 % (Varian protocol, point difference) | **yes**: the same definition |
| Symmetry "102 % point ratio", "2 % area" | 102 %, 2 % | 103 % (Elekta), −4.09 % (Varian) | **no**: different definitions; use parity and baselines |
| Flatness "2 % variance", "2 % IEC ratio", "2 % CAX ratio" | 2 %, 102 %, 1.02 | 0.76 % (Varian), 101.74 % (Elekta), 101.22 % | **no**: the suite's flatness definitions and field region differ from pylinac's protocols |
| WL `perfect` | BB at isocentre | max 2D 0.00 mm, PASS | **yes** |
| WL `1mm_out` | BB 1 mm out | shift y = +1.00 mm | **yes** |
| WL `complex (2, 3, 6)` vs `outlier` | one gantry image 5 mm off | gantry isocentre 0.04 mm vs **5.01 mm** | **yes**, as a comparison |
| WL `complex (2, 3, 6)` | x 2, y 3, z 6 mm | shift (−2.00, −3.01, **+6.00**) | **no, vertical sign**: pylinac's own generator reports `up = +6` as shift z = **−6**. Either the suite's z means "down", or its gantry projection is flipped. Its x and y agree with pylinac |
| WL `1mm_right` | BB 1 mm right | shift (−0.87, 0.00, −0.47), gantry isocentre 1.70 mm | **no**: two images are mis-tagged as gantry 45° (suite bug) |

Other suite issues to know about (from reading its code at `1014da2`):

- **There is no machine-readable ground truth.** The truths live in file names, docstrings and
  `docs/IMAGEOPTIONS.md`. A `manifest.json` written beside the images (truth, units, conventions, metric
  definitions) would make it a test oracle rather than a picture generator.
- **Winston-Lutz noise is unseeded,** so its WL images differ on every run. Field images are deterministic.
- **Duplicate output names overwrite each other:** `1mm_right_couch_315`, `penumbra_1_mm` and `penumbra_2_mm` are each
  written twice.
- Also: three artifact images are float64; the WL jaw tags say ±50 mm for a 50 mm field; and the WL truth tables
  contain a 0.717/0.707 typo.

These are in the suite, not in PyBeam QA. They are recorded in `test_known_bugs.py` so nobody mistakes them for
PyBeam errors.

## 5. What testing found in PyBeam QA itself

| Finding | Kind | Where |
|---|---|---|
| An unreadable file leaves the Winston-Lutz worksheet stuck at "Analysis in progress…": the worker loads images on the GUI thread, outside its `try`, so neither `analysis_failed` nor a dialog appears | bug, **fixed** on `integ/docs-catphan-ci` (images now load inside the worker's `try`) | `core/analysis/wlutz.py`; `test_failure_paths.py` |
| The Field Analysis "interpolation resolution" setting has no effect: the worksheet never passes it to the worker | bug, **fixed** on `integ/docs-catphan-ci` | `field_analysis_widgets.py` `start_analysis`; `test_parity.py` |
| Every other Field Analysis setting reaches pylinac correctly (protocol, centring, edge method, normalisation, interpolation, in-field ratio, slope exclusion) | parity | `test_parity.py` |
| PyBeam's `QWinstonLutz` override of `analyze()` gives exactly pylinac's numbers for a gantry-only set | parity | `test_parity.py` |
| A Winston-Lutz result of 1.01 mm FAILs against a 1.0 mm tolerance (strict `<`) | design, see `results-stability.md` | `set_analysis_outcome` |
| Field Analysis `add_files()` cannot take paths; the others can | testability | `field_analysis_widgets.py:240` |

And in the two unmerged CatPhan branches, see `adding-a-pylinac-test.md` §4:

- neither works as committed, between them because of four undefined status constants, one missing import, one wrong
  pylinac keyword, and result fields that pylinac does not have;
- one branch stops the whole app from starting.

All of these would have been caught by one launcher test and one known-answer test.

## 6. Screenshots

Set `PYBEAM_SHOTS=/some/folder` and the tests save each window they analyse (`helpers.save_shot`), e.g.
`wl-left-1.5mm.png` showing the Winston-Lutz worksheet with "Maximum 2D distance (CAX to BB): 1.46 mm" and outcome
FAIL. Screenshots render the real widgets offscreen; they are useful for documentation and for reviewing a
change's visual effect, but assertions should read widget state, not pixels.
