#!/usr/bin/env python3
"""Compare, file by file, the delivered sheets of seeds 01, 15 and 26 written here against the
sheets that were on disk before anything was built.

The baseline is evidence/baseline-sheets.sha256, taken before the first compile of this study. One
row per sheet per series, so that a single byte of difference has a name.
"""
import csv, hashlib, os, sys

H = "/data/scrollagent/runs/rev1/orphan-guard"
SEEDS = ["PHerc1447-seed01", "PHerc1447-seed15", "PHerc1447-seed26"]
SERIES = ["plain", "guard"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def baseline():
    out = {}
    with open(os.path.join(H, "evidence", "baseline-sheets.sha256")) as f:
        for line in f:
            sha, path = line.split()
            parts = path.split("/")
            out[(parts[-3], parts[-1])] = sha
    return out


def main():
    base = baseline()
    rows = 0
    identical = 0
    with open(os.path.join(H, "evidence", "sheets-identity.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["attempt", "series", "sheet", "baseline_sha256", "run_sha256",
                    "byte_identical", "baseline_file", "run_file"])
        for series in SERIES:
            for a in SEEDS:
                o = os.path.join(H, "scratch", "out", series, a, "C40")
                names = sorted((k[1] for k in base if k[0] == a),
                               key=lambda n: int(n.split("_")[1].split(".")[0]))
                for n in names:
                    bfile = ("/data/scrollagent/runs/rev1/seed-search-1447/out/%s/C40/%s" % (a, n))
                    rfile = os.path.join(o, n)
                    if os.path.exists(rfile):
                        s = sha256(rfile)
                    else:
                        s = "the run wrote no such file"
                    same = "yes" if s == base[(a, n)] else "no"
                    identical += same == "yes"
                    rows += 1
                    w.writerow([a, series, n, base[(a, n)], s, same, bfile, rfile])
    print("sheets compared: %d, byte identical: %d" % (rows, identical))


if __name__ == "__main__":
    sys.exit(main())
