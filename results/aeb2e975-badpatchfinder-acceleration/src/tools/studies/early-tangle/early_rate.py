#!/usr/bin/env python3
"""early-tangle, the second declared quantity: the share of the log's first N lines that announce
a patch and its match count.

A watcher can read this on a running growth with no clock and no instrumentation: count the lines,
count the ones matching `Patch <n> has <m> matches`, divide. The ladder of N and the bar are in
DECLARATION.md's dated addition of 2026-09-21T15:18:57Z, written before this ran.
"""
import csv
import os

S = "/data/scrollagent/runs/rev1/early-tangle"
SEARCH = "/data/scrollagent/runs/rev1/seed-search-1447"
LADDER = [10000, 50000, 100000, 500000]
NM = "not measurable"
RIBBON_MAX_FAN_OUT = 10.0


def population():
    out = {}
    lines = open(os.path.join(SEARCH, "evidence", "alignment-fanout.csv")).read().splitlines(True)
    if lines[0].lstrip().startswith('"#'):
        lines = lines[1:]
    for r in csv.DictReader(lines):
        if r["fan_out"] == NM:
            continue
        f = float(r["fan_out"])
        out[r["attempt"]] = (f, "ribbon" if f < RIBBON_MAX_FAN_OUT else "tangle")
    return out


def scan(path):
    """Announcements among the first N lines, for each N, and the log's total lines."""
    hits = {n: 0 for n in LADDER}
    total = 0
    biggest = max(LADDER)
    with open(path, errors="replace") as f:
        for line in f:
            total += 1
            if line.startswith("Patch ") and line.rstrip().endswith(" matches"):
                for n in LADDER:
                    if total <= n:
                        hits[n] += 1
            elif total > biggest:
                pass
    return hits, total


def main():
    pop = population()
    rows = []
    for a, (fan, label) in sorted(pop.items(), key=lambda kv: kv[1][0]):
        path = os.path.join(SEARCH, "log", "growth-%s.txt" % a)
        if not os.path.exists(path):
            continue
        hits, total = scan(path)
        for n in LADDER:
            ok = total >= n
            rows.append(dict(attempt=a, fan_out="%.2f" % fan, kind=label, log_lines=total, n=n,
                             announcements_in_first_n=hits[n] if ok else NM,
                             share_of_first_n=("%.6f" % (hits[n] / n)) if ok else NM,
                             n_over_log_lines="%.6f" % (n / total)))
    note = (
        "# one row per seed and per N of the ladder 10000 50000 100000 500000, declared in the "
        "dated addition of DECLARATION.md before this ran. share_of_first_n is how many of the "
        "first N lines of that growth's own standard output, "
        "seed-search-1447/log/growth-<attempt>.txt, have the shape `Patch <n> has <m> matches`. "
        "It is what a watcher of a running growth can read with no clock and no instrumentation. "
        "n_over_log_lines is N over the whole log, the declaration's earliness test, and a value "
        "above 0.10 fails it. fan_out and kind come from "
        "seed-search-1447/evidence/alignment-fanout.csv and are not decided here. A log shorter "
        "than N is not measurable at that N, never a pass.")
    out = os.path.join(S, "evidence", "early-rate.csv")
    with open(out, "w", newline="") as f:
        f.write('"%s"\n' % note)
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("wrote %s, %d rows" % (out, len(rows)))


if __name__ == "__main__":
    main()
