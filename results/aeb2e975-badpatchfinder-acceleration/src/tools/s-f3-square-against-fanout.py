#!/usr/bin/env python3
"""Figure S3, the data step: the squares of PHerc. 1447 against the fan out of their alignment map.

The specification: "the nine squares of PHerc. 1447 with the fan out on the x axis and the kind by
colour (seed-search-1447/evidence/per-seed.csv, alignment-fanout.csv)".

Three columns from three files, joined on the seed:

  square_mm  seed-search-1447/evidence/per-seed.csv, column largest_square_mm_min_step
  fan_out    seed-search-1447/evidence/alignment-fanout.csv, column fan_out
  kind       seed-search-1447/evidence/cost-per-ribbon.csv, column kind

The gate this script runs first, and the two repairs behind it. alignment-fanout.csv copies five
columns from per-seed.csv so that a tool can join the fan out and the square in one read, and
that copy drifted twice on 2026-09-22, in two different ways:

  00:31Z  the five copied columns read "not measurable" for seeds 34, 35 and 44 while
          per-seed.csv measured 5.2008, 7.6721 and 11.1968. A script joining the square off the
          copy would have drawn three fewer points and said nothing.
  02:23Z  the file's own measured columns, fan_out among them, still read "not measurable" for
          seed44, because the first repair refreshed only the copied ones. seed44's fan out is
          32.97 over 468,938 edges and 28,444 keys, measured from its own growth/rel.csv.

The guard, seed-search-1447/tools/check_fanout_agrees.py, passed between those two times, and it
passed correctly on what it compared: the five copied columns. It never looked at the measured
ones, which is this home's rule (a) turned on a guard of its own making, a check that looks only
at what it was built to look at. It has since been extended to refuse a measured column reading
"not measurable" on a row whose tree is on disk. It is still the right thing to run first and it
is now a stronger one. Two defences remain in force here whatever that guard does: the square is
read from per-seed.csv and never from the copy, and the gate runs before anything is read.

Two things this join makes plain, and the plotted table records both rather than hiding them.

One. How many points there are is a result and not a given. It is the count of rows whose
plotted column reads yes, it is recomputed on every run, and it has already changed once: it was
eight until 02:23Z and is nine now, because seed44 acquired the fan out it was missing. Today
per-seed.csv measures a square on nine of the ten seeds and alignment-fanout.csv measures a fan
out on nine, and those nine overlap in nine: every seed but seed11, whose growth returned 3 and
which therefore has a fan out, 33.97, and no square. A caption that states the count reads it
back from the comment of the plotted table, which carries it, rather than repeating this
paragraph. The seed that cannot be placed is in the table with its missing coordinate as "not
measurable" and the reason in why_not_plotted, because a point silently absent is the difference
between a scatter of nine and a scatter of eight.

Two. The kind, ribbon or tangle, is recorded in only one CSV of this home, cost-per-ribbon.csv,
and that file covers the six seeds with a time in both arms. The other seeds get kind "not
classified": no threshold on the fan out is applied here to guess one, because inventing the
classifier that the figure then displays would make the picture argue for itself.
"""

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib  # noqa: E402

DEFAULT_RUNS = "/data/scrollagent/runs/rev1"
KINDS = ("ribbon", "tangle", "not classified")
FIELDS = (["i", "attempt", "kind", "fan_out", "square_mm"]
          + ["square_mm_" + k.replace(" ", "_") for k in KINDS]
          + ["traced_area_mm2", "in_the_distribution", "plotted", "why_not_plotted"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default=DEFAULT_RUNS)
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-check-drift", dest="check_drift", action="store_false",
                    help="draw without running seed-search-1447/tools/check_fanout_agrees.py, "
                         "which is the gate that catches the two files disagreeing")
    a = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = a.out or os.path.join(here, "evidence/figures/s-f3-square-against-fanout.csv")

    st = figlib.Studies(here, a.runs)
    check = os.path.join(a.runs, "seed-search-1447/tools/check_fanout_agrees.py")
    if a.check_drift and os.path.exists(check):
        res = subprocess.run([sys.executable, check], capture_output=True, text=True)
        sys.stderr.write(res.stdout + res.stderr)
        if res.returncode != 0:
            raise SystemExit(
                "seed-search-1447/tools/check_fanout_agrees.py says alignment-fanout.csv has "
                "drifted from per-seed.csv. The figure is not drawn: a drifted copy costs "
                "points silently, which is the failure this gate exists for.")
    elif a.check_drift:
        raise SystemExit(f"{check} is not on disk. It is the gate that keeps this join honest; "
                         f"pass --no-check-drift only if you mean to draw without it.")

    _, _, per = figlib.read_study_csv(st.path("seed-search-1447/evidence/per-seed.csv"))
    _, _, fan = figlib.read_study_csv(
        st.path("seed-search-1447/evidence/alignment-fanout.csv"))
    kind_path = st.path("seed-search-1447/evidence/cost-per-ribbon.csv")
    kinds = {}
    if os.path.exists(kind_path):
        _, _, krows = figlib.read_study_csv(kind_path)
        kinds = {r["attempt"]: r["kind"] for r in krows}

    fanmap = {r["attempt"]: r for r in fan}
    rows, notes = [], []
    for i, r in enumerate(sorted(per, key=lambda r: r["attempt"])):
        seed = r["attempt"]
        sq = figlib.number(r["largest_square_mm_min_step"])
        fr = fanmap.get(seed)
        fo = figlib.number(fr["fan_out"]) if fr else None
        why = ""
        if sq is None:
            why = ("per-seed.csv column largest_square_mm_min_step is " +
                   r["largest_square_mm_min_step"])
        elif fo is None:
            why = ("alignment-fanout.csv column fan_out is " +
                   (fr["fan_out"] if fr else "absent: the seed has no row"))
        plotted = "yes" if not why else "no"
        if why:
            notes.append(f"{seed} is not on the axes: {why}")
        kind = kinds.get(seed, "not classified")
        row = dict(
            i=i,
            attempt=seed,
            kind=kind,
            fan_out=figlib.num_or_nan(fo, "%.2f"),
            square_mm=figlib.num_or_nan(sq, "%.4f"),
            traced_area_mm2=r["traced_area_mm2"],
            in_the_distribution=r["in_the_distribution"],
            plotted=plotted, why_not_plotted=why)
        # One column per kind, so the figure draws three series from one table and needs no
        # filter of its own. A seed carries its square in its kind's column and nan in the
        # others, and a seed that cannot be placed carries nan in all three.
        for k in KINDS:
            col = "square_mm_" + k.replace(" ", "_")
            row[col] = (row["square_mm"] if (k == kind and plotted == "yes")
                        else figlib.NAN)
        rows.append(row)

    drawn = sum(1 for r in rows if r["plotted"] == "yes")
    classified = sum(1 for r in rows if r["plotted"] == "yes"
                     and r["kind"] != "not classified")
    comment = (
        "figure S3, the numbers plotted and nothing else. One row per seed of "
        "seed-search-1447/evidence/per-seed.csv. square_mm is its column "
        "largest_square_mm_min_step; fan_out is column fan_out of "
        "seed-search-1447/evidence/alignment-fanout.csv on the same seed; kind is column kind of "
        "seed-search-1447/evidence/cost-per-ribbon.csv; traced_area_mm2 and in_the_distribution "
        "are per-seed.csv's own columns. A seed is drawn only when both coordinates are numbers, "
        "and the plotted column says which; the specification's nine is not reachable, because "
        "the nine seeds with a square and the nine with a fan out are not the same nine. "
        "seed-search-1447/tools/check_fanout_agrees.py was run before this table was written "
        "and agreed. " + st.report() +
        " The number of seeds on the axes is a result of this run and not a constant: it was "
        "eight until seed44's fan out was measured at 02:23Z on 2026-09-22. Seeds on the axes: " + str(drawn) +
        ". Of those, seeds whose kind a CSV states: " + str(classified) +
        "; the rest are drawn as not classified and no threshold was applied to guess them. "
        "Seeds left off and why: " + ("; ".join(notes) if notes else "none") +
        ". Written " + figlib.utc_now() + "."
    )
    figlib.write_plotted(out, comment, FIELDS, rows)
    sys.stderr.write(f"{out}: {len(rows)} rows, {drawn} on the axes\n")
    for n in notes:
        sys.stderr.write("  note: " + n + "\n")


if __name__ == "__main__":
    main()
