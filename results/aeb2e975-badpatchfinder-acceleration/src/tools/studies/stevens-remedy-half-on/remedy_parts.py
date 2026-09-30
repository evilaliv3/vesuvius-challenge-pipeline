#!/usr/bin/env python3
"""stevens-remedy-half-on step 1: one row per part of Stevens' remedy at 62cbc21 (pipeline9), evidence/remedy-parts.csv.
Every quoted line is checked verbatim (whitespace stripped) against `git show 62cbc21:pipeline9/<file>` at the line named,
and searched in the house's two build trees (seeds-at-scale-1447/scratch/src/build/delivered and .../corrected, the
latter is seed73's binary) and in the delivered runners' stage list. A quote not found at its line stops the tool."""
import csv, subprocess, sys

CLONE = "/data/repositories/scrollreading"
R1 = "/data/scrollagent/runs/rev1"
HOUSE = {"delivered": R1 + "/seeds-at-scale-1447/scratch/src/build/delivered",
         "corrected": R1 + "/seeds-at-scale-1447/scratch/src/build/corrected"}
OUT = R1 + "/stevens-remedy-half-on/evidence/remedy-parts.csv"
RUNNERS = [R1 + "/seeds-at-scale-1447/tools/run_seed_v%d.sh" % v for v in (3, 4, 5, 6)]
STAGES = 'for st in "c" "l" "vm 10" "hm 10" "fm 30 10"; do'

P = [
 # part, report12 method, file, line, quote, what it does, default, why, how to turn on
 ("M1a pairs and chains 2 to 5", "method 1", "simpaper10.cpp", 820,
  "bpf->FindBadPatchesGeneral(*am,patches,2,badPatches,badPatchScores);",
  "stage c: chains of length 2 (pairs); followed at 824, 832, 840 by lengths 3, 4, 5, each only on sequences free of patches already found",
  "on", "stage c is the first stage of the delivered list; nothing guards the four calls", "already on"),
 ("M1a length 5", "method 1", "simpaper10.cpp", 840,
  "bpf->FindBadPatchesGeneral(*am,patches,5,badPatches,badPatchScores);",
  "stage c: the last round, chains of length 5 (report12 page 3: lengths 2 to 5)", "on", "unconditional", "already on"),
 ("M1b threshold", "method 1", "badpatchfinder.cpp", 392,
  "BP_MAX_XYZ_DISTANCE*(length-1))",
  "a chain is inconsistent when the largest normal projected 3D distance between points of equal 2D coordinate exceeds 10 voxels times (length-1); BP_MAX_XYZ_DISTANCE is 10 in parameters.h:56 and parameters.json",
  "on", "10 voxels is a live threshold, not a disabling one", "already on"),
 ("M1c greedy removal", "method 1", "badpatchfinder.cpp", 440, "bpt++;",
  "the patch in most inconsistent chains is marked bad and its chains erased, repeated until none is left; after erase() the iterator is incremented again, so the chain following an erased one is skipped in that pass (it is caught in a later pass, since the outer loop repeats while any chain remains) and an erase of the last element increments end()",
  "on (with a defect)", "it runs by default; the skip delays but does not stop removal; not measured here", "already on"),
 ("M1d consumption", "method 1", "simpaper10.cpp", 1014, "LoadBadPatches(badPatches,manualBadRel);",
  "stage vm reads badpatches.csv (stage c's output) and manualBadPatch.csv, and builds the visit orders without those patches: the offending patches are dropped from every sheet",
  "on", "stage vm is in the delivered list and calls it unconditionally", "already on"),
 ("M1e old pair finder (mode b)", "method 1 (superseded)", "simpaper10.cpp", 782,
  "bpf->FindBadPatches(*am,patches,badPatches,badPatchScores);",
  "pairs only; readme.md: 'b : Obsolete function for finding bad patches. Use c instead.'",
  "off", "mode b is not in the delivered list and is superseded by c", "not part of the remedy as documented"),
 ("M2a bridge detection", "method 2", "simpaper10.cpp", 1073,
  "bpf->FindNeighbourProblems(neighbourList,patches,badBridges,newBadBridges,patchOrders[i],patchPositionss[i]);",
  "stage vm: per component, a patch whose two neighbours are placed further apart than its diameter plus their radii is a bridge; written to badbridgess_out.csv",
  "on (detection only)", "it runs inside vm, but its output file is read by no delivered stage", "see M2b, M2c"),
 ("M2b bridge output not consumed", "method 2", "simpaper10.cpp", 1061, "// remember to copy this to badbridges.csv",
  "the bridges go to badbridgess_out.csv with a NEW line per component; the stages that read badbridges.csv are n, nm and o only (1496, 1545, 1581); no delivered stage reads it",
  "off (as a drop)", "report12 page 4: bridges are not removed directly but 'given a high weighting as likely problems in the subsequent optimization step', that is method 3; the copy is a manual step", "copy without NEW lines to badbridges.csv, then run nm (method 3)"),
 ("M2c direct bridge drop", "method 2", "simpaper10.cpp", 593, "if (includeBadBridges)",
  "LoadBadPatches can add badbridges.csv to the bad patches; its parameter defaults to false (571) and no call passes true (907, 1014 two argument; 1491, 1540, 1576 pass false)",
  "off (dead code)", "no caller sets includeBadBridges, and report12 argues against a direct drop", "not part of the remedy as documented; not turned on"),
 ("M3 simulated annealing, several components", "method 3", "simpaper10.cpp", 1510, 'if (mode=="nm")',
  "AnnealAll: searches a set of extra patches to exclude, scoring each state by flattened area minus normal projected 3D disagreement of points sharing a 2D cell; writes annealState_out.csv",
  "off", "mode nm (and n, 1466) is not in the delivered stage list, nor in readme.md steps 10 to 14, which run c, l, v, h, f; readme item n says the result is used only after a manual copy to manualBadPatch.csv", "nm 10 <iterations> after vm 10, then cp annealState_out.csv manualBadPatch.csv, then vm 10, hm 10, fm 30 10"),
 ("M3b annealing result read", "method 3", "simpaper10.cpp", 586, 'std::ifstream is(OUTPUT_DIR "/manualBadPatch.csv");',
  "LoadBadPatches adds manualBadPatch.csv when present: the only door by which method 3's exclusions reach the sheets",
  "on (reads nothing)", "the file is absent from every delivered tree, so it adds no patch", "write it from annealState_out.csv"),
 ("M3c annealing random stream", "method 3", "anneal.cpp", 675, "std::mt19937 rng(std::random_device{}());",
  "the annealing draws from the hardware random device, not RANDOM_SEED or SIMPAPER_SEED", "property", "two runs on one tree differ", "no switch: one run is one draw"),
]


def show(f):
    return subprocess.check_output(["git", "-C", CLONE, "show", "62cbc21:pipeline9/" + f]).decode("utf-8", "replace").split("\n")


def norm(s):
    return "".join(s.split())


def main():
    cache, house = {}, {}
    rows = []
    for part, meth, f, ln, q, what, dflt, why, how in P:
        if f not in cache:
            cache[f] = show(f)
        if norm(q) not in norm(cache[f][ln - 1]):
            sys.exit("quote not at %s:%d: %r / %r" % (f, ln, q, cache[f][ln - 1]))
        found = {}
        for k, d in HOUSE.items():
            if (k, f) not in house:
                house[(k, f)] = open("%s/%s" % (d, f), errors="replace").read().split("\n")
            q2 = norm(q.replace('OUTPUT_DIR "/manualBadPatch.csv"', 'outPath("/manualBadPatch.csv")'))
            hits = [i + 1 for i, l in enumerate(house[(k, f)]) if q2 in norm(l)]
            found[k] = ("yes at " + ";".join(map(str, hits))) if hits else "no"
        rows.append([part, meth, "pipeline9/" + f, ln, q, what, dflt, why, how, found["delivered"], found["corrected"]])
    stage_ok = all(STAGES in open(r).read() for r in RUNNERS)
    nm_in_runners = any('"nm' in open(r).read() for r in RUNNERS)
    t = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    with open(OUT, "w", newline="") as fh:
        fh.write("# written by stevens-remedy-half-on/tools/remedy_parts.py at %s: one row per part of the remedy in "
                 "WillStevens/scrollreading 62cbc21 pipeline9 (git show, clone untouched); line = line in that commit; "
                 "every quote checked verbatim at its line; house_* = lines of the same quote in "
                 "seeds-at-scale-1447/scratch/src/build/delivered and build/corrected (seed73's binary; OUTPUT_DIR read as "
                 "outPath). Delivered stage list '%s' found in run_seed_v3 to v6: %s; any nm stage in those runners: %s.\n"
                 % (t, STAGES, "yes" if stage_ok else "no", "yes" if nm_in_runners else "no"))
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["part", "report12_method", "file", "line_62cbc21", "quote", "what_it_does", "default_in_chain",
                    "why", "how_to_turn_on", "house_delivered_source", "house_corrected_source"])
        w.writerows(rows)
    print("%d rows, stage list %s, nm in runners %s" % (len(rows), stage_ok, nm_in_runners))


main()
