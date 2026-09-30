#!/usr/bin/env python3
"""The sums this study's outcome quotes, computed from the CSVs the tools wrote, so that no total
in the prose is added up by hand.

Reads evidence/step-counts-model.csv, evidence/step-counts-measured.csv,
evidence/step-counts-pruned-model.csv and evidence/phases.csv, and writes evidence/totals.csv.
"""
import csv, os, sys
from collections import defaultdict

S = "/data/scrollagent/runs/rev1/c-stage-cost"
E = os.path.join(S, "evidence")


def read(name):
    with open(os.path.join(E, name)) as f:
        return list(csv.DictReader(l for l in f if not l.startswith("#")))


def main():
    rows = []

    model = read("step-counts-model.csv")
    for a in sorted({r["attempt"] for r in model}):
        tot = sum(int(r["odometer_steps"]) for r in model if r["attempt"] == a)
        rows.append(["odometer steps, all four rounds, model", a, tot,
                     "sum of evidence/step-counts-model.csv column odometer_steps"])
        last = [r for r in model if r["attempt"] == a and r["length"] == "5"][0]
        rows.append(["share of the steps that are the round at length 5, per cent", a,
                     "%.2f" % (100.0 * int(last["odometer_steps"]) / tot),
                     "step-counts-model.csv, length 5 over the sum"])

    meas = read("step-counts-measured.csv")
    for variant in sorted({r["variant"] for r in meas}):
        for a in sorted({r["attempt"] for r in meas if r["variant"] == variant}):
            tot = sum(int(r["odometer_steps"]) for r in meas
                      if r["variant"] == variant and r["attempt"] == a)
            rows.append(["odometer steps, all four rounds, measured, %s" % variant, a, tot,
                         "sum of evidence/step-counts-measured.csv column odometer_steps"])

    m40 = sum(int(r["odometer_steps"]) for r in model if r["attempt"] == "PHerc1447-seed40")
    p40 = sum(int(r["odometer_steps"]) for r in meas
              if r["variant"] == "pruned" and r["attempt"] == "PHerc1447-seed40")
    rows.append(["factor between the unpruned model and the pruned counter", "PHerc1447-seed40",
                 "%.0f" % (m40 / p40), "the two sums above, divided"])

    pm = read("step-counts-pruned-model.csv")
    rows.append(["pruned steps, all four rounds, the model written before the change",
                 "PHerc1447-seed40", sum(int(r["pruned_steps"]) for r in pm),
                 "sum of evidence/step-counts-pruned-model.csv column pruned_steps"])

    ph = read("phases.csv")
    agg = defaultdict(lambda: defaultdict(float))
    for r in ph:
        for k in ("setup_seconds", "odometer_seconds", "sequences_seconds", "cover_seconds"):
            agg[(r["tag"], r["attempt"])][k] += float(r[k])
    for (tag, a), d in sorted(agg.items()):
        for k, v in d.items():
            rows.append(["%s summed over the four rounds, arm %s" % (k, tag), a, "%.2f" % v,
                         "sum of evidence/phases.csv column %s" % k])
        rows.append(["the four phases together, arm %s" % tag, a,
                     "%.2f" % sum(d.values()), "sum of the four columns of phases.csv"])

    out = os.path.join(E, "totals.csv")
    with open(out, "w", newline="") as fh:
        fh.write("# every total the outcome of this study quotes, added up here from the CSVs the "
                 "tools wrote and not by hand. quantity says what it is, attempt which tree, "
                 "value the number, and source which file and column it was summed from.\n")
        w = csv.writer(fh)
        w.writerow(["quantity", "attempt", "value", "source"])
        w.writerows(rows)
    for r in rows:
        print("%-62s %-18s %s" % (r[0][:62], r[1], r[2]))
    print("written to %s" % out)


if __name__ == "__main__":
    sys.exit(main())
