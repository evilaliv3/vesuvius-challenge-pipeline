#!/usr/bin/env python3
"""Read the `Phase seconds:` lines a diagnostic timer build prints and write them as a CSV.

Usage: phases_csv.py <tag> <log> [<tag> <log> ...]
"""
import csv, os, re, sys

S = "/data/scrollagent/runs/rev1/c-stage-cost"
OUT = os.path.join(S, "evidence", "phases.csv")
PAT = re.compile(r"^Phase seconds: length=(\d+) setup=([0-9.]+) odometer=([0-9.]+) "
                 r"sequences=([0-9.]+) cover=([0-9.]+)")


def main():
    new = not os.path.exists(OUT)
    with open(OUT, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            fh.write("# the three phases of FindBadPatchesGeneral, timed inside the stage itself "
                     "by a diagnostic build (tools/apply_timers.py, omp_get_wtime), one row per "
                     "chain length. setup is PrecomputeNormals and the indexing of the patches; "
                     "odometer is the while loop that enumerates the chains; sequences is the "
                     "parallel placement pass and the serial pass that prints and scores them; "
                     "cover is the greedy loop that condemns one patch per pass. The timer build "
                     "is an instrument and is not in the delivered series.\n")
            w.writerow(["tag", "attempt", "length", "setup_seconds", "odometer_seconds",
                        "sequences_seconds", "cover_seconds", "log"])
        args = sys.argv[1:]
        for i in range(0, len(args), 2):
            tag, log = args[i], args[i + 1]
            m = re.search(r"(PHerc1447-seed\d+)", log)
            if not m:
                raise SystemExit("the log name does not say which seed it is: " + log)
            attempt = m.group(1)
            with open(log, errors="replace") as f:
                for line in f:
                    m = PAT.match(line)
                    if m:
                        w.writerow([tag, attempt, m.group(1), m.group(2), m.group(3),
                                    m.group(4), m.group(5), log])
                        print(line.rstrip())
    print("written to %s" % OUT)


if __name__ == "__main__":
    sys.exit(main())
