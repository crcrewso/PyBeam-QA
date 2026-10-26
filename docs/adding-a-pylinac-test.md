# Adding a pylinac test that PyBeam QA does not implement yet

This guide explains how a pylinac analysis becomes a PyBeam QA tool, step by step, using the code on `main` and the
two unmerged CatPhan/CT branches on this fork as worked examples. It also lists which pylinac analyses are still
missing.

Everything marked **measured** below was run on a Linux test VM (Ubuntu 24.04, Python 3.12, PySide6 6.7.0, pylinac
3.49.0) in October 2026. Anything else is read from the code. Line numbers refer to `main` at `2d6e275`.

Related documents:

- [`gui-testing-and-validation.md`](gui-testing-and-validation.md): how to test a tool once it exists, including
  headless GUI tests and known-answer images from linac-dicom-image-suite.
- [`results-stability.md`](results-stability.md): how to keep results trustworthy as pylinac changes underneath them.

---

## 1. What exists today, and what pylinac offers

### Implemented

| Launcher card | Window → worksheet | Core module (worker) | PDF report |
|---|---|---|---|
| Photon output calibration | `PhotonsMainWindow` → `QPhotonsWorksheet` | `core/calibration/trs398.py` (PyBeam's own TRS-398 maths, **not** pylinac) | `PhotonCalibrationReport` |
| Electron output calibration | `ElectronsMainWindow` → `QElectronsWorksheet` | `core/calibration/trs398.py` | `ElectronCalibrationReport` |
| Winston-Lutz analysis | `WinstonLutzMainWindow` → `QWLutzWorksheet` | `core/analysis/wlutz.py` (`QWinstonLutzWorker`) | `WinstonLutzReport` |
| Picket-fence analysis | `PicketFenceMainWindow` → `QPicketFenceWorksheet` | `core/analysis/picket_fence.py` | `PicketFenceReport` |
| Star-shot analysis | `StarshotMainWindow` → `QStarshotWorksheet` | `core/analysis/starshot.py` | `StarshotReport` |
| Field analysis | `FieldAnalysisMainWindow` → `QFieldAnalysisWorksheet` | `core/analysis/field_analysis.py` | `FieldAnalysisReport` |
| Planar imaging analysis | `PlanarImagingMainWindow` → `QPlanarImagingWorksheet` | `core/analysis/planar_imaging.py` (13 phantoms) | `PlanarImagingReport` |

**Measured:** all five pylinac-backed windows open from their launcher cards headless. The two calibration cards
switch a page inside the main window instead of opening one.

### Not implemented: candidates, in suggested order

The source for this list is pylinac 3.45, the version used elsewhere on this machine; 3.49 has the same classes.

| pylinac analysis | Class(es) | Input | Why it is a good next tool | Notes |
|---|---|---|---|---|
| **CT / CBCT phantoms** | `CatPhan503/504/600/604/700`, `QuartDVT`, `ACRCT`, `ACRMRILarge`, `CIRS062M`, `TomoCheese` | a folder or zip of a CT series | Daily/monthly CBCT QA is routine; two branches have already tried it (§4) | Demo data exists for 503/504/600/604, Quart and TomoCheese. Input is a *series*, not an image, so the worksheet differs from the others |
| **VMAT** | `DRGS`, `DRMLC`, `DRCS` | exactly two EPID images (open + DMLC) | Standard Varian VMAT commissioning and QA | `analyze(tolerance=1.5)`; there is no public `save_analyzed_image` in 3.45. Plotting is `plot_analyzed_image` |
| **Field profile analysis** | `FieldProfileAnalysis` | one image | pylinac's newer, metric-plugin field analysis; overlaps the existing Field Analysis tool | Could extend the existing tool rather than add a card |
| **Light/radiation coincidence** | `StandardImagingFC2`, `IMTLRad`, `DoselabRLf`, `IsoAlign`, `SNCFSQA` | one image | Monthly mechanical QA | Same base class as planar imaging; easiest new card to add |
| **Multi-target Winston-Lutz** | `WinstonLutzMultiTargetMultiField` | a folder | SRS off-axis QA | Needs a `BBArrangement`; `plot_summary` is not implemented in pylinac |
| **TG-51** | `TG51Photon`, `TG51ElectronLegacy`, `TG51ElectronModern` | typed values, not images | Complements the TRS-398 worksheets | PyBeam's TRS-398 is its own code, so decide first whether TG-51 should use pylinac's classes |
| **Machine logs** | `Dynalog`, `TrajectoryLog`, `MachineLogs` | log files | Patient-specific QA trending | Not image-based. There is no `analyze()`: gamma is computed from `log.fluence` |
| Nuclear medicine | `PlanarUniformity`, `CenterOfRotation`, `TomographicUniformity`, … | NM image stacks | Only if the clinic wants it | No PDF or demo data in pylinac |
| Digital mammography | `ACRDigitalMammography` | one image | Unlikely in radiotherapy | Not exported from `pylinac/__init__` |

---

## 2. How a test is wired: the Starshot path, end to end

Starshot is the cleanest template: the worker does all the pylinac work, and the UI receives plain data.

```
app_main_win.ui (card "starshotAnalysis")
   │  click → AppMainWin.eventFilter → open_window("starshot", StarshotMainWindow)
   ▼
StarshotMainWindow(QAToolsWindow)            ui/linac_qa/starshot_widgets.py
   │  one tab per worksheet
   ▼
QStarshotWorksheet(QWidget)                  ui/linac_qa/starshot_widgets.py
   │  self.ui = Ui_QStarshotWorksheet()      ← ui/py_ui/starshot_worksheet_ui.py ← ui/qt_ui/starshot_worksheet.ui
   │  Analyze → QStarshotWorker moved to a QThread
   ▼
QStarshotWorker(QObject).analyze()           core/analysis/starshot.py
   │  QStarshot(Starshot) … analyze(…)  → emits analysis_results_ready(dict) or analysis_failed(str)
   ▼
worksheet.show_analysis_results(dict)       pyqtgraph plots, results form, PASS/FAIL
   │  Generate report
   ▼
StarshotReport(BaseReport).save_report()     core/tools/report.py (reportlab + pdfrw)
```

### 2.1 The launcher card and registration (`ui/app_main_win.py`)

Clicks are caught with an event filter, not a signal. There is no central registry: each test is wired in four
places in `ui/app_main_win.py`:

1. **Import** the window class (lines 22-28).
2. **`installEventFilter`** on the card's `QFrame` (lines 55-61), e.g.
   `self._ui.starshotAnalysis.installEventFilter(self)`.
3. **A key in `self.qa_windows`** (line 67). This dictionary keeps one window per test.
4. **A branch in `eventFilter`** (line 160 onwards):

   ```python
   elif event.type() == QEvent.Type.MouseButtonPress and source is self._ui.starshotAnalysis:
       self.open_window("starshot", StarshotMainWindow)
       return True
   ```

`open_window` (line 196) creates the window, or, if one is already open, calls its `add_new_worksheet()` **with no
arguments**. Every override of `add_new_worksheet` therefore needs default arguments.

### 2.2 The window and the worksheet contract

`QAToolsWindow` (`ui/linac_qa/qa_tools_win.py:27`) is the shared base window. It provides the tabs, the File/View/
Tools/Help menus, the status-bar `AnalysisInfoLabel`, and close confirmation. When the user switches tabs,
`tab_window_changed` (line 92) reads three things from the worksheet. This is the **implicit contract every worksheet
must meet**:

| Worksheet must provide | Type | Used for |
|---|---|---|
| `analysis_info_signal` | `Signal(dict)` with `{"state": AnalysisInfoLabel.X, "message": str \| None}` | Status bar updates, and tests (see the testing guide) |
| `analysis_state` | one of `AnalysisInfoLabel.IDLE/IN_PROGRESS/COMPLETE/FAILED` | Restoring the status bar on tab switch |
| `analysis_message` | `str \| None` | Same |

`AnalysisInfoLabel` defines **only** `IDLE`, `IN_PROGRESS`, `COMPLETE` and `FAILED` (`ui/util_widgets/statusbar.py`).
Using any other name, such as `BUSY`, raises when the user presses Analyze. That is **measured** on one of the CatPhan
branches (§4).

There is no shared worksheet base class. The file list, its context menu, check-marks, progress bar, PASS/FAIL styling
and report dialog are copied into each `*_widgets.py`. Copy them from the closest existing test.

### 2.3 The Designer file and generated code

- **Source:** `ui/qt_ui/<name>.ui`, e.g. `starshot_worksheet.ui`, whose root class is `QStarshotWorksheet`.
- **Generated:** `ui/py_ui/<name>_ui.py`, class `Ui_<RootClass>`. **Never edit generated files by hand**; the next
  regeneration silently overwrites them (§4 shows this happening).
- **Regenerate** with `ui/convertUI.sh`, a bash script run from `ui/`: `pyside6-uic` for every `.ui`, and `pyside6-rcc`
  for `icons.qrc`.
- **Use PySide6 6.7.0** to regenerate. Every committed generated file says it was made by 6.7.0. **Measured:** with
  6.7.0, `convertUI.sh` reproduces every committed `*_ui.py` byte for byte.
- **`icons_rc.py` always changes** when regenerated (930 lines differ on a fresh clone), because `pyside6-rcc` embeds
  the icon files' modification times. Commit `icons_rc.py` **only when `icons.qrc` or an icon really changed**;
  otherwise `git checkout -- ui/py_ui/icons_rc.py`.
- Add any new `.ui` file to `ui/qt_ui/pyBeamQA.pyproject`.
- Resources: icons are listed in `ui/qt_ui/icons.qrc` under the prefixes `/colorIcons`, `/actionIcons`, `/misc_icons`
  and `/anim`. Widget modules import `ui.py_ui.icons_rc` to register them.

**Editing `.ui` files without Qt Designer on your workstation.** Qt Designer ships inside PySide6
(`pyside6-designer`). If you would rather not install Qt tooling on a clinical or managed Windows machine, do the
Designer work on a Linux VM:

```bash
uv venv -p 3.12 ~/venv-pybeam
uv pip install -p ~/venv-pybeam/bin/python "PySide6==6.7.0" pyqtgraph pylinac reportlab pdfrw py_linq
source ~/venv-pybeam/bin/activate
pyside6-designer ui/qt_ui/<name>.ui          # interactive; needs a desktop session or X forwarding
(cd ui && bash convertUI.sh)                 # regenerate ui/py_ui/*
git checkout -- ui/py_ui/icons_rc.py         # unless icons changed
```

`.ui` files are XML, so small changes such as copying a launcher card can also be made in a text editor and checked
by regenerating.

### 2.4 The core module and the worker thread (`core/analysis/<test>.py`)

Two classes per test, by convention:

- **`Q<PylinacClass>`**: a subclass or wrapper of the pylinac class, adding `get_publishable_plots()` (matplotlib
  figures saved to `io.BytesIO` as PDF, for the report).
- **`Q<Name>Worker(QObject)`** with these class-level signals:

  ```python
  analysis_results_ready = Signal(dict)
  analysis_failed = Signal(str)
  thread_finished = Signal()
  analysis_progress = Signal(str)   # optional
  ```

  and an `analyze()` slot. In it, build the pylinac object, call `analyze(...)`, put **plain data** in a dict, emit
  it, then emit `thread_finished`. On an exception, emit `analysis_failed(message)` and `thread_finished`.

The worksheet wires it up the same way in every test (`starshot_widgets.py`, from line 550):

```python
self.qthread = QThread()
self.worker.moveToThread(self.qthread)
self.worker.analysis_failed.connect(self.qthread.quit)
self.worker.analysis_failed.connect(self.on_analysis_failed)
self.worker.thread_finished.connect(self.qthread.quit)
self.worker.thread_finished.connect(self.worker.deleteLater)
self.worker.analysis_results_ready.connect(self.show_analysis_results)
self.qthread.started.connect(self.worker.analyze)
self.qthread.finished.connect(self.qthread.deleteLater)
self.qthread.start()
```

Three lessons from the existing code:

1. **Load and construct pylinac objects inside `analyze()`, inside its `try`, not in the worker's `__init__`.** The
   worker is constructed on the GUI thread. **Measured** on Winston-Lutz (`QWinstonLutzWorker.__init__`,
   `core/analysis/wlutz.py:130`): a file that cannot be read raises *before* the `try`. No `analysis_failed` is
   emitted and no error dialog appears; the worksheet stays at "Analysis in progress…" with its buttons disabled
   until it is closed. Picket fence, field analysis and planar imaging also load in `__init__`, because their `Q*`
   classes create pyqtgraph items there; keep new tests' pyqtgraph work on the GUI side.
2. **Connect bound methods, not lambdas.** Several worksheets use `connect(lambda data: self.show_...(data))`. A
   bound method guarantees the call is queued onto the GUI thread.
3. **Decide PASS/FAIL in one place, on raw values.** The worksheets compare values to tolerances in the UI
   (`set_analysis_outcome`). See [`results-stability.md`](results-stability.md) for why pass/fail should move into
   core code.

### 2.5 Results display

The existing tools draw with **pyqtgraph** (`pg.GraphicsLayoutWidget`, `ImageItem`, `ScatterPlotItem`), and add a
results `QFormLayout` or a summary `QTextEdit` inside `analysisInfoVL`. Several tools also have an
`Advanced<XX>View(QMainWindow)`. pylinac's own matplotlib plots are used only for the PDF report.

### 2.6 The PDF report (`core/tools/report.py`)

Subclass `BaseReport` (line 40) as the existing reports do (`StarshotReport`, line 361):

- `set_user_details`
- `set_analysis_details`
- `set_plot_summary`, which embeds the `get_publishable_plots()` PDFs with `PdfImage`
- `save_report`

The stack is reportlab, pdfrw and the vendored `core/tools/toreportlab.py`. **Add a class; do not reorganise the
file.** One of the CatPhan branches rewrote it and broke the calibration windows (§4).

---

## 3. Checklist: adding a new test

Use `<name>` for the module stem (e.g. `vmat`), `<Name>` for class names (e.g. `VMAT`), and `<key>` for the
`qa_windows` key (e.g. `vmat_analysis`).

1. **Designer: launcher card.** In `ui/qt_ui/app_main_win.ui`:
   - Copy an existing card `QFrame` (e.g. `starshotAnalysis`, line 759) into `verticalLayout_5` (line 337).
   - Give it, its icon label and its text label new object names.
   - Add a `QFrame#<newCard>:hover {…}` rule to `testListFrame`'s stylesheet (around line 304).
2. **Designer: worksheet.** Copy `ui/qt_ui/starshot_worksheet.ui` to `ui/qt_ui/<name>_worksheet.ui` and set the root
   class to `Q<Name>Worksheet`.
   - Keep the object names the copied code expects: `imageListWidget`, `addImgBtn`, `analyzeBtn`, `genReportBtn`,
     `outcomeLE`, `analysisInfoVL`, `analysisImageVL`, `image_vl_spacer` (and `advancedViewBtn` if used).
   - Replace the configuration form with the new analysis' parameters.
   - Add the file to `pyBeamQA.pyproject`.
3. **Regenerate** with `(cd ui && bash convertUI.sh)` under PySide6 6.7.0, and revert `icons_rc.py` unless icons
   changed.
4. **Core:** create `core/analysis/<name>.py` with `Q<Name>` and `Q<Name>Worker` as in §2.4.
5. **Worksheet and window:** create `ui/linac_qa/<name>_widgets.py` with:
   - `<Name>MainWindow(QAToolsWindow)`: `window_title = "<Name> ‒ PyBeam QA"`,
     `add_new_worksheet(self, worksheet_name=None, enable_icon=True)`, and menu actions.
   - `Q<Name>Worksheet(QWidget)`: the contract from §2.2, `add_files(self, files=None)` accepting a list of paths
     (this makes it testable; see the testing guide), `start_analysis`, `show_analysis_results`,
     `on_analysis_failed`, `set_analysis_outcome`, and `generate_report`.
6. **Register** in `ui/app_main_win.py`: import, `installEventFilter`, `qa_windows["<key>"]`, and the `eventFilter`
   branch (§2.1).
7. **Report:** add `<Name>Report(BaseReport)` to `core/tools/report.py`.
8. **Dependencies:** if you add a library, update the README requirements and the About dialog
   (`ui/util_widgets/dialogs.py`).
9. **Tests:**
   - add a launcher test and at least one known-answer test under `tests/gui/` (see
     [`gui-testing-and-validation.md`](gui-testing-and-validation.md));
   - fill in the matching stub in `tests/gui/test_planned_tools.py`;
   - add the new tool's reference cases to the baselines (see [`results-stability.md`](results-stability.md)).
10. **README:** add the tool to the feature table.

---

## 4. Worked examples: the two CatPhan/CT branches

Both branches are unmerged, AI-generated and unreviewed. They were run on the VM against pylinac's public CatPhan
demo datasets (503, 600 and 604).

| | `copilot/fix-1` (3 commits, 2025-05-25) | `codegen-bot/add-catphan-analysis` (6 commits, 2025-08-21) |
|---|---|---|
| Files | `core/analysis/ct.py`, `ui/linac_qa/ct_widgets.py`, `ui/app_main_win.py`, **both** `ui/qt_ui/app_main_win.ui` and `ui/py_ui/app_main_win_ui.py` | `core/analysis/catphan.py`, `ui/linac_qa/catphan_widgets.py`, `ui/py_ui/catphan_worksheet_ui.py`, `ui/app_main_win.py`, **only** `ui/py_ui/app_main_win_ui.py`; plus a 1,092-line rewrite of `core/tools/report.py`, `main.py`, `pyproject.toml` and the README |
| Registration (§2.1) | The four edits, done correctly (`ct_analysis` key). **Measured:** the key is present and the card is wired | The four edits in `app_main_win.py`, but the card exists **only in generated code**: no `.ui` source, so the next `convertUI.sh` deletes it |
| Worksheet UI | Built in Python (`setup_ui`), no `.ui` file | A generated `Ui_QCatPhanWorksheet` with **no `.ui` source** |
| Does the app start? | Yes | **No. Measured:** `ImportError: cannot import name 'PhotonCalibrationReport' from 'core.tools.report'`. The rewrite renamed the class, and the TRS-398 window still imports the old name |
| Does the window open? | **No. Measured:** `NameError: name 'QListWidget' is not defined` (`ct_widgets.py:133` uses it, but it is not imported) | Opened directly, yes |
| Does an analysis run? | **Not as committed.** With the missing import and two undefined status constants (`AnalysisInfoLabel.SUCCESS` and `.FAILURE`) patched in a scratch copy, **measured:** the analysis completes for CatPhan 503, 600 and 604 (a few seconds each). But the worksheet shows **only "Phantom Type"**: its summary code looks for `hu_linearity` and `uniformity` attributes that pylinac's `results_data()` does not have, because pylinac nests them under `ctp404`, `ctp486`, `ctp528` and `ctp515`. The analysis succeeds and the user sees nothing, which is the result-shape problem in [`results-stability.md`](results-stability.md) | **No. Measured:** pressing Analyze raises `AttributeError: … 'AnalysisInfoLabel' has no attribute 'BUSY'` for all three phantoms. With `BUSY` patched in a scratch copy, **measured:** <br>• its *Add folder* path raises `IsADirectoryError` (the folder is passed to pylinac as if it were a file); <br>• its *Add files* path reaches pylinac and raises `TypeError: CatPhanBase.analyze() got an unexpected keyword argument 'low_contrast_threshold'` (pylinac's parameter is `low_contrast_tolerance`); <br>• its failure handler then raises on a third undefined status, `AnalysisInfoLabel.ERROR` |

### What to take from them

- **From `copilot/fix-1`:** the *shape* of a correct change — the Designer card edited in the `.ui` and regenerated,
  the four registration edits, a `Q…Worker` on a `QThread`, and an `Advanced…View`.
- **From `codegen-bot`:** the parameter set worth exposing for CatPhan (HU, scaling, thickness and low-contrast
  tolerances; memory-efficient mode; per-module plots for HU linearity, uniformity, MTF and low contrast) and a
  `pyproject.toml` with uv. **Avoid** its process mistakes:
  - generated files edited without their `.ui` sources;
  - a shared module (`report.py`) rewritten instead of extended;
  - a status constant (`BUSY`) the base class doesn't define.

  Each of them breaks something outside the new tool, and none is caught without tests. That is the case for
  `tests/gui/`.
- **From both:** check names against the installed pylinac and against PyBeam's own classes rather than guessing.
  - Between them, the two branches use four status names that `AnalysisInfoLabel` does not define: `BUSY`,
    `SUCCESS`, `FAILURE` and `ERROR`.
  - They use one pylinac keyword that `analyze()` does not accept, and read two result attributes that
    `results_data()` does not have.
  - A one-line launcher test and a one-image known-answer test would have caught every one of these.
  - Reading pylinac's results through a PyBeam result model (see `results-stability.md`) puts the result-shape
    knowledge in one place, where a unit test can check it.
- **CT input differs from the other tools.** pylinac's CatPhan classes take a **folder or zip of a whole series**,
  not one image. `copilot/fix-1` picks a single zip; `codegen-bot` takes a list of files or a folder. A worksheet for
  series input needs its own list item type (one item per series), and its `add_files` should accept folders and zips.

---

## 5. Known issues found while writing this guide

These are on `main` and worth fixing alongside any new tool:

1. **Winston-Lutz worker loads images on the GUI thread, outside its `try`** (`core/analysis/wlutz.py:130-137`).
   An unreadable file leaves the worksheet stuck at "Analysis in progress…" (measured; see
   `tests/gui/test_known_bugs.py`).
2. **Field Analysis `add_files()` takes no paths** (`field_analysis_widgets.py:240`). The other tools accept
   `add_files(files=None)`; matching them makes the tool scriptable and testable.
3. **The "Add Image(s)" menu action is bound to the first worksheet's `add_files`**, not the current tab's (every
   `*MainWindow.__init__`).
4. **`main.py` sets the Windows AppUserModelID to `radlab.pybeamqa-0.1.2`**, while `core/__init__.py` says `0.2.0`.
5. **README requirements omit `reportlab` and `py_linq`**, which the code imports, and list `PySide6_utils`, which
   nothing imports.
6. **`core/configuration/data/workspace.json` stores `"workspace_path": "null"` as a string**, so the first-run
   setup wizard check (`== None` in `main.py`) never fires (read, not run).
7. **pylinac compatibility:** README says 3.22+. The app runs on 3.49.0 (measured: all windows open, and the
   Winston-Lutz and Picket Fence known-answer tests pass). `ui/__init__.py` monkey-patches
   `pylinac.core.array_utils.normalize` for versions ≤ 3.27.
