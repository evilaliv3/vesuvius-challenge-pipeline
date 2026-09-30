#!/usr/bin/env python3
"""Check that no run of this study has written into a tree in place.

Every working copy is a hard link copy of scratch/pristine/<tree>, so a stage that opened an
existing patch file or rel.csv for writing would have changed the pristine copy through the link.
This tool recomputes the pristine copy's content fingerprint, by the recipe of
tools/tree_inventory.py, and compares it with the value that tool read from the original tree
before anything in this study ran.

Writes evidence/pristine-check.csv, one row per pristine copy, and exits non zero if any row
fails, because a failure means a run was destructive and everything after it is suspect.
"""
import csv, hashlib, os, subprocess, sys

S = "/data/scrollagent/runs/rev1/c-stage-on-0139"
PRISTINE = os.path.join(S, "scratch", "pristine")
TREES = os.path.join(S, "evidence", "trees.csv")
OUT = os.path.join(S, "evidence", "pristine-check.csv")


def file_sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def content(path):
    pdir, rel = os.path.join(path, "patches"), os.path.join(path, "rel.csv")
    lines = []
    for n in sorted(os.listdir(pdir)):
        p = os.path.join(pdir, n)
        lines.append("%s %d %s" % (n, os.path.getsize(p), file_sha(p)))
    lines.append("rel.csv %d %s" % (os.path.getsize(rel), file_sha(rel)))
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def main():
    when = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    with open(TREES) as f:
        want = {r["tree"]: r["content_sha256"]
                for r in csv.DictReader(l for l in f if not l.startswith("#"))
                if r["exists"] == "yes"}
    bad = 0
    with open(OUT, "w", newline="") as f:
        f.write("# one row per pristine copy under scratch/pristine. expected_sha256 is the "
                "content fingerprint tools/tree_inventory.py took from the ORIGINAL tree before "
                "this study ran anything; measured_sha256 is the same recipe applied now to the "
                "pristine copy, whose patch files are the inodes every working copy hard links "
                "to. unchanged reads no if any stage wrote into a tree in place.\n")
        w = csv.writer(f)
        w.writerow(["tree", "expected_sha256", "measured_sha256", "unchanged", "checked_utc"])
        for tid, exp in sorted(want.items()):
            d = os.path.join(PRISTINE, tid)
            if not os.path.isdir(d):
                w.writerow([tid, exp, "no pristine copy on disk", "not measurable", when])
                continue
            got = content(d)
            ok = "yes" if got == exp else "no"
            bad += ok == "no"
            w.writerow([tid, exp, got, ok, when])
            print(tid, ok)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
