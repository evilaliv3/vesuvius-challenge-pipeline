#!/usr/bin/env python3
"""Third version of accepted_names.py: new copies of the renamed tables, with «winding» for «lamina» in the label.

Written 2026-09-24 by an agent of the coordinator, on the director's ruling of 2026-09-24T10:54:00Z: the
English word is «winding», not «lamina». So the label that accepted_names_v2.py wrote, «accepted by a
certificate that cuts a sharp change of lamina and not a gradual one», becomes «accepted by a certificate
that cuts a sharp change of winding and not a gradual one» in every table. Nothing measured changes.

Everything else is version 2's, unchanged: the column names stay accepted_uncalibrated_* as version 1 wrote
them, every copy is written from the SOURCE (the file the measuring tool wrote) with version 1's column map
and the label map below, and the two numbers of the header are read from the files, never typed. Version 2
and its copies are kept unchanged (a copy is never rewritten), and so are the sources.

Checks, each a column of evidence/renames-v3-2026-09-24.csv: rows and columns equal to the source; every
cell byte equal to the source's except the relabelled; no «certified» left outside names of folders and
tools; no «uncalibrated certificate» and no «lamina» left in any cell; and against the version 2 copy, the
header equal and the cells that differ, all of which must be version 2's label becoming this one.

    accepted_names_v3.py      all copies; refused while run_1667.sh (process group 3957333) is alive
"""
import csv, hashlib, io, os, re, subprocess, sys

R = "/data/scrollagent/runs/rev1"
TOOL = "certified-area/tools/accepted_names_v3.py"
MAP_OUT = os.path.join(R, "certified-area/evidence/renames-map-v3-2026-09-24.csv")
LOG_OUT = os.path.join(R, "certified-area/evidence/renames-v3-2026-09-24.csv")
RULING = "director's ruling of 2026-09-24T10:54:00Z on the word, on the verdict of 2026-09-24T10:16:29Z on the stitched test"
PHRASE = "accepted by a certificate that cuts a sharp change of winding and not a gradual one"
V2_PHRASE = "accepted by a certificate that cuts a sharp change of lamina and not a gradual one"
OLD_PHRASE = "accepted by an uncalibrated certificate"
RUN_1667_PGID = "3957333"

# old column name -> new column name: version 1's map, unchanged (see the docstring for why)
COLS = {
    "certified_area_cm2": "accepted_uncalibrated_area_cm2",
    "certified_square_mm": "accepted_uncalibrated_square_mm",
    "certified_square_cells": "accepted_uncalibrated_square_cells",
    "certified_cells": "accepted_uncalibrated_cells",
    "certified_share_of_cells": "accepted_uncalibrated_share_of_cells",
    "largest_certified_area_cm2": "largest_accepted_uncalibrated_area_cm2",
    "certified_union_under_tenth_of_summed": "accepted_uncalibrated_union_under_tenth_of_summed",
    "certified_rows_compared_with_certified_area": "accepted_uncalibrated_rows_compared_with_area_study",
    "certified_cells_asis": "accepted_uncalibrated_cells_asis",
    "certified_cm2_asis": "accepted_uncalibrated_cm2_asis",
    "certified_cells_pitchband": "accepted_uncalibrated_cells_pitchband",
    "certified_cm2_pitchband": "accepted_uncalibrated_cm2_pitchband",
    "certified_cells_equals_certified_area": "accepted_uncalibrated_cells_equals_area_study",
    "certified_area_cm2_asis": "accepted_uncalibrated_area_cm2_asis",
    "certified_area_cm2_pitchband": "accepted_uncalibrated_area_cm2_pitchband",
    "certified_area_cm2_pitchspan": "accepted_uncalibrated_area_cm2_pitchspan",
    "certified_square_mm_asis": "accepted_uncalibrated_square_mm_asis",
    "certified_square_mm_pitchband": "accepted_uncalibrated_square_mm_pitchband",
    "certified_square_mm_pitchspan": "accepted_uncalibrated_square_mm_pitchspan",
    "certified_share_of_cells_pitchband": "accepted_uncalibrated_share_of_cells_pitchband",
    "calibrated_mode": "mode_named_by_calibration_decision",
    "certified_area_cm2_calibrated_mode": "accepted_uncalibrated_area_cm2_pitchband_as_named",
    "certified_above_4_2_cm2_sends_reading_here": "accepted_uncalibrated_above_4_2_cm2_sends_reading_here",
    "certified_area_cm2_sum_asis": "accepted_uncalibrated_area_cm2_sum_asis",
    "certified_area_cm2_sum_pitchband": "accepted_uncalibrated_area_cm2_sum_pitchband",
    "certified_area_cm2_sum_pitchspan": "accepted_uncalibrated_area_cm2_sum_pitchspan",
    "largest_certified_area_cm2_calibrated_mode": "largest_accepted_uncalibrated_area_cm2_pitchband_as_named",
}

# whole cell value -> new value (labels, not names)
LABELS_EXACT = {
    "certified asis": PHRASE + ", asis",
    "certified pitchband": PHRASE + ", pitchband",
    "no: no published 0826 surface exists to be certified":
        "no: no published 0826 surface exists for the certificate to measure",
    # calibrate_step4.py writes this label itself, in column certificate_status
    OLD_PHRASE: PHRASE,
    # stitch_adjacent.py writes this label on its decision row, in column certificate_status
    "accepted by a certificate calibrated for sharp changes only (mode asis)": PHRASE + " (mode asis)",
}
# substring -> new substring
LABELS_SUB = {
    "certified beside": PHRASE + " beside",
    "the bound no certified area can pass": "the bound no area " + PHRASE + " can pass",
    "three modes, the calibrated one from": "three modes, the one named by",
    OLD_PHRASE: PHRASE,
}

KEEP = ["certified-area", "certified_region", "certified-region-selftest", "certified-PHerc0800", "certified-PHerc1667"]

# (source, version 2 copy, version 3 copy)
COPIES = [
    ("certified-area/evidence/certified-area.csv", "certified-area/evidence/accepted-uncalibrated-area-v2.csv",
     "certified-area/evidence/accepted-uncalibrated-area-v3.csv"),
    ("certified-area/evidence/certified-area-summary.csv", "certified-area/evidence/accepted-uncalibrated-area-summary-v2.csv",
     "certified-area/evidence/accepted-uncalibrated-area-summary-v3.csv"),
    ("certified-area/evidence/certified-area-status-step4.csv", "certified-area/evidence/accepted-uncalibrated-area-status-step4-v2.csv",
     "certified-area/evidence/accepted-uncalibrated-area-status-step4-v3.csv"),
    ("certified-area/evidence/calibration-regions.csv", "certified-area/evidence/calibration-regions-renamed-v2.csv",
     "certified-area/evidence/calibration-regions-renamed-v3.csv"),
    ("certified-area/evidence/calibration-step4-regions.csv", "certified-area/evidence/calibration-step4-regions-renamed-v2.csv",
     "certified-area/evidence/calibration-step4-regions-renamed-v3.csv"),
    ("certified-area/evidence/calibration-step4.csv", "certified-area/evidence/calibration-step4-renamed-v2.csv",
     "certified-area/evidence/calibration-step4-renamed-v3.csv"),
    ("certified-area/evidence/calibration-stitched.csv", "certified-area/evidence/calibration-stitched-renamed-v2.csv",
     "certified-area/evidence/calibration-stitched-renamed-v3.csv"),
    ("coverage-union-1447/evidence/union.csv", "coverage-union-1447/evidence/union-renamed-v2.csv",
     "coverage-union-1447/evidence/union-renamed-v3.csv"),
    ("coverage-union-1447/evidence/union-per-sheet.csv", "coverage-union-1447/evidence/union-per-sheet-renamed-v2.csv",
     "coverage-union-1447/evidence/union-per-sheet-renamed-v3.csv"),
    ("field-0826-0800/evidence/field.csv", "field-0826-0800/evidence/field-renamed-v2.csv",
     "field-0826-0800/evidence/field-renamed-v3.csv"),
    ("field-0826-0800/evidence/field-sums.csv", "field-0826-0800/evidence/field-sums-renamed-v2.csv",
     "field-0826-0800/evidence/field-sums-renamed-v3.csv"),
    ("field-0826-0800/evidence/certified-PHerc0800.csv", "field-0826-0800/evidence/accepted-uncalibrated-PHerc0800-v2.csv",
     "field-0826-0800/evidence/accepted-uncalibrated-PHerc0800-v3.csv"),
]


def now():
    return subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def split(p):
    """(comment lines, header, rows) of a house CSV whose comment lines start with # or "#."""
    rows = list(csv.reader(io.StringIO(open(p, newline="").read())))
    comments, body = [], []
    for r in rows:
        if not body and r and r[0].lstrip().startswith("#"):
            comments.append(r)
        else:
            body.append(r)
    if not body:
        raise SystemExit("refuse: %s has no header row" % p)
    return comments, body[0], body[1:]


def writer_of(comments):
    m = re.search(r"written by ([A-Za-z0-9_./-]+\.(?:py|sh))", " ".join(",".join(c) for c in comments))
    return m.group(1) if m else "not named in its header"


def leftover(s):
    t = s
    for k in KEEP:
        t = t.replace(k, "")
    return re.findall(r"(?i)certif(?!icate)\w*", t)


NAME_RE = re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(sorted(map(re.escape, COLS), key=len, reverse=True))
                     + r")(?![A-Za-z0-9_])")


def relabel(v):
    if v in LABELS_EXACT:
        return LABELS_EXACT[v]
    for a, b in LABELS_SUB.items():
        v = v.replace(a, b)
    return NAME_RE.sub(lambda m: COLS[m.group(1)], v)


def one_value(rel, key, col):
    _, h, rows = split(os.path.join(R, rel))
    hit = [dict(zip(h, r)) for r in rows if all(dict(zip(h, r)).get(k) == v for k, v in key.items())]
    if len(hit) != 1:
        raise SystemExit("refuse: %s has %d rows %s, one expected" % (rel, len(hit), key))
    if hit[0].get(col, "") == "":
        raise SystemExit("refuse: %s row %s column %s is empty or missing" % (rel, key, col))
    return hit[0][col]


def the_numbers():
    st = "certified-area/evidence/calibration-stitched.csv"
    s_asis = one_value(st, {"kind": "stitched sharp jump", "mode": "asis"}, "certified_share_of_cells")
    s_floor = one_value(st, {"kind": "stitched sharp jump", "mode": "asis"}, "lowest_reachable_share")
    j_asis = one_value("certified-area/evidence/calibration-step4.csv", {"kind": "known jump", "mode": "asis"},
                       "certificate_status")  # the label, checked below
    j_share = one_value("certified-area/evidence/calibration-step4.csv", {"kind": "known jump", "mode": "asis"},
                        "certified_share_of_cells")
    if s_asis != s_floor:
        raise SystemExit("refuse: the stitched asis share %s is not the floor %s: the sharp jump is not shown cut"
                         % (s_asis, s_floor))
    if float(j_share) < 0.5:
        raise SystemExit("refuse: seed11 after is kept at %s by asis, under half: the gradual switch is cut and the "
                         "label would be false" % j_share)
    return s_asis, s_floor, j_share, j_asis


def one(src_rel, v1_rel, out_rel, nums):
    src, out = os.path.join(R, src_rel), os.path.join(R, out_rel)
    comments, hdr, rows = split(src)
    for h in hdr:
        if leftover(h) and h not in COLS:
            raise SystemExit("refuse: %s column %r says certified and is not in the map" % (src_rel, h))
    new_hdr = [COLS.get(h, h) for h in hdr]
    if len(set(new_hdr)) != len(new_hdr):
        raise SystemExit("refuse: %s: two columns map to one name" % src_rel)
    new_rows, relabelled, equal = [], 0, 0
    for r in rows:
        if len(r) != len(hdr):
            raise SystemExit("refuse: %s: a row of %d cells under a header of %d" % (src_rel, len(r), len(hdr)))
        nr = [relabel(v) for v in r]
        for a, b in zip(r, nr):
            if a == b:
                equal += 1
            else:
                relabelled += 1
        new_rows.append(nr)
    left = sorted({w for r in [new_hdr] + new_rows for v in r for w in leftover(v)})
    if left:
        raise SystemExit("refuse: %s: words left after the map: %s" % (out_rel, left))
    old_left = sum(1 for r in [new_hdr] + new_rows for v in r if "uncalibrated certificate" in v)
    if old_left:
        raise SystemExit("refuse: %s: %d cells still say «uncalibrated certificate»" % (out_rel, old_left))
    lamina_left = sum(1 for r in [new_hdr] + new_rows for v in r if "lamina" in v.lower())
    if lamina_left:
        raise SystemExit("refuse: %s: %d cells still say «lamina»" % (out_rel, lamina_left))
    t = now()
    src_sha = sha(src)
    s_asis, s_floor, j_share, _ = nums
    head = ("# renamed copy of %s (sha256 %s), written by %s at %s under the %s: the winding certificate cuts a "
            "sharp change of winding (certified-area/evidence/calibration-stitched.csv, the stitched sharp jump kept at "
            "%s by asis, the floor %s, both seams cut) and not a gradual one (certified-area/evidence/calibration-step4.csv, "
            "seed11 after kept at %s by asis), so a label reads «%s». Column names stay accepted_uncalibrated_* as "
            "accepted_names.py wrote them, because readers name them. The numbers are the source's, written by %s, whose "
            "header there says how each column was computed; every cell is byte equal to the source's except %d "
            "relabelled. Map: certified-area/evidence/renames-map-v2-2026-09-24.csv."
            % (src_rel, src_sha, TOOL, t, RULING, s_asis, s_floor, j_share, PHRASE, writer_of(comments), relabelled))
    tmp = out + ".tmp"
    with open(tmp, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([head])
        w.writerow(new_hdr)
        w.writerows(new_rows)
    _, h2, r2 = split(tmp)
    if len(r2) != len(rows) or len(h2) != len(hdr):
        os.remove(tmp)
        raise SystemExit("refuse: %s read back %d rows %d columns, source %d %d"
                         % (out_rel, len(r2), len(h2), len(rows), len(hdr)))
    back_equal = sum(1 for ra, rb in zip(rows, r2) for a, b in zip(ra, rb) if a == b)
    if back_equal != equal:
        os.remove(tmp)
        raise SystemExit("refuse: %s: %d cells equal on read back, %d when written" % (out_rel, back_equal, equal))
    # against the version 2 copy: every differing cell must be version 2's label turned into this one
    _, h1, r1 = split(os.path.join(R, v1_rel))
    if len(r1) != len(r2) or h1 != h2:
        os.remove(tmp)
        raise SystemExit("refuse: %s: header or row count differs from the version 2 copy %s" % (out_rel, v1_rel))
    pairs = [(a, b) for ra, rb in zip(r1, r2) for a, b in zip(ra, rb) if a != b]
    good = [p for p in pairs if p[0].replace(V2_PHRASE, PHRASE) == p[1]]
    if len(good) != len(pairs):
        os.remove(tmp)
        raise SystemExit("refuse: %s: %d cells differ from the version 2 copy other than by the label"
                         % (out_rel, len(pairs) - len(good)))
    v1_diff, v1_diff_label, v1_hdr_equal = len(pairs), len(good), "yes"
    os.replace(tmp, out)
    renamed = [(a, b) for a, b in zip(hdr, new_hdr) if a != b]
    return {
        "utc": t, "source": src_rel, "source_sha256": src_sha, "source_tool": writer_of(comments),
        "version_2_copy": v1_rel, "output": out_rel, "output_sha256": sha(out),
        "rows_source": len(rows), "rows_output": len(r2), "rows_equal": "yes" if len(rows) == len(r2) else "no",
        "columns_source": len(hdr), "columns_output": len(h2), "columns_renamed": len(renamed),
        "cells_relabelled_from_source": relabelled, "cells_byte_equal_to_source": equal,
        "cells_byte_equal_on_read_back": back_equal,
        "header_equal_to_version_2_copy": v1_hdr_equal,
        "cells_differing_from_version_2_copy": v1_diff,
        "of_which_version_2_label_to_new": v1_diff_label,
        "words_certified_left_outside_names": len(left), "cells_saying_uncalibrated_certificate": old_left,
        "cells_saying_lamina": lamina_left,
        "tool": TOOL,
    }


def write_map():
    t = now()
    with open(MAP_OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["# the labels changed by %s at %s under the %s, and the files it wrote; column names are "
                    "version 1's (certified-area/evidence/renames-map-2026-09-24.csv) and are not changed; version 2's map is "
                    "certified-area/evidence/renames-map-v2-2026-09-24.csv"
                    % (TOOL, t, RULING)])
        w.writerow(["kind", "old", "new", "tool"])
        for old, new in LABELS_EXACT.items():
            w.writerow(["label, whole cell", old, new, TOOL])
        for old, new in LABELS_SUB.items():
            w.writerow(["label, inside a cell", old, new, TOOL])
        w.writerow(["column names", "accepted_uncalibrated_*", "unchanged: paper_numbers.py of works aeb2e975, "
                    "e44c8116 and f211b3cf, the ink step (b) declaration map and the readers of version 1 copies "
                    "name them; a rename would break them and change nothing measured", TOOL])
        for s, v1, o in COPIES:
            w.writerow(["file", s + " (version 2 copy " + v1 + ")", o, TOOL])


def run_1667_alive():
    return RUN_1667_PGID in subprocess.check_output(["ps", "-eo", "pgid="]).decode().split()


def main():
    if run_1667_alive():
        raise SystemExit("refuse: process group %s (run_1667.sh) is alive and rewrites field.csv" % RUN_1667_PGID)
    nums = the_numbers()
    if nums[3] != OLD_PHRASE:
        raise SystemExit("refuse: calibration-step4.csv seed11 after row reads %r, not the old label" % nums[3])
    results = [one(s, v1, o, nums) for s, v1, o in COPIES]
    new = not os.path.exists(LOG_OUT)
    with open(LOG_OUT, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(results[0]))
        if new:
            csv.writer(fh).writerow(["# one row per version 3 copy, written by %s; each check is a column: rows and "
                                     "columns equal to the source, every cell byte equal but the relabelled, the count "
                                     "read back, the cells that differ from the version 2 copy and how many of them are "
                                     "version 2's label turned into this one, no «certified» left outside names of folders "
                                     "and tools, no cell saying «uncalibrated certificate», no cell saying «lamina»" % TOOL])
            w.writeheader()
        w.writerows(results)
    write_map()
    for r in results:
        print("%s: %d rows, %d relabelled from source, %s differing from v2 (%s label)"
              % (r["output"], r["rows_output"], r["cells_relabelled_from_source"],
                 r["cells_differing_from_version_2_copy"], r["of_which_version_2_label_to_new"]))


if __name__ == "__main__":
    main()
