# This file is a copy of tools/upstream_check.py of the working tree and differs from it in one
# way only: the absolute paths of the machine the measurements ran on are replaced by paths
# inside this folder, with VILLA_UPSTREAM for the clone of ScrollPrize/villa it reads. Nothing
# else is changed.
#!/usr/bin/env python3
"""Is the defect still in the published code? Asked of the repository, not of memory.

A referee reading a paper about a defect will ask whether it has since been repaired. This tool
asks the question of the clone: it takes the file the defect lives in, the tip of upstream's
default branch, and reports whether any commit between our pinned commit and that tip touches the
file at all. It writes what it found to a CSV, so the paper can say it with a macro instead of a
sentence somebody has to keep up to date.

It reads the clone and never changes it: no fetch, no checkout, no merge. Fetch yourself first if
you want a fresher answer, when no fit is using a tree copied from that clone, and point --clone
and --tip at the clone that has the fresher ref.

Two guards, because a count of zero has two causes and only one of them is interesting: the tool
stops if a path it was asked about does not exist at the tip (2026-09-17: the paths here were
missing the volume-cartographer/ prefix, so every count was zero for the wrong reason), and it
reads the file at the tip to say whether the divided return is still there and on which line.

Usage: upstream_check.py [--clone DIR] [--tip REF] [--out evidence/upstream-check.csv]
"""
import argparse
import csv
import os
import subprocess

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLONE = os.environ.get("VILLA_UPSTREAM") or os.path.join(SRC, "villa")
PIN = "23adee047dea06526151d3a152a7d85de8da478b"
TIP = "origin/main"
FILES = ["volume-cartographer/core/src/normalgridtools.cpp",
         "volume-cartographer/core/include/vc/core/util/normalgridtools.hpp"]
SOURCE = FILES[0]
DEFECT = "return score/wsum"
OUT = os.path.join(SRC, "evidence", "upstream-check.csv")


def git(clone, *a):
    return subprocess.check_output(["git", "-C", clone, *a], text=True).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clone", default=CLONE)
    ap.add_argument("--tip", default=TIP)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    clone, tip = a.clone, git(a.clone, "rev-parse", a.tip)
    ahead = git(clone, "rev-list", "--count", f"{PIN}..{tip}")
    when = git(clone, "log", "-1", "--format=%cI", tip)

    # Is the divided return still there, and on which line? A commit count says what nobody
    # touched; this says what the file holds.
    src = git(clone, "show", f"{tip}:{SOURCE}").split("\n")
    hits = [i + 1 for i, line in enumerate(src) if DEFECT in line]
    if len(hits) != 1:
        raise SystemExit(f"upstream_check: {DEFECT!r} found {len(hits)} times in {SOURCE} at "
                         f"{tip[:9]}, expected once: read the file before quoting a line number")
    defect_line = hits[0]

    rows = []
    for f in FILES:
        for ref in (PIN, tip):
            if subprocess.call(["git", "-C", clone, "cat-file", "-e", f"{ref}:{f}"]) != 0:
                raise SystemExit(f"upstream_check: {f} does not exist at {ref[:9]}: a count of "
                                 f"commits touching a path that is not there is always zero")
        touching = git(clone, "log", "--format=%h", f"{PIN}..{tip}", "--", f)
        n = len([x for x in touching.splitlines() if x])
        rows.append(dict(file=f, pinned=PIN[:9], tip=tip[:9], commits_ahead=ahead,
                         tip_date=when[:10], commits_touching_file=n,
                         still_as_pinned="yes" if n == 0 else "no",
                         defect_line_at_tip=defect_line if f == SOURCE else ""))
        print(f"  {f}: {n} commits touch it between {PIN[:9]} and {tip[:9]} "
              f"({ahead} ahead, tip of {when[:10]})")
    print(f"  {DEFECT!r} is at line {defect_line} of {SOURCE} at {tip[:9]}")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(), w.writerows(rows)
    print(f"written {a.out} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
