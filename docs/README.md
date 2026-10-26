# PyBeam QA developer documentation

| Document | Read it when |
|---|---|
| [`adding-a-pylinac-test.md`](adding-a-pylinac-test.md) | You want to add a pylinac analysis PyBeam QA doesn't have yet: what exists, what's missing, how a tool is wired end to end, a checklist, two worked examples (the unmerged CatPhan/CT branches), and the CatPhan tool this branch adds by following the checklist (§4.1) |
| [`gui-testing-and-validation.md`](gui-testing-and-validation.md) | You want to check that the GUI gives right answers: headless pytest-qt tests, known-answer images from pylinac and from linac-dicom-image-suite, and what testing found |
| [`results-stability.md`](results-stability.md) | You are upgrading pylinac, or designing how results are decided and recorded: an architecture for keeping results trustworthy as pylinac changes |
| [`../tests/gui/README.md`](../tests/gui/README.md) | You want to run the tests (`tests/gui` for the GUI, `tests/unit` for result models) |

Written in October 2026 against `main` at `2d6e275`. Measurements were made on a Linux VM with Python 3.12,
PySide6 6.7.0 and pylinac 3.49.0. Statements marked *measured* were run; the rest is read from the code.
