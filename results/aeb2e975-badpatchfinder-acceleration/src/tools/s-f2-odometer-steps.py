#!/usr/bin/env python3
"""Figure S2, the data step: the odometer's steps before and after, on a logarithmic axis.

The specification: "the odometer's steps before and after (51,500,264,151 against 946,327 on
seed40), a bar on a log axis (c-stage-cost/evidence/totals.csv)". Those two numbers are not typed
here and are not typed in the figure: they are read from that file, and if the file disagrees with
the specification the file wins and the outcome says so.

c-stage-cost/evidence/totals.csv is a quantity table: three columns, quantity, attempt and value,
with source naming the CSV each total was summed from. Three of its quantities are the ones this
figure needs, and they are matched on the exact string, never on a substring, because "measured,
pruned" and "measured, unpruned" differ by one word and a substring match would silently take
whichever came first:

  before  "odometer steps, all four rounds, model"                 the enumeration as the walk in
                                                                   the source describes it
  after   "odometer steps, all four rounds, measured, pruned"      the counter in the changed arm
  control "odometer steps, all four rounds, measured, unpruned"    the counter in the arm that
                                                                   ships, where it exists

The table is written one row per seed and one column per series, which is the form every plotted
table of this work uses and the reason is in tools/figlib.py: pgfplotstable parses every cell of
a column the figure plots, so a missing total has to be a number or the figure does not compile.
A seed that has one of the three series and not another carries nan in that column and the
study's own words in the status column beside it. It is never given a zero: zero steps is a
statement about the enumeration and none of these seeds made it.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib  # noqa: E402

DEFAULT_RUNS = "/data/scrollagent/runs/rev1"
SERIES = [
    ("modelled_steps", "odometer steps, all four rounds, model"),
    ("counted_pruned_steps", "odometer steps, all four rounds, measured, pruned"),
    ("counted_unpruned_steps", "odometer steps, all four rounds, measured, unpruned"),
]
FIELDS = (["i", "attempt"]
          + [c for c, _ in SERIES]
          + [c + "_status" for c, _ in SERIES]
          + ["source_file", "source_column"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default=DEFAULT_RUNS)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = a.out or os.path.join(here, "evidence/figures/s-f2-odometer-steps.csv")

    st = figlib.Studies(here, a.runs)
    path = st.path("c-stage-cost/evidence/totals.csv")
    _, _, srows = figlib.read_study_csv(path)

    table = {}
    for r in srows:
        for col, quantity in SERIES:
            if r["quantity"] == quantity:
                table.setdefault(r["attempt"], {})[col] = (r["value"], r["source"])

    # Ordered by the modelled count, largest first, and a seed that has no modelled count goes
    # last by name rather than being sorted as if it had zero steps. A default in a sort key is
    # a measurement nobody wrote, exactly like a default in a lookup.
    def order(seed):
        got = table[seed].get("modelled_steps")
        value = figlib.number(got[0]) if got else None
        return (value is None, -(value or 0.0), seed)

    attempts = sorted(table, key=order)
    rows, notes, sources = [], [], set()
    for i, attempt in enumerate(attempts):
        row = {"i": i, "attempt": attempt,
               "source_file": "c-stage-cost/evidence/totals.csv",
               "source_column": "value on the row whose quantity is the series name"}
        for col, quantity in SERIES:
            got = table[attempt].get(col)
            if got is None:
                notes.append(f"{attempt} has no row for the quantity {quantity}")
                row[col] = figlib.NAN
                row[col + "_status"] = figlib.NOT_MEASURABLE
                continue
            value, source = got
            row[col] = figlib.num_or_nan(value, "%.0f")
            row[col + "_status"] = ("measured" if row[col] != figlib.NAN
                                    else figlib.NOT_MEASURABLE)
            sources.add(source)
        rows.append(row)

    comment = (
        "figure S2, the numbers plotted and nothing else. One row per seed, one column per "
        "series. Every value is column value of c-stage-cost/evidence/totals.csv on the row "
        "whose quantity is the series the column is named for: modelled_steps from the "
        "quantity odometer steps, all four rounds, model; counted_pruned_steps from the same "
        "quantity with measured, pruned; counted_unpruned_steps with measured, unpruned. Each "
        "of those values is itself a sum, and that file's source column names the per round CSV "
        "it was summed from: " + ("; ".join(sorted(sources)) if sources else "none") + ". A "
        "series a seed has no row for carries nan and its status column carries the study's own "
        "words, so the panel has a gap and never a bar at zero. Seeds are ordered by the "
        "modelled count, largest first. " + st.report() + " What is missing: "
        + ("; ".join(notes) if notes else "nothing") + ". Written " + figlib.utc_now() + "."
    )
    figlib.write_plotted(out, comment, FIELDS, rows)
    sys.stderr.write(f"{out}: {len(rows)} rows\n")
    for n in notes:
        sys.stderr.write("  note: " + n + "\n")


if __name__ == "__main__":
    main()
