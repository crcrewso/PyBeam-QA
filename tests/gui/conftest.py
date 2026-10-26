"""Shared set-up for PyBeam QA GUI tests (pytest-qt).

PyBeam QA expects to run from the repository root (relative paths in main.py and core/tools), so the tests do too.
QT_QPA_PLATFORM=offscreen lets them run with no display; under Xvfb (`xvfb-run pytest tests/gui`) they also work.
See tests/gui/README.md and docs/gui-testing-and-validation.md.
"""
import json
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
os.chdir(REPO)
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def pytest_addoption(parser):
    parser.addoption("--update-baselines", action="store_true", default=False,
                     help="write tests/gui/baselines/pylinac-<version>.json from this run (after reviewing the drift)")


@pytest.fixture(scope="session", autouse=True)
def linac_devices():
    """The report dialogs read the treatment-unit list; main.py normally loads it at start-up."""
    from core.tools.devices import DeviceManager
    DeviceManager.loadDevices("core/tools/list.json")


@pytest.fixture(autouse=True)
def no_modal_dialogs(monkeypatch):
    """A failed analysis opens a modal MessageDialog, which would block an unattended run forever."""
    from ui.util_widgets.dialogs import MessageDialog
    monkeypatch.setattr(MessageDialog, "exec", lambda self: 0)


@pytest.fixture(scope="session")
def baseline_store(request):
    """Collects every baseline case of the session; see test_baselines.py and docs/results-stability.md."""
    from baselines import BaselineStore
    store = BaselineStore(Path(__file__).resolve().parent / "baselines",
                          update=request.config.getoption("--update-baselines"))
    yield store
    store.finish()


@pytest.fixture(scope="session")
def fauxpid_images(tmp_path_factory):
    """linac-dicom-image-suite (package FauxPID) known-answer images, generated once per session.
    Skips the requesting tests when FauxPID is not installed (see tests/gui/README.md)."""
    gen = pytest.importorskip("FauxPID.images.create_image", reason="linac-dicom-image-suite (FauxPID) not installed")
    root = tmp_path_factory.mktemp("fauxpid") / "Images"
    g = gen.ImageGenerator(file_out_directory=root, include_png=False)
    for method in ("generate_cax_offset_images", "generate_field_size_images", "generate_flatness_images",
                   "generate_symmetry_images", "generate_penumbra_images", "generate_winston_lutz_images"):
        getattr(g, method)()
    return root
