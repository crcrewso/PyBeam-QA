<p align="center">
<img src="https://github.com/Quantico-Bullet/PyBeam-QA/blob/main/ui/qt_ui/icons/ic_app_alt.svg?sanitize=true">
</p>

# PyBeam QA

PyBeam QA is a graphical user interface program for performing quality assurance tests in radiotherapy. The program currently runs on Pylinac and PySide6.

## Features
The program is still in early development and may contain bugs. Tools are flagged as either 
'Complete', 'In-progress' or 'Planned'. Planned features are those not yet implemented.

| QA Tool | Status |
| --------------- | --------------- |
| TRS 398 Photon & Electron output calibration | Complete |
| Picket fence | Complete |
| Winston-Lutz analysis | Complete |
| Star-shot analysis | Complete |
| Field analysis | Complete |
| Planar imaging analysis | Complete |
| CatPhan CT/CBCT analysis (503, 504, 600, 604, 700) | In-progress |

Developer documentation (adding pylinac tests, GUI testing, keeping results stable across pylinac versions) is in
[`docs/`](docs/README.md); the GUI and unit tests are in [`tests/`](tests/gui/README.md).

The program includes some of these complementary features:

- Interactive QA plots with export capabilities.
- Professional looking QA reports.
- Quick creation of benchmark images and tests.

## Requirements
- Python 3.12. PySide6 6.7.0 supports Python up to 3.12, and 3.12 is the version the dependency lock is made and
tested for.
- The packages in [`requirements.txt`](requirements.txt), which pins every package exactly. In particular:
  - pylinac 3.49.0. Results can move between pylinac versions, so it is pinned, and upgraded on purpose (see
    [`docs/results-stability.md`](docs/results-stability.md));
  - PySide6 6.7.0, the version that generated `ui/py_ui/`;
  - pyqtgraph, reportlab, pdfrw, py_linq, numpy, scipy and matplotlib.

The direct dependencies are listed in [`requirements.in`](requirements.in), which also says how to recompile the
lock.

## Installation
1. Download the source code from the repository.
2. (Optional but highly recommended) Create a virtual environment for PyBeam-QA to avoid dependency conflicts
with existing python libraries, e.g. `python3.12 -m venv .venv`.
3. Install the dependencies: `pip3 install -r requirements.txt` (or `uv pip install -r requirements.txt`).

## Quick start
To run the application simply navigate to the source code directory and run the following command:\
`python main.py` or `python3 main.py`
