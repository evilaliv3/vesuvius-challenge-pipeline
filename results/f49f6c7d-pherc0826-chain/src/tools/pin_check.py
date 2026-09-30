#!/usr/bin/env python3
"""pin_check.py PINS.csv: every file a pins table names (paths relative to src/) has the sha256 written beside it.

A figure that is drawn outside the build (Figure C25, from the raw scan, approved before it entered the article) is shipped
with its tool, its plotted table and its PNG pinned; the build runs this instead of redrawing it, and stops on any
difference. Standard library only.
"""
import csv, hashlib, os, sys

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    pins = sys.argv[1]
    with open(pins, newline="") as fh:
        rows = list(csv.DictReader(l for l in fh if not l.startswith("#")))
    bad = []
    for r in rows:
        p = os.path.join(SRC, r["file"])
        h = hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else "missing"
        if h != r["sha256"]:
            bad.append("%s is %s, pinned %s" % (r["file"], h, r["sha256"]))
    for b in bad:
        print("  !! " + b)
    print("pin_check.py: %s, %d file(s), %d differ" % (os.path.basename(pins), len(rows), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
