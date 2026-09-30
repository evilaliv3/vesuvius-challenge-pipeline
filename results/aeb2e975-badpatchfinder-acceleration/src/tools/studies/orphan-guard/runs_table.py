#!/usr/bin/env python3
"""One row per stage run by this study, read back from the run logs the scripts wrote."""
import csv, glob, os, re, sys

H = "/data/scrollagent/runs/rev1/orphan-guard"
LINE = re.compile(r"^(\S+) \[(plain|guard) (PHerc1447-seed\d+)\] stage '([^']+)' rc=(-?\d+) in (\d+) s(?:, sheets (\d+))?")


def main():
    rows = []
    for log in sorted(glob.glob(os.path.join(H, "log", "run-*.txt"))):
        with open(log, errors="replace") as f:
            for line in f:
                m = LINE.match(line.strip())
                if m:
                    ended, series, attempt, stage, rc, secs, sheets = m.groups()
                    rows.append([attempt, series, stage, rc, secs,
                                 sheets if sheets is not None else "not applicable",
                                 ended, os.path.basename(log)])
    out = os.path.join(H, "evidence", "runs.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["attempt", "series", "stage", "return_code", "wall_clock_seconds",
                    "delivered_sheets_after_the_stage", "ended_utc", "run_log"])
        w.writerows(rows)
    print("%d rows written to %s" % (len(rows), out))


if __name__ == "__main__":
    sys.exit(main())
