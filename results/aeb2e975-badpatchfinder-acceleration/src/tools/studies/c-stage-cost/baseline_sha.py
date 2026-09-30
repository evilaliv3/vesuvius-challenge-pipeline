#!/usr/bin/env python3
"""The sha256 of everything the downstream of the six seeds has on disk today, taken once, before
this study runs a single stage.

The reference trees belong to seed-search-1447 and are read only here. Two files are written:
evidence/reference-files.csv, one row per file, and evidence/reference-files.sha256 in the plain
`sha256  path` form, so the same claim can be checked with sha256sum -c by anyone.

missing-C40.txt is left out: it is written by the zarr reader from the state of the chunk cache and
is not an output of the chain.
"""
import csv, hashlib, os, subprocess, sys

S = "/data/scrollagent/runs/rev1/c-stage-cost"
REF = "/data/scrollagent/runs/rev1/seed-search-1447/out"
SEEDS = ["PHerc1447-seed01", "PHerc1447-seed15", "PHerc1447-seed26",
         "PHerc1447-seed38", "PHerc1447-seed40", "PHerc1447-seed48"]
SKIP = {"missing-C40.txt"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    when = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    rows = []
    for a in SEEDS:
        d = os.path.join(REF, a, "C40")
        for n in sorted(os.listdir(d)):
            p = os.path.join(d, n)
            if not os.path.isfile(p) or n in SKIP:
                continue
            rows.append([a, n, sha256(p), os.path.getsize(p), p, when])
    out = os.path.join(S, "evidence", "reference-files.csv")
    with open(out, "w", newline="") as f:
        f.write("# every file at the top of seed-search-1447/out/<attempt>/C40 as it stands today, "
                "before this study ran anything. attempt is the seed; file is the name; sha256 and "
                "bytes are of the file on disk; path is where it was read; taken_utc is the time "
                "from `date -u` when the reading started. missing-C40.txt is excluded: the zarr "
                "reader writes it from the state of the chunk cache, it is not an output of the "
                "chain. This is the reference every run of this study is compared against.\n")
        w = csv.writer(f)
        w.writerow(["attempt", "file", "sha256", "bytes", "path", "taken_utc"])
        w.writerows(rows)
    with open(os.path.join(S, "evidence", "reference-files.sha256"), "w") as f:
        for r in rows:
            f.write("%s  %s\n" % (r[2], r[4]))
    sheets = sum(1 for r in rows if r[1].startswith("patch_") and r[1].endswith(".bin"))
    print("files: %d over %d seeds, of which delivered sheets: %d, written to %s"
          % (len(rows), len(SEEDS), sheets, out))


if __name__ == "__main__":
    sys.exit(main())
