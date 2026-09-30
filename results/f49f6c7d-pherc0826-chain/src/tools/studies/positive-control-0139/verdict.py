#!/usr/bin/env python3
"""positive-control-0139/tools/verdict.py STAGE [VARIANT ...]: one row of evidence/verdict.csv by the bar of DECLARATION.md,
read from evidence/control.csv at k = 4 (the common region). Theirs = rows of surface «theirs», variant lattice. Ours = rows
of surfaces «ours-*» whose variant is among the given ones (all variants when none is given). Appends, never rewrites.
Written 2026-09-29 by an agent of the coordinator."""
import csv, os, subprocess, sys

S = "/data/scrollagent/runs/rev1/positive-control-0139"
TOOL = "positive-control-0139/tools/verdict.py"


def now():
    return subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True, check=True).stdout.strip()


def main():
    stage = sys.argv[1]; want = set(sys.argv[2:])
    rows = [r for r in csv.DictReader(l for l in open(S + "/evidence/control.csv") if not l.startswith('"#')) if r["k_vox"] == "4"]
    th = [r for r in rows if r["surface"] == "theirs" and r["variant"] == "lattice" and not r["common_with"].startswith("theirs")]
    ou = [r for r in rows if r["surface"].startswith("ours") and (not want or r["variant"] in want)]
    num = lambda rr: [r for r in rr if r["ba"] != "not measurable"]
    desc = lambda r: "%s %s k%s m%s %s %s ba %s n_common %s" % (r["surface"], r["variant"], r["orientation_k"], r["orientation_m"],
                                                               r["direction"], r["checkpoint"], r["ba"], r["n_common"])
    tb = max(num(th), key=lambda r: float(r["ba"])) if num(th) else None
    ob = max(num(ou), key=lambda r: float(r["ba"])) if num(ou) else None
    tba = float(tb["ba"]) if tb else None
    oba = float(ob["ba"]) if ob else None
    n_nm = len(ou) - len(num(ou))
    if tba is None or not ou:
        branch = "not measurable: theirs or ours has no scored row"
    elif tba < 0.70:
        branch = "control not valid: theirs best ba under 0.70, the bar decides nothing about our sheets"
    elif oba is not None and oba >= 0.70:
        branch = "ours reaches 0.70: the best orientation of ours is the one to use on 0826"
    elif oba is None or oba < 0.60:
        branch = "theirs at least 0.70 and ours below 0.60 in every row: our render path is wrong, the 12 readings on 0826 are void"
    else:
        branch = "neither branch of the bar: theirs at least 0.70, ours best between 0.60 and 0.70"
    p = S + "/evidence/verdict.csv"
    new = not os.path.exists(p)
    with open(p, "a", newline="") as f:
        if new:
            f.write(f'"# written by {TOOL}; the bar of DECLARATION.md (director 2026-09-29T06:22:17Z) read from evidence/control.csv at k = 4, common region; appended, never rewritten"\n')
            csv.writer(f).writerow(["tool", "time", "stage", "variants_of_ours", "theirs_rows", "theirs_best_ba", "theirs_best_row",
                                    "ours_rows", "ours_rows_not_measurable", "ours_rows_at_or_above_060", "ours_best_ba",
                                    "ours_best_row", "branch"])
        csv.writer(f).writerow([TOOL, now(), stage, " ".join(sorted(want)) or "all", len(th), tb["ba"] if tb else "not measurable",
                                desc(tb) if tb else "", len(ou), n_nm, sum(1 for r in num(ou) if float(r["ba"]) >= 0.60),
                                ob["ba"] if ob else "not measurable", desc(ob) if ob else "", branch])
    print(branch)


if __name__ == "__main__":
    main()
