#!/usr/bin/env python3
"""wave5_sources.py [min_mm]: the source seeds of the fifth wave of chain-0826 (PLAN item 95 (b), owner's word 2026-09-28T12:22:40Z).

Copy of tools/wave4_sources.py, written 2026-09-28T12:4xZ by a coordinator agent. Changes, and no others: the draw file
is seeds-PHerc0826-draw6712.csv (draws 1 to 6712, so a fourth wave seed can be a source), min_mm defaults to 15.0,
the output is evidence/wave5-sources.csv, the texts name the fifth wave. wave4_sources.py's text follows.

New file, written 2026-09-27T20:2xZ by a coordinator agent. Reads every evidence/squares-PHerc0826-<seed>.csv (rows
after the tool line), keeps the rows with status «measured», and for each seed takes the sheet with the largest
square_mm_min_step. A seed is a source when that value is at least min_mm (default 10.0). The seed point is read from
evidence/seeds-PHerc0826-draw6400.csv (the attempt's row); the chunk share and group from evidence/seed-rule.csv.
A seed with no measured sheet is written with best «not measurable» and is never a source.
Writes evidence/wave4-sources.csv (first line names this tool and the time), one row per squares file, sorted by the
seed's draw_order; is_source yes or no.
"""
import csv, glob, os, subprocess, sys

S = "/data/scrollagent/runs/rev1/chain-0826"
E = os.path.join(S, "evidence")
TOOL = "chain-0826/tools/wave5_sources.py"


def rows(p):
    L = [l for l in open(p, newline="") if not l.lstrip().startswith('"#')]
    return list(csv.DictReader(L))


def main():
    min_mm = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0
    draw = {r["attempt"]: r for r in rows(os.path.join(E, "seeds-PHerc0826-draw6712.csv"))}
    rule = {r["attempt"]: r for r in rows(os.path.join(E, "seed-rule.csv"))}
    out = []
    for p in sorted(glob.glob(os.path.join(E, "squares-PHerc0826-seed*.csv"))):
        R = rows(p)
        a = os.path.basename(p)[len("squares-"):-len(".csv")]
        m = [r for r in R if r["status"] == "measured"]
        d = draw[a]
        ru = rule.get(a, {})
        if m:
            b = max(m, key=lambda r: float(r["square_mm_min_step"]))
            best, sheet, cells, ci, cj = b["square_mm_min_step"], b["sheet"], b["square_cells"], b["square_corner_i"], b["square_corner_j"]
            src = "yes" if float(best) >= min_mm else "no"
        else:
            best, sheet, cells, ci, cj, src = "not measurable", "", "", "", "", "no"
        out.append({"attempt": a, "draw_order": int(d["draw_order"]), "seed_x": d["seed_x"], "seed_y": d["seed_y"],
                    "seed_z": d["seed_z"], "sheets_rows": len(R), "sheets_measured": len(m),
                    "best_square_mm_min_step": best, "best_sheet": sheet, "best_square_cells": cells,
                    "best_square_corner_i": ci, "best_square_corner_j": cj,
                    "pred_chunk_share_255": ru.get("pred_chunk_share_255", "not listed"),
                    "seed_rule_group": ru.get("group", "not listed"), "squares_file": "evidence/" + os.path.basename(p),
                    "is_source": src})
    out.sort(key=lambda r: r["draw_order"])
    t = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    dst = os.path.join(E, "wave5-sources.csv")
    with open(dst + ".part", "w", newline="") as f:
        f.write('"# written by %s at %s: one row per squares file of chain-0826; best = largest square_mm_min_step over the '
                'seed\'s measured sheets; is_source yes when best >= %.4f mm (fifth wave, PLAN item 95 (b))"\n'
                % (TOOL, t, min_mm))
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()), lineterminator="\n")
        w.writeheader(); w.writerows(out)
    os.replace(dst + ".part", dst)
    n = sum(1 for r in out if r["is_source"] == "yes")
    print("%s: %d squares files, %d sources at >= %.4f mm, %d with no measured sheet"
          % (dst, len(out), n, min_mm, sum(1 for r in out if r["sheets_measured"] == 0)))


if __name__ == "__main__":
    main()
