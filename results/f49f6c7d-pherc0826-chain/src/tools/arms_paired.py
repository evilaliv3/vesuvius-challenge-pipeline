#!/usr/bin/env python3
"""Item 91's arms compared on the seeds they share, one pair of neighbouring arms at a time.

arms.csv gives each arm's medians over the seeds IT completed, which differ from arm to arm while the
runs finish; a difference between two such medians is partly a difference of seeds. This reads
stevens-changes-0826-91/per-run.csv (this work's snapshot), keeps for each pair (A and B, B and C,
C and D) the seeds whose outcome is «completed» in both arms, and writes the median of each measure in
each arm over exactly those seeds, both beside each other. It divides nothing. With no shared seed a
median is «not measurable, no shared seed», never zero.

Usage: arms_paired.py [--out PATH]
"""
import argparse, csv, os, statistics, subprocess

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(S, "evidence", "studies", "stevens-changes-0826-91", "per-run.csv")
MEASURES = ["cpu_seconds", "wall_seconds", "sheets", "stevens_formula_cm2", "best_square_mm", "a2_share"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(S, "evidence", "derived", "arms-paired.csv"))
    a = ap.parse_args()
    with open(P, newline="") as fh:
        runs = list(csv.DictReader(l for l in fh if not l.lstrip().startswith(('"#', "#"))))
    done = {(r["arm"], r["attempt"]): r for r in runs if r["outcome"] == "completed"}
    out = []
    for old, new in (("A", "B"), ("B", "C"), ("C", "D")):
        shared = sorted({s for (arm, s) in done if arm == old} & {s for (arm, s) in done if arm == new})
        for m in MEASURES:
            row = {"pair": old + new, "shared_seeds": len(shared), "seeds": ";".join(shared), "measure": m}
            for arm, k in ((old, "old"), (new, "new")):
                vals = [float(done[(arm, s)][m]) for s in shared if done[(arm, s)][m] not in ("", "not measurable")]
                row["%s_arm" % k] = arm
                row["%s_median" % k] = ("%.4f" % statistics.median(vals)) if vals else "not measurable"
            out.append(row)
    now = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    with open(a.out, "w", newline="") as fh:
        fh.write('"# written by src/tools/arms_paired.py at %s from the snapshot of stevens-changes-0826-91/per-run.csv: '
                 'medians over the seeds completed in both arms of each pair; nothing divided"\n' % now)
        w = csv.DictWriter(fh, fieldnames=["pair", "shared_seeds", "seeds", "measure", "old_arm", "old_median", "new_arm", "new_median"])
        w.writeheader()
        w.writerows(out)
    for r in out:
        if r["measure"] in ("stevens_formula_cm2", "cpu_seconds"):
            print("  %s %-20s shared %d: %s | %s" % (r["pair"], r["measure"], r["shared_seeds"], r["old_median"], r["new_median"]))


if __name__ == "__main__":
    main()
