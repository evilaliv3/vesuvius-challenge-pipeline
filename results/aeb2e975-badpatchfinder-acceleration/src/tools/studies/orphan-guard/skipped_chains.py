#!/usr/bin/env python3
"""Read the guard's own report out of each stage log and write one row per chain length.

The guard prints, once for every call of FindBadPatchesGeneral:

    Chains refused for a patch with no geometry: length=<n> chains=<c> patches=<p>
    Patches with no geometry: <id> <id> ...

Nothing here counts anything itself: the numbers are the ones the stage wrote, read back from the
log named in the row, and the orphan count of the tree comes from badpatch-crash's own CSV.
"""
import csv, glob, os, re, sys

H = "/data/scrollagent/runs/rev1/orphan-guard"
ORPHANS = "/data/scrollagent/runs/rev1/badpatch-crash/evidence/orphans-per-tree.csv"
LINE = re.compile(r"^Chains refused for a patch with no geometry: length=(\d+) chains=(\d+) patches=(\d+)$")


def tree_orphans():
    """ids_in_rel_with_no_patch_file and the reachable count, by the tree those rows name."""
    out = {}
    with open(ORPHANS) as f:
        for r in csv.DictReader(f):
            key = r["tree"].rstrip("/").split("/")[-2] if r["tree"].endswith(("growth", "C40")) else r["tree"]
            out[r["tree"]] = (r["ids_in_rel_with_no_patch_file"],
                              r["of_those_reachable_as_second_of_a_kept_length_2_chain"])
    return out


def orphans_for(attempt):
    o = tree_orphans()
    for tree, v in o.items():
        if attempt in tree:
            return v
    if "seed34" in attempt:
        return o["/data/scrollagent/runs/rev1/badpatch-crash/scratch/C40"]
    return ("not measured by badpatch-crash", "not measured by badpatch-crash")


def main():
    rows = []
    for log in sorted(glob.glob(os.path.join(H, "log", "chain-*-c.txt"))):
        name = os.path.basename(log)
        m = re.match(r"chain-(plain|guard)-(PHerc1447-seed\d+)-c\.txt$", name)
        if not m:
            continue
        series, attempt = m.group(1), m.group(2)
        reported = []
        with open(log, errors="replace") as f:
            prev = None
            for line in f:
                line = line.rstrip("\n")
                mm = LINE.match(line)
                if mm:
                    prev = mm.groups()
                    continue
                if prev is not None and line.startswith("Patches with no geometry:"):
                    ids = line.split(":", 1)[1].split()
                    reported.append((prev[0], prev[1], prev[2], ids))
                    prev = None
        rel_orphans, reachable = orphans_for(attempt)
        if not reported:
            rows.append([attempt, series, "not reported", "not reported", "not reported", "",
                         rel_orphans, reachable, log,
                         "the binary of this series carries no guard, so it prints no report"])
        for length, chains, patches, ids in reported:
            rows.append([attempt, series, length, chains, patches, " ".join(ids),
                         rel_orphans, reachable, log,
                         "written by the stage itself, one line per call of FindBadPatchesGeneral"])
    out = os.path.join(H, "evidence", "skipped-chains.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["attempt", "series", "chain_length", "chains_refused",
                    "distinct_patches_without_geometry", "patch_ids",
                    "tree_ids_in_rel_with_no_patch_file", "tree_of_those_reachable",
                    "log", "where_the_number_comes_from"])
        w.writerows(rows)
    print("%d rows written to %s" % (len(rows), out))
    for r in rows:
        print(r[0], r[1], "length", r[2], "chains", r[3], "patches", r[4])


if __name__ == "__main__":
    sys.exit(main())
