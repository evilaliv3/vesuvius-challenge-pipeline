#!/usr/bin/env python3
"""The whole standard output of the `c` stage of one arm against another, line for line.

Adapted from runs/rev1/c-stage-cost/tools/stdout_identity.py. What was adapted: that tool compared
an arm with a reference log written by an earlier run on disk; this one compares two arms of this
study, both run here, on the identity runs of phase 1. The reason for the check is unchanged and
is why it is worth the lines: the `c` stage prints every chain it keeps, in the order it keeps it,
then the score of each, then the patches it condemns in the order it condemns them. Two runs whose
whole standard output agrees line for line took the same decisions in the same order, and not only
ended in the same files.

The orphan guard, `corrections/00007`, prints two kinds of line of its own that the unguarded arm
cannot print. When one side has the guard and the other does not, those lines and nothing else are
removed before the comparison, and how many were removed is in the row.

Usage: stdout_identity.py <arm_a> <arm_b>
Appends to evidence/stdout-identity.csv.
"""
import csv, hashlib, os, subprocess, sys

S = "/data/scrollagent/runs/rev1/c-stage-on-0139"
OUT = os.path.join(S, "evidence", "stdout-identity.csv")
GUARD = (b"Chains refused for a patch with no geometry", b"Patches with no geometry")
HAS_GUARD = {"plain": False, "guarded": True, "c2": True}


def read(path, strip_guard):
    kept, removed, total = [], 0, 0
    with open(path, "rb") as f:
        for line in f:
            total += 1
            if strip_guard and line.startswith(GUARD):
                removed += 1
            else:
                kept.append(line)
    return b"".join(kept), total, removed


def main():
    a, b = sys.argv[1], sys.argv[2]
    strip = HAS_GUARD[a] != HAS_GUARD[b]
    when = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    with open(os.path.join(S, "evidence", "trees.csv")) as f:
        trees = [r["tree"] for r in csv.DictReader(l for l in f if not l.startswith("#"))
                 if r["exists"] == "yes"]
    new = not os.path.exists(OUT)
    diff = 0
    with open(OUT, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            fh.write("# the whole standard output of the c stage of two arms, line for line, on "
                     "the identity runs of phase 1. lines_a and lines_b are what each arm "
                     "printed; guard_lines_removed is how many lines of the two kinds the orphan "
                     "guard prints were removed from the guarded side when the other side has no "
                     "guard, and nothing else is ever removed. identical is yes only when the two "
                     "byte streams are equal.\n")
            w.writerow(["arm_a", "arm_b", "tree", "lines_a", "lines_b", "guard_lines_removed",
                        "sha256_a", "sha256_b", "identical", "log_a", "log_b", "compared_utc"])
        for t in trees:
            pa = os.path.join(S, "log", "chain-id-%s-%s-r1-c.txt" % (a, t))
            pb = os.path.join(S, "log", "chain-id-%s-%s-r1-c.txt" % (b, t))
            if not (os.path.exists(pa) and os.path.exists(pb)):
                continue
            ba, na, ra = read(pa, strip and HAS_GUARD[a])
            bb, nb, rb = read(pb, strip and HAS_GUARD[b])
            same = ba == bb
            diff += not same
            w.writerow([a, b, t, na, nb, ra + rb, hashlib.sha256(ba).hexdigest(),
                        hashlib.sha256(bb).hexdigest(), "yes" if same else "no", pa, pb, when])
            print("%s vs %s on %s: %s" % (a, b, t, "identical" if same else "DIFFERENT"))
    return 1 if diff else 0


if __name__ == "__main__":
    sys.exit(main())
