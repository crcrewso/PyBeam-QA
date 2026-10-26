# PyBeam QA
# Copyright (C) 2024 Kagiso Lebang
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""CatPhan CT/CBCT analysis (pylinac's CatPhan503/504/600/604/700) for PyBeam QA.

The worker follows docs/adding-a-pylinac-test.md §2.4: everything that touches pylinac - loading the series,
analysing it, drawing its figures - happens inside ``analyze()``, inside its ``try``, on the worker thread. The GUI
receives plain data: a :class:`core.results.catphan.CatPhanResult` and image bytes.
"""

import gc
import hashlib
import io
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot
from pylinac import CatPhan503, CatPhan504, CatPhan600, CatPhan604, CatPhan700
from pylinac import __version__ as pylinac_version

from core.results.catphan import CatPhanResult, from_pylinac

PHANTOMS = {"CatPhan 503": CatPhan503,
            "CatPhan 504": CatPhan504,
            "CatPhan 600": CatPhan600,
            "CatPhan 604": CatPhan604,
            "CatPhan 700": CatPhan700}

CONTRAST_METHODS = ["Michelson", "Weber", "Ratio", "RMS", "Difference"]  # pylinac.core.contrast.Contrast values

DEFAULT_PARAMETERS = dict(hu_tolerance=40.0, scaling_tolerance=1.0, thickness_tolerance=0.2, low_contrast_tolerance=1,
                          cnr_threshold=15.0, contrast_method="Michelson", visibility_threshold=0.15)


def input_sha256(source: str) -> str:
    """SHA-256 of the analysed input (the .zip, or every file in the folder, by name and content) for the record
    printed in the report: it lets anyone confirm later which data a result came from."""
    path = Path(source)
    files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
    digest = hashlib.sha256()
    for f in files:
        digest.update(f.name.encode())
        with open(f, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
    return digest.hexdigest()


def load_catphan(phantom: str, source: str):
    """A pylinac CatPhan object from a .zip of the series or a folder of its DICOM files."""
    cls = PHANTOMS[phantom]
    path = Path(source)
    if path.is_file() and path.suffix.lower() == ".zip":
        return cls.from_zip(str(path))
    if path.is_dir():
        return cls(str(path))
    raise FileNotFoundError(f"{source} is neither a .zip of a CT series nor a folder of DICOM files")


def result_from(ct, parameters: dict) -> CatPhanResult:
    """The decided result of an analysed pylinac CatPhan object, given the parameters it was analysed with."""
    return from_pylinac(ct.results_data(as_dict=True),
                        low_contrast_required=parameters["low_contrast_tolerance"],
                        scaling_tolerance_mm=parameters["scaling_tolerance"],
                        thickness_tolerance_mm=parameters["thickness_tolerance"],
                        nominal_slice_thickness_mm=float(ct.ctp404.slice_thickness))


class QCatPhanWorker(QObject):
    """Runs one CatPhan analysis on a worker thread."""

    analysis_progress = Signal(str)
    analysis_results_ready = Signal(dict)
    analysis_failed = Signal(str)
    thread_finished = Signal()

    def __init__(self, source: str, phantom: str, parameters: dict, origin_slice: int | None = None):
        super().__init__()
        # Store only: nothing that can fail runs on the GUI thread.
        self._source = source
        self._phantom = phantom
        self._parameters = dict(parameters)
        self._origin_slice = origin_slice

    @Slot()
    def analyze(self):
        try:
            self.analysis_progress.emit("Loading CT series...")
            ct = load_catphan(self._phantom, self._source)

            self.analysis_progress.emit("Analysing CT series...")
            ct.analyze(**self._parameters, origin_slice=self._origin_slice)

            result = result_from(ct, self._parameters)

            self.analysis_progress.emit("Drawing figures...")
            image_png = io.BytesIO()
            ct.save_analyzed_image(image_png, format="png", dpi=110, bbox_inches="tight")
            report_pdf = io.BytesIO()
            ct.save_analyzed_image(report_pdf, format="pdf", bbox_inches="tight")
            report_pdf.seek(0)

            self.analysis_results_ready.emit({"result": result,
                                              "analyzed_image_png": image_png.getvalue(),
                                              "report_plots": [report_pdf],
                                              "phantom": self._phantom,
                                              "source": self._source,
                                              "parameters": dict(self._parameters, origin_slice=self._origin_slice),
                                              "pylinac_version": pylinac_version,
                                              "input_sha256": input_sha256(self._source)})
            del ct
            gc.collect()

        except Exception as err:
            self.analysis_failed.emit(traceback.format_exception_only(err)[-1].strip())

        finally:
            self.thread_finished.emit()
