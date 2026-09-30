#!/usr/bin/env python3
"""early-tangle: the running mean of the announced match count over the first K patches.

The growth prints one line per patch of the shape `Patch <n> has <m> matches`. This reads the
first K of them for each K of the declared ladder and writes the mean of m, together with where
the K-th such line sits among all of them, which DECLARATION.md fixes as the proxy for how early
in the growth it arrives. Nothing else of the log is read.

The population and the labels are the declaration's and are not decided here: they are read from
seed-search-1447/evidence/alignment-fanout.csv, column fan_out, and a seed with no fan_out is not
in the population.
"""
import csv
import os
import re

S = "/data/scrollagent/runs/rev1/early-tangle"
SEARCH = "/data/scrollagent/runs/rev1/seed-search-1447"
LADDER = [50, 100, 200, 500, 1000, 2000]
NM = "not measurable"
LINE = re.compile(r"^Patch (\d+) has (\d+) matches\s*$")
# The ribbon/tangle boundary of the declaration: the two groups of alignment-fanout.csv have
# nothing between 4.64 and 27.40, so any cut in that gap gives the same labels. 10 is in it.
RIBBON_MAX_FAN_OUT = 10.0


def population():
    """The seeds with a measured fan out, and their label, from the search's own CSV."""
    out = {}
    path = os.path.join(SEARCH, "evidence", "alignment-fanout.csv")
    lines = open(path).read().splitlines(True)
    if lines[0].lstrip().startswith('"#'):
        lines = lines[1:]
    for r in csv.DictReader(lines):
        if r["fan_out"] == NM:
            continue
        f = float(r["fan_out"])
        out[r["attempt"]] = (f, "ribbon" if f < RIBBON_MAX_FAN_OUT else "tangle")
    return out


def read_log(path):
    """Every m of `Patch <n> has <m> matches`, in the order the growth printed them."""
    ms = []
    with open(path, errors="replace") as f:
        for line in f:
            if line.startswith("Patch "):
                m = LINE.match(line)
                if m:
                    ms.append(int(m.group(2)))
    return ms


def main():
    pop = population()
    rows = []
    for a, (fan, label) in sorted(pop.items(), key=lambda kv: kv[1][0]):
        path = os.path.join(SEARCH, "log", "growth-%s.txt" % a)
        if not os.path.exists(path):
            rows.append(dict(attempt=a, fan_out="%.2f" % fan, kind=label, announced=NM,
                             k=NM, mean_matches_first_k=NM, share_of_announcements=NM))
            continue
        ms = read_log(path)
        for k in LADDER:
            if len(ms) < k:
                rows.append(dict(attempt=a, fan_out="%.2f" % fan, kind=label,
                                 announced=len(ms), k=k, mean_matches_first_k=NM,
                                 share_of_announcements=NM))
                continue
            rows.append(dict(attempt=a, fan_out="%.2f" % fan, kind=label, announced=len(ms), k=k,
                             mean_matches_first_k="%.4f" % (sum(ms[:k]) / k),
                             share_of_announcements="%.6f" % (k / len(ms))))
    note = (
        "# one row per seed and per K of the declared ladder 50 100 200 500 1000 2000. "
        "mean_matches_first_k is the mean of m over the first K lines of the shape "
        "`Patch <n> has <m> matches` in that growth's own standard output, "
        "seed-search-1447/log/growth-<attempt>.txt, and nothing else of the log is read. "
        "announced is how many such lines the whole growth printed. share_of_announcements is "
        "K over announced, which DECLARATION.md fixes as the proxy for how early the K-th line "
        "arrives and states its assumption, that patches are announced at a roughly even rate. "
        "fan_out and kind are copied from seed-search-1447/evidence/alignment-fanout.csv and are "
        "not decided here; the cut at 10 falls in the empty gap between 4.64 and 27.40, so any "
        "cut in that gap gives the same labels. A seed with fewer than K announcements is not "
        "measurable at that K, never a pass.")
    out = os.path.join(S, "evidence", "early-mean.csv")
    with open(out, "w", newline="") as f:
        f.write('"%s"\n' % note)
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("wrote %s, %d rows" % (out, len(rows)))


if __name__ == "__main__":
    main()
