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

"""PASS/FAIL, decided in one place (docs/results-stability.md, section 2).

Every decision is made the same way:

1. **At a stated resolution.** The measured value is rounded to the criterion's resolution (half away from zero), and
   the rounded value is compared. A change in pylinac smaller than the resolution cannot change an outcome.
2. **With one boundary rule everywhere: a value equal to the tolerance passes.** "At most 1.0 mm" passes 1.00 mm;
   "at least 2 ROIs" passes 2.
3. **With a borderline flag.** A measured value within one measurement step of the tolerance is *borderline*: the
   outcome is still PASS or FAIL, but it is shown as "PASS (borderline)" or "FAIL (borderline)", so a result that a
   pixel could flip is read with care.

The numbers themselves (resolutions and measurement steps for each test) are policy, kept in core/criteria.py.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum


class Bound(Enum):
    AT_MOST = "at most"    # PASS if value <= tolerance (deviations, distances)
    AT_LEAST = "at least"  # PASS if value >= tolerance (counts of things seen)


def _dec(x: float) -> Decimal:
    return Decimal(repr(float(x)))


def at_resolution(value: float, resolution: float) -> float:
    """``value`` rounded to a multiple of ``resolution``, half away from zero, in exact decimal arithmetic (so that
    1.005 at 0.01 is 1.01, not the 1.00 that binary floating point gives)."""
    steps = (_dec(value) / _dec(resolution)).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return float(steps * _dec(resolution))


def _fmt(x: float) -> str:
    return f"{x:g}"


@dataclass(frozen=True)
class Criterion:
    """One tolerance, and how it is decided."""
    name: str            # e.g. "max 2D CAX-to-BB distance"
    tolerance: float     # e.g. 1.0
    resolution: float    # the decision precision, e.g. 0.01
    unit: str = ""       # e.g. "mm"; shown in rules and details
    bound: Bound = Bound.AT_MOST
    step: float | None = None  # measurement step for the borderline band; None means one resolution step;
                               # 0 means no band (for counts)

    def decide(self, value: float, step: float | None = None) -> "Decision":
        """Decide ``value``. ``step`` overrides the criterion's measurement step for this measurement (e.g. one pixel
        of this image at isocentre)."""
        step = self.step if step is None else step
        step = self.resolution if step is None else step
        decided = at_resolution(value, self.resolution)
        if self.bound is Bound.AT_MOST:
            passed = _dec(decided) <= _dec(self.tolerance)
        else:
            passed = _dec(decided) >= _dec(self.tolerance)
        borderline = step > 0 and abs(_dec(value) - _dec(self.tolerance)) <= _dec(step)
        return Decision(self, float(value), decided, passed, borderline, float(step))

    @property
    def rule(self) -> str:
        """The rule in words, e.g. "at most 1 mm, decided at 0.01 mm"."""
        unit = f" {self.unit}" if self.unit else ""
        return f"{self.bound.value} {_fmt(self.tolerance)}{unit}, decided at {_fmt(self.resolution)}{unit}"


@dataclass(frozen=True)
class Decision:
    criterion: Criterion
    value: float          # as measured, full precision
    decided_value: float  # the value at the criterion's resolution: what was compared with the tolerance
    passed: bool
    borderline: bool      # within one measurement step of the tolerance
    step: float           # the measurement step used for the borderline band

    @property
    def outcome(self) -> str:
        return outcome_text(self.passed, self.borderline)

    def describe(self) -> str:
        """E.g. "1.01 mm: FAIL (borderline; at most 1 mm, decided at 0.01 mm)"."""
        unit = f" {self.criterion.unit}" if self.criterion.unit else ""
        return f"{_fmt(self.decided_value)}{unit}: {self.outcome} ({self.criterion.rule})"


def outcome_text(passed: bool, borderline: bool) -> str:
    return ("PASS" if passed else "FAIL") + (" (borderline)" if borderline else "")


def combine(decisions) -> tuple[bool, bool]:
    """(passed, borderline) for several decisions that must all pass.

    A pass is borderline if any of its decisions is. A failure is borderline only if every failing decision is: one
    clear failure makes the whole a clear failure."""
    decisions = list(decisions)
    passed = all(d.passed for d in decisions)
    if passed:
        return True, any(d.borderline for d in decisions)
    return False, all(d.borderline for d in decisions if not d.passed)
