#!/usr/bin/env python3
"""Compare every file a run of this study wrote at the top of its C40 copy against the reference
sha256 taken before the study started (evidence/reference-files.csv).

Not the ten delivered sheets alone: every file the downstream writes, because a change that fired
where it should not could move a CSV of the c stage and leave the sheets alone. A file in one tree
and not in the other is a row that says so and counts as not identical.

Usage: compare_outputs.py <tag> [<tag> ...]
Appends to evidence/identity.csv and prints the count.
"""
import csv, hashlib, os, subprocess, sys

S = "/data/scrollagent/runs/rev1/c-stage-cost"
REFCSV = os.path.join(S, "evidence", "reference-files.csv")
OUT = os.path.join(S, "evidence", "identity.csv")
SKIP = {"missing-C40.txt"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def reference():
    ref = {}
    with open(REFCSV) as f:
        for line in f:
            if line.startswith("#"):
                continue
            rows = csv.reader([line])
            break
        r = csv.DictReader(f, fieldnames=["attempt", "file", "sha256", "bytes", "path",
                                          "taken_utc"])
        for row in r:
            ref[(row["attempt"], row["file"])] = row
    return ref


def main():
    ref = reference()
    when = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    new = not os.path.exists(OUT)
    total = same = 0
    with open(OUT, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            fh.write("# one row per file compared. tag is the arm of this study, attempt the "
                     "seed, file the name at the top of C40. reference_sha256 comes from "
                     "evidence/reference-files.csv, taken before this study ran anything, and "
                     "run_sha256 is of the file this arm wrote. byte_identical is yes only when "
                     "the two strings are equal; a file present on one side only is a row that "
                     "says so and is not identical. missing-C40.txt is excluded, it is written by "
                     "the zarr reader and is not an output of the chain.\n")
            w.writerow(["tag", "attempt", "file", "reference_sha256", "run_sha256",
                        "byte_identical", "run_path", "compared_utc"])
        for tag in sys.argv[1:]:
            root = os.path.join(S, "scratch", "out", tag)
            if not os.path.isdir(root):
                raise SystemExit("no arm at %s" % root)
            for attempt in sorted(os.listdir(root)):
                d = os.path.join(root, attempt, "C40")
                run_names = set(n for n in os.listdir(d)
                                if os.path.isfile(os.path.join(d, n)) and n not in SKIP)
                ref_names = set(k[1] for k in ref if k[0] == attempt)
                for n in sorted(run_names | ref_names):
                    p = os.path.join(d, n)
                    rs = ref[(attempt, n)]["sha256"] if (attempt, n) in ref \
                        else "absent from the reference tree"
                    xs = sha256(p) if n in run_names else "the run wrote no such file"
                    ok = "yes" if rs == xs else "no"
                    total += 1
                    same += ok == "yes"
                    w.writerow([tag, attempt, n, rs, xs, ok, p, when])
    print("files compared: %d, byte identical: %d, different: %d" % (total, same, total - same))


if __name__ == "__main__":
    sys.exit(main())
