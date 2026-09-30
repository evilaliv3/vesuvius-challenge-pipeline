#!/usr/bin/env python3
"""What separates the noA8 arm from the plain arm, counted from the two built source trees.

Not from the patch files: from the trees build.sh actually compiled, so that a patch that applied
with fuzz or a rebase that drifted would show up here as a difference nobody declared. One row per
source file that differs, with the number of lines added and removed in each direction, and the
verdict column saying whether that file's difference is A8's content, a diagnostic of A8's that
carries no work, or something unexpected.

Usage: arm_diff.py   ... writes evidence/arm-construction.csv
"""
import csv, os, subprocess

Q = "/data/scrollagent/runs/rev1/quiet-bench"
A = os.path.join(Q, "scratch/src/build/plain-repro")
B = os.path.join(Q, "scratch/src/build/noA8")
OUT = os.path.join(Q, "evidence", "arm-construction.csv")
SKIP = (".o", ".orig", ".rej")
NOTE = ('"# what separates the noA8 arm from the plain arm, read from the two SOURCE TREES build.sh '
        'compiled and not from the patch files. lines_only_in_plain and lines_only_in_noA8 are the '
        'counts of - and + lines of `diff -u` between the two files. The plain tree is the series '
        'build + performance + corrections-inert + corrections/00001..00006, which rebuilds the '
        'binary c-stage-cost/scratch/bin/plain/simpaper10 byte for byte (see '
        'evidence/binaries.csv, label plain-repro). The noA8 tree is that series with '
        'performance/00002 taken out, three of its patches rebased because their context came '
        'from 00002, and 00002\'s two outPath conversions carried back in: '
        'tools/rebase_00001_for_noA8.sh says why, one dated block per case."')
HEAD = ["file", "lines_only_in_plain", "lines_only_in_noA8", "what_the_difference_is"]
WHAT = {
    "badpatchfinder.cpp": "A8 itself: the per thread RenderState, the parallel loops over pairs "
                          "and over chains, PrecomputeNormals and the normals cache, and Clear "
                          "touching only the cells that were dirtied",
    "badpatchfinder.h":   "A8 itself: the RenderState struct, the normals cache member, the "
                          "pairStats instrumentation, and the #undef of COLLECT_DISTANCE_DISTRIB "
                          "that stops the 2000 by 2000 distance array being cleared per pair",
    "simpaper10.cpp":     "A8's off grid diagnostic only, three lines: a counter zeroed before the "
                          "stage and printed after it. A8's two outPath conversions in this file "
                          "are carried into the noA8 arm on purpose and are therefore not here",
}


def main():
    rows = []
    for name in sorted(set(os.listdir(A)) | set(os.listdir(B))):
        if name.endswith(SKIP) or name in ("simpaper10", "bin2tifxyz", "parameters.json"):
            continue
        a, b = os.path.join(A, name), os.path.join(B, name)
        if not (os.path.isfile(a) and os.path.isfile(b)):
            rows.append([name, "not measurable", "not measurable",
                         "present in one tree only, which was not expected"])
            continue
        p = subprocess.run(["diff", "-u", a, b], capture_output=True)
        if p.returncode == 0:
            continue
        body = p.stdout.split(b"\n")[2:]
        minus = sum(1 for l in body if l.startswith(b"-"))
        plus = sum(1 for l in body if l.startswith(b"+"))
        rows.append([name, minus, plus, WHAT.get(name, "NOT DECLARED, look at it")])
    with open(OUT, "w", newline="") as f:
        f.write(NOTE + "\n")
        w = csv.writer(f)
        w.writerow(HEAD)
        for r in rows:
            w.writerow(r)
    print("wrote %s, %d files differ" % (OUT, len(rows)))
    for r in rows:
        print("  %-24s -%s +%s" % (r[0], r[1], r[2]))


if __name__ == "__main__":
    main()
