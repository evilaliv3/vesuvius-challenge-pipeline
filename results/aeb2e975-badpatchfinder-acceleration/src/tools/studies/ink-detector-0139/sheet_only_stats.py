#!/usr/bin/env python3
"""Tool of ink-detector-0139 (PLAN 64): the sheet columns of the descriptive row for a sheet with no signal-null-v2 row
(director's note 2026-09-24T18:21:06Z, seed325 S1). Written 2026-09-24 by an agent of the coordinator.

  sheet_only_stats.py --label L --tifxyz T --pred P --voxel-mm V --checkpoint C [--accepted-area-cm2 A] [--certificate-status S]

Same code as signal_null.py v2 for the sheet columns: region = SN.valid_on_crop(sheet tifxyz, whole render) (test2's rule
without the copies, which do not exist); c_sheet = SN.coherent_mask share at u8 >= 128 (components >= 1000 px);
ext_* = SN.ext_stats (their u8 >= 200 and 0.5 mm bounding box floor), opposite direction not inferred. Existing prediction
only; nothing inferred, fetched or rendered. Appends one row to evidence/descriptive-sheet-only.csv, which
descriptive_row.py merges.
"""
import argparse, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import signal_null as SN  # noqa: E402

OUT = os.path.join(SN.EVID, "descriptive-sheet-only.csv")
HDR = ["tool", "time", "label", "checkpoint", "region_rule", "n_region", "region_cm2", "c_sheet", "ink_share_sheet",
       "mean_u8_sheet", "ext_threshold_u8", "ext_floor_mm", "ext_floor_px", "ext_px_ge_sheet", "ext_floor_components_sheet",
       "ext_px_ge_both", "ext_floor_components_both", "theirs_0826_floor_components_both", "theirs_0826_px_both",
       "theirs_0826_array_px", "voxel_mm", "accepted_uncalibrated_area_cm2", "certificate_status", "sheet_pred"]


def main():
    ap = argparse.ArgumentParser()
    for k in ("--label", "--tifxyz", "--pred", "--voxel-mm", "--checkpoint"):
        ap.add_argument(k, required=True)
    ap.add_argument("--accepted-area-cm2", default="not applicable")
    ap.add_argument("--certificate-status", default="not applicable")
    a = ap.parse_args()
    pred = SN.SC.load_pred(a.pred, None)
    h, w = pred.shape
    region = SN.valid_on_crop(a.tifxyz, [0, 0, w, h])
    nR = int(region.sum())
    coh = SN.coherent_mask(pred >= SN.INK_U8, region)
    ex = SN.ext_stats({"sheet": pred, "plus": pred, "minus": pred}, None, region, float(a.voxel_mm), SN.external_ref())
    vv = float(a.voxel_mm)
    row = {"tool": "ink-detector-0139/tools/sheet_only_stats.py", "time": SN.now(), "label": a.label, "checkpoint": a.checkpoint,
           "region_rule": "signal_null.valid_on_crop(sheet tifxyz, whole render); no copies",
           "n_region": nR, "region_cm2": f"{nR * vv ** 2 / 100:.4f}", "c_sheet": f"{coh.sum() / max(1, nR):.5f}",
           "ink_share_sheet": f"{((pred >= SN.INK_U8) & region).sum() / max(1, nR):.5f}",
           "mean_u8_sheet": f"{pred[region].mean():.2f}", "voxel_mm": a.voxel_mm,
           "accepted_uncalibrated_area_cm2": a.accepted_area_cm2, "certificate_status": a.certificate_status,
           "sheet_pred": a.pred}
    for k in HDR:
        if k not in row:
            row[k] = ex[k]
    SN.TOOL = "ink-detector-0139/tools/sheet_only_stats.py"
    SN.append_row(OUT, HDR, row, "sheet columns of the descriptive row for a sheet with no signal-null-v2 row, same code as "
                  "signal_null.py v2 (coherent_mask, ext_stats); director's note 2026-09-24T18:21:06Z")
    print({k: row[k] for k in ("label", "checkpoint", "n_region", "c_sheet", "ext_px_ge_sheet", "ext_floor_components_sheet")})


if __name__ == "__main__":
    main()
