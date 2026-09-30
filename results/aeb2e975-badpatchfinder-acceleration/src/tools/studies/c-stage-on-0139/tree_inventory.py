#!/usr/bin/env python3
"""The PHerc0139 growth trees this study may run: what is on disk, and its fingerprint.

Writes evidence/trees.csv, one row per tree named in DECLARATION.md, whether or not it exists.
Nothing is written into any tree: this tool only reads.

The fan out is the standing column of coordinator.md's addition of 2026-09-21T16:19:00Z: twice
the edges over the keys of rel.csv. Edges are the lines of rel.csv; keys are the distinct patch
numbers that appear in its first two columns, which is what the alignment map is keyed by.

`content_sha256` is a fingerprint of the tree's content, not of its path: the sha256 of the
sorted listing of `name size sha256` over every file under patches/ together with rel.csv. Two
trees with the same value hold the same patches and the same relations byte for byte.
"""
import csv, hashlib, os, subprocess, sys

S = "/data/scrollagent/runs/rev1/c-stage-on-0139"
R = "/data/scrollagent/runs/rev1"
TREES = [
    ("repeat", os.path.join(R, "growth-repeat", "out", "growth")),
    ("b40", os.path.join(R, "reference-b40", "out", "growth")),
    ("D150", os.path.join(R, "seed-distance-ladder", "out", "growth-D150")),
    ("D450", os.path.join(R, "seed-distance-ladder", "out", "growth-D450")),
    ("P2", os.path.join(R, "why-the-growth-stops", "out", "growth-P2")),
    ("C", os.path.join(R, "why-the-growth-stops", "out", "growth-C")),
    ("S", os.path.join(R, "why-the-growth-stops", "out", "growth-S")),
    ("A", os.path.join(R, "held-patch", "out", "growth-A")),
    ("ceiling24000", os.path.join(R, "ceiling-24000", "out", "growth")),
]
HEADER = [
    "tree",                 # the id this study gives it
    "path",                 # where it is on disk, read only
    "exists",               # yes when the folder and its patches/ and rel.csv are all there
    "patch_files",          # ls of patches/, counted
    "rel_edges",            # lines of rel.csv
    "rel_keys",             # distinct patch numbers in columns 1 and 2 of rel.csv
    "fan_out",              # 2 * rel_edges / rel_keys, the standing column
    "bytes_on_disk",        # du -sb of the tree
    "content_sha256",       # see the module docstring
    "note",                 # why a tree is not runnable, when it is not
]


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def file_sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    out = os.path.join(S, "evidence", "trees.csv")
    with open(out, "w", newline="") as f:
        f.write("# one row per PHerc0139 growth tree named in DECLARATION.md, read only. "
                "rel_edges is the line count of rel.csv, rel_keys the distinct patch numbers in "
                "its first two columns, fan_out twice the first over the second. content_sha256 "
                "is the sha256 of the sorted 'name size sha256' listing of every file under "
                "patches/ plus rel.csv, so two trees with equal values hold the same content.\n")
        w = csv.writer(f)
        w.writerow(HEADER)
        for tid, path in TREES:
            pdir, rel = os.path.join(path, "patches"), os.path.join(path, "rel.csv")
            if not os.path.isdir(path):
                w.writerow([tid, path, "no", "", "", "", "", "", "", "the folder is not on disk"])
                print(tid, "absent")
                continue
            if not os.path.isdir(pdir) or not os.listdir(pdir):
                w.writerow([tid, path, "no", 0, "", "", "", "", "",
                            "patches/ is absent or empty: a check on an input reads its content"])
                print(tid, "no patches")
                continue
            if not os.path.isfile(rel) or os.path.getsize(rel) == 0:
                w.writerow([tid, path, "no", len(os.listdir(pdir)), "", "", "", "", "",
                            "rel.csv is absent or empty"])
                print(tid, "no rel.csv")
                continue
            names = sorted(os.listdir(pdir))
            edges, keys = 0, set()
            with open(rel) as fh:
                for r in csv.reader(fh):
                    if not r:
                        continue
                    edges += 1
                    keys.add(r[0].strip())
                    keys.add(r[1].strip())
            lines = []
            for n in names:
                p = os.path.join(pdir, n)
                lines.append("%s %d %s" % (n, os.path.getsize(p), file_sha(p)))
            lines.append("rel.csv %d %s" % (os.path.getsize(rel), file_sha(rel)))
            content = sha256_bytes("\n".join(lines).encode())
            nbytes = int(subprocess.check_output(["du", "-sb", path]).split()[0])
            w.writerow([tid, path, "yes", len(names), edges, len(keys),
                        "%.4f" % (2.0 * edges / len(keys)), nbytes, content, ""])
            print(tid, len(names), edges, len(keys), content[:16])


if __name__ == "__main__":
    sys.exit(main())
