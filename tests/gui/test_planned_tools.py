"""Planned tests, as described stubs. Each one is skipped until its tool or feature exists; the docstring says what to
check and where the inputs come from. When you implement one, delete the skip marker and follow the patterns in
test_launcher.py (registration), test_known_answers.py (truth), test_parity.py (plumbing) and test_baselines.py (drift).

The tools listed here are the pylinac analyses PyBeam QA does not implement yet (docs/adding-a-pylinac-test.md, §1),
plus gaps in the tests of the tools it does implement.
"""
import pytest

planned = pytest.mark.skip(reason="planned: see the docstring")


# --- gaps in tests of existing tools -----------------------------------------------------------------------------

@planned
def test_starshot_reports_a_known_wobble():
    """Starshot has no generator in pylinac. Build the spokes the way PyBeam's own Benchmark Test dialog does
    (StarshotMainWindow.init_test_dialog: FilteredFieldLayer strips rotated about a chosen centre), plant a known
    isocentre offset per spoke pair, and check the worksheet's minimum-circle diameter and PASS/FAIL against the
    tolerance spin-box. Truth tolerance: one pixel at isocentre."""


@planned
def test_planar_imaging_matches_pylinac_for_every_phantom():
    """Parity for each of the 13 phantoms the Planar Imaging worksheet offers (LeedsTOR, QC-3, Las Vegas, SNC kV/MV,
    PTW EPID QC, IBA Primus A, Doselab MC2 kV/MV, …): load pylinac's demo image for that phantom
    (pylinac downloads demo files on first use; cache them for CI), analyse in the worksheet, and compare the
    contrast/MTF results with a direct pylinac call using the worksheet's settings."""


@planned
def test_every_tool_writes_its_pdf_report():
    """For each tool: run a known-answer analysis, then drive generate_report with its QDialog accepted and the save
    path set to tmp_path (patch worksheet_save_report), and check that a PDF is written with the expected page count.
    Expected to expose the suspected Winston-Lutz report KeyError: winston_lutz_widgets.py reads
    current_results["summary_plot"], which the worker no longer sets (wlutz.py, commented out)."""


@planned
def test_trs398_photon_worksheet_matches_reference_values():
    """Enter the IAEA TRS-398 worked example (or a locally verified set) into the photon worksheet and compare
    k_TP, k_pol, k_s, k_Q and dose per MU with the published values, and with pylinac.calibration.trs398 as parity.
    Same for electrons."""


@planned
def test_field_analysis_profiler_device():
    """pylinac's DeviceFieldAnalysis reads SNC Profiler .prm files (demo: 6fff.prm). If the Field Analysis tool gains
    device input, add a parity test against DeviceFieldAnalysis."""


# --- new tools (pylinac analyses not implemented yet) -------------------------------------------------------------

@planned
def test_catphan504_and_700_series():
    """The CatPhan tool is implemented and tested on pylinac's 503, 600 and 604 demo series (test_catphan.py). pylinac
    has a 504 demo (not cached here) and no 700 demo: add both to test_catphan_matches_pylinac when the data is
    available - the 700 needs a local, non-clinical scan."""


@planned
def test_quart_and_acr_phantoms():
    """QuartDVT (demo quart.zip), ACRCT and ACRMRILarge (no demo data: needs a local, non-clinical scan): analyse to
    COMPLETE and match pylinac (parity). ACR MRI low-contrast detectability is new in pylinac 3.45: pin its version."""


@planned
def test_vmat_drgs_drmlc_known_deviation():
    """DRGS/DRMLC/DRCS take exactly two images (open + DMLC). Use pylinac's demo zips for parity (max/abs-mean
    deviation, per-segment ratios). For a truth test, build the pair with pylinac's image generator: an open field and
    the same field with one segment scaled by a known percentage, and check that segment's deviation and PASS/FAIL
    at the 1.5 % default tolerance."""


@planned
def test_field_profile_analysis_metrics():
    """pylinac's FieldProfileAnalysis (metric plug-ins): flatness difference, symmetry point difference, penumbra,
    CAX-to-edge. Truths: linac-dicom-image-suite's penumbra and CAX offset sets (pixel-snapped, see
    test_known_answers.py); parity: a direct FieldProfileAnalysis call with the same metrics."""


@planned
def test_light_radiation_coincidence_known_offset():
    """StandardImagingFC2 / IMTLRad / DoselabRLf / IsoAlign / SNCFSQA: parity on pylinac's demo images (fc2.dcm,
    …). Truth: pylinac.core.image_generator.utils.generate_lightrad with a known field/BB offset."""


@planned
def test_multi_target_winston_lutz_known_bb_positions():
    """WinstonLutzMultiTargetMultiField: generate with generate_winstonlutz_multi_bb_multi_field and a known
    BBArrangement, plant per-BB offsets, check each BB's reported error and the max. Demo: SNC_MTWL_demo.zip."""


@planned
def test_tg51_worksheet_matches_reference_values():
    """If a TG-51 worksheet is added: the TG-51 addendum worked examples (photon and electron), compared with the
    worksheet's k_Q, P_ion, P_pol, P_TP and dose/MU; parity with pylinac.calibration.tg51 classes."""


@planned
def test_machine_log_gamma_matches_pylinac():
    """Dynalog / TrajectoryLog: pylinac's demo logs (AQA.dlg+BQA.dlg, Tlog.bin). Check gamma pass rate and RMS leaf
    error against a direct calc_map() with the same doseTA/distTA/threshold/resolution."""


# --- the results-stability architecture (docs/results-stability.md) -------------------------------------------------

@planned
def test_remaining_tools_decide_through_the_decision_module():
    """core/decision.py decides CatPhan and Winston-Lutz (tests/unit/test_decision.py). Starshot, Picket Fence and Field
    Analysis still compare with a strict < in set_analysis_outcome. For each: add its criteria to core/criteria.py
    (resolution and borderline band, with the reason), plant a known answer at exactly the tolerance and one pixel
    either side, and check that the worksheet shows PASS (borderline) / FAIL (borderline) / PASS / FAIL accordingly."""


@planned
def test_result_models_from_stored_pylinac_results():
    """For each tool's result model: from_pylinac() applied to a stored results_data(as_json=True) sample from each
    supported pylinac version gives the same model. A new pylinac version that reshapes results fails here, at unit
    level, instead of silently showing nothing in the worksheet."""


@planned
def test_reports_carry_provenance():
    """Every PDF report and its JSON sidecar record PyBeam QA version and commit, pylinac/numpy/scipy/PySide6
    versions, the result schema version, all analysis parameters, and the SHA-256 of each input file; re-running the
    analysis from the sidecar with the same versions reproduces the reported numbers exactly."""
