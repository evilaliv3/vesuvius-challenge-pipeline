#!/usr/bin/env python3
"""Per tree, how many files the two arms agree on, and the distinction that matters.

tools/hash_run.py walks the whole working copy, so evidence/identity.csv has a row for every file
in it. Most of those rows are the growth tree carried along: patches/, rel.csv, surface.bp,
boundary.bp. Those files are hard links to the same inode in both arms, so their agreement is true
by construction and says nothing; quoting «46,074 files identical» would be a strong sounding
number that most of its rows do not support. The check that those files were not modified is
tools/check_pristine.py, which compares the pristine copy with a fingerprint taken from the
original tree before this study ran anything.

So this tool splits the rows in two and reports both:

  written_by_downstream   the files at the top of the working copy, which are what the five
                          stages write, the ten delivered sheets among them;
  carried_input           everything under patches/, surface.bp and boundary.bp, plus rel.csv:
                          the growth tree, hard linked, identical by construction.

Writes evidence/identity-by-tree.csv.
"""
import collections, csv, os, subprocess, sys

S = "/data/scrollagent/runs/rev1/c-stage-on-0139"
IDENT = os.path.join(S, "evidence", "identity.csv")
OUT = os.path.join(S, "evidence", "identity-by-tree.csv")


def main():
    when = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    agg = collections.OrderedDict()
    diff_names = collections.defaultdict(list)
    with open(IDENT) as f:
        for r in csv.DictReader(l for l in f if not l.startswith("#")):
            k = (r["arm_a"], r["arm_b"], r["tree"])
            a = agg.setdefault(k, {"w": 0, "wd": 0, "c": 0, "cd": 0})
            written = "/" not in r["relpath"]
            bad = r["byte_identical"] != "yes"
            if written:
                a["w"] += 1
                a["wd"] += bad
            else:
                a["c"] += 1
                a["cd"] += bad
            if bad:
                diff_names[k].append(r["relpath"])
    with open(OUT, "w", newline="") as f:
        f.write("# one row per pair of arms and tree, from evidence/identity.csv. "
                "written_by_downstream counts the files at the top of the working copy, which is "
                "what the five stages write; carried_input counts the growth tree carried along, "
                "hard linked between the arms and therefore identical by construction, whose real "
                "check is evidence/pristine-check.csv. differing_files names every file that is "
                "not byte identical, and is empty when there is none.\n")
        w = csv.writer(f)
        w.writerow(["arm_a", "arm_b", "tree", "written_by_downstream", "written_differing",
                    "carried_input", "carried_differing", "differing_files", "summarised_utc"])
        for k, a in agg.items():
            w.writerow([k[0], k[1], k[2], a["w"], a["wd"], a["c"], a["cd"],
                        " ".join(sorted(diff_names[k])), when])
    print(open(OUT).read())


if __name__ == "__main__":
    sys.exit(main())
