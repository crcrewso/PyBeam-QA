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

The program includes some of these complementary features:

- Interactive QA plots with export capabilities.
- Professional looking QA reports.
- Quick creation of benchmark images and tests.

## Requirements
As of current the program depends on the following:
- Python (3.10+)
- PySide6 (6.4+)
- PySide6_utils (1.2+)
- pylinac (3.22.0+)
- pyqtgraph (0.13.3+)
- pdfrw (0.4)
- matplotlib (3.5+)
- numpy (1.20+)
- scipy (1.7+)
- reportlab (3.6+)

## Installation

### Method 1: Using uv (Recommended)
1. Install uv if you don't have it already:
   ```
   pip install uv
   ```
2. Download the source code from the repository.
3. Create a virtual environment and install the package:
   ```
   uv venv
   uv pip install -e .
   ```
4. For development, install development dependencies:
   ```
   uv pip install -e ".[dev]"
   ```

### Method 2: Using pip with pyproject.toml
1. Download the source code from the repository.
2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the package and all dependencies:
   ```
   pip install -e .
   ```
4. For development, install development dependencies:
   ```
   pip install -e ".[dev]"
   ```

### Method 3: Manual Installation
1. Download the source code from the repository.
2. (Optional but highly recommended) Create a virtual environment for PyBeam-QA to avoid dependency conflicts
with existing python libraries. You can use a dependency manager such as `venv` or `conda`.
3. Install all the required dependencies using `pip`:
   ```
   pip install PySide6>=6.4.0 PySide6-utils>=1.2.0 pylinac>=3.22.0 pyqtgraph>=0.13.3 pdfrw==0.4 matplotlib>=3.5.0 numpy>=1.20.0 scipy>=1.7.0 reportlab>=3.6.0
   ```

## Development

### Code Formatting and Linting
This project uses [ruff](https://github.com/astral-sh/ruff) for linting and formatting:

1. Format code:
   ```
   ruff format .
   ```

2. Lint code:
   ```
   ruff check .
   ```

3. Lint and fix automatically fixable issues:
   ```
   ruff check --fix .
   ```

### Testing
Run tests with pytest:
```
pytest
```

With coverage report:
```
pytest --cov=core --cov=ui
```

## Quick start
To run the application simply navigate to the source code directory and run the following command:\
`python main.py` or `python3 main.py`
