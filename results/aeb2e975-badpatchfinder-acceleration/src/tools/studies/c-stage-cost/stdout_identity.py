#!/usr/bin/env python3
"""The standard output of the c stage of an arm against the standard output of the run that wrote
the sheets on disk.

This is a wider check than the output files. The c stage prints every chain it keeps, in the order
it keeps it, then the score of each, then the patches it condemns in the order it condemns them.
Two runs whose whole standard output agrees line for line took the same decisions in the same
order, not only ones that ended in the same files.

The orphan guard of PLAN 47 step one prints two lines of its own per chain length, which the
reference run could not print because it predates the guard. Those two kinds of line, and nothing
else, are removed from the arm's output before the comparison, and the count of removed lines is
in the row.

Usage: stdout_identity.py <tag> [<tag> ...]
"""
import csv, hashlib, os, subprocess, sys

S = "/data/scrollagent/runs/rev1/c-stage-cost"
REFLOG = "/data/scrollagent/runs/rev1/seed-search-1447/log/chain-%s-C40-c.txt"
OUT = os.path.join(S, "evidence", "stdout-identity.csv")
GUARD = ("Chains refused for a patch with no geometry",
         "Patches with no geometry")


def main():
    when = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    new = not os.path.exists(OUT)
    with open(OUT, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            fh.write("# the whole standard output of the c stage, line for line, against the run "
                     "that wrote the sheets on disk. arm_lines_total is what the arm printed, "
                     "guard_lines_removed is how many of them are the two lines per chain length "
                     "that the orphan guard prints and the reference run could not, and "
                     "arm_lines_compared is the rest. identical is yes only when the two byte "
                     "streams are equal. sha256 columns are of the two streams compared.\n")
            w.writerow(["tag", "attempt", "reference_lines", "arm_lines_total",
                        "guard_lines_removed", "arm_lines_compared", "reference_sha256",
                        "arm_sha256", "identical", "reference_log", "arm_log", "compared_utc"])
        for tag in sys.argv[1:]:
            for s in ["seed01", "seed15", "seed26", "seed38", "seed40", "seed48"]:
                a = "PHerc1447-" + s
                ref = REFLOG % a
                arm = os.path.join(S, "log", "chain-%s-%s-c.txt" % (tag, a))
                if not (os.path.exists(ref) and os.path.exists(arm)):
                    continue
                rb = open(ref, "rb").read()
                kept, removed, total = [], 0, 0
                for line in open(arm, "rb"):
                    total += 1
                    if line.startswith(tuple(g.encode() for g in GUARD)):
                        removed += 1
                    else:
                        kept.append(line)
                ab = b"".join(kept)
                w.writerow([tag, a, rb.count(b"\n"), total, removed, len(kept),
                            hashlib.sha256(rb).hexdigest(), hashlib.sha256(ab).hexdigest(),
                            "yes" if rb == ab else "no", ref, arm, when])
                print("%s %s: %s" % (tag, a, "identical" if rb == ab else "DIFFERENT"))
    print("written to %s" % OUT)


if __name__ == "__main__":
    sys.exit(main())
