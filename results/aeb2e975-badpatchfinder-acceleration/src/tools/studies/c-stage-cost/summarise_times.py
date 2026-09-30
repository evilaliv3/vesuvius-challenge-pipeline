#!/usr/bin/env python3
"""The c stage time of every seed in every arm, read back from evidence/runs.csv, beside the time
the run that wrote the sheets on disk took.

The reference times are read from the logs of seed-search-1447, not typed here: the uncapped runs
of seeds 38, 40 and 48 (log/uncapped-seed*.txt) and the seed runner's own rows for seeds 01, 15
and 26 (evidence/runs/PHerc1447-seed*.csv, quantity downstream_stage_c_seconds).

evidence/runs.csv carries one repeated header row, written by a second process of an earlier
version of tools/run_arm.py; any row whose first field is the word tag is skipped here and the
raw file is left as it was written.

Writes evidence/c-stage-times.csv.
"""
import csv, os, re, sys

S = "/data/scrollagent/runs/rev1/c-stage-cost"
SS = "/data/scrollagent/runs/rev1/seed-search-1447"
SEEDS = ["PHerc1447-seed01", "PHerc1447-seed15", "PHerc1447-seed26",
         "PHerc1447-seed38", "PHerc1447-seed40", "PHerc1447-seed48"]
ARMS = ["c1", "c2"]


def reference():
    ref = {}
    for a in SEEDS:
        p = os.path.join(SS, "log", "uncapped-%s.txt" % a.split("-")[1])
        if os.path.exists(p):
            for line in open(p):
                m = re.search(r"stage 'c' rc=(\d+) in (\d+) s", line)
                if m and m.group(1) == "0":
                    ref[a] = (m.group(2), "uncapped run, " + p)
        if a in ref:
            continue
        p = os.path.join(SS, "evidence", "runs", a + ".csv")
        for r in csv.reader(open(p)):
            if len(r) > 2 and r[1] == "downstream_stage_c_seconds":
                ref[a] = (r[2], "seed runner row, " + p)
    return ref


def main():
    ref = reference()
    rows = []
    with open(os.path.join(S, "evidence", "runs.csv")) as f:
        for r in csv.reader(l for l in f if not l.startswith("#")):
            if not r or r[0] == "tag":
                continue
            rows.append(r)
    out = os.path.join(S, "evidence", "c-stage-times.csv")
    with open(out, "w", newline="") as fh:
        fh.write("# the c stage of each seed, in each arm of this study, against the run that "
                 "wrote the sheets on disk. arm_seconds is read back from evidence/runs.csv, "
                 "column seconds, on the rows whose stage is c; reference_seconds is read from "
                 "the log or the CSV named in reference_source and is not typed here. "
                 "speedup is reference_seconds over arm_seconds. cores_busy_at_start says how "
                 "loaded the shared machine was when the arm started, which matters: this "
                 "workload lives in the last level cache and the reference runs had the machine "
                 "to themselves for part of their time. under_ten_minutes is the director's bar, "
                 "600 s, applied to the arm's time.\n")
        w = csv.writer(fh)
        w.writerow(["arm", "attempt", "arm_seconds", "return_code", "cores_busy_at_start",
                    "reference_seconds", "reference_source", "speedup",
                    "speedup_is", "spread_over_the_runs", "under_ten_minutes"])
        for arm in ARMS:
            for a in SEEDS:
                hit = [r for r in rows if r[0] == arm and r[1] == a and r[4] == "c"]
                if not hit:
                    continue
                r = hit[-1]
                secs, rc, busy = float(r[5]), r[6], r[8]
                rs, src = ref.get(a, ("not measurable", "no reference run recorded"))
                sp = "%.1f" % (float(rs) / secs) if rs != "not measurable" else "not measurable"
                # item 11 of the after bench list, 2026-09-22: the row says which two numbers
                # were divided and over how many runs, so a factor can be checked where it is
                # printed. This tool takes the LAST run of each arm and seed, one run, so the
                # spread column says that rather than showing a zero.
                sp_is = ("%s over %s, the reference over this arm's seconds" % (rs, r[5])
                         if rs != "not measurable" else "not measurable")
                w.writerow([arm, a, r[5], rc, busy, rs, src, sp, sp_is,
                            "not measurable, one run: this tool takes the last run of each "
                            "arm and seed",
                            "yes" if secs < 600 else "no"])
                print("%-3s %-18s %8s s  reference %8s s  speedup %8s  under ten minutes %s"
                      % (arm, a, r[5], rs, sp, "yes" if secs < 600 else "no"))
    print("written to %s" % out)


if __name__ == "__main__":
    sys.exit(main())
