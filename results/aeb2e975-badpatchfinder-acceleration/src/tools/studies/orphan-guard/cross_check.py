#!/usr/bin/env python3
"""The guard's own report against the diagnosis that preceded it.

badpatch-crash instrumented the same source to print, for every chain that would throw, the
element that was missing from the patches map: 202 chains and 73 distinct ids
(evidence/key-containers.csv of that study, one row per id, times_reported_missing per row).
The guard counts the chains it refuses and the ids in them. The two are compared here as sets and
as counts; neither number is retyped, both are read from the file that carries it.
"""
import csv, os, sys

H = "/data/scrollagent/runs/rev1/orphan-guard"
KC = "/data/scrollagent/runs/rev1/badpatch-crash/evidence/key-containers.csv"
LOG = os.path.join(H, "log", "chain-guard-PHerc1447-seed34-c.txt")


def guard_report():
    chains = patches = None
    ids = None
    with open(LOG, errors="replace") as f:
        for line in f:
            if line.startswith("Chains refused for a patch with no geometry: length=2 "):
                bits = dict(p.split("=") for p in line.split(": ", 1)[1].split())
                chains, patches = int(bits["chains"]), int(bits["patches"])
            elif chains is not None and line.startswith("Patches with no geometry:"):
                ids = set(int(x) for x in line.split(":", 1)[1].split())
                break
    if ids is None:
        raise SystemExit("the guard printed no length 2 report in " + LOG)
    return chains, patches, ids


def diagnosis():
    ids, reported = set(), 0
    with open(KC) as f:
        for r in csv.DictReader(f):
            ids.add(int(r["patch"]))
            reported += int(r["times_reported_missing"])
    return ids, reported


def main():
    chains, patches, gids = guard_report()
    dids, reported = diagnosis()
    out = os.path.join(H, "evidence", "cross-check.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["quantity", "from_the_guard", "from_the_diagnosis", "agree", "guard_file",
                    "diagnosis_file"])
        w.writerow(["chains refused at length 2", chains, reported,
                    "yes" if chains == reported else "no", LOG, KC])
        w.writerow(["distinct patches with no geometry", patches, len(dids),
                    "yes" if patches == len(dids) else "no", LOG, KC])
        w.writerow(["the set of those patches", "%d ids" % len(gids), "%d ids" % len(dids),
                    "yes" if gids == dids else "no", LOG, KC])
        w.writerow(["ids the guard names and the diagnosis does not",
                    " ".join(str(i) for i in sorted(gids - dids)) or "none", "", "", LOG, KC])
        w.writerow(["ids the diagnosis names and the guard does not", "",
                    " ".join(str(i) for i in sorted(dids - gids)) or "none", "", LOG, KC])
    print("chains %d vs %d, patches %d vs %d, sets equal %s"
          % (chains, reported, patches, len(dids), gids == dids))
    print("written to " + out)


if __name__ == "__main__":
    sys.exit(main())
