#!/usr/bin/env python3
"""For each seed of seed-search-1447: was the growth's output tree empty when the growth started?

The growth opens surface.bp and boundary.bp where it finds them (simpaper10.cpp:325 and 326 of
the built corrected copy) and creates neither: the runner only does mkdir -p. A chunk file under
surface.bp whose mtime is older than the start of the growth was therefore written by an earlier
run into the same directory, and its points still carry that earlier run's patch ids.

The start of the growth is taken as the mtime of the tree's rel.csv, which the growth writes last,
minus growth_wall_clock_seconds from the study's own evidence/runs/<attempt>.csv. Read only.
"""
import csv, os, subprocess, sys

S = "/data/scrollagent/runs/rev1/seed-search-1447"
OUT = "/data/scrollagent/runs/rev1/growth-bookkeeping/evidence/tree-freshness.csv"


def wall(attempt):
    p = os.path.join(S, "evidence", "runs", attempt + ".csv")
    if not os.path.exists(p):
        return None
    for r in csv.DictReader(open(p)):
        if r["quantity"] == "growth_wall_clock_seconds":
            try:
                return float(r["value"])
            except ValueError:
                return None
    return None


def main():
    rows = []
    for attempt in sorted(os.listdir(os.path.join(S, "out"))):
        g = os.path.join(S, "out", attempt, "growth")
        bp = os.path.join(g, "surface.bp")
        rel = os.path.join(g, "rel.csv")
        w = wall(attempt)
        if not os.path.isdir(bp):
            rows.append([attempt, "no surface.bp", "", "", "", "", ""])
            continue
        chunks = []
        for root, dirs, files in os.walk(bp):
            for f in files:
                chunks.append(os.path.getmtime(os.path.join(root, f)))
        if not chunks:
            rows.append([attempt, 0, "", "", "", "", ""])
            continue
        relm = os.path.getmtime(rel) if os.path.exists(rel) else ""
        if relm and w:
            start = relm - w
            older = sum(1 for c in chunks if c < start - 1)
        else:
            start, older = "", "not measurable"
        iso = lambda t: subprocess.check_output(
            ["date", "-u", "-d", "@%.3f" % t, "+%FT%T.%3NZ"]).decode().strip()
        rows.append([attempt, len(chunks), iso(min(chunks)), iso(max(chunks)),
                     iso(start) if start else "not measurable",
                     "%.0f" % w if w else "not measurable", older])
    with open(OUT, "w", newline="") as fh:
        wtr = csv.writer(fh)
        wtr.writerow(["# one row per seed of seed-search-1447. chunk_files: files under "
                      "growth/surface.bp. oldest_chunk_mtime and newest_chunk_mtime: their mtimes "
                      "in UTC. growth_started: mtime of growth/rel.csv minus "
                      "growth_wall_clock_seconds of the study's evidence/runs/<attempt>.csv, "
                      "which is when the growth that wrote the tree began. "
                      "chunks_older_than_the_growth_start: chunk files written before it, with a "
                      "second of slack, which are the points an earlier run into the same "
                      "directory left behind."])
        wtr.writerow(["attempt", "chunk_files", "oldest_chunk_mtime", "newest_chunk_mtime",
                      "growth_started", "growth_wall_clock_seconds",
                      "chunks_older_than_the_growth_start"])
        for r in rows:
            wtr.writerow(r)
    for r in rows:
        print(r)


if __name__ == "__main__":
    sys.exit(main())
