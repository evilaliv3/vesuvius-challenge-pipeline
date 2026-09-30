#!/usr/bin/env python3
"""Tool of ink-detector-0139 (PLAN 64): the descriptive row, no null (DECLARATION.md addition of 2026-09-24T17:23:21Z,
director 2026-09-24T17:22:24Z). Written 2026-09-24 by an agent of the coordinator.

Reads evidence/signal-null-v2.csv (existing predictions only, nothing inferred) and rewrites evidence/descriptive-row.csv
whole: one row per (sheet or segment, region, checkpoint), the sheet columns copied from the source row. For a 1447 sheet
with several null rows (half pitch, gapmin) the sheet columns must agree across them (check column); the latest is cited.
A missing source row reads «not measurable: source row not written».
Extension of 2026-09-24T18:2xZ (director's note 18:21:06Z): SHEET_ONLY targets take their sheet columns from
evidence/descriptive-sheet-only.csv (tool sheet_only_stats.py, same signal_null.py v2 code, region = the sheet's own valid
pixels, no copies); a checkpoint named in NOT_INFERRED reads «not measurable: not inferred».
"""
import csv, os, subprocess

S = "/data/scrollagent/runs/rev1/ink-detector-0139"
SRC = os.path.join(S, "evidence", "signal-null-v2.csv")
OUT = os.path.join(S, "evidence", "descriptive-row.csv")
TOOL = "ink-detector-0139/tools/descriptive_row.py"
NM = "not measurable: source row not written"
COPY = ["n_region", "region_cm2", "c_sheet", "ink_share_sheet", "mean_u8_sheet", "ext_threshold_u8", "ext_floor_mm",
        "ext_floor_px", "ext_px_ge_sheet", "ext_floor_components_sheet", "ext_px_ge_both", "ext_floor_components_both",
        "theirs_0826_floor_components_both", "theirs_0826_px_both", "theirs_0826_array_px", "voxel_mm",
        "accepted_uncalibrated_area_cm2", "certificate_status", "sheet_pred"]
SHEET_COLS = ["n_region", "c_sheet", "ink_share_sheet", "mean_u8_sheet", "ext_px_ge_sheet", "ext_floor_components_sheet"]
TARGETS = [  # (name, scroll, what, source labels, region_kind)
    ("published-w035", "PHerc0139", "labelled ink", ["published-w035"], "supervised"),
    ("published-w035", "PHerc0139", "labelled no ink", ["published-w035"], "supervised-noink"),
    ("published-w040", "PHerc0139", "labelled ink", ["published-w040"], "supervised"),
    ("published-w040", "PHerc0139", "labelled no ink", ["published-w040"], "supervised-noink"),
    ("FILL-SEED376-S0-pitchband", "PHerc1447", "our sheet, no labels",
     ["FILL-SEED376-S0-pitchband", "FILL-SEED376-S0-pitchband-gapmin"], "valid"),
    ("FILL-SEED316-S1-pitchband", "PHerc1447", "our sheet, no labels",
     ["FILL-SEED316-S1-pitchband", "FILL-SEED316-S1-pitchband-gapmin"], "valid"),
]
SHEET_ONLY = [("DELIV-seed325-S1-pitchband", "PHerc1447", "our sheet, no labels, sheet only (no null row)", "valid")]
NOT_INFERRED = {("DELIV-seed325-S1-pitchband", "seed43")}
SO = os.path.join(S, "evidence", "descriptive-sheet-only.csv")
HDR = ["tool", "time", "status", "sheet_or_segment", "scroll", "what", "region_kind", "checkpoint"] + COPY + \
      ["source_rows", "sheet_columns_agree_across_null_rows"]


def main():
    t = subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True, check=True).stdout.strip()
    rows = [r for r in csv.DictReader(l for l in open(SRC) if not l.startswith("#"))]
    out = []
    for name, scroll, what, labels, kind in TARGETS:
        for ck in ("seed42", "seed43"):
            src = [r for r in rows if r["label"] in labels and r["region_kind"] == kind and r["checkpoint"] == ck]
            o = {"tool": TOOL, "time": t, "status": "descriptive, no null", "sheet_or_segment": name, "scroll": scroll,
                 "what": what, "region_kind": kind, "checkpoint": ck}
            if not src:
                o.update({c: NM for c in COPY}); o["source_rows"] = NM; o["sheet_columns_agree_across_null_rows"] = NM
            else:
                last = src[-1]
                o.update({c: last[c] for c in COPY})
                o["source_rows"] = "; ".join(f"{r['label']} {r['time']}" for r in src)
                agree = all(all(r[c] == last[c] for c in SHEET_COLS) for r in src)
                o["sheet_columns_agree_across_null_rows"] = ("yes" if agree else "NO") if len(src) > 1 else "one row"
                if not agree:
                    raise SystemExit(f"refuse: sheet columns differ across the null rows of {name} {ck}")
            out.append(o)
    so = [r for r in csv.DictReader(l for l in open(SO) if not l.startswith("#"))] if os.path.exists(SO) else []
    for name, scroll, what, kind in SHEET_ONLY:
        for ck in ("seed42", "seed43"):
            o = {"tool": TOOL, "time": t, "status": "descriptive, no null", "sheet_or_segment": name, "scroll": scroll,
                 "what": what, "region_kind": kind, "checkpoint": ck}
            src = [r for r in so if r["label"] == name and r["checkpoint"] == ck]
            if (name, ck) in NOT_INFERRED:
                o.update({c: "not measurable: not inferred" for c in COPY + ["source_rows", "sheet_columns_agree_across_null_rows"]})
            elif not src:
                o.update({c: NM for c in COPY + ["source_rows", "sheet_columns_agree_across_null_rows"]})
            else:
                o.update({c: src[-1][c] for c in COPY})
                o["source_rows"] = f"evidence/descriptive-sheet-only.csv {src[-1]['time']} ({src[-1]['region_rule']})"
                o["sheet_columns_agree_across_null_rows"] = "no null row"
            out.append(o)
    with open(OUT, "w", newline="") as f:
        f.write(f"# by {TOOL}, {t}; descriptive, no null (director 2026-09-24T17:22:24Z; DECLARATION.md addition "
                "2026-09-24T17:23:21Z): sheet columns of evidence/signal-null-v2.csv, existing predictions, untreated windows; "
                "c_sheet = share of the region in components >= 1000 px at u8 >= 128; ext_* = Miller and Mueller's u8 >= 200 "
                "and 0.5 mm bounding box floor on our output; theirs_0826_* their numbers on 0826\n")
        w = csv.DictWriter(f, HDR); w.writeheader(); w.writerows(out)
    for o in out:
        print(o["sheet_or_segment"], o["region_kind"], o["checkpoint"], o["c_sheet"], o["ext_floor_components_sheet"],
              o["ext_floor_components_both"], o["sheet_columns_agree_across_null_rows"])


if __name__ == "__main__":
    main()
