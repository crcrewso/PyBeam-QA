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

"""How each test's tolerances are decided: the resolutions and measurement steps, in one reviewable place.

The tolerances themselves come from the user (the worksheet's spin-boxes). What is stated here is the rest of the rule
(core/decision.py): the precision each value is decided at, and how close to the tolerance counts as borderline.
Change these deliberately, with a note of why; they decide clinical outcomes.

| Test | Value decided | Resolution | Borderline band |
|---|---|---|---|
| CatPhan HU linearity | abs(measured - nominal) per material | 1 HU | 1 HU |
| CatPhan uniformity | abs(measured) per ROI (nominal 0 HU) | 1 HU | 1 HU |
| CatPhan geometry | abs(node distance - 50 mm) per line | 0.01 mm | 0.01 mm |
| CatPhan slice thickness | abs(measured - nominal) | 0.01 mm | 0.01 mm |
| CatPhan low contrast | ROIs seen (at least the number required) | 1 ROI | none |
| Winston-Lutz | max 2D CAX-to-BB distance, and each image's | 0.01 mm | one pixel at isocentre |

Why these bands:
- CT numbers are whole HU, so one HU is both the resolution and the step.
- pylinac measures CatPhan node positions and wire widths to a fraction of a pixel. A one-pixel band (0.5-1 mm on
  these scans) would be wider than the tolerances themselves (1 mm, 0.2 mm) and flag every result, so until a
  repeatability measurement says otherwise the band is one resolution step.
- An EPID pixel at isocentre (about 0.34 mm on an AS1200 at 100 cm) is the scale on which a Winston-Lutz result can
  move between deliveries, and pylinac's own image generator places the BB on whole pixels.

The boundary rule is the same everywhere: a value equal to the tolerance passes. pylinac itself uses "<=" for HU and
uniformity but a strict "<" for geometry and slice thickness, so at exactly the tolerance PyBeam QA can pass a value
pylinac would fail; that difference is deliberate (docs/results-stability.md, section 2).
"""

from core.decision import Bound, Criterion

GEOMETRY_NOMINAL_MM = 50.0  # pylinac's CTP404 node spacing (GeometricLine.nominal_length_mm)


def catphan_hu(tolerance_hu: float) -> Criterion:
    return Criterion("HU difference", tolerance_hu, resolution=1.0, unit="HU")


def catphan_uniformity(tolerance_hu: float) -> Criterion:
    return Criterion("uniformity HU", tolerance_hu, resolution=1.0, unit="HU")


def catphan_geometry(tolerance_mm: float) -> Criterion:
    return Criterion("node distance error", tolerance_mm, resolution=0.01, unit="mm")


def catphan_thickness(tolerance_mm: float) -> Criterion:
    return Criterion("slice thickness error", tolerance_mm, resolution=0.01, unit="mm")


def catphan_low_contrast(required: int) -> Criterion:
    return Criterion("low-contrast ROIs seen", required, resolution=1, unit="ROI(s)", bound=Bound.AT_LEAST, step=0)


def winston_lutz(tolerance_mm: float) -> Criterion:
    """Decide with ``step=`` one pixel at isocentre of the images analysed (the largest, if they differ)."""
    return Criterion("CAX-to-BB distance", tolerance_mm, resolution=0.01, unit="mm")
