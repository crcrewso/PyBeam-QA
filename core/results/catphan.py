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

"""The CatPhan result model.

``from_pylinac`` is the only code in PyBeam QA that knows the shape of pylinac's CatPhan results
(``CatPhanBase.results_data(as_dict=True)``). The worksheet and the report read a :class:`CatPhanResult`, so a change
in pylinac's result shape is fixed here and caught by tests/unit/test_catphan_results.py, instead of silently showing
nothing in the worksheet. Values are kept at full precision; rounding happens only when they are displayed.
"""

from dataclasses import dataclass
from typing import Any

from core.results import ResultShapeError

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class HUMaterial:
    name: str
    measured_hu: float
    nominal_hu: float
    difference_hu: float
    stdev_hu: float
    passed: bool


@dataclass(frozen=True)
class UniformityROI:
    name: str
    measured_hu: float
    stdev_hu: float
    passed: bool


@dataclass(frozen=True)
class LowContrastROI:
    name: str
    visibility: float
    seen: bool


@dataclass(frozen=True)
class Check:
    """One pass/fail criterion, and the numbers it was decided on."""
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class CatPhanResult:
    schema_version: int
    pylinac_version: str
    phantom_model: str
    roll_deg: float
    origin_slice: int
    num_images: int
    # CTP404: HU linearity, geometry (scaling), slice thickness
    hu_tolerance: float
    hu_materials: tuple[HUMaterial, ...]
    hu_passed: bool
    geometry_line_distances_mm: tuple[float, ...]
    geometry_avg_line_distance_mm: float
    geometry_passed: bool
    slice_thickness_mm: float
    thickness_passed: bool
    # CTP486: uniformity
    uniformity_index: float
    integral_non_uniformity: float
    uniformity_rois: tuple[UniformityROI, ...]
    uniformity_passed: bool
    # CTP528: spatial resolution (informational: pylinac has no pass/fail for MTF). A level the scan does not resolve
    # is None (pylinac 3.49 returns None for 10-60 % on its CatPhan 503 demo series).
    mtf_lp_mm: tuple[tuple[int, float | None], ...]
    # CTP515: low contrast (absent on the CatPhan 503)
    low_contrast_available: bool
    low_contrast_rois: tuple[LowContrastROI, ...]
    low_contrast_rois_seen: int
    low_contrast_required: int
    warnings: tuple[str, ...]

    def mtf(self, percent: int) -> float | None:
        """Spatial resolution (lp/mm) at the given relative MTF, e.g. ``mtf(50)``."""
        return dict(self.mtf_lp_mm).get(percent)

    @property
    def low_contrast_passed(self) -> bool | None:
        if not self.low_contrast_available:
            return None
        return self.low_contrast_rois_seen >= self.low_contrast_required

    @property
    def checks(self) -> tuple[Check, ...]:
        """Every criterion the outcome is decided on. MTF is reported but not judged (pylinac sets no limit)."""
        failing_hu = [m.name for m in self.hu_materials if not m.passed]
        checks = [
            Check("HU linearity", self.hu_passed,
                  f"all within ±{self.hu_tolerance:g} HU" if self.hu_passed
                  else f"outside ±{self.hu_tolerance:g} HU: {', '.join(failing_hu)}"),
            Check("Geometry (scaling)", self.geometry_passed, f"mean node distance {self.geometry_avg_line_distance_mm:.2f} mm"),
            Check("Slice thickness", self.thickness_passed, f"{self.slice_thickness_mm:.2f} mm"),
            Check("Uniformity", self.uniformity_passed, f"uniformity index {self.uniformity_index:.2f}"),
        ]
        if self.low_contrast_available:
            checks.append(Check("Low contrast", bool(self.low_contrast_passed),
                                f"{self.low_contrast_rois_seen} ROI(s) seen, {self.low_contrast_required} required"))
        return tuple(checks)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def failed_checks(self) -> tuple[Check, ...]:
        return tuple(c for c in self.checks if not c.passed)


def _get(data: dict, *path: str, at: str = "") -> Any:
    """``data[path[0]][path[1]]...``, or a ResultShapeError naming the full location (``at`` is the prefix)."""
    node: Any = data
    for key in path:
        if not isinstance(node, dict) or key not in node:
            where = ".".join(p for p in (at, *path) if p)
            raise ResultShapeError(f"pylinac CatPhan results have no '{where}' (expected in schema {SCHEMA_VERSION}); "
                                   f"this pylinac version reshaped its results - update core/results/catphan.py")
        node = node[key]
    return node


def from_pylinac(data: dict, *, low_contrast_required: int) -> CatPhanResult:
    """Build the result from ``CatPhanBase.results_data(as_dict=True)``.

    ``low_contrast_required`` is the analysis' ``low_contrast_tolerance``: the number of low-contrast ROIs that must be
    seen for the low-contrast check to pass (pylinac's documented meaning of that parameter).
    """
    ctp404, ctp486, ctp528 = _get(data, "ctp404"), _get(data, "ctp486"), _get(data, "ctp528")

    def hu_material(key, r):
        at = f"ctp404.hu_rois.{key}"
        return HUMaterial(name=str(_get(r, "name", at=at)), measured_hu=float(_get(r, "value", at=at)),
                          nominal_hu=float(_get(r, "nominal_value", at=at)),
                          difference_hu=float(_get(r, "difference", at=at)),
                          stdev_hu=float(_get(r, "stdev", at=at)), passed=bool(_get(r, "passed", at=at)))

    def uniformity_roi(key, r):
        at = f"ctp486.rois.{key}"
        return UniformityROI(name=str(_get(r, "name", at=at)), measured_hu=float(_get(r, "value", at=at)),
                             stdev_hu=float(_get(r, "stdev", at=at)), passed=bool(_get(r, "passed", at=at)))

    hu = tuple(hu_material(k, r) for k, r in _get(ctp404, "hu_rois", at="ctp404").items())
    uniformity = tuple(uniformity_roi(k, r) for k, r in _get(ctp486, "rois", at="ctp486").items())
    mtf = tuple(sorted((int(k), None if v is None else float(v))
                       for k, v in _get(ctp528, "mtf_lp_mm", at="ctp528").items()))
    ctp515 = data.get("ctp515")
    if ctp515:
        low = tuple(LowContrastROI(name=str(name), visibility=float(_get(r, "visibility", at=f"ctp515.roi_results.{name}")),
                                   seen=bool(_get(r, "passed visibility", at=f"ctp515.roi_results.{name}")))
                    for name, r in _get(ctp515, "roi_results", at="ctp515").items())
        seen = int(_get(ctp515, "num_rois_seen", at="ctp515"))
    else:
        low, seen = (), 0
    return CatPhanResult(
        schema_version=SCHEMA_VERSION,
        pylinac_version=str(_get(data, "pylinac_version")),
        phantom_model=str(_get(data, "catphan_model")),
        roll_deg=float(_get(data, "catphan_roll_deg")),
        origin_slice=int(_get(data, "origin_slice")),
        num_images=int(_get(data, "num_images")),
        hu_tolerance=float(_get(data, "ctp404", "hu_tolerance")),
        hu_materials=hu,
        hu_passed=bool(_get(data, "ctp404", "hu_linearity_passed")),
        geometry_line_distances_mm=tuple(float(x) for x in _get(data, "ctp404", "line_distances_mm")),
        geometry_avg_line_distance_mm=float(_get(data, "ctp404", "avg_line_distance_mm")),
        geometry_passed=bool(_get(data, "ctp404", "geometry_passed")),
        slice_thickness_mm=float(_get(data, "ctp404", "measured_slice_thickness_mm")),
        thickness_passed=bool(_get(data, "ctp404", "thickness_passed")),
        uniformity_index=float(_get(data, "ctp486", "uniformity_index")),
        integral_non_uniformity=float(_get(data, "ctp486", "integral_non_uniformity")),
        uniformity_rois=uniformity,
        uniformity_passed=bool(_get(data, "ctp486", "passed")),
        mtf_lp_mm=mtf,
        low_contrast_available=bool(ctp515),
        low_contrast_rois=low,
        low_contrast_rois_seen=seen,
        low_contrast_required=int(low_contrast_required),
        warnings=tuple(str(w) for w in data.get("warnings") or ()),
    )
