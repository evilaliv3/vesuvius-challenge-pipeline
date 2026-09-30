#!/usr/bin/env python3
"""evidence/field.csv, PLAN 68: one row per published surface of PHerc0826, PHerc0800 and Stevens' PHerc1667 output.

Every number is read back from the CSV the measuring tool wrote, named in the row's sources column; nothing is
measured here. A value the tools did not write is «not measurable», never zero. A row whose certified area in the
calibrated mode passes 4.2 cm2 on 0826 or 0800 says yes in certified_above_4_2_cm2_sends_reading_here (the director's
falsifier of 2026-09-24T07:36:15Z). Checks are columns: square_equals_reference against published-segments-eligible,
and rows_expected against rows_got per input CSV.

Also writes evidence/field-sums.csv: per scroll, the sums over its surfaces of delivered area and certified area per
mode (surfaces summed with every overlap counted: a bound, not a deduplicated coverage), beside Stevens' own wording.

    field_table.py
"""
import csv, glob, json, os, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(S, "evidence")
R = "/data/scrollagent/runs/rev1"
ME = "field-0826-0800/tools/field_table.py"
NM = "not measurable"
BAR = 4.2
MODES = ("asis", "pitchband", "pitchspan")
REF = os.path.join(R, "published-segments-eligible/evidence/segments-eligible.csv")
DECISION = os.path.join(R, "certified-area/evidence/calibration-decision.csv")

COLS = ["scroll", "surface", "source", "where_published", "voxel_um", "voxel_source", "prediction_for_coverage",
        "in_first_light_window", "cells_delivered", "step_i_mm", "step_j_mm", "delivered_area_cm2",
        "square_delivered_mm", "square_delivered_reference_mm", "square_equals_reference", "covered_share_tol1",
        "covered_share_swapped_xy", "frame_fitting_better", "square_covered_mm"] + \
       ["certified_area_cm2_%s" % m for m in MODES] + ["certified_square_mm_%s" % m for m in MODES] + \
       ["certified_share_of_cells_pitchband", "cells_outside_axis", "calibrated_mode", "calibration_note",
        "certified_area_cm2_calibrated_mode", "certified_above_4_2_cm2_sends_reading_here", "axis_source",
        "pitch_source", "status", "note", "sources", "tool"]


def rows(path):
    L = [l for l in open(path, newline="") if not l.lstrip('"').startswith("#")]
    return list(csv.DictReader(L))


def one(path, expect=1):
    rr = rows(path)
    if len(rr) != expect:
        sys.exit("REFUSED: %s holds %d rows, %d expected" % (path, len(rr), expect))
    return rr


def rel(p):
    return os.path.relpath(p, R)


def blank(**kw):
    r = {c: NM for c in COLS}
    r.update(kw)
    r["tool"] = ME
    return r


def decision():
    d = rows(DECISION)
    if len(d) != 1:
        sys.exit("REFUSED: %s holds %d rows" % (DECISION, len(d)))
    return d[0]["decision"]


def surface_rows(scroll, where, window, axis_src, pitch_src, ref=None, note_extra="", cal_note=""):
    vox_man = json.load(open("/data/scrollagent/pipeline/datasets/manifests/%s.json" % scroll))
    mode = decision()
    cov = {r["label"]: r for r in rows(os.path.join(EV, "covered-%s.csv" % scroll))}
    cert = {}
    for r in rows(os.path.join(EV, "certified-%s.csv" % scroll)):
        cert[(r["label"], r["mode"])] = r
    out = []
    for f in sorted(glob.glob(os.path.join(EV, "squares-delivered-%s-*.csv" % scroll))):
        name = os.path.basename(f)[len("squares-delivered-%s-" % scroll):-4]
        label = "%s:%s" % (scroll, name)
        d = one(f)[0]
        cf = os.path.join(EV, "squares-covered-%s-%s.csv" % (scroll, name))
        c = one(cf)[0] if os.path.exists(cf) else None
        cv = cov.get(label)
        r = blank(scroll=scroll, surface=name, where_published=where, voxel_um=vox_man["voxel_um"],
                  voxel_source="pipeline/datasets/manifests/%s.json voxel_um_source" % scroll,
                  prediction_for_coverage=vox_man.get("prediction_for_coverage", vox_man.get("source", NM)),
                  in_first_light_window=window, axis_source=axis_src, pitch_source=pitch_src,
                  calibration_note=cal_note)
        r["source"] = "published"
        if d["status"] != "measured":
            r.update(status="square not measurable: " + d["status"])
        else:
            si, sj, n = float(d["step_i_mm"]), float(d["step_j_mm"]), int(d["points"])
            r.update(cells_delivered=n, step_i_mm=d["step_i_mm"], step_j_mm=d["step_j_mm"],
                     delivered_area_cm2="%.6f" % (n * si * sj / 100.0), square_delivered_mm=d["square_mm_min_step"])
        if ref is not None:
            rr = ref.get(name)
            r["square_delivered_reference_mm"] = rr if rr is not None else NM
            r["square_equals_reference"] = ("yes" if rr is not None and rr == r["square_delivered_mm"]
                                            else "NO" if rr is not None else NM)
        else:
            r["square_delivered_reference_mm"] = "no earlier measurement of this surface"
            r["square_equals_reference"] = NM
        if cv:
            r.update(covered_share_tol1=cv["covered_share"], covered_share_swapped_xy=cv["covered_share_swapped_xy"],
                     frame_fitting_better=cv["frame_fitting_better"])
        if c and c["status"] == "measured":
            r["square_covered_mm"] = c["square_mm_min_step"]
        for m in MODES:
            k = cert.get((label, m))
            if k:
                r["certified_area_cm2_%s" % m] = k["certified_area_cm2"]
                r["certified_square_mm_%s" % m] = k["certified_square_mm"]
                if m == "pitchband":
                    r["certified_share_of_cells_pitchband"] = k["certified_share_of_cells"]
                    r["cells_outside_axis"] = k["cells_outside_axis"]
        r["calibrated_mode"] = mode
        a = r["certified_area_cm2_%s" % mode]
        r["certified_area_cm2_calibrated_mode"] = a
        if scroll in ("PHerc0826", "PHerc0800"):
            r["certified_above_4_2_cm2_sends_reading_here"] = NM if a == NM else ("yes" if float(a) > BAR else "no")
        else:
            r["certified_above_4_2_cm2_sends_reading_here"] = "not applicable, the falsifier names 0826 and 0800 only"
        r["status"] = r["status"] if r["status"] != NM else "measured"
        r["note"] = note_extra
        r["sources"] = "; ".join(rel(p) for p in [f, cf, os.path.join(EV, "covered-%s.csv" % scroll),
                                                 os.path.join(EV, "certified-%s.csv" % scroll)] if os.path.exists(p))
        out.append(r)
    return out


def main():
    ref = {r["segment"]: r["square_mm_min_step"] for r in rows(REF) if r["scroll"] == "PHerc0800"}
    table = []
    # PHerc0826: nothing published that carries volume coordinates
    table.append(blank(
        scroll="PHerc0826", surface="none published", source="not published",
        where_published="bucket PHerc0826/ has no segments/ prefix; representations/ holds predictions/surfaces "
                        "(m7 zarr, normal-grids), predictions/lasagna and umbilicus/ only (evidence/bucket-listing.txt); "
                        "dl.ash2txt spiral_datasets/PHerc0826 holds tracks/ only, the fit's input "
                        "(evidence/spiral-datasets-listing.txt); first-light-pherc0826 at ee8eef1 publishes renders and "
                        "crops (analysis/), renders/ holds README.md and .gitkeep only, no mesh or tifxyz",
        voxel_um=json.load(open("/data/scrollagent/pipeline/datasets/manifests/PHerc0826.json"))["voxel_um"],
        voxel_source="pipeline/datasets/manifests/PHerc0826.json voxel_um_source",
        prediction_for_coverage="on disk, data/datasets/PHerc0826/0 (m7 L0); not read, no surface to test",
        in_first_light_window="no published surface lies in the window w010 to w065, slices 10,000 to 11,000: their "
                              "spiral fit wrote 240 tifxyz (winding range [10, 130), their logs/2026-08-27-spiral-fit-"
                              "run-stats.md) and none is in the repository or the bucket; their render is 4560 x "
                              "392760 px at 9.362 um (analysis/.../mechanical_analysis_summary.json image_shape, "
                              "native_um_per_px), a picture without volume coordinates",
        axis_source="published umbilicus 20250821151701-umbilicus-20260808113303.json exists; not needed",
        calibrated_mode=decision(),
        certified_above_4_2_cm2_sends_reading_here="no: no published 0826 surface exists to be certified",
        status="not measurable, no published surface",
        note="Miller and Mueller: «I didn't see any ink in the window» (README), threshold 0.7843 on 0139 w035",
        sources="field-0826-0800/evidence/bucket-listing.txt; field-0826-0800/evidence/spiral-datasets-listing.txt; "
                "field-0826-0800/scratch/first-light-pherc0826 (git ee8eef11e57c)"))
    table += surface_rows(
        "PHerc0800", "s3://vesuvius-challenge-open-data/PHerc0800/segments/<id>/mesh/<id>-on-20250521135224-8.64um.tifxyz",
        "not applicable (0800)", "field-0826-0800/evidence/umbilicus-PHerc0800.csv and axis-quality-PHerc0800.csv "
        "(house ladder, no published umbilicus)", "field-0826-0800/evidence/pitch-PHerc0800/pitch-adopted.csv",
        ref=ref, note_extra="auto_grown segments of 2025-10-28/29 on volume 20250521135224, tifxyz step 20 voxels, "
                            "the step the calibration was made at",
        cal_note="calibrated on published tifxyz at step 20 voxels, this surface's step")
    stevens = glob.glob(os.path.join(EV, "squares-delivered-PHerc1667-*.csv"))
    if stevens:
        table += surface_rows(
            "PHerc1667", "https://dl.ash2txt.org/community-uploads/will/s4_10_components_tifxyz.zip (1,303,244,621 bytes, "
            "Last-Modified 2026-09-01T01:00:57Z)", "not applicable (1667)",
            "field-0826-0800/evidence/umbilicus-PHerc1667*.csv (house ladder on the medial prediction, no published "
            "umbilicus found)", "field-0826-0800/evidence/pitch-PHerc1667/pitch-adopted.csv",
            note_extra="Stevens' ten components, taken as the output of the award «around 365 cm² of coverage on PHerc. "
                       "1667» (scrollprize.org/winners); the zip is not tied to the 365 in words by him. Coverage is on "
                       "bruniss' s4_059_medial_ome.zarr, the prediction his chain grew from, not an organisers' m7",
            cal_note="calibration made at step 20 voxels; these components are at step 4, where item 65 step 4 is still "
                     "open: the calibrated mode is read as stated in calibration-decision.csv and is not calibrated at step 4")
    else:
        table.append(blank(scroll="PHerc1667", surface="Stevens' ten components", source="published, not yet measured",
                           status="not measurable yet: fetch or measurement not finished"))
    table.append(blank(
        scroll="PHerc1667", surface="the 20 segments of the bucket (w011 to w041 flatboi and one merged)",
        source="published by others", where_published="s3://vesuvius-challenge-open-data/PHerc1667/segments/",
        status="not measured: item 68 asks for Stevens' output on 1667; no row of these carries his name "
               "(metadata.json has no match for Stevens)", sources="field-0826-0800/evidence/bucket-listing.txt"))
    out = os.path.join(EV, "field.csv")
    with open(out, "w", newline="") as fh:
        fh.write('"# one row per published surface of PHerc0826, PHerc0800 and Stevens\' PHerc1667 output (and one row '
                 'per source that publishes none), written by %s from the CSVs named in the sources column. square: '
                 'seed-search-1447/tools/square.py as delivered and on the cells covered at 1 voxel; coverage: '
                 'covered_by_prediction.covered_mask through field-0826-0800/tools/covered_field.py; certificate: '
                 'certified-area/tools/certified_region.py through field-0826-0800/tools/certified_region_field.py, three '
                 'modes, the calibrated one from certified-area/evidence/calibration-decision.csv. delivered_area_cm2 = '
                 'cells x step_i_mm x step_j_mm, the bound no certified area can pass. not measurable is never zero."\n' % ME)
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in table:
            w.writerow(r)
    # sums
    sums = []
    for sc in ("PHerc0800", "PHerc1667"):
        rs = [r for r in table if r["scroll"] == sc and r["source"] == "published" and r["delivered_area_cm2"] != NM]
        if not rs:
            continue
        s = {"scroll": sc, "surfaces": len(rs),
             "delivered_area_cm2_sum": "%.4f" % sum(float(r["delivered_area_cm2"]) for r in rs)}
        for m in MODES:
            v = [r["certified_area_cm2_%s" % m] for r in rs]
            s["certified_area_cm2_sum_%s" % m] = NM if NM in v else "%.4f" % sum(float(x) for x in v)
        s["largest_certified_area_cm2_calibrated_mode"] = max(
            (float(r["certified_area_cm2_calibrated_mode"]) for r in rs if r["certified_area_cm2_calibrated_mode"] != NM),
            default=NM)
        s["their_wording"] = ("«around 365 cm² of coverage on PHerc. 1667» (scrollprize.org/winners, August 2026)"
                              if sc == "PHerc1667" else "")
        s["how"] = "sum over the surfaces of this scroll, every overlap counted: a bound, not a deduplicated coverage"
        sums.append(s)
    with open(os.path.join(EV, "field-sums.csv"), "w", newline="") as fh:
        fh.write('"# per scroll, sums over the rows of evidence/field.csv, written by %s"\n' % ME)
        keys = ["scroll", "surfaces", "delivered_area_cm2_sum"] + ["certified_area_cm2_sum_%s" % m for m in MODES] + \
               ["largest_certified_area_cm2_calibrated_mode", "their_wording", "how"]
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for s in sums:
            w.writerow(s)
    print("wrote %s, %d rows; field-sums.csv, %d rows" % (rel(out), len(table), len(sums)))


if __name__ == "__main__":
    main()
