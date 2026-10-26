"""Baseline tests: the full results of fixed reference cases, stored per pylinac version in tests/gui/baselines/.
They exist to make drift visible across pylinac upgrades, not to judge correctness (truth and parity tests do that).
Workflow: docs/results-stability.md, "An upgrade procedure, end to end". Write a baseline with --update-baselines."""
import pytest

from helpers import field_image, field_metrics, run_worksheet, wl_images


def wl_case(qtbot, folder, **offsets):
    from ui.linac_qa.winston_lutz_widgets import WinstonLutzMainWindow
    files = wl_images(folder, **offsets)
    _, ws = run_worksheet(qtbot, WinstonLutzMainWindow, files, lambda w: w.ui.bb_size_dsb.setValue(5.0))
    r = ws.current_results
    metrics = {k: r[k] for k in ("max_2d_cax_to_bb_mm", "median_2d_cax_to_bb_mm", "mean_2d_cax_to_bb_mm",
                                 "gantry_3d_iso_diameter_mm")}
    metrics.update({f"bb_shift_{a}_mm": r["bb_shift_vector"][a] for a in "xyz"})
    return files, metrics


def pf_case(qtbot, folder):
    from pylinac.core.image_generator import AS1200Image, FilteredFieldLayer, GaussianFilterLayer, generate_picketfence
    from ui.linac_qa.picket_fence_widgets import PicketFenceMainWindow
    image = folder / "pf.dcm"
    generate_picketfence(AS1200Image(sid=1500), FilteredFieldLayer, file_out=str(image),
                         final_layers=[GaussianFilterLayer(sigma_mm=1)])
    _, ws = run_worksheet(qtbot, PicketFenceMainWindow, [image])
    pf = ws.current_results["picket_fence_obj"]
    return [image], {"max_error_mm": pf.max_error, "abs_median_error_mm": pf.abs_median_error}


def field_case(qtbot, folder, image=None, **slopes):
    from ui.linac_qa.field_analysis_widgets import FieldAnalysisMainWindow
    image = image or field_image(folder / "field.dcm", **slopes)
    _, ws = run_worksheet(qtbot, FieldAnalysisMainWindow, [image])
    return [image], field_metrics(ws)


def catphan_case(qtbot, folder, zip_name, phantom):
    from pylinac.core.io import retrieve_demo_file
    from ui.linac_qa.catphan_widgets import CatPhanMainWindow
    try:
        source = retrieve_demo_file(zip_name)
    except Exception as err:
        pytest.skip(f"pylinac demo file {zip_name} unavailable: {err}")
    _, ws = run_worksheet(qtbot, CatPhanMainWindow, [source], lambda w: w.ui.phantomCB.setCurrentText(phantom))
    r = ws.analysis_data["result"]
    metrics = {f"hu_{m.name.replace(' ', '_').replace('%', 'pct')}": m.measured_hu for m in r.hu_materials}
    metrics.update(roll_deg=r.roll_deg, uniformity_index=r.uniformity_index, slice_thickness_mm=r.slice_thickness_mm,
                   geometry_avg_line_distance_mm=r.geometry_avg_line_distance_mm,
                   low_contrast_rois_seen=r.low_contrast_rois_seen)
    metrics.update({f"mtf_{p}_lp_mm": v for p, v in r.mtf_lp_mm if v is not None})
    return [source], metrics


CASES = {
    "catphan604_demo": lambda qtbot, d, _: catphan_case(qtbot, d, "CatPhan604.zip", "CatPhan 604"),
    "wl_left_0.5mm": lambda qtbot, d, _: wl_case(qtbot, d, offset_mm_left=0.5),
    "wl_left2_in3_up6": lambda qtbot, d, _: wl_case(qtbot, d, offset_mm_left=2, offset_mm_in=3, offset_mm_up=6),
    "pf_perfect": lambda qtbot, d, _: pf_case(qtbot, d),
    "field_open_100mm": lambda qtbot, d, _: field_case(qtbot, d),
    "field_tilted_100mm": lambda qtbot, d, _: field_case(qtbot, d, slope_x=0.05, slope_y=-0.03),
}
FAUXPID_CASES = {  # linac-dicom-image-suite images; skipped when FauxPID is not installed
    "fauxpid_flatness_two_percent_variance": ("Flatness", "flatness_two_percent_variance_10x10"),
    "fauxpid_symmetry_two_percent_x_point_ratio": ("Symmetry", "symmetry_two_percent_x_point_ratio_10x10"),
    "fauxpid_penumbra_2_mm": ("Penumbra", "penumbra_2_mm"),
    "fauxpid_cax_offset_7_mm_x_and_y": ("CAX Offset", "cax_offset_7_mm_x_and_y_10x10"),
}


@pytest.mark.parametrize("case_id", sorted(CASES))
def test_baseline(qtbot, tmp_path, baseline_store, case_id):
    inputs, metrics = CASES[case_id](qtbot, tmp_path, None)
    baseline_store.check(case_id, inputs, metrics)


@pytest.mark.parametrize("case_id", sorted(FAUXPID_CASES))
def test_baseline_fauxpid(qtbot, tmp_path, baseline_store, fauxpid_images, case_id):
    folder, stem = FAUXPID_CASES[case_id]
    inputs, metrics = field_case(qtbot, tmp_path, image=fauxpid_images / folder / f"{stem}.dcm")
    baseline_store.check(case_id, inputs, metrics)
