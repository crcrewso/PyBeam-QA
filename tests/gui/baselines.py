"""Per-pylinac-version result baselines (see docs/results-stability.md, "How the baseline prototype works").

- Same pylinac version as the stored baseline: values must match to 1e-6 (relative); a change means non-determinism or an
  environment change, and the test fails.
- No baseline for this version: the newest older one is used in drift mode; every metric that moved more than its review
  band is written to tests/gui/drift-report.json and the test is marked xfail, so an upgrade produces a reviewable report.
- Input images are fingerprinted by pixel data and beam angles (pylinac stamps new UIDs and dates on every file it
  generates), so a moved image generator shows up as "input changed", not as analysis drift.
- `pytest tests/gui --update-baselines` writes baselines/pylinac-<version>.json from the current run.
"""
import hashlib
import importlib.metadata as metadata
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pydicom
import pytest

SAME_VERSION_RTOL = 1e-6
# Review bands across pylinac versions: changes smaller than these are recorded in the baseline but not reported.
REVIEW_BANDS = (("_mm", 0.02), ("_mm_", 0.02), ("flatness", 0.02), ("symmetry", 0.02), ("error", 0.005))
DEFAULT_BAND = 1e-6


def band(metric):
    return next((b for key, b in REVIEW_BANDS if key in metric), DEFAULT_BAND)


def stack_versions():
    return {p: metadata.version(p) for p in ("pylinac", "numpy", "scipy", "PySide6")}


def input_digest(paths):
    """SHA-256 over each image's pixel data and beam angles, in a stable order."""
    h = hashlib.sha256()
    for p in sorted(str(x) for x in paths):
        ds = pydicom.dcmread(p)
        h.update(bytes(ds.PixelData))
        for tag in ("GantryAngle", "BeamLimitingDeviceAngle", "PatientSupportAngle"):
            h.update(str(getattr(ds, tag, "")).encode())
    return h.hexdigest()


def _version_key(name):
    parts = name.removeprefix("pylinac-").removesuffix(".json").split(".")
    return tuple(int(x) if x.isdigit() else 0 for x in parts)


class BaselineStore:
    def __init__(self, folder: Path, update: bool):
        self.folder, self.update = folder, update
        self.versions = stack_versions()
        self.path = folder / f"pylinac-{self.versions['pylinac']}.json"
        self.ref_path = self.path if self.path.exists() else self._newest_older()
        self.ref = json.loads(self.ref_path.read_text()) if self.ref_path else None
        self.recorded, self.drift = {}, {}

    def _newest_older(self):
        mine = _version_key(self.path.name)
        older = [p for p in self.folder.glob("pylinac-*.json") if _version_key(p.name) < mine]
        return max(older, key=lambda p: _version_key(p.name)) if older else None

    def check(self, case_id: str, inputs, metrics: dict):
        metrics = {k: float(v) for k, v in metrics.items()}
        digest = input_digest(inputs)
        self.recorded[case_id] = {"input_sha256": digest, "metrics": metrics}
        if self.update:
            return
        if self.ref is None:
            pytest.skip("no baseline yet: review the results, then run with --update-baselines")
        old = self.ref["cases"].get(case_id)
        if old is None:
            pytest.skip(f"case not in {self.ref_path.name}: run with --update-baselines")
        same_version = self.ref_path == self.path
        if old["input_sha256"] != digest:
            self.drift[case_id] = {"input_changed": True}
            msg = "input changed: pylinac's image generator moved, so analysis drift cannot be judged for this case"
            pytest.fail(msg) if same_version else pytest.xfail(msg)
        diffs = {}
        for k, v in metrics.items():
            ov = old["metrics"].get(k)
            if ov is None:
                diffs[k] = {"old": None, "new": v}
            elif not (math.isclose(v, ov, rel_tol=SAME_VERSION_RTOL, abs_tol=1e-9) if same_version
                      else abs(v - ov) <= band(k)):
                diffs[k] = {"old": ov, "new": v, "delta": v - ov, "review_band": band(k)}
        if diffs:
            self.drift[case_id] = diffs
            summary = "; ".join(f"{k}: {d['old']} -> {d['new']}" for k, d in diffs.items())
            if same_version:
                pytest.fail(f"changed on the same pylinac version ({self.versions}): {summary}")
            pytest.xfail(f"drift against {self.ref_path.name}: {summary}")

    def finish(self):
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if self.update and self.recorded:
            existing = json.loads(self.path.read_text())["cases"] if self.path.exists() else {}
            existing.update(self.recorded)
            self.folder.mkdir(exist_ok=True)
            self.path.write_text(json.dumps({"written": now, "versions": self.versions,
                                             "cases": dict(sorted(existing.items()))}, indent=1) + "\n")
        if self.drift:
            report = {"written": now, "compared_with": self.ref_path.name if self.ref_path else None,
                      "current_versions": self.versions,
                      "reference_versions": self.ref.get("versions") if self.ref else None, "drift": self.drift}
            (self.folder.parent / "drift-report.json").write_text(json.dumps(report, indent=1) + "\n")
