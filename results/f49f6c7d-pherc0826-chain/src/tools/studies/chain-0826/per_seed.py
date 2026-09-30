#!/usr/bin/env python3
# chain-0826 copy of seeds-at-scale-1447/tools/per_seed_v4.py, written 2026-09-26 by a coordinator agent (DECLARATION.md part 2):
# paths and names moved to chain-0826 and PHerc0826 (study root, prediction, raw volume, draw and queue file names, ledger
# slugs chain-0826-deliver-*); every other change is listed below this line; the text after the list is the original's.
#   A. DRAW_CSV is required (no default); the seed rule rows read are those of PHerc0826; the note names the manifest voxel.
"""per_seed_v4.py: per_seed_v3.py with THREE changes, in a new file (2026-09-25T19:2xZ, DECLARATION.md addition of
2026-09-25T19:13:31Z), so the v10 queue gets its own table and per-seed-queue-v9.csv is never overwritten:
  1. $PER_SEED_OUT defaults to evidence/per-seed-queue.csv and $SURVIVORS to evidence/queue.txt;
  2. $DRAW_CSV defaults to evidence/seeds-PHerc0826-draw3000.csv (header and first 1,500 rows byte for byte the
     draw1500 file's: evidence/draw3000-prefix-check.csv); deliver_guarded20.sh passes the largest checked draw file;
  3. the note names this tool and the queue file it read.
--- per_seed_v3.py's docstring follows ---
per_seed_v3.py: per_seed_v2.py with TWO changes, in a new file (2026-09-24T10:3xZ, director's order of
2026-09-24T10:16:29Z point 2, DECLARATION.md addition of 2026-09-24T10:25:15Z), so the v9 queue gets its own table
and evidence/per-seed-queue-v7.csv is never overwritten:
  1. the table is $PER_SEED_OUT (default evidence/per-seed-queue-v9.csv) and $SURVIVORS defaults to
     evidence/queue-v9.txt;
  2. $DRAW_CSV defaults to evidence/seeds-PHerc0826-draw1500.csv (header and first 750 rows byte for byte the
     draw750 file's: evidence/draw1500-prefix-check.csv).
--- per_seed_v2.py's docstring follows ---
per_seed_v2.py: per_seed.py with these changes, in a new file (2026-09-23T19:3xZ, director's ruling of 19:14:15Z),
so the seeds v7 grows get a table while per_seed.py keeps writing evidence/per-seed.csv for the 27 survivors:
  1. the seeds are those of $SURVIVORS (default evidence/queue-v7.txt, the queue deliver_guarded7.sh reads);
  2. coordinates come from $DRAW_CSV (default evidence/seeds-PHerc0826-draw750.csv, whose first 150 rows are
     byte for byte evidence/seeds-PHerc1447.csv: evidence/draw750-prefix-check.csv);
  3. the table is evidence/per-seed-queue-v7.csv, with four more columns read from evidence/seed-rule.csv
     (tools/seed_rule_check.py): pred_chunk_share_255, raw_at_seed, passes_rule, seed_rule_group; a seed with
     no row there is «not measurable» in all four;
  4. the first line names this tool.
--- per_seed.py's docstring follows ---
Assemble evidence/per-seed.csv for seeds-at-scale-1447: one row per survivor, from the files the runs wrote.

Written 2026-09-23T18:5xZ on the director's ruling of 18:44:45Z, item 2. This study had no per seed table
until now (seed-search-1447/tools/per_seed.py is that study's, with its ten written into the file); this is
its reading adapted to the 27 survivors of evidence/the-survivors.txt and to the two runners and two binary
series this study has, with the two columns the ruling asks for:

  delivering_binary   which binary delivered the seed's sheets: «delivered <sha256 head>» (build.sh
                      delivered, corrected plus work S's acceleration, scratch/bin-delivered) or «old
                      corrected <sha256 head>» (build.sh corrected, scratch/bin), read from the
                      binary_sha256 row of the run CSV whose downstream_return_code is 0; «not delivered»
                      when no downstream returned 0.
  cap_death_first     «yes, rc 124 at <time>» when the old runner's downstream died at its cap before the
                      seed was delivered: its CSV says downstream_return_code 124 with a numeric
                      downstream_cap_seconds, and the time is that of the runner's own log line
                      «stage '<x>' rc=124» or «downstream budget spent before stage» in log/fleet-<seed>.txt
                      (if the CSV says 124 and the log has no such line: «yes, time not measurable»);
                      «no» when a downstream ended and none died at the cap; «not measurable, no downstream
                      has ended» otherwise.

Every other value is copied from the CSV that carries it:
  coordinates            evidence/seeds-PHerc1447.csv
  growth rows            evidence/runs/<seed>.csv (v3 form «attempt,quantity,...» or v4 form «tool,attempt,...»)
  delivered downstream   evidence/runs/<seed>-delivered-downstream.csv (run_seed_v4.sh downstream_only)
  squares                evidence/squares-<seed>.csv, column square_mm_min_step, rows with status measured
  traced area            evidence/area-<seed>.csv, quantity traced_area_mm2
A missing value is «not measurable», never a default.

Header check: if evidence/per-seed.csv exists its header is compared with this version's columns; if they
differ it refuses, unless --new-header is given, and then the old file is kept beside as
per-seed.before-<time>.csv. The script prints the count of seeds it expected (the survivors file) and the
count of rows it wrote, and refuses if they differ.

Usage: per_seed.py [--new-header]
"""
import csv
import datetime
import os
import re
import shutil
import sys

S = "/data/scrollagent/runs/rev1/chain-0826"
TOOL = "chain-0826/tools/per_seed.py"
NM = "not measurable"
OUT = os.environ.get("PER_SEED_OUT", os.path.join(S, "evidence", "per-seed-queue.csv"))
SURV = os.environ.get("SURVIVORS", os.path.join(S, "evidence", "queue.txt"))
DRAW = os.environ["DRAW_CSV"]   # chain-0826: required, no default
RULE = os.path.join(S, "evidence", "seed-rule.csv")
NOTE = ("# written by chain-0826/tools/per_seed.py: one row per seed of the queue file " + os.path.basename(SURV) + ". The four seed rule columns are read from evidence/seed-rule.csv. "
        "delivering_binary names the series and the sha256 head of the binary whose downstream returned 0; "
        "cap_death_first says whether the old binary's downstream died at its cap before that, with the time of "
        "the runner's own rc 124 log line. largest_square_mm_min_step is the largest over the seed's sheets of "
        "tools/square.py's square_mm_min_step (seed-search-1447's tool, voxel read from the PHerc0826 manifest, 9.362 um). A value nobody measured is "
        "not measurable.")
COLUMNS = ["attempt", "seed_x", "seed_y", "seed_z", "growth_return_code", "growth_wall_clock_seconds",
           "growth_patches", "growth_rel_csv_lines", "old_downstream_return_code", "old_downstream_cap_seconds",
           "delivered_downstream_return_code", "delivering_binary", "cap_death_first", "delivered_sheets",
           "sheets_measured", "largest_square_mm_min_step", "largest_square_on_sheet", "traced_area_mm2", "pred_chunk_share_255", "raw_at_seed", "passes_rule", "seed_rule_group"]


def kv(path):
    """quantity -> value of a run CSV in either form; the last row of a repeated name wins."""
    if not os.path.exists(path):
        return None
    out = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            out[r["quantity"]] = r["value"]
    return out


def is_v3(path):
    return os.path.exists(path) and open(path).readline().startswith("attempt,quantity,")


def rows_after_comment(path):
    if not os.path.exists(path):
        return []
    lines = open(path, newline="").read().splitlines(True)
    if lines and lines[0].lstrip().startswith('"#'):
        lines = lines[1:]
    return list(csv.DictReader(lines))


def cap_death_time(attempt):
    path = os.path.join(S, "log", "fleet-%s.txt" % attempt)
    if not os.path.exists(path):
        return None
    t = None
    for line in open(path, errors="replace"):
        if " v4 " in line:
            continue
        if re.search(r"stage '[^']+' rc=124|downstream budget spent before stage", line):
            t = line.split()[0]
    return t


def v(d, k):
    if d is None or d.get(k, "") == "":
        return NM
    return d[k]


def main():
    new_header = "--new-header" in sys.argv[1:]
    survivors = [l.strip() for l in open(SURV) if l.strip()]
    coords = {r["attempt"]: r for r in rows_after_comment(DRAW)}
    rule = {}
    for r in rows_after_comment(RULE):
        if r["attempt"].startswith("PHerc0826-"):
            rule.setdefault(r["attempt"], r)
    rows = []
    for a in survivors:
        runp = os.path.join(S, "evidence", "runs", "%s.csv" % a)
        run = kv(runp)
        old = run if is_v3(runp) else None
        full4 = run if (run is not None and not is_v3(runp)) else None
        dd = kv(os.path.join(S, "evidence", "runs", "%s-delivered-downstream.csv" % a))
        c = coords.get(a)
        if c is None:
            raise SystemExit("%s is not in %s" % (a, DRAW))

        # which downstream delivered, latest runner first: delivered downstream, v4 full, old v3
        binary = "not delivered"
        deliverer = None
        for d, series in ((dd, "delivered"), (full4, "delivered"), (old, "old corrected")):
            if d is not None and d.get("downstream_return_code") == "0":
                sha = d.get("binary_sha256", "")
                binary = "%s %s" % (series, sha[:12] if sha else NM)
                deliverer = d
                break

        old_rc = v(old, "downstream_return_code")
        old_cap = v(old, "downstream_cap_seconds")
        if old is not None and old_rc == "124" and re.fullmatch(r"\d+", old_cap):
            t = cap_death_time(a)
            cap_first = "yes, rc 124 at %s" % t if t else "yes, time not measurable"
        elif deliverer is not None or (old is not None and old_rc not in (NM, "not run")) \
                or (dd is not None and "downstream_return_code" in dd):
            cap_first = "no"
        else:
            cap_first = "not measurable, no downstream has ended"

        squares = [r for r in rows_after_comment(os.path.join(S, "evidence", "squares-%s.csv" % a))
                   if r.get("status") == "measured" and r.get("square_mm_min_step") not in ("", NM, None)]
        area = kv(os.path.join(S, "evidence", "area-%s.csv" % a))
        if deliverer is not None and squares:
            best = max(squares, key=lambda r: float(r["square_mm_min_step"]))
            sq, sheet = "%.4f" % float(best["square_mm_min_step"]), best["sheet"]
        else:
            sq, sheet = NM, NM
        growth = old if old is not None else full4
        rows.append({
            "attempt": a,
            "seed_x": c["seed_x"], "seed_y": c["seed_y"], "seed_z": c["seed_z"],
            "growth_return_code": v(growth, "growth_return_code"),
            "growth_wall_clock_seconds": v(growth, "growth_wall_clock_seconds"),
            "growth_patches": v(growth, "growth_patches"),
            "growth_rel_csv_lines": v(growth, "growth_rel_csv_lines"),
            "old_downstream_return_code": old_rc,
            "old_downstream_cap_seconds": old_cap,
            "delivered_downstream_return_code": v(dd, "downstream_return_code"),
            "delivering_binary": binary,
            "cap_death_first": cap_first,
            "delivered_sheets": v(deliverer, "delivered_sheets"),
            "sheets_measured": str(len(squares)) if deliverer is not None and squares else NM,
            "largest_square_mm_min_step": sq,
            "largest_square_on_sheet": sheet,
            "traced_area_mm2": v(area, "traced_area_mm2") if deliverer is not None else NM,
            "pred_chunk_share_255": rule[a]["pred_chunk_share_255"] if a in rule else NM,
            "raw_at_seed": rule[a]["raw_at_seed"] if a in rule else NM,
            "passes_rule": rule[a]["passes_rule"] if a in rule else NM,
            "seed_rule_group": rule[a]["group"] if a in rule else NM,
        })

    for r in rows:
        if list(r.keys()) != COLUMNS:
            raise SystemExit("row keys differ from COLUMNS for %s" % r["attempt"])
    if len(rows) != len(survivors):
        raise SystemExit("expected %d rows, built %d" % (len(survivors), len(rows)))

    if os.path.exists(OUT):
        existing = rows_after_comment(OUT)
        with open(OUT, newline="") as f:
            lines = f.read().splitlines()
        hdr_line = lines[1] if lines and lines[0].startswith('"#') else lines[0]
        hdr = next(csv.reader([hdr_line]))
        if hdr != COLUMNS:
            if not new_header:
                raise SystemExit("REFUSED: %s has header %s, this version writes %s; rerun with --new-header "
                                 "to keep the old file beside and write the new one" % (OUT, hdr, COLUMNS))
            keep = OUT.replace(".csv", ".before-%s.csv" % datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))
            shutil.copy2(OUT, keep)
            print("header changed, old file kept at %s (%d rows)" % (keep, len(existing)))

    tmp = OUT + ".tmp"
    with open(tmp, "w", newline="") as f:
        f.write('"%s"\n' % NOTE)
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    os.replace(tmp, OUT)
    print("expected %d survivors, wrote %d rows to %s" % (len(survivors), len(rows), OUT))


if __name__ == "__main__":
    sys.exit(main())
