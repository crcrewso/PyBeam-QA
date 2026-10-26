# Keeping results trustworthy as pylinac changes

**The problem.** PyBeam QA's numbers come from pylinac, and pylinac's numbers move between releases:

- algorithms are refined;
- defaults change;
- result data changes shape (fields renamed, nested, or turned into pydantic models);
- rounding and interpolation choices propagate.

None of these is a bug in itself, but each can:

- change a reported value slightly;
- flip a borderline PASS to FAIL;
- break a worksheet that reads a field which no longer exists;
- make an old report impossible to reproduce.

The same happens to the synthetic images used to test PyBeam, because pylinac's image generator also lives in
pylinac.

This document proposes an architecture that makes those movements **visible, attributable and reviewable**, instead
of silent. The pieces are independent and can be adopted one at a time. A working prototype of the testing half is
in `tests/gui/`.

---

## What was measured while writing this

Measured on a Linux VM, October 2026, with PyBeam QA `main`, pylinac 3.49.0 and PySide6 6.7.0.

| Observation | Why it matters |
|---|---|
| A field offset planted as **1.0 mm** was reported as **1.008 mm** (also 5→5.05, 10→10.09, 3→3.03, 7→7.06 mm) | pylinac's image generator snaps offsets to whole pixels (0.336 mm on an AS1200 panel). The ground truth itself carries ±½ pixel of quantisation |
| A Winston-Lutz BB planted **1.0 mm** out was reported as **1.01 mm** and the worksheet said **FAIL** against a 1.0 mm tolerance | A rounding-level difference decided the outcome. On a real machine, a pylinac release that moved this by 0.01 mm would flip clinical results with no change to the linac |
| Images labelled "2 % flatness" in linac-dicom-image-suite read **0.76 %** under PyBeam's Varian protocol, and its "102 % point-ratio symmetry" image read **103 %** | "The same metric" depends on its definition, field region and normalisation. Truths are only truths for one definition |
| A Winston-Lutz set with a 6 mm vertical BB offset came back with the **opposite vertical sign** from pylinac's own generator | Coordinate conventions differ between tools. A reference set must state its conventions and be checked against the analysis library once |
| `results_data()` objects, `as_dict` layouts and plot method names differ between pylinac 3.40 and 3.45 (e.g. VMAT gained `plotly_analyzed_images` and DRCS fields; Winston-Lutz gained `missing_axis_value`) | Worksheets that read pylinac objects directly break when shapes change |
| The `copilot/fix-1` CatPhan branch, once its crashes were patched, analysed all three demo phantoms, but **displayed only the phantom name**: its code reads `hu_linearity` and `uniformity` attributes that pylinac's result does not have (pylinac nests them under `ctp404` and similar). The `codegen-bot` branch passed `low_contrast_threshold` where pylinac expects `low_contrast_tolerance` | Shape and signature mismatches fail **silently** (nothing shown) or late (only when a user presses Analyze). An adapter with a unit test against a stored pylinac result catches both at test time |

---

## The architecture

```
                 ┌──────────────── pylinac (pinned) ────────────────┐
images, params → │ analysis classes   │ image_generator (test-only) │
                 └─────────┬───────────────────────────────────────┘
                           │ raw pylinac objects (version-specific shapes)
                 ┌─────────▼──────────┐
                 │ 1. Adapter layer   │ core/analysis/<test>.py → core/results/<test>.py
                 │   (one per test)   │ converts pylinac output → PyBeam result model (full precision)
                 └─────────┬──────────┘
                 ┌─────────▼──────────┐   ┌──────────────────────────┐
                 │ 2. Decision module │◄──│ tolerance, resolution,   │
                 │   PASS/FAIL/BORDER │   │ boundary rule (per test) │
                 └─────────┬──────────┘   └──────────────────────────┘
                 ┌─────────▼──────────┐
                 │ 3. Provenance      │ versions, parameters, input SHA-256, schema version
                 └─────────┬──────────┘
          ┌────────────────┼─────────────────┐
     worksheet display   PDF report     JSON sidecar (re-analysable record)
     (4. presentation rounding only here)
```

### 1. An adapter layer that owns the result shape

Today a worksheet receives a dict that often carries the **live pylinac object** (`"picket_fence_obj"`,
`"field_analysis_obj"`, `"planar_img_obj"`) and reads pylinac attributes directly, both in the UI and in the
report. Every pylinac shape change therefore lands in two or three files per test.

Proposal: each test gets a small, PyBeam-owned result model, e.g. `core/results/winston_lutz.py`. It is a dataclass
or pydantic model with an explicit `schema_version` and **full-precision** values with units in the field names
(`max_2d_cax_to_bb_mm`).

- The worker builds it from pylinac's `results_data()` in **one function**, `from_pylinac(obj) -> WinstonLutzResult`,
  and emits it instead of the pylinac object.
- The worksheet, the report and the decision module read only the model.
- When pylinac renames or reshapes something, only `from_pylinac` changes, and a unit test of `from_pylinac` against a
  stored pylinac `results_data(as_json=True)` sample catches it.
- Plots are the exception: they still need the pylinac object or arrays, so keep a separate, optional `plots` payload
  rather than mixing it into the result.

### 2. One decision module, on raw values, with an explicit resolution

Today each worksheet's `set_analysis_outcome` compares a value with the tolerance spin-box in UI code. The boundary
rule is implicit: Winston-Lutz, Starshot and Picket Fence all use a strict `<`, so a value exactly at the tolerance
FAILs, and nothing says so on screen. Proposal: a single `core/decision.py`:

```python
@dataclass(frozen=True)
class Criterion:
    name: str                 # "max_2d_cax_to_bb_mm"
    tolerance: float          # 1.0
    resolution: float         # 0.01 – the decision precision, stated by the test's owner
    inclusive: bool = True    # PASS if value <= tolerance (state it; don't let it vary by test)
    action_level: float | None = None

def decide(value: float, c: Criterion) -> Outcome:
    q = round(value / c.resolution) * c.resolution          # decide at the stated precision, once
    if (q <= c.tolerance) if c.inclusive else (q < c.tolerance):
        return Outcome.PASS if not borderline(value, c) else Outcome.PASS_BORDERLINE
    return Outcome.FAIL if not borderline(value, c) else Outcome.FAIL_BORDERLINE

def borderline(value, c):     # within one measurement step of the line → flag it, don't hide it
    return abs(value - c.tolerance) <= measurement_step(c)
```

- **The resolution is a stated, reviewed number per test**, not an accident of display formatting. A pylinac change
  below that resolution cannot change an outcome.
- **The boundary rule is the same everywhere** (`<=` or `<`, chosen once).
- **"Borderline" is surfaced in the UI and in the report.** A result within one measurement step of the tolerance —
  for an EPID, roughly one pixel at isocentre — is shown as such, so a 1.008 mm against 1.0 mm FAIL is read with the
  care it deserves.
- The worksheet only *displays* the outcome.

### 3. Provenance with every result

Every analysis records, and every report prints in a small appendix:

- PyBeam QA version and git commit;
- pylinac, numpy, scipy and PySide6 versions;
- the result `schema_version`;
- every analysis parameter (tolerances, protocol, BB size, edge method…);
- the SHA-256 of every input file;
- the analysis time and time zone.

Write the same record as a **JSON sidecar** next to the PDF (`report.pdf` → `report.pybeamqa.json`). That turns any
past result into something that can be **re-run with the exact versions it was produced with**, months later, when
someone asks why a number changed.

pylinac already puts `pylinac_version` and `date_of_analysis` in `results_data()`; this extends the idea to the
whole stack.

### 4. Presentation rounding only at the edge

Round only when formatting for the screen or the PDF, through one formatter per quantity type (mm to 2 decimals, %
to 2, HU to 1, …). Never compare rounded strings and never store rounded values in the result model. This keeps
"what the analysis said", "what was shown" and "what was decided" separate and auditable.

### 5. Pin pylinac, and upgrade on purpose

- **Pin exact versions in a lockfile** (`uv.lock`, or `requirements.txt` with `==`) for every release of PyBeam QA.
  The README's "pylinac 3.22.0+" means two installations of the same PyBeam release can report different numbers.
- **Upgrade pylinac as a reviewed change**, with the drift report described below attached to the pull request.
- **Run a canary in CI:** the test suite against the newest pylinac, allowed to fail, producing the drift report, so
  changes are seen before anyone upgrades.

---

## Testing that separates three different questions

A single "expected value" assertion mixes three questions that fail for different reasons. Separating them is what
makes drift manageable. All three exist in `tests/gui/`.

| Kind | Question | Expected value comes from | Tolerance | Fails when | Owner action |
|---|---|---|---|---|---|
| **Truth** | Does the tool measure the physics right? | Planted in a synthetic image (BB offset, field size, penumbra) | The input's own uncertainty, e.g. ±½ pixel = ±0.17 mm on AS1200, plus the analysis' known bias | the tool is wrong | fix the code |
| **Parity** | Does the GUI show what pylinac computed? | A direct pylinac call on the same file with the same parameters, in the same run | exact (1e-9) | GUI plumbing is wrong (wrong parameter passed, wrong field displayed, unit slip) | fix the plumbing |
| **Baseline** | Has anything moved since we last looked? | A stored snapshot per pylinac version (`tests/gui/baselines/`) | tiny for the same version; a review band across versions | anything changed: pylinac, numpy, the generator, or PyBeam | **review**: accept (update the snapshot, note why) or reject (pin back, fix) |

Truth and parity tests are **version-independent**, so they keep passing across pylinac upgrades unless something
is genuinely wrong. Baseline tests are **expected** to change across versions; their job is to make the change
visible and to force a human decision.

### How the baseline prototype works (`tests/gui/test_baselines.py`)

- Reference cases are deterministic synthetic inputs, generated without random noise, so they are byte-identical
  between runs on one pylinac version. Each case records the **SHA-256 of its inputs** in the baseline. If the
  generator itself changed, the test reports **"input changed"** rather than "analysis changed", which separates
  generator drift from analysis drift.
- Baselines are stored per pylinac version: `tests/gui/baselines/pylinac-<version>.json`. They hold full-precision
  values plus the versions of pylinac, numpy, scipy and PySide6.
- **Same pylinac version:** values must match within 1e-6 (relative). A failure here means non-determinism or an
  environment change, which is worth knowing about.
- **No baseline for this version:** the newest older baseline is used in *drift mode*. Every metric that moved more
  than its review band is listed in `tests/gui/drift-report.json`, and the test is marked `xfail` with a summary, so
  an upgrade shows up as a reviewable report instead of a wall of failures.
- `pytest tests/gui --update-baselines` writes the snapshot for the current version once the drift has been reviewed.

### Frozen reference images (recommended next step)

Generated inputs move when pylinac's generator moves. For long-lived baselines, also keep a **frozen reference image
set**: the generated DICOM files, with a `MANIFEST.json` of SHA-256 values, ground truths, units and coordinate
conventions. Store it outside the git repository (a release asset or a shared drive), because EPID images are
megabytes each. Baseline tests then run on the frozen files, and generator drift can no longer move them at all.

Do not use clinical images for this. Synthetic images with stated truths are enough, and they can be shared.

---

## An upgrade procedure, end to end

1. Bump pylinac in the lockfile on a branch.
2. Run `pytest tests/gui`. Truth and parity tests must still pass; if not, something broke.
3. Read `tests/gui/drift-report.json`: which metrics moved, by how much, and whether any crossed a decision
   resolution or a tolerance.
4. For each material change, find the reason in pylinac's changelog and decide whether it is acceptable.
5. Accept: run `pytest tests/gui --update-baselines`, commit the new `baselines/pylinac-<new>.json`, and record the
   reasoning in the PR and the changelog.
6. If an accepted change can move a clinical outcome, say so in the release notes, so that sites can re-baseline their
   own trend charts.

---

## What to do first

In order of value for the effort:

1. Pin pylinac exactly, and record versions in reports (an afternoon).
2. Move PASS/FAIL into one decision module with stated resolutions and a "borderline" flag (a day or two).
3. Adopt the three-kind test layout (the prototype is in `tests/gui/`).
4. Introduce result models test by test, starting with the next new tool, so that it never reads pylinac objects in
   the UI.
5. Freeze a reference image set.
