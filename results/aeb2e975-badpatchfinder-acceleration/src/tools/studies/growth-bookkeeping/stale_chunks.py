#!/usr/bin/env python3
"""The chunk files of seed34's surface.bp that predate the growth that wrote its rel.csv.

Equivalent command line: find growth/surface.bp -type f ! -newermt "2026-09-21 01:10:05" -printf
'%T@ %p\n'. The threshold is the start of the growth, computed in tools/tree_freshness.py as the
mtime of growth/rel.csv minus growth_wall_clock_seconds of seed-search-1447's own
evidence/runs/PHerc1447-seed34.csv. Read only: nothing under seed-search-1447 is written.
"""
import csv, os, subprocess

G = "/data/scrollagent/runs/rev1/seed-search-1447/out/PHerc1447-seed34/growth"
START = 1789938611.876   # 2026-09-21T01:10:11.876Z, from tools/tree_freshness.py
OUT = "/data/scrollagent/runs/rev1/growth-bookkeeping/evidence/stale-chunks-seed34.csv"


def iso(t):
    return subprocess.check_output(["date", "-u", "-d", "@%.3f" % t, "+%FT%T.%3NZ"]).decode().strip()


def main():
    stale, fresh = [], 0
    for root, dirs, files in os.walk(os.path.join(G, "surface.bp")):
        for f in files:
            p = os.path.join(root, f)
            m = os.path.getmtime(p)
            if m < START - 1:
                stale.append((m, os.path.relpath(p, G), os.path.getsize(p)))
            else:
                fresh += 1
    stale.sort()
    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["# every file under growth/surface.bp whose mtime is before the start of the "
                    "growth that wrote growth/rel.csv, one per row, oldest first. They were "
                    "written by an earlier run into the same folder and the growth of "
                    "2026-09-21T01:10:11Z opened them as its starting surface. "
                    "chunk: path relative to the growth tree. mtime: UTC. bytes: file size. "
                    "The last row is a summary line with chunk = TOTAL."])
        w.writerow(["chunk", "mtime", "bytes"])
        for m, p, b in stale:
            w.writerow([p, iso(m), b])
        w.writerow(["TOTAL", "%d stale of %d files under surface.bp, from %s to %s"
                    % (len(stale), len(stale) + fresh, iso(stale[0][0]), iso(stale[-1][0])),
                    sum(b for _, _, b in stale)])
    print(open(OUT).read().splitlines()[-1])
    print("stale", len(stale), "fresh", fresh)


if __name__ == "__main__":
    main()
