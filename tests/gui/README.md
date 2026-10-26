# GUI tests

Headless tests that drive PyBeam QA's real windows with pytest-qt. Background and findings:
[`docs/gui-testing-and-validation.md`](../../docs/gui-testing-and-validation.md). Why there are three kinds of
test: [`docs/results-stability.md`](../../docs/results-stability.md).

## Run

From the repository root, with Python 3.12:

```bash
uv venv -p 3.12 .venv-tests
uv pip install -p .venv-tests/bin/python -r tests/gui/requirements.txt
# optional, for the linac-dicom-image-suite tests (otherwise they are skipped):
uv pip install -p .venv-tests/bin/python "FauxPID @ git+https://github.com/crcrewso/linac-dicom-image-suite.git@1014da2"
.venv-tests/bin/python -m pytest tests/gui
```

`QT_QPA_PLATFORM=offscreen` is set automatically, so no display is needed. To save screenshots:
`PYBEAM_SHOTS=/tmp/shots pytest tests/gui`.

**Expected result**, measured with pylinac 3.49.0, PySide6 6.7.0 and FauxPID 1014da2: **48 passed, 7 xfailed,
16 skipped** (the planned-test stubs), in about 80 s. With a pylinac version that has no baseline yet, the 9
baseline tests skip, or report drift against an older baseline.

## Files

| File | What |
|---|---|
| `conftest.py` | runs from the repo root, offscreen; stubs modal dialogs; `--update-baselines`; session fixture that generates the FauxPID images |
| `helpers.py` | `run_worksheet` (add files, tick, press Analyze, wait), image generators, pixel snapping, field metrics |
| `test_launcher.py` | each launcher card opens its tool; the worksheet contract |
| `test_known_answers.py` | **truth**: planted answers (WL BB offsets and shift axes, perfect picket fence, CAX offset, field size, penumbra, symmetry, WL sets) |
| `test_parity.py` | **parity**: worksheet results equal a direct pylinac call with the worksheet's settings |
| `test_baselines.py`, `baselines.py`, `baselines/` | **baseline**: per-pylinac-version snapshots and drift reports |
| `test_known_bugs.py` | strict expected failures: PyBeam bugs and reference-image bugs |
| `test_planned_tools.py` | described stubs for planned tools and missing tests |
| `requirements.txt` | the pinned test environment |

## Baselines and pylinac upgrades

- **Same pylinac version as a stored baseline:** results must match to 1e-6.
- **A different version:** the newest older baseline is used, drift beyond the review bands is written to
  `tests/gui/drift-report.json`, and those tests are marked xfail.
- **After reviewing the drift:** `pytest tests/gui --update-baselines` stores the new version's snapshot. Commit it
  with a note of what changed and why that is acceptable.
