#!/usr/bin/env python3
"""A post hoc side check, not part of the answer: the raw grids under segments/raw/.

PHerc1203 publishes no segment. Its segments/ prefix holds one entry, raw/, and under it 22
grids written by vc_grow_seg_from_seed. Those grids name no volume in their metadata, so under
the declaration of this study they are not meshes on the scroll's own volume and no number of
theirs enters evidence/segments-eligible.csv or the answer. This file measures them anyway, in
its own table, for one reason: to say whether anything published under PHerc1203 at all comes
near 20 mm, and to say it with a calibration instead of an assumption.

The calibration is PHerc1447, which publishes both. For the segments whose uuid appears both as a
published segment and under raw/, the same measurer reads both grids and the two squares are put
side by side. A raw grid that measures like its published mesh says the raw frame is the volume
frame on that scroll, and that is the only ground on which the PHerc1203 rows can be read at all.

The measurement is measure_grids.segment_row, called unchanged. Two descriptive cells are
rewritten after the call, mesh_name and mesh_on_our_volume, because the tool fills them from the
chosen mesh and a raw grid has no published volume id to claim: writing yes there would be the
false cell this home keeps paying for.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import measure_grids as mg  # noqa: E402

NOT_MEASURABLE = mg.NOT_MEASURABLE
COLUMNS = ["scroll", "grid_kind", "published_counterpart",
           "published_square_mm_min_step", "raw_minus_published_mm"] + mg.SEGMENT_COLUMNS

NOTE = (
    "# post hoc side check, no number of it enters the answer of this study. One row per grid "
    "under s3 segments/raw/ of PHerc1447 and PHerc1203, measured by measure_grids.segment_row, "
    "the same function that measured the published meshes, with that scroll's own voxel. A raw "
    "grid names no volume in its meta.json, so mesh_on_our_volume reads the reason and never yes. "
    "published_counterpart is the published segment with the same uuid, which exists on PHerc1447 "
    "and on no PHerc1203 grid, and raw_minus_published_mm is the calibration: how far the raw "
    "grid's square falls from the published mesh's square of the same segment."
)


def published_rows(path):
    if not os.path.exists(path):
        return {}
    with open(path, newline="") as fh:
        lines = [ln for ln in fh.read().splitlines() if ln and not ln.startswith('"#')]
    out = {}
    for r in csv.DictReader(lines):
        uuid = r["segment"].split("-", 1)[1] if "-" in r["segment"] else r["segment"]
        out[uuid] = r
    return out


def main():
    root, evidence, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    rows = []
    for scroll in sorted(os.listdir(root)):
        sdir = os.path.join(root, scroll)
        if not os.path.isdir(sdir):
            continue
        voxel_um, source = mg.voxel_module.voxel_um(scroll)
        sys.stderr.write("%s: voxel %s um, %s\n" % (scroll, voxel_um, source))
        pub = published_rows(os.path.join(evidence, "segments-%s.csv" % scroll))
        for uuid in sorted(os.listdir(sdir)):
            where = os.path.join(sdir, uuid)
            if not os.path.isdir(where):
                continue
            row = mg.segment_row(uuid, where, uuid, voxel_um, mg.TARGET_MM, source="raw")
            row["mesh_name"] = "segments/raw/%s, no volume id in its meta.json" % uuid
            row["mesh_on_our_volume"] = "not measurable: the raw meta names no volume"
            row["scroll"] = scroll
            row["grid_kind"] = "raw"
            counterpart = pub.get(uuid)
            row["published_counterpart"] = counterpart["segment"] if counterpart else "none"
            if counterpart and counterpart["status"] == "measured" and row["status"] == "measured":
                row["published_square_mm_min_step"] = counterpart["square_mm_min_step"]
                row["raw_minus_published_mm"] = round(
                    float(row["square_mm_min_step"]) - float(counterpart["square_mm_min_step"]), 4)
            else:
                row["published_square_mm_min_step"] = NOT_MEASURABLE
                row["raw_minus_published_mm"] = NOT_MEASURABLE
            rows.append(row)
            sys.stderr.write("%s %s: %s, %s mm\n" % (scroll, uuid, row["status"],
                                                     row["square_mm_min_step"]))
    with open(out_path, "w", newline="") as fh:
        fh.write('"%s"\n' % NOTE)
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, NOT_MEASURABLE) for c in COLUMNS})
    measured = [r for r in rows if r["status"] == "measured"]
    print("rows %d, measured %d" % (len(rows), len(measured)))
    for scroll in sorted(set(r["scroll"] for r in rows)):
        m = [r for r in measured if r["scroll"] == scroll]
        if not m:
            continue
        big = max(float(r["square_mm_min_step"]) for r in m)
        print("%s: %d measured, largest %s mm, reaching 20 mm %d" % (
            scroll, len(m), big, sum(1 for r in m if r["reaches_20mm"] == "yes")))
    cal = [r for r in measured if r["raw_minus_published_mm"] != NOT_MEASURABLE]
    if cal:
        d = [abs(float(r["raw_minus_published_mm"])) for r in cal]
        print("calibration pairs %d, largest absolute difference %.4f mm" % (len(cal), max(d)))


if __name__ == "__main__":
    main()
