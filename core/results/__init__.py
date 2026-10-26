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

"""PyBeam QA's own result models: one per tool, built from pylinac's output in one place (``from_pylinac``), so
that the worksheets and reports never read pylinac objects directly. See docs/results-stability.md."""


class ResultShapeError(ValueError):
    """pylinac returned results in a shape this version of PyBeam QA does not understand."""
