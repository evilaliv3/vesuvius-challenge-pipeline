#!/usr/bin/env python3
"""Figure S1, the data step: the c stage before and after, per seed, on two scrolls.

What it draws, in the specification's words: "the c stage before and after, per seed, on a
logarithmic axis, seeds ordered by fan out; two scrolls side by side".

Where every number comes from, and there is no other source:

  panel PHerc1447
    after_seconds    c-stage-cost/evidence/c-stage-times.csv, column arm_seconds, rows arm = c2
    before_seconds   the same file, column reference_seconds, the same rows
    reference_source the same file, column reference_source, carried into the plotted table so a
                     reader sees which "before" is an uncapped run and which is a seed runner row
    cores_busy       the same file, column cores_busy_at_start
    fan_out          seed-search-1447/evidence/alignment-fanout.csv, column fan_out, which is the
                     ordering the specification asks for

  panel PHerc0139
    plain, c2, guarded   c-stage-on-0139/evidence/c-stage-times.csv, column median_seconds, one
                     row per tree and arm, with min_seconds and max_seconds as the observed
                     range. This half is drawn as a range and not as a before and after pair:
                     see the note on panel_0139 below.
    verdict          c-stage-on-0139/evidence/c-stage-diff.csv, columns verdict, delta_percent
                     and ranges_overlap on the pair plain against c2
    cores_busy       c-stage-times.csv, columns cores_busy_min and cores_busy_max

  identity, added 2026-09-28 (director's figure pass, owner's word: identical output marked
  where the evidence shows it)
    identity_files_1447, identity_identical_1447
                     c-stage-cost/evidence/identity.csv, rows tag = c2 of the seed: the files
                     compared and how many read byte_identical yes
    stdout_identical_1447  c-stage-cost/evidence/stdout-identity.csv, column identical, row
                     tag = c2 of the seed
    identity_mark_1447     the seconds of the drawn after bar when every file compared and the
                     standard output are identical, nan otherwise, so the mark is drawn only
                     where the evidence shows identity
    identity_files_0139, identity_differing_0139
                     c-stage-on-0139/evidence/identity-by-tree.csv, columns
                     written_by_downstream and written_differing, row arm_a plain, arm_b c2
    identity_mark_0139     column c2_max of the tree when written_differing is 0, nan otherwise

  optional, when the quiet bench of PLAN 58 has finished
    quiet-bench/evidence/c-stage-runs.csv, column seconds, grouped by tag and attempt, added as
    the columns quiet_median_seconds and quiet_runs and as the column machine set to quiet. Until
    that file carries the seeds, the panel is drawn from the shared machine numbers and every row
    says so in its own machine column, because a second measured beside other work is not the
    second the caption would otherwise be claiming.

The table is wide: one row per position on the abscissa, one column per series, the two panels
side by side in the same row. tools/figlib.py says why, and it was measured rather than assumed.
A series with no value at a position carries nan, which pgfplots drops, and never a zero; the
study's own words stay in the status and verdict columns beside the numbers. The left panel has
six seeds and the right seven trees, so the last row carries only the right panel's columns.
"""

import argparse
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib  # noqa: E402

DEFAULT_RUNS = "/data/scrollagent/runs/rev1"
ARMS_0139 = ("plain", "c2", "guarded")
FIELDS = (["i",
           "seed_1447", "seed_label_1447", "fan_out", "before_seconds", "after_seconds", "speedup",
           "quiet_factor_plain_over_c2", "quiet_factor_label", "quiet_comparable",
           "machine_1447", "cores_busy_1447", "reference_source",
           "quiet_plain_seconds", "quiet_c2_seconds", "quiet_noA8_seconds", "quiet_runs",
           "tree_0139"]
          + [f"{arm}_{k}" for arm in ARMS_0139 for k in ("median", "min", "max")]
          + ["runs_0139", "delta_percent_plain_to_c2", "verdict", "ranges_overlap",
             "machine_0139", "cores_busy_0139_min", "cores_busy_0139_max",
             "identity_files_1447", "identity_identical_1447", "stdout_identical_1447",
             "identity_mark_1447", "identity_files_0139", "identity_differing_0139",
             "identity_mark_0139"])


def identity_columns(st, left, right, notes):
    """Mark identical output where the evidence shows it, and nowhere else.

    PHerc. 1447: the files the c2 arm wrote against the sha256 taken before any stage ran, and
    the whole standard output of its c stage. The mark sits on the drawn after bar, so it is
    written only when that bar is drawn (a quiet pair) and every comparison of the seed reads yes.
    PHerc. 0139: the files the downstream wrote, plain against c2, per tree.
    """
    _, _, irows = figlib.read_study_csv(st.path("c-stage-cost/evidence/identity.csv"))
    _, _, orows = figlib.read_study_csv(st.path("c-stage-cost/evidence/stdout-identity.csv"))
    for row in left:
        seed = row["seed_1447"]
        mine = [r for r in irows if r["tag"] == "c2" and r["attempt"] == seed]
        out = [r for r in orows if r["tag"] == "c2" and r["attempt"] == seed]
        same = sum(1 for r in mine if r["byte_identical"] == "yes")
        row["identity_files_1447"] = str(len(mine)) if mine else figlib.NOT_MEASURABLE
        row["identity_identical_1447"] = str(same) if mine else figlib.NOT_MEASURABLE
        row["stdout_identical_1447"] = out[0]["identical"] if len(out) == 1 else figlib.NOT_MEASURABLE
        after = figlib.number(row.get("quiet_c2_seconds"))
        ok = mine and same == len(mine) and row["stdout_identical_1447"] == "yes"
        row["identity_mark_1447"] = "%.1f" % after if (ok and after is not None) else figlib.NAN
        if not ok:
            notes.append(f"{seed}: identity not shown by the evidence, no mark")
        elif after is None:
            notes.append(f"{seed}: identical, but no quiet pair is drawn, so no mark")
    _, _, brows = figlib.read_study_csv(st.path("c-stage-on-0139/evidence/identity-by-tree.csv"))
    pair = {r["tree"]: r for r in brows if r["arm_a"] == "plain" and r["arm_b"] == "c2"}
    for row in right:
        r = pair.get(row["tree_0139"])
        if r is None:
            row["identity_files_0139"] = row["identity_differing_0139"] = figlib.NOT_MEASURABLE
            row["identity_mark_0139"] = figlib.NAN
            notes.append(f"{row['tree_0139']}: no identity row, no mark")
            continue
        row["identity_files_0139"] = r["written_by_downstream"]
        row["identity_differing_0139"] = r["written_differing"]
        top = figlib.number(row.get("c2_max"))
        row["identity_mark_0139"] = ("%.1f" % top if (r["written_differing"] == "0" and top is not None)
                                     else figlib.NAN)


def panel_1447(st, notes):
    """PHerc. 1447: the before and after pair of each seed, ordered by fan out."""
    times = st.path("c-stage-cost/evidence/c-stage-times.csv")
    fanf = st.path("seed-search-1447/evidence/alignment-fanout.csv")
    _, _, trows = figlib.read_study_csv(times)
    _, _, frows = figlib.read_study_csv(fanf)
    fan = {r["attempt"]: figlib.number(r["fan_out"]) for r in frows}

    c2 = [r for r in trows if r["arm"] == "c2"]
    ordered = sorted(c2, key=lambda r: (fan.get(r["attempt"]) is None,
                                        fan.get(r["attempt"]) or 0.0))
    out = []
    for r in ordered:
        seed = r["attempt"]
        after = figlib.number(r["arm_seconds"])
        before = figlib.number(r["reference_seconds"])
        if after is None or before is None:
            notes.append(f"{seed}: a time is not a number in c-stage-times.csv")
        out.append({
            "seed_1447": seed,
            "seed_label_1447": seed.replace("PHerc1447-", ""),
            "fan_out": figlib.num_or_nan(fan.get(seed), "%.2f"),
            "before_seconds": figlib.num_or_nan(before, "%.1f"),
            "after_seconds": figlib.num_or_nan(after, "%.1f"),
            "speedup": (figlib.NAN if (before is None or not after)
                        else "%.1f" % (before / after)),
            "machine_1447": "shared",
            "cores_busy_1447": r["cores_busy_at_start"],
            "reference_source": r["reference_source"],
        })
    return out


def panel_0139(st, notes):
    """The reference scroll, drawn as a range and not as a before and after pair.

    Corrected on 2026-09-22 on the coordinator's instruction, after c-stage-on-0139 landed. On
    PHerc. 0139 the change is not a speedup: four of the seven trees are not separable from the
    spread of their own repeated runs and three are faster by single or low double digit
    percentages. Two bars on a logarithmic axis would be two bars of the same height, and a
    reader would take that for a figure that failed rather than for the result it is. So this
    panel carries, per tree and per arm, the median of the repeated runs with the observed
    minimum and maximum around it, which is the only form in which "not separable from the
    spread" is visible at all.

    The verdict is not restated in prose: it is column verdict of
    c-stage-on-0139/evidence/c-stage-diff.csv on the pair plain against c2, carried into the
    table beside the delta and the ranges_overlap flag that produced it.
    """
    path = st.path("c-stage-on-0139/evidence/c-stage-times.csv")
    if not os.path.exists(path):
        notes.append("PHerc0139 panel pending: c-stage-on-0139/evidence/c-stage-times.csv is "
                     "not on disk")
        return []
    _, _, trows = figlib.read_study_csv(path)

    diff_path = st.path("c-stage-on-0139/evidence/c-stage-diff.csv")
    verdicts = {}
    if os.path.exists(diff_path):
        _, _, drows = figlib.read_study_csv(diff_path)
        for r in drows:
            if r.get("arm_a") == "plain" and r.get("arm_b") == "c2":
                verdicts[r["tree"]] = r
    else:
        notes.append("c-stage-on-0139/evidence/c-stage-diff.csv is not on disk: the table has "
                     "no verdict column and the caption must not state one")

    trees, by_tree = [], {}
    for r in trows:
        if r["tree"] not in trees:
            trees.append(r["tree"])
        by_tree[(r["tree"], r["arm"])] = r

    out = []
    for tree in trees:
        d = verdicts.get(tree, {})
        row = {"tree_0139": tree,
               "delta_percent_plain_to_c2": d.get("delta_percent", figlib.NAN),
               "verdict": d.get("verdict", figlib.NOT_MEASURABLE),
               "ranges_overlap": d.get("ranges_overlap", figlib.NOT_MEASURABLE),
               "machine_0139": "shared"}
        runs_seen, busy_lo, busy_hi = [], [], []
        for arm in ARMS_0139:
            r = by_tree.get((tree, arm))
            if r is None:
                notes.append(f"{tree} has no row for the arm {arm}")
                for k in ("median", "min", "max"):
                    row[f"{arm}_{k}"] = figlib.NAN
                continue
            row[f"{arm}_median"] = figlib.num_or_nan(r["median_seconds"], "%.1f")
            row[f"{arm}_min"] = figlib.num_or_nan(r["min_seconds"], "%.1f")
            row[f"{arm}_max"] = figlib.num_or_nan(r["max_seconds"], "%.1f")
            runs_seen.append(r["runs"])
            busy_lo.append(r["cores_busy_min"])
            busy_hi.append(r["cores_busy_max"])
        row["runs_0139"] = ";".join(sorted(set(runs_seen)))
        row["cores_busy_0139_min"] = min(busy_lo, key=lambda v: figlib.number(v) or 0.0) \
            if busy_lo else figlib.NOT_MEASURABLE
        row["cores_busy_0139_max"] = max(busy_hi, key=lambda v: figlib.number(v) or 0.0) \
            if busy_hi else figlib.NOT_MEASURABLE
        out.append(row)
    return out


def bench_columns(st, left, notes):
    """The quiet bench of PLAN 58, when it has written rows for these seeds."""
    path = st.path("quiet-bench/evidence/c-stage-runs.csv")
    if not os.path.exists(path):
        notes.append("quiet bench pending: quiet-bench/evidence/c-stage-runs.csv is not on disk")
        return
    _, _, brows = figlib.read_study_csv(path)
    groups = {}
    for r in brows:
        if r.get("return_code") != "0" or r.get("cap_bit") == "yes":
            continue
        s = figlib.number(r["seconds"])
        if s is None:
            continue
        groups.setdefault((r["attempt"], r["binary_label"]), []).append(s)
    if not groups:
        notes.append("quiet bench pending: no completed uncapped run in c-stage-runs.csv")
        return
    for row in left:
        seed = row["seed_1447"]
        n = []
        for arm in ("plain", "c2", "noA8"):
            vals = groups.get((seed, arm))
            row[f"quiet_{arm}_seconds"] = (figlib.NAN if not vals
                                           else "%.1f" % statistics.median(vals))
            if vals:
                n.append(len(vals))
        row["quiet_runs"] = ";".join(str(k) for k in n) if n else figlib.NOT_MEASURABLE
        # The factor the panel prints over each pair, and whether the pair exists at all.
        # The afternoon before and after are NOT a pair: on the three ribbons the before was
        # taken at twenty four threads and the after at four, so the before bar came out
        # SHORTER than the after and the panel said the change had made the stage slower. The
        # panel now draws the quiet pair only, and a seed with no quiet pair is marked.
        qp = groups.get((seed, "plain"))
        qc = groups.get((seed, "c2"))
        if qp and qc:
            f = statistics.median(qp) / statistics.median(qc)
            row["quiet_factor_plain_over_c2"] = "%.1f" % f
            row["quiet_factor_label"] = ("%.0f times" % f) if f >= 10 else ("%.2f times" % f)
            row["quiet_comparable"] = "yes"
        else:
            row["quiet_factor_plain_over_c2"] = figlib.NAN
            row["quiet_factor_label"] = ""
            row["quiet_comparable"] = "no, no quiet pair; the shared machine numbers beside it were taken at different thread counts and are not a pair"
            row["seed_label_1447"] = row["seed_label_1447"] + " (no quiet pair)"
        # machine_1447 describes before_seconds and after_seconds, which stay shared machine
        # numbers whatever the bench adds. Leaving it at the bare word «shared» on a row that
        # now also carries quiet columns invites a reader to apply it to the whole row, so the
        # row says which half it covers as soon as the other half exists.
        if n:
            row["machine_1447"] = ("shared for before_seconds and after_seconds, quiet for the "
                                   "quiet_ columns")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default=DEFAULT_RUNS)
    ap.add_argument("--out", default=None)
    ap.add_argument("--bench", action="store_true",
                    help="add the quiet bench columns of PLAN 58 when that study has them")
    a = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = a.out or os.path.join(here, "evidence/figures/s-f1-c-stage-before-after.csv")

    notes = []
    st = figlib.Studies(here, a.runs)
    left = panel_1447(st, notes)
    right = panel_0139(st, notes)
    if a.bench:
        bench_columns(st, left, notes)
        # The three seeds with a quiet pair come first so the left panel can draw them and
        # nothing else; fan out still orders within each group.
        left.sort(key=lambda r: (r.get("quiet_comparable", "no") != "yes",
                                 figlib.number(r.get("fan_out")) or 0.0))
    identity_columns(st, left, right, notes)

    rows = figlib.wide_rows(max(len(left), len(right)))
    for k, row in enumerate(rows):
        if k < len(left):
            row.update(left[k])
        if k < len(right):
            row.update(right[k])
        for f in FIELDS:
            row.setdefault(f, figlib.NAN if f.endswith(
                ("_seconds", "_median", "_min", "_max", "fan_out", "speedup",
                 "delta_percent_plain_to_c2", "identity_mark_1447", "identity_mark_0139")) else "")

    comment = (
        "figure S1, the numbers plotted and nothing else. One row per position on the abscissa; "
        "the left panel's six seeds and the right panel's seven trees share the row index and "
        "each has its own columns. Left, PHerc. 1447: before_seconds is column "
        "reference_seconds and after_seconds is column arm_seconds of "
        "c-stage-cost/evidence/c-stage-times.csv on the rows whose arm is c2, ordered by column "
        "fan_out of seed-search-1447/evidence/alignment-fanout.csv, with that file's own "
        "reference_source saying for each seed whether the before is an uncapped run or a seed "
        "runner row. Right, PHerc. 0139: the median, minimum and maximum seconds of each arm "
        "over the repeated runs, columns median_seconds, min_seconds and max_seconds of "
        "c-stage-on-0139/evidence/c-stage-times.csv, with verdict, delta_percent and "
        "ranges_overlap of c-stage-on-0139/evidence/c-stage-diff.csv on the pair plain against "
        "c2. The two panels are drawn differently because they say different things: a pair of "
        "bars on the right would be two bars of the same height. Every second here was measured "
        "on a machine carrying other work, which the machine columns record; the quiet bench of "
        "PLAN 58 fills the quiet_ columns and the caption is rewritten with them. identity_ columns: "
        "rows tag c2 of c-stage-cost/evidence/identity.csv (files, byte_identical yes) and of "
        "c-stage-cost/evidence/stdout-identity.csv (identical), and columns written_by_downstream "
        "and written_differing of c-stage-on-0139/evidence/identity-by-tree.csv on the pair plain "
        "against c2; a mark column carries the height it is drawn at only where every comparison "
        "reads identical. A value the "
        "study has not measured is nan and never zero. " + st.report() + " Notes: "
        + ("; ".join(notes) if notes else "none") + ". Written " + figlib.utc_now() + "."
    )
    figlib.write_plotted(out, comment, FIELDS, rows)
    sys.stderr.write(f"{out}: {len(rows)} rows\n")
    for n in notes:
        sys.stderr.write("  note: " + n + "\n")


if __name__ == "__main__":
    main()
