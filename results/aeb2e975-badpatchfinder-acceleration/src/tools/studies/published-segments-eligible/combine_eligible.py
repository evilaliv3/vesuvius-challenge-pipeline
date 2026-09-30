#!/usr/bin/env python3
"""The one table of the three eligible scrolls, and every number the outcome quotes, recomputed.

The measurement is not here. It is tools/measure_grids.py, copied unchanged from
runs/rev1/published-segments, and the per scroll ranking is tools/combine_and_rank.py from the
same study. This file only puts the measured rows of the scrolls into one table with the scroll
and its voxel on every row, and recomputes every count, every superlative and every comparison
over every row the word covers, including the rows of the reference scroll PHerc0139, which are
read back from that study's own evidence and never copied out of its prose.

A quantity that cannot be measured is written not measurable and never zero. A scroll that
publishes no segment is counted in its own lines, with the prefix listing as the source.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import measure_grids as mg  # noqa: E402

NOT_MEASURABLE = mg.NOT_MEASURABLE
TARGET_MM = mg.TARGET_MM
REFERENCE = "/data/scrollagent/runs/rev1/published-segments/evidence/segments.csv"
SCROLLS = ["PHerc1447", "PHerc0800", "PHerc1203"]
COLUMNS = ["scroll"] + mg.SEGMENT_COLUMNS

NOTE = (
    "# one row per published segment of the three eligible scrolls that have a segments prefix, "
    "PHerc1447, PHerc0800 and PHerc1203, plus one reference row marked ours, which is the best of "
    "our ten delivered C40 sheets on PHerc0139 and is the 12.1230 mm this study is read against. "
    "The columns are those of runs/rev1/published-segments/evidence/segments.csv with the scroll "
    "added in front. Every row is measured by tools/measure_grids.py, copied unchanged from that "
    "study: the square is the exact largest axis aligned fully covered square of the grid, a "
    "pixel of the tifxyz is a cell, a cell is covered when its three values are neither all zero "
    "nor all -1, the two cell steps are the median 3D distance in voxels between neighbouring "
    "covered cells along each axis, and square_mm_min_step is cells times the SMALLER step times "
    "the voxel. voxel_um is that scroll's own value from its own manifest through "
    "pipeline/datasets/voxel.py, 8.640 um for PHerc1447 and PHerc0800, 9.362 for PHerc1203 and "
    "for the reference row, never a default and never another scroll's value. A mesh counts only "
    "when it is on that scroll's own volume_id, and is never replaced by a mesh on another scan."
)


def rows(path):
    with open(path, newline="") as fh:
        lines = [ln for ln in fh.read().splitlines() if ln and not ln.startswith('"#')]
    return list(csv.DictReader(lines))


def listing_counts(scroll, evidence):
    """What the segments/ prefix lists, read off the saved listing and not off a memory."""
    path = os.path.join(evidence, "segments-listed-%s.txt" % scroll)
    entries = [ln.split("PRE ", 1)[1].rstrip("/") for ln in open(path).read().splitlines()
               if " PRE " in ln]
    return entries, [e for e in entries if e != "raw"], ("raw" in entries)


def stats(prefix, measured, out, column_of=lambda c: c):
    """Counts and superlatives over a list of measured rows, each recomputed over all of them."""
    n = len(measured)
    if n == 0:
        out.append([prefix + "largest_square_mm", NOT_MEASURABLE, "square_mm_min_step", 0])
        out.append([prefix + "smallest_square_mm", NOT_MEASURABLE, "square_mm_min_step", 0])
        return
    mm = [float(r["square_mm_min_step"]) for r in measured]
    big, small = max(mm), min(mm)
    out.append([prefix + "segments_reaching_20mm",
                sum(1 for r in measured if r["reaches_20mm"] == "yes"), "reaches_20mm", n])
    out.append([prefix + "segments_not_reaching_20mm",
                sum(1 for r in measured if r["reaches_20mm"] != "yes"), "reaches_20mm", n])
    out.append([prefix + "segments_reaching_20mm_holes_filled",
                sum(1 for r in measured if r["reaches_20mm_holes_filled"] == "yes"),
                "reaches_20mm_holes_filled", n])
    out.append([prefix + "largest_square_mm", big, "square_mm_min_step", n])
    out.append([prefix + "largest_square_mm_on",
                ";".join(r["segment"] for r in measured
                         if float(r["square_mm_min_step"]) == big), "segment", n])
    out.append([prefix + "smallest_square_mm", small, "square_mm_min_step", n])
    out.append([prefix + "smallest_square_mm_on",
                ";".join(r["segment"] for r in measured
                         if float(r["square_mm_min_step"]) == small), "segment", n])
    out.append([prefix + "largest_square_cells",
                max(int(r["square_cells"]) for r in measured), "square_cells", n])
    out.append([prefix + "size_ceiling_mm_max",
                max(float(r["size_ceiling_mm"]) for r in measured), "size_ceiling_mm", n])
    out.append([prefix + "size_ceiling_mm_min",
                min(float(r["size_ceiling_mm"]) for r in measured), "size_ceiling_mm", n])
    out.append([prefix + "segments_whose_whole_grid_is_under_20mm",
                sum(1 for r in measured if float(r["size_ceiling_mm"]) < TARGET_MM),
                "size_ceiling_mm", n])
    for lim in ("size", "outline", "enclosed_pores", "none"):
        out.append([prefix + "segments_limited_by_" + lim,
                    sum(1 for r in measured if r["limit"] == lim), "limit", n])
    out.append([prefix + "step_i_voxel_min", min(float(r["step_i_voxel"]) for r in measured),
                "step_i_voxel", n])
    out.append([prefix + "step_i_voxel_max", max(float(r["step_i_voxel"]) for r in measured),
                "step_i_voxel", n])
    out.append([prefix + "step_j_voxel_min", min(float(r["step_j_voxel"]) for r in measured),
                "step_j_voxel", n])
    out.append([prefix + "step_j_voxel_max", max(float(r["step_j_voxel"]) for r in measured),
                "step_j_voxel", n])
    out.append([prefix + "fill_fraction_min", min(float(r["fill_fraction"]) for r in measured),
                "fill_fraction", n])
    out.append([prefix + "fill_fraction_max", max(float(r["fill_fraction"]) for r in measured),
                "fill_fraction", n])
    out.append([prefix + "grid_cells_min", min(int(r["cells_i"]) * int(r["cells_j"])
                                               for r in measured), "cells_i,cells_j", n])
    out.append([prefix + "grid_cells_max", max(int(r["cells_i"]) * int(r["cells_j"])
                                               for r in measured), "cells_i,cells_j", n])
    out.append([prefix + "all_zero_cells_total", sum(int(r["all_zero_cells"]) for r in measured),
                "all_zero_cells", n])
    out.append([prefix + "invalid_marker_cells_total",
                sum(int(r["invalid_marker_cells"]) for r in measured), "invalid_marker_cells", n])


def main():
    evidence = sys.argv[1]
    table_path = os.path.join(evidence, "segments-eligible.csv")
    rank_path = os.path.join(evidence, "ranking.csv")

    # the reference row of ours, taken from the per scroll combined table written by
    # tools/combine_and_rank.py, which chose it by a maximum over every row of the control
    ours = [r for r in rows(os.path.join(evidence, "segments-PHerc1447-with-ours.csv"))
            if r["source"] == "ours"]
    if len(ours) != 1:
        sys.exit("expected exactly one row marked ours")
    ours = ours[0]

    per_scroll = {}
    allrows = []
    for s in SCROLLS:
        path = os.path.join(evidence, "segments-%s.csv" % s)
        got = rows(path) if os.path.exists(path) else []
        per_scroll[s] = got
        for r in got:
            r2 = {"scroll": s}
            r2.update({c: r.get(c, NOT_MEASURABLE) for c in mg.SEGMENT_COLUMNS})
            allrows.append(r2)
    ours_row = {"scroll": "PHerc0139"}
    ours_row.update({c: ours.get(c, NOT_MEASURABLE) for c in mg.SEGMENT_COLUMNS})
    allrows.append(ours_row)

    with open(table_path, "w", newline="") as fh:
        fh.write('"%s"\n' % NOTE)
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        for r in allrows:
            w.writerow(r)

    back = rows(table_path)
    out = []
    ours_mm = float(ours["square_mm_min_step"])
    eligible_measured = [r for r in back if r["scroll"] != "PHerc0139" and r["status"] == "measured"]

    for s in SCROLLS:
        entries, segs, has_raw = listing_counts(s, evidence)
        mine = [r for r in back if r["scroll"] == s]
        measured = [r for r in mine if r["status"] == "measured"]
        p = s + "_"
        out.append([p + "voxel_um", (mine[0]["voxel_um"] if mine
                                     else mg.voxel_module.voxel_um(s)[0]), "voxel_um",
                    len(mine) or 1])
        out.append([p + "prefix_entries_listed", len(entries), "segments-listed-%s.txt" % s,
                    len(entries)])
        out.append([p + "prefix_holds_a_raw_folder", "yes" if has_raw else "no",
                    "segments-listed-%s.txt" % s, len(entries)])
        out.append([p + "segments_published", len(segs), "segments-listed-%s.txt" % s,
                    len(entries)])
        out.append([p + "segments_with_a_mesh_on_its_own_volume",
                    sum(1 for r in mine if r["mesh_on_our_volume"] == "yes"),
                    "mesh_on_our_volume", len(mine)])
        out.append([p + "segments_measured", len(measured), "status", len(mine)])
        out.append([p + "segments_not_measurable", len(mine) - len(measured), "status", len(mine)])
        stats(p, measured, out)
        if measured:
            out.append([p + "segments_larger_than_ours", sum(
                1 for r in measured if float(r["square_mm_min_step"]) > ours_mm),
                "square_mm_min_step", len(measured)])
            out.append([p + "segments_smaller_than_ours", sum(
                1 for r in measured if float(r["square_mm_min_step"]) < ours_mm),
                "square_mm_min_step", len(measured)])
            out.append([p + "rank_of_ours_among_its_rows", 1 + sum(
                1 for r in measured if float(r["square_mm_min_step"]) > ours_mm),
                "square_mm_min_step", len(measured) + 1])

    stats("eligible_all_three_", eligible_measured, out)
    out.append(["eligible_segments_measured_all_three", len(eligible_measured), "status",
                len(back) - 1])
    out.append(["eligible_segments_published_all_three",
                sum(1 for r in back if r["scroll"] != "PHerc0139"), "scroll", len(back)])
    out.append(["ours_square_mm", ours_mm, "square_mm_min_step", 1])
    out.append(["ours_row", ours["segment"], "segment", 1])
    out.append(["ours_voxel_um", ours["voxel_um"], "voxel_um", 1])
    out.append(["ours_step_i_voxel", ours["step_i_voxel"], "step_i_voxel", 1])
    out.append(["ours_fill_fraction", ours["fill_fraction"], "fill_fraction", 1])
    out.append(["eligible_segments_larger_than_ours",
                sum(1 for r in eligible_measured
                    if float(r["square_mm_min_step"]) > ours_mm), "square_mm_min_step",
                len(eligible_measured)])
    out.append(["rank_of_ours_among_all_eligible_rows",
                1 + sum(1 for r in eligible_measured
                        if float(r["square_mm_min_step"]) > ours_mm), "square_mm_min_step",
                len(eligible_measured) + 1])

    # the reference scroll, recomputed from its own evidence and never quoted out of its prose
    ref = [r for r in rows(REFERENCE) if r["source"] == "published"]
    ref_measured = [r for r in ref if r["status"] == "measured"]
    out.append(["reference_PHerc0139_segments_published", len(ref), "segment", len(ref)])
    out.append(["reference_PHerc0139_segments_measured", len(ref_measured), "status", len(ref)])
    out.append(["reference_PHerc0139_segments_not_measurable", len(ref) - len(ref_measured),
                "status", len(ref)])
    stats("reference_PHerc0139_", ref_measured, out)
    if ref_measured:
        out.append(["reference_PHerc0139_segments_larger_than_the_largest_eligible",
                    sum(1 for r in ref_measured if float(r["square_mm_min_step"]) >
                        max(float(x["square_mm_min_step"]) for x in eligible_measured)),
                    "square_mm_min_step", len(ref_measured)])
        out.append(["ratio_largest_reference_over_largest_eligible",
                    round(max(float(r["square_mm_min_step"]) for r in ref_measured)
                          / max(float(r["square_mm_min_step"]) for r in eligible_measured), 4),
                    "square_mm_min_step", len(ref_measured) + len(eligible_measured)])

    # the voxel trap, quantified: what the largest eligible square would read if the reference
    # scroll's voxel had been used on a scroll whose scan is 8.640 um. It is not a measurement of
    # anything, it is the size of the error the voxel rule prevented, and it is computed here from
    # the same rows rather than worked out by hand.
    if eligible_measured:
        big_row = max(eligible_measured, key=lambda r: float(r["square_mm_min_step"]))
        if float(big_row["voxel_um"]) != 0:
            wrong = float(big_row["square_mm_min_step"]) * 9.362 / float(big_row["voxel_um"])
            out.append(["largest_eligible_square_mm_if_the_reference_voxel_had_been_used",
                        round(wrong, 4), "square_mm_min_step,voxel_um", 1])
            out.append(["largest_eligible_square_reaches_20mm_even_with_that_wrong_voxel",
                        "yes" if wrong >= TARGET_MM else "no",
                        "square_mm_min_step,voxel_um", 1])

    # the post hoc side check on the raw grids, kept apart from every quantity above
    raw_path = os.path.join(evidence, "raw-grids-check.csv")
    if os.path.exists(raw_path):
        raw = [r for r in rows(raw_path) if r["status"] == "measured"]
        for s_ in sorted(set(r["scroll"] for r in raw)):
            m = [r for r in raw if r["scroll"] == s_]
            mm = [float(r["square_mm_min_step"]) for r in m]
            q = "raw_check_%s_" % s_
            out.append([q + "grids_measured", len(m), "status", len(m)])
            out.append([q + "grids_reaching_20mm",
                        sum(1 for r in m if r["reaches_20mm"] == "yes"), "reaches_20mm", len(m)])
            out.append([q + "largest_square_mm", max(mm), "square_mm_min_step", len(m)])
            out.append([q + "largest_square_mm_on",
                        ";".join(r["segment"] for r in m
                                 if float(r["square_mm_min_step"]) == max(mm)), "segment", len(m)])
            out.append([q + "smallest_square_mm", min(mm), "square_mm_min_step", len(m)])
            out.append([q + "step_i_voxel_min", min(float(r["step_i_voxel"]) for r in m),
                        "step_i_voxel", len(m)])
            out.append([q + "step_i_voxel_max", max(float(r["step_i_voxel"]) for r in m),
                        "step_i_voxel", len(m)])
        cal = [r for r in raw if r["raw_minus_published_mm"] != NOT_MEASURABLE]
        if cal:
            d = sorted(abs(float(r["raw_minus_published_mm"])) for r in cal)
            out.append(["raw_check_calibration_pairs", len(cal), "raw_minus_published_mm",
                        len(cal)])
            out.append(["raw_check_calibration_largest_absolute_difference_mm", round(d[-1], 4),
                        "raw_minus_published_mm", len(cal)])
            out.append(["raw_check_calibration_median_absolute_difference_mm",
                        round(d[len(d) // 2], 4), "raw_minus_published_mm", len(cal)])
            out.append(["raw_check_calibration_pairs_within_1_5mm",
                        sum(1 for x in d if x <= 1.5), "raw_minus_published_mm", len(cal)])

    with open(rank_path, "w", newline="") as fh:
        fh.write('"# every number of OUTCOME.md, recomputed over every row it covers from '
                 'evidence/segments-eligible.csv and, for the reference scroll rows, from '
                 'runs/rev1/published-segments/evidence/segments.csv. No value here is taken off '
                 'a single row or out of any prose. A scroll with no measured row carries not '
                 'measurable in its superlatives and never a zero."\n')
        w = csv.writer(fh)
        w.writerow(["quantity", "value", "column_read", "rows_covered"])
        w.writerows(out)
    print("wrote %s (%d rows) and %s (%d quantities)" % (
        table_path, len(back), rank_path, len(out)))


if __name__ == "__main__":
    main()
