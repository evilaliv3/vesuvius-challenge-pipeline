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

REVISED 2026-09-23T19:4xZ (coordinator), on the director's seed rule of 2026-09-23T19:14:15Z: a
seed counts only if its voxel is 255 with six neighbours 255, the raw masked scan is grey at its
point, and its prediction chunk holds at most 0.5 of 255. The rule is read per seed from
  seeds-at-scale-1447/evidence/seed-rule.csv, group delivered-22-september-1447
(written by seeds-at-scale-1447/tools/seed_rule_check.py), and its columns are copied into
per-seed.csv beside the seed, with seed_rule_xyz_equal checking that the row is the same point. A
seed missing from that group stops the tool: a rule that is not measured is not a pass.
The summary's `value` is now taken over the seeds ON PAPYRUS (passes_rule yes) that are in the
distribution. The aggregate over the ten as it stood before the rule is kept only in the column
`all_ten_seven_of_them_in_air`, with `all_ten_over_what` saying what it was taken over, so that a
reader who quotes it sees that seven of the ten grew in the prediction's air blocks. The files as
they were before this revision are kept beside the new ones as *-before-seed-rule-20260923T193859Z.
"""
import csv
import os
import re
import statistics
import sys

S = "/data/scrollagent/runs/rev1/seed-search-1447"
LADDER = "/data/scrollagent/runs/rev1/seed-ladder-1447"
SCROLL = "PHerc1447"
NM = "not measurable"
SEED_RULE = "/data/scrollagent/runs/rev1/seeds-at-scale-1447/evidence/seed-rule.csv"
SEED_RULE_GROUP = "delivered-22-september-1447"
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
    "column and is counted apart, never folded into a median with the seeds that finished. "
    "From 2026-09-23 the last eight columns are the seed rule of the director, 2026-09-23T19:14:15Z, "
    "copied from seeds-at-scale-1447/evidence/seed-rule.csv group delivered-22-september-1447 "
    "(seeds-at-scale-1447/tools/seed_rule_check.py): passes_seed_rule is yes only when the voxel "
    "and its six neighbours are 255, the raw masked scan is grey at the point and the prediction "
    "chunk holds at most 0.5 of 255; a seed that fails it grew in air and is named so.")


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


def seed_rule():
    """The seed rule's row for each of the ten, from its group in seed-rule.csv; refuses a gap."""
    out = {}
    for r in read_rows(SEED_RULE):
        if r["group"] == SEED_RULE_GROUP:
            if r["attempt"] in out:
                sys.exit("per_seed.py: %s holds %s twice in group %s"
                         % (SEED_RULE, r["attempt"], SEED_RULE_GROUP))
            out[r["attempt"]] = r
    want = ["%s-%s" % (SCROLL, s) for s in TEN]
    missing = [a for a in want if a not in out]
    if missing or len(out) != len(want):
        sys.exit("per_seed.py: %s group %s: expected the %d seeds, found %d, missing %s"
                 % (SEED_RULE, SEED_RULE_GROUP, len(want), len(out), missing))
    return out


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


def downstream_seconds_from_log(attempt):
    """The wall clock of the five delivery stages, summed from the runner's own log.

    run_seed_v3.sh wrote `downstream_wall_clock_seconds` into the run CSV; tools/finish_seed.sh,
    the runner that rescued the seeds that v3 left with an empty cap, does not. It prints one
    line per stage instead, `stage '<name>' rc=<rc> in <n> s`, and this sums those. It is the
    same reading of a runner's own standard output that absent_chunks_from_log does, and it is
    read only for the seeds finished by that runner: the column says which runner the row is
    from, so a reader can see the two are not the same measurement.
    """
    for name in ("uncapped-%s.txt" % attempt, "finish-%s.txt" % attempt):
        path = os.path.join(S, "log", name)
        if not os.path.exists(path):
            continue
        total = 0
        seen = False
        for line in open(path, errors="replace"):
            m = re.search(r"stage '[^']+' rc=0 in (\d+) s", line)
            if m:
                total += int(m.group(1))
                seen = True
        if seen:
            return str(total)
    return None


# A seed can be run more than once, and each runner writes the same quantities under its own
# suffix. read_kv keeps the last row of a repeated name, so a retry inside one runner resolves by
# itself; this table chooses between runners. It is ordered latest runner first and a new runner
# is added HERE, not by a reader guessing the name: returning the earlier row when a later one
# exists is how this tool read six delivered seeds as three on 2026-09-21.
RUNNERS = [("_c2arm", "c-stage-cost arm c2"),
           ("_regrown", "regrow_seed44.sh"),
           ("_v2", "finish_seed.sh"),
           ("", "run_seed_v3.sh")]


def latest(run, quantity):
    """The value of a quantity, from the latest runner that wrote one, and that runner's name."""
    for suffix, name in RUNNERS:
        if quantity + suffix in run:
            return run[quantity + suffix], name
    return NM, NM


def main():
    out_dir = os.path.join(S, "evidence")
    if len(sys.argv) == 3 and sys.argv[1] == "--out-dir":
        out_dir = sys.argv[2]
    elif len(sys.argv) != 1:
        sys.exit("usage: per_seed.py [--out-dir <dir>]")
    rule = seed_rule()
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

        rc, growth_runner = latest(run, "growth_return_code")
        finished = rc == "0"
        down_rc, runner = latest(run, "downstream_return_code")
        delivered = finished and down_rc == "0"

        measured = [r for r in squares
                    if r.get("status") == "measured" and r.get("square_mm_min_step") not in ("", NM)]
        if delivered and measured:
            best = max(float(r["square_mm_min_step"]) for r in measured)
            best_sheet = max(measured, key=lambda r: float(r["square_mm_min_step"]))["sheet"]
            reach = sum(1 for r in measured if r.get("reaches_20mm") == "yes")
            traced = area.get("traced_area_mm2", NM)
            sheets = latest(run, "delivered_sheets")[0]
            if sheets == NM:
                sheets = str(len(squares))
        else:
            best = NM
            best_sheet = NM
            reach = NM
            traced = area.get("traced_area_mm2", NM) if delivered else NM
            sheets = latest(run, "delivered_sheets")[0] if delivered else NM

        rows.append({
            "attempt": a,
            "seed_x": c.get("seed_x", NM),
            "seed_y": c.get("seed_y", NM),
            "seed_z": c.get("seed_z", NM),
            "binary_sha256": sha,
            "binary_matches_the_ladder": matches,
            "growth_return_code": rc,
            "growth_wall_clock_seconds": latest(run, "growth_wall_clock_seconds")[0],
            "growth_finished_by_itself": "yes" if finished else "no",
            "growth_patches": latest(run, "growth_patches")[0],
            "growth_rel_csv_lines": latest(run, "growth_rel_csv_lines")[0],
            "growth_absent_chunks": (run.get("growth_missing_chunks", NM)
                                     if run.get("growth_missing_chunks", NM) != NM
                                     else (absent_chunks_from_log(a) or NM)),
            "downstream_return_code": down_rc,
            "growth_runner": growth_runner,
            "downstream_runner": runner,
            "downstream_wall_clock_seconds": (
                run.get("downstream_wall_clock_seconds")
                or (downstream_seconds_from_log(a) if delivered else None) or NM),
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
        sr = rule[a]
        rows[-1].update({
            "seed_rule_xyz_equal": "yes" if all(
                sr["seed_" + k] == rows[-1]["seed_" + k] for k in "xyz") else "no",
            "pred_chunk_share_255": sr["pred_chunk_share_255"],
            "test_share_at_most_0_5": sr["test_share_at_most_0_5"],
            "raw_chunk_status": sr["raw_chunk_status"],
            "raw_at_seed": sr["raw_at_seed"],
            "test_raw_grey": sr["test_raw_grey"],
            "passes_seed_rule": sr["passes_rule"],
            "on_papyrus_or_in_air": "on papyrus" if sr["passes_rule"] == "yes" else "in air",
        })
        if rows[-1]["seed_rule_xyz_equal"] != "yes":
            sys.exit("per_seed.py: %s: the seed rule's point is not this seed's point" % a)

    out = os.path.join(out_dir, "per-seed.csv")
    with open(out, "w", newline="") as f:
        f.write('"%s"\n' % PER_SEED_NOTE)
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("wrote %s, %d rows" % (out, len(rows)))

    inside_all = [r for r in rows if r["in_the_distribution"] == "yes"]
    outside_all = [r for r in rows if r["in_the_distribution"] != "yes"]
    papyrus = [r for r in rows if r["passes_seed_rule"] == "yes"]
    air = [r for r in rows if r["passes_seed_rule"] != "yes"]
    inside = [r for r in papyrus if r["in_the_distribution"] == "yes"]
    outside = [r for r in papyrus if r["in_the_distribution"] != "yes"]
    air_in = [r for r in air if r["in_the_distribution"] == "yes"]
    short = lambda rs: ", ".join(r["attempt"].replace(SCROLL + "-", "") for r in rs) or "none"

    def values(rs):
        return (sorted(float(r["largest_square_mm_min_step"]) for r in rs),
                sorted(float(r["traced_area_mm2"]) for r in rs if r["traced_area_mm2"] != NM),
                sorted(int(r["growth_patches"]) for r in rs))

    sq, tr, pa = values(inside)
    sq_all, tr_all, pa_all = values(inside_all)
    over = ("over the %d seeds on papyrus in the distribution (%s)" % (len(inside), short(inside)))
    over_all = ("over the %d seeds of the ten in the distribution, %d of them in air (%s)"
                % (len(inside_all), len(air_in), short(air_in)))

    def stats(values):
        if not values:
            return {k: NM for k in ("maximum", "median", "minimum", "range")}, "no seed"
        conv = ("the average of the two middle values" if len(values) % 2 == 0
                else "the middle value")
        return {"maximum": values[-1], "median": statistics.median(values),
                "minimum": values[0], "range": "%s to %s" % (values[0], values[-1])}, conv

    def block(name, values, values_all, unit):
        st, conv = stats(values)
        st_all, conv_all = stats(values_all)
        out = []
        for k in ("maximum", "median", "minimum", "range"):
            out.append([name, k, st[k], unit,
                        over + (", " + conv if k == "median" else ""),
                        st_all[k], over_all + (", " + conv_all if k == "median" else "")])
        return out

    def reach(rs):
        return (sum(1 for r in rs if r["sheets_reaching_20mm"] not in (NM, 0)),
                sum(int(r["sheets_reaching_20mm"]) for r in rs if r["sheets_reaching_20mm"] != NM))

    sout = os.path.join(out_dir, "summary.csv")
    with open(sout, "w", newline="") as f:
        f.write('"# written by seed-search-1447/tools/per_seed.py. From 2026-09-23 (the director\'s seed '
                'rule of 2026-09-23T19:14:15Z) value is taken over the seeds on papyrus, passes_rule '
                'yes in seeds-at-scale-1447/evidence/seed-rule.csv group %s; the column '
                'all_ten_seven_of_them_in_air keeps the aggregate over the ten as it stood before the '
                'rule and all_ten_over_what says what it was taken over. The file before this '
                'revision is summary-before-seed-rule-20260923T193859Z.csv."\n' % SEED_RULE_GROUP)
        w = csv.writer(f)
        w.writerow(["quantity", "statistic", "value", "unit", "over_what",
                    "all_ten_seven_of_them_in_air", "all_ten_over_what"])
        w.writerow(["population", "seeds declared", len(rows), "count",
                    "the ten of DECLARATION.md", len(rows), "the ten of DECLARATION.md"])
        w.writerow(["population", "seeds on papyrus", len(papyrus), "count",
                    "passes_rule yes in seeds-at-scale-1447/evidence/seed-rule.csv: %s"
                    % short(papyrus), len(rows), "the ten, before the seed rule existed"])
        w.writerow(["population", "seeds in air", len(air), "count",
                    "passes_rule no: " + "; ".join(
                        "%s raw chunk %s, prediction chunk share %s"
                        % (r["attempt"].replace(SCROLL + "-", ""), r["raw_chunk_status"],
                           r["pred_chunk_share_255"]) for r in air),
                    len(air), "the same seven, counted in every aggregate of this column"])
        w.writerow(["population", "seeds in the distribution", len(inside), "count",
                    "on papyrus, growth returned zero, downstream returned zero, at least one sheet "
                    "measured", len(inside_all),
                    "growth returned zero, downstream returned zero, at least one sheet measured"])
        w.writerow(["population", "seeds out of the distribution", len(outside), "count",
                    "; ".join("%s: %s" % (r["attempt"], r["why_not_in_the_distribution"])
                              for r in outside) or "none of the seeds on papyrus",
                    len(outside_all),
                    "; ".join("%s: %s" % (r["attempt"], r["why_not_in_the_distribution"])
                              for r in outside_all) or "none"])
        for row in block("largest_square_mm_min_step", sq, sq_all, "mm"):
            w.writerow(row)
        for row in block("traced_area_mm2", tr, tr_all, "mm2"):
            w.writerow(row)
        for row in block("growth_patches", pa, pa_all, "count"):
            w.writerow(row)
        (s1, t1), (s1a, t1a) = reach(inside), reach(inside_all)
        w.writerow(["sheets_reaching_20mm", "seeds with at least one", s1, "count", over,
                    s1a, over_all])
        w.writerow(["sheets_reaching_20mm", "sheets in total", t1, "count", over, t1a, over_all])
        best = max(sq) if sq else None
        best_all = max(sq_all) if sq_all else None
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
            w.writerow(["comparison", name, value, "mm", what, value, "the same constant"])
            if best is not None and name != "director_rule_spread":
                w.writerow(["comparison", "our maximum minus " + name, round(best - value, 4), "mm",
                            "our maximum over the seeds on papyrus; positive means it is larger, "
                            "and the 2.6213 mm rule decides whether that counts as beating it",
                            round(best_all - value, 4) if best_all is not None else NM,
                            "our maximum " + over_all])
    print("wrote %s" % sout)


if __name__ == "__main__":
    sys.exit(main())
