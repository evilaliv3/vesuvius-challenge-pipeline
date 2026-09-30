#!/usr/bin/env python3
"""Assemble evidence/per-seed.csv and evidence/summary.csv from the files the run wrote.

One row per seed, and the row is the result. The summary that follows quotes the maximum, the
median and the range, and it quotes them over the seeds whose growth returned zero and were
delivered and measured, never over a mixture of those and of seeds that did not finish. Which
seeds are in that population, and which are not and why, is written in the summary itself, so a
reader cannot take a median without seeing what it was taken over.

Every value is copied from the CSV that carries it and none is recomputed here:
  coordinates            seed-ladder-1447/evidence/attempts.csv, columns seed_x, seed_y, seed_z
  binary sha256          evidence/runs/<attempt>.csv, quantity binary_sha256, and the gate row
  growth rc and seconds  evidence/runs/<attempt>.csv
  patches, rel.csv lines evidence/runs/<attempt>.csv
  square, reaches 20 mm  evidence/squares-<attempt>.csv, column square_mm_min_step over its rows
  traced area            evidence/area-<attempt>.csv, quantity traced_area_mm2

The median of an even count is the average of the two middle values, which is written into the
summary beside the number so that nobody has to guess the convention.
"""
import csv
import os
import statistics
import sys

S = "/data/scrollagent/runs/rev1/seed-search-1447"
LADDER = "/data/scrollagent/runs/rev1/seed-ladder-1447"
SCROLL = "PHerc1447"
NM = "not measurable"
TEN = ["seed01", "seed11", "seed15", "seed26", "seed34", "seed35", "seed38", "seed40",
       "seed44", "seed48"]

PER_SEED_NOTE = (
    "# one row per seed of the ten of DECLARATION.md, the ten drawn seeds of PHerc. 1447 that "
    "were still growing when seed-ladder-1447 stopped them at its cap of 120 seconds, grown here "
    "to the end with simpaper10 g 36000 and delivered with c, l, vm 10, hm 10, fm 30 10 at "
    "SIMPAPER_PATCH_LIMIT 40000. The voxel is 8.640 um, this scroll's own value from "
    "pipeline/datasets/manifests/PHerc1447.json through pipeline/datasets/voxel.py, never the "
    "9.362 um of PHerc0139. square_mm_min_step is the side of the exact largest axis aligned "
    "fully covered square of a delivered sheet, in millimetres with the smaller of that sheet's "
    "two measured cell steps, and the column here is the largest of that over the sheets of the "
    "seed. A seed whose growth returned non zero carries not measurable in every measured "
    "column and is counted apart, never folded into a median with the seeds that finished.")


def absent_chunks_from_log(attempt):
    """The count of zarr chunks absent during growth, from the growth's own standard output.

    The first runner wrote `not measurable` whenever ZARR_MISSING_LIST left no file, and a file is
    left only when something was missing. The binary prints the count either way, so the silence
    was a false unknown: seed01 and seed15 were both a measured zero. run_seed_v2.sh reads the
    line directly; this reads it back for the seeds that ran before that change.
    """
    path = os.path.join(S, "log", "growth-%s.txt" % attempt)
    if not os.path.exists(path):
        return None
    marker = "Zarr chunks absent from disk during growth:"
    for line in reversed(open(path, errors="replace").read().splitlines()):
        if marker in line:
            return line.split(marker, 1)[1].strip().split()[0]
    return None


def read_kv(path):
    out = {}
    if not os.path.exists(path):
        return out
    with open(path) as f:
        for r in csv.DictReader(f):
            out[r["quantity"]] = r["value"]
    return out


def read_rows(path, skip_comment=True):
    if not os.path.exists(path):
        return []
    lines = open(path).read().splitlines(True)
    if skip_comment and lines and lines[0].lstrip().startswith('"#'):
        lines = lines[1:]
    return list(csv.DictReader(lines))


def ladder_coords():
    out = {}
    with open(os.path.join(LADDER, "evidence", "attempts.csv")) as f:
        for r in csv.DictReader(f):
            if r["scroll"] == SCROLL:
                out[r["attempt"]] = r
    return out


def gate_sha():
    out = {}
    for r in read_rows(os.path.join(S, "evidence", "binary-gate.csv"), skip_comment=False):
        if r["expectation"] == "matches_ladder_sha256":
            out[r["attempt"]] = (r["sha256"], r["passes"])
    return out


def main():
    coords = ladder_coords()
    gate = gate_sha()
    rows = []
    for s in TEN:
        a = "%s-%s" % (SCROLL, s)
        run = read_kv(os.path.join(S, "evidence", "runs", "%s.csv" % a))
        squares = read_rows(os.path.join(S, "evidence", "squares-%s.csv" % a))
        area = read_kv(os.path.join(S, "evidence", "area-%s.csv" % a))
        c = coords.get(a, {})
        sha, matches = gate.get(a, (NM, NM))

        rc = run.get("growth_return_code", NM)
        finished = rc == "0"
        down_rc = run.get("downstream_return_code", NM)
        delivered = finished and down_rc == "0"

        measured = [r for r in squares
                    if r.get("status") == "measured" and r.get("square_mm_min_step") not in ("", NM)]
        if delivered and measured:
            best = max(float(r["square_mm_min_step"]) for r in measured)
            best_sheet = max(measured, key=lambda r: float(r["square_mm_min_step"]))["sheet"]
            reach = sum(1 for r in measured if r.get("reaches_20mm") == "yes")
            traced = area.get("traced_area_mm2", NM)
            sheets = run.get("delivered_sheets", str(len(squares)))
        else:
            best = NM
            best_sheet = NM
            reach = NM
            traced = area.get("traced_area_mm2", NM) if delivered else NM
            sheets = run.get("delivered_sheets", NM) if delivered else NM

        rows.append({
            "attempt": a,
            "seed_x": c.get("seed_x", NM),
            "seed_y": c.get("seed_y", NM),
            "seed_z": c.get("seed_z", NM),
            "binary_sha256": sha,
            "binary_matches_the_ladder": matches,
            "growth_return_code": rc,
            "growth_wall_clock_seconds": run.get("growth_wall_clock_seconds", NM),
            "growth_finished_by_itself": "yes" if finished else "no",
            "growth_patches": run.get("growth_patches", NM),
            "growth_rel_csv_lines": run.get("growth_rel_csv_lines", NM),
            "growth_absent_chunks": (run.get("growth_missing_chunks", NM)
                                     if run.get("growth_missing_chunks", NM) != NM
                                     else (absent_chunks_from_log(a) or NM)),
            "downstream_return_code": down_rc,
            "downstream_wall_clock_seconds": run.get("downstream_wall_clock_seconds", NM),
            "delivered_sheets": sheets,
            "sheets_measured": len(measured) if delivered else NM,
            "voxel_um": 8.64,
            "largest_square_mm_min_step": ("%.4f" % best) if best != NM else NM,
            "largest_square_on_sheet": best_sheet,
            "sheets_reaching_20mm": reach,
            "traced_area_mm2": traced,
            "in_the_distribution": "yes" if (delivered and measured) else "no",
            # Stopped is not failed, and the two must not read alike. A seed with no run record was
            # never grown; a seed whose record stops after the binary row was grown and stopped
            # before its growth ended. Neither is a growth that ran and returned an error.
            "why_not_in_the_distribution": "" if (delivered and measured) else (
                "never grown: the study was stopped by the owner at 2026-09-20T20:29Z" if not run else
                "grown and stopped before the growth ended, by the owner's stop of "
                "2026-09-20T20:29Z: stopped, not failed" if "growth_return_code" not in run else
                "the growth returned %s and did not finish" % rc if not finished else
                "the downstream returned %s" % down_rc if not delivered else
                "no sheet came back measured"),
        })

    out = os.path.join(S, "evidence", "per-seed.csv")
    with open(out, "w", newline="") as f:
        f.write('"%s"\n' % PER_SEED_NOTE)
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("wrote %s, %d rows" % (out, len(rows)))

    inside = [r for r in rows if r["in_the_distribution"] == "yes"]
    outside = [r for r in rows if r["in_the_distribution"] != "yes"]
    sq = sorted(float(r["largest_square_mm_min_step"]) for r in inside)
    tr = sorted(float(r["traced_area_mm2"]) for r in inside if r["traced_area_mm2"] != NM)
    pa = sorted(int(r["growth_patches"]) for r in inside)

    def block(name, values, unit):
        if not values:
            return [[name, "maximum", NM, unit, "no seed is in the distribution"],
                    [name, "median", NM, unit, "no seed is in the distribution"],
                    [name, "minimum", NM, unit, "no seed is in the distribution"]]
        conv = ("the average of the two middle values" if len(values) % 2 == 0
                else "the middle value")
        return [
            [name, "maximum", values[-1], unit, "over the %d seeds in the distribution" % len(values)],
            [name, "median", statistics.median(values), unit,
             "over the %d seeds in the distribution, %s" % (len(values), conv)],
            [name, "minimum", values[0], unit, "over the %d seeds in the distribution" % len(values)],
            [name, "range", "%s to %s" % (values[0], values[-1]), unit,
             "the smallest and the largest of the %d" % len(values)],
        ]

    sout = os.path.join(S, "evidence", "summary.csv")
    with open(sout, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["quantity", "statistic", "value", "unit", "over_what"])
        w.writerow(["population", "seeds declared", len(rows), "count",
                    "the ten of DECLARATION.md"])
        w.writerow(["population", "seeds in the distribution", len(inside), "count",
                    "growth returned zero, downstream returned zero, at least one sheet measured"])
        w.writerow(["population", "seeds out of the distribution", len(outside), "count",
                    "; ".join("%s: %s" % (r["attempt"], r["why_not_in_the_distribution"])
                              for r in outside) or "none"])
        for row in block("largest_square_mm_min_step", sq, "mm"):
            w.writerow(row)
        for row in block("traced_area_mm2", tr, "mm2"):
            w.writerow(row)
        for row in block("growth_patches", pa, "count"):
            w.writerow(row)
        w.writerow(["sheets_reaching_20mm", "seeds with at least one",
                    sum(1 for r in inside if r["sheets_reaching_20mm"] not in (NM, 0)), "count",
                    "over the %d seeds in the distribution" % len(inside)])
        w.writerow(["sheets_reaching_20mm", "sheets in total",
                    sum(int(r["sheets_reaching_20mm"]) for r in inside
                        if r["sheets_reaching_20mm"] != NM), "count",
                    "over the %d seeds in the distribution" % len(inside)])
        best = max(sq) if sq else None
        for name, value, what in (
                ("best_published_segment_of_PHerc1447", 13.5262,
                 "published-segments-eligible/evidence/segments-eligible.csv, segment "
                 "20251105093211-z_dbg_gen_00320, column square_mm_min_step, voxel 8.64 um"),
                ("base_on_PHerc0139", 12.1230,
                 "the same file, row marked ours, a DIFFERENT scroll at voxel 9.362 um, quoted "
                 "as a different scroll and never as a target"),
                ("director_rule_spread", 2.6213,
                 "seed-distance-ladder, the spread one chain parameter produced by itself: "
                 "beating a number by less than this is not beating it")):
            w.writerow(["comparison", name, value, "mm", what])
            if best is not None and name != "director_rule_spread":
                w.writerow(["comparison", "our maximum minus " + name, round(best - value, 4), "mm",
                            "positive means our maximum is larger, and the 2.6213 mm rule decides "
                            "whether that counts as beating it"])
    print("wrote %s" % sout)


if __name__ == "__main__":
    sys.exit(main())
