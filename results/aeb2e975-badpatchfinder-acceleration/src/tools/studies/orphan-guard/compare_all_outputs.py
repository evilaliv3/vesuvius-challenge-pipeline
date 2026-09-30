#!/usr/bin/env python3
"""Every file the downstream wrote at the top of C40, not the ten sheets alone, compared against
the tree seed-search-1447 has on disk.

The declared bar is the delivered sheets. This is the wider look, because a guard that fired where
it should not could move a CSV of the c stage and leave the sheets alone.
"""
import csv, hashlib, os, sys

H = "/data/scrollagent/runs/rev1/orphan-guard"
S = "/data/scrollagent/runs/rev1/seed-search-1447"
SEEDS = ["PHerc1447-seed01", "PHerc1447-seed15", "PHerc1447-seed26"]
SERIES = ["plain", "guard"]
SKIP = {"missing-C40.txt"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def top_files(d):
    return sorted(n for n in os.listdir(d)
                  if os.path.isfile(os.path.join(d, n)) and n not in SKIP)


def main():
    out = os.path.join(H, "evidence", "all-outputs-identity.csv")
    n = same = 0
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["attempt", "series", "file", "reference_sha256", "run_sha256",
                    "byte_identical", "reference_file", "run_file"])
        for series in SERIES:
            for a in SEEDS:
                ref = os.path.join(S, "out", a, "C40")
                run = os.path.join(H, "scratch", "out", series, a, "C40")
                names = sorted(set(top_files(ref)) | set(top_files(run)))
                for name in names:
                    rf, xf = os.path.join(ref, name), os.path.join(run, name)
                    rs = sha256(rf) if os.path.exists(rf) else "absent from the reference tree"
                    xs = sha256(xf) if os.path.exists(xf) else "absent from the run tree"
                    ok = "yes" if rs == xs else "no"
                    n += 1
                    same += ok == "yes"
                    w.writerow([a, series, name, rs, xs, ok, rf, xf])
    print("files compared: %d, byte identical: %d" % (n, same))


if __name__ == "__main__":
    sys.exit(main())
