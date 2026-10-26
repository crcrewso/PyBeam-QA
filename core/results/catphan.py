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

PASS/FAIL is decided here, by core/decision.py with the criteria in core/criteria.py, from the measured values.
pylinac's own pass/fail flags are kept beside the decisions (``pylinac_flags``) so the two can be compared.
"""

from dataclasses import dataclass
from typing import Any

from core import criteria
from core.decision import Decision, combine, outcome_text
from core.results import ResultShapeError

SCHEMA_VERSION = 2  # 2: decisions by core/decision.py; nominal slice thickness and tolerances recorded


@dataclass(frozen=True)
class HUMaterial:
    name: str
    measured_hu: float
    nominal_hu: float
    difference_hu: float
    stdev_hu: float
    decision: Decision  # on abs(difference_hu)

    @property
    def passed(self) -> bool:
        return self.decision.passed


@dataclass(frozen=True)
class UniformityROI:
    name: str
    measured_hu: float
    stdev_hu: float
    decision: Decision  # on abs(measured_hu); the nominal is 0 HU

    @property
    def passed(self) -> bool:
        return self.decision.passed


@dataclass(frozen=True)
class LowContrastROI:
    name: str
    visibility: float
    seen: bool


@dataclass(frozen=True)
class Check:
    """One pass/fail criterion of the phantom, the decisions it rests on, and a one-line summary of them."""
    name: str
    passed: bool
    borderline: bool
    detail: str
    decisions: tuple[Decision, ...]

    @property
    def outcome(self) -> str:
        return outcome_text(self.passed, self.borderline)


def _check(name: str, decisions, detail: str) -> Check:
    decisions = tuple(decisions)
    passed, borderline = combine(decisions)
    return Check(name, passed, borderline, detail, decisions)


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
    scaling_tolerance_mm: float
    geometry_line_distances_mm: tuple[float, ...]
    geometry_avg_line_distance_mm: float
    geometry_decisions: tuple[Decision, ...]  # one per line, on abs(distance - 50 mm)
    nominal_slice_thickness_mm: float
    thickness_tolerance_mm: float
    slice_thickness_mm: float
    thickness_decision: Decision  # on abs(measured - nominal)
    # CTP486: uniformity
    uniformity_index: float
    integral_non_uniformity: float
    uniformity_rois: tuple[UniformityROI, ...]
    # CTP528: spatial resolution (informational: pylinac has no pass/fail for MTF). A level the scan does not resolve
    # is None (pylinac 3.49 returns None for 10-60 % on its CatPhan 503 demo series).
    mtf_lp_mm: tuple[tuple[int, float | None], ...]
    # CTP515: low contrast (absent on the CatPhan 503)
    low_contrast_available: bool
    low_contrast_rois: tuple[LowContrastROI, ...]
    low_contrast_rois_seen: int
    low_contrast_required: int
    low_contrast_decision: Decision | None
    # pylinac's own verdicts, for comparison only: (check name, passed)
    pylinac_flags: tuple[tuple[str, bool], ...]
    warnings: tuple[str, ...]

    def mtf(self, percent: int) -> float | None:
        """Spatial resolution (lp/mm) at the given relative MTF, e.g. ``mtf(50)``."""
        return dict(self.mtf_lp_mm).get(percent)

    @property
    def hu_passed(self) -> bool:
        return combine(m.decision for m in self.hu_materials)[0]

    @property
    def geometry_passed(self) -> bool:
        return combine(self.geometry_decisions)[0]

    @property
    def thickness_passed(self) -> bool:
        return self.thickness_decision.passed

    @property
    def uniformity_passed(self) -> bool:
        return combine(r.decision for r in self.uniformity_rois)[0]

    @property
    def low_contrast_passed(self) -> bool | None:
        return None if self.low_contrast_decision is None else self.low_contrast_decision.passed

    @property
    def checks(self) -> tuple[Check, ...]:
        """Every criterion the outcome is decided on. MTF is reported but not judged (pylinac sets no limit)."""
        hu_tol = f"±{self.hu_tolerance:g} HU"
        failing = [f"{m.name} ({m.difference_hu:+.0f})" for m in self.hu_materials if not m.passed]
        worst = max(self.hu_materials, key=lambda m: abs(m.difference_hu))
        checks = [
            _check("HU linearity", (m.decision for m in self.hu_materials),
                   f"outside {hu_tol}: {', '.join(failing)}" if failing
                   else f"all within {hu_tol} (largest {worst.difference_hu:+.0f} HU, {worst.name})"),
            _check("Geometry (scaling)", self.geometry_decisions,
                   f"node distances {min(self.geometry_line_distances_mm):.2f}-{max(self.geometry_line_distances_mm):.2f}"
                   f" mm (nominal {criteria.GEOMETRY_NOMINAL_MM:g} ± {self.scaling_tolerance_mm:g} mm)"),
            _check("Slice thickness", (self.thickness_decision,),
                   f"{self.slice_thickness_mm:.2f} mm (nominal {self.nominal_slice_thickness_mm:.2f} "
                   f"± {self.thickness_tolerance_mm:g} mm)"),
            _check("Uniformity", (r.decision for r in self.uniformity_rois),
                   f"ROIs {min(r.measured_hu for r in self.uniformity_rois):+.0f} to "
                   f"{max(r.measured_hu for r in self.uniformity_rois):+.0f} HU (within ±{self.hu_tolerance:g} HU of 0);"
                   f" uniformity index {self.uniformity_index:.2f}"),
        ]
        if self.low_contrast_decision is not None:
            checks.append(_check("Low contrast", (self.low_contrast_decision,),
                                 f"{self.low_contrast_rois_seen} ROI(s) seen, {self.low_contrast_required} required"))
        return tuple(checks)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def borderline(self) -> bool:
        """A pass with any borderline check; a failure whose failing checks are all borderline."""
        checks = self.checks
        if self.passed:
            return any(c.borderline for c in checks)
        return all(c.borderline for c in checks if not c.passed)

    @property
    def outcome(self) -> str:
        """"PASS", "PASS (borderline)", "FAIL" or "FAIL (borderline)"."""
        return outcome_text(self.passed, self.borderline)

    @property
    def failed_checks(self) -> tuple[Check, ...]:
        return tuple(c for c in self.checks if not c.passed)

    @property
    def disagreements_with_pylinac(self) -> tuple[str, ...]:
        """Checks where PyBeam's decision differs from pylinac's own flag. Expected only at a boundary, where the
        decision resolution or PyBeam's single boundary rule differs from pylinac's (core/criteria.py)."""
        mine = {c.name: c.passed for c in self.checks}
        return tuple(name for name, flag in self.pylinac_flags if name in mine and mine[name] != flag)

    @property
    def decision_criteria(self):
        """The criteria this result was decided with, one per check, for the record."""
        return tuple((c.name, c.decisions[0].criterion) for c in self.checks)


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


def from_pylinac(data: dict, *, low_contrast_required: int, scaling_tolerance_mm: float,
                 thickness_tolerance_mm: float, nominal_slice_thickness_mm: float) -> CatPhanResult:
    """Build and decide the result from ``CatPhanBase.results_data(as_dict=True)``.

    The keyword arguments are the analysis settings and the one scan property that pylinac's results do not carry:
    ``low_contrast_required`` is the analysis' ``low_contrast_tolerance`` (the number of low-contrast ROIs that must be
    seen, pylinac's documented meaning), the tolerances are those passed to ``analyze()``, and
    ``nominal_slice_thickness_mm`` is the series' nominal slice thickness (pylinac's ``ctp404.slice_thickness``).
    core/analysis/catphan.py ``result_from`` supplies them all from an analysed pylinac object.
    """
    ctp404, ctp486, ctp528 = _get(data, "ctp404"), _get(data, "ctp486"), _get(data, "ctp528")
    hu_tolerance = float(_get(data, "ctp404", "hu_tolerance"))
    hu_criterion = criteria.catphan_hu(hu_tolerance)
    uniformity_criterion = criteria.catphan_uniformity(hu_tolerance)

    def hu_material(key, r):
        at = f"ctp404.hu_rois.{key}"
        difference = float(_get(r, "difference", at=at))
        return HUMaterial(name=str(_get(r, "name", at=at)), measured_hu=float(_get(r, "value", at=at)),
                          nominal_hu=float(_get(r, "nominal_value", at=at)), difference_hu=difference,
                          stdev_hu=float(_get(r, "stdev", at=at)), decision=hu_criterion.decide(abs(difference)))

    def uniformity_roi(key, r):
        at = f"ctp486.rois.{key}"
        value = float(_get(r, "value", at=at))
        return UniformityROI(name=str(_get(r, "name", at=at)), measured_hu=value,
                             stdev_hu=float(_get(r, "stdev", at=at)), decision=uniformity_criterion.decide(abs(value)))

    hu = tuple(hu_material(k, r) for k, r in _get(ctp404, "hu_rois", at="ctp404").items())
    uniformity = tuple(uniformity_roi(k, r) for k, r in _get(ctp486, "rois", at="ctp486").items())
    lines = tuple(float(x) for x in _get(data, "ctp404", "line_distances_mm"))
    geometry = criteria.catphan_geometry(scaling_tolerance_mm)
    thickness_mm = float(_get(data, "ctp404", "measured_slice_thickness_mm"))
    mtf = tuple(sorted((int(k), None if v is None else float(v))
                       for k, v in _get(ctp528, "mtf_lp_mm", at="ctp528").items()))
    ctp515 = data.get("ctp515")
    if ctp515:
        low = tuple(LowContrastROI(name=str(name), visibility=float(_get(r, "visibility", at=f"ctp515.roi_results.{name}")),
                                   seen=bool(_get(r, "passed visibility", at=f"ctp515.roi_results.{name}")))
                    for name, r in _get(ctp515, "roi_results", at="ctp515").items())
        seen = int(_get(ctp515, "num_rois_seen", at="ctp515"))
        low_decision = criteria.catphan_low_contrast(int(low_contrast_required)).decide(seen)
    else:
        low, seen, low_decision = (), 0, None
    return CatPhanResult(
        schema_version=SCHEMA_VERSION,
        pylinac_version=str(_get(data, "pylinac_version")),
        phantom_model=str(_get(data, "catphan_model")),
        roll_deg=float(_get(data, "catphan_roll_deg")),
        origin_slice=int(_get(data, "origin_slice")),
        num_images=int(_get(data, "num_images")),
        hu_tolerance=hu_tolerance,
        hu_materials=hu,
        scaling_tolerance_mm=float(scaling_tolerance_mm),
        geometry_line_distances_mm=lines,
        geometry_avg_line_distance_mm=float(_get(data, "ctp404", "avg_line_distance_mm")),
        geometry_decisions=tuple(geometry.decide(abs(d - criteria.GEOMETRY_NOMINAL_MM)) for d in lines),
        nominal_slice_thickness_mm=float(nominal_slice_thickness_mm),
        thickness_tolerance_mm=float(thickness_tolerance_mm),
        slice_thickness_mm=thickness_mm,
        thickness_decision=criteria.catphan_thickness(thickness_tolerance_mm).decide(
            abs(thickness_mm - float(nominal_slice_thickness_mm))),
        uniformity_index=float(_get(data, "ctp486", "uniformity_index")),
        integral_non_uniformity=float(_get(data, "ctp486", "integral_non_uniformity")),
        uniformity_rois=uniformity,
        mtf_lp_mm=mtf,
        low_contrast_available=bool(ctp515),
        low_contrast_rois=low,
        low_contrast_rois_seen=seen,
        low_contrast_required=int(low_contrast_required),
        low_contrast_decision=low_decision,
        pylinac_flags=(("HU linearity", bool(_get(data, "ctp404", "hu_linearity_passed"))),
                       ("Geometry (scaling)", bool(_get(data, "ctp404", "geometry_passed"))),
                       ("Slice thickness", bool(_get(data, "ctp404", "thickness_passed"))),
                       ("Uniformity", bool(_get(data, "ctp486", "passed")))),
        warnings=tuple(str(w) for w in data.get("warnings") or ()),
    )
