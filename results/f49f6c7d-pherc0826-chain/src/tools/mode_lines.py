#!/usr/bin/env python3
"""The source lines of Stevens' simpaper10 that the article cites, found in the published commit.

It reads pipeline9/simpaper10.cpp at scrollreading commit 62cbc21 (the upstream as published, the
base of item 91's arm A) with `git show`, from the local clone /data/repositories/scrollreading, and
writes one row per cited place: the key the article uses, the line number, and the line's text, so
a reader can check that the line says what the prose says it does. The file itself is GPL 3 and is
not copied here. A key whose pattern is found zero times or more than once stops the tool.

Usage: mode_lines.py [--out PATH] [--repo PATH]
"""
import argparse, csv, os, re, subprocess, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMIT, PATH = "62cbc21", "pipeline9/simpaper10.cpp"
# key -> (pattern, which occurrence, 1 based[, how many matches the file must have, default 1])
KEYS = [
    ("usage_g", r'fprintf\(stderr,"g - default', 1),
    ("mode_g", r'if \(mode=="g"\)', 1),
    ("g_generate", r"GeneratePatches\(patches,am,numPatches\);", 1, 2),
    ("mode_l", r'if \(mode=="l"\)', 1),
    ("l_centre", r"p\.second\.CentreVolCoords\(v\)", 1),
    ("mode_c", r'if \(mode=="c"\)', 1),
    ("c_round_2", r"FindBadPatchesGeneral\(\*am,patches,2,", 1),
    ("c_round_5", r"FindBadPatchesGeneral\(\*am,patches,5,", 1),
    ("mode_vm", r'if \(mode=="vm"\)', 1),
    ("vm_orders", r"numComponents = MakeVisitOrders\(", 1),
    ("vm_bridges", r"FindNeighbourProblems\(neighbourList,patches,badBridges,newBadBridges,patchOrders\[i\]", 1),
    ("mode_hm", r'if \(mode=="hm"\)', 1),
    ("hm_springs", r"PatchSpringSimulation pss\(QUADMESH_SIZE,OUTPUT_DIR,i\);", 1),
    ("hm_run", r"pss\.run\(50\);", 2, 2),
    ("mode_fm", r'if \(mode=="fm"\)', 1),
    ("param_surface_zarr", r'^#define SURFACE_ZARR ', 1, 1, "pipeline9/parameters.h"),
    ("surface_zarr_open", r'new PatchGenerator\(string\(SURFACE_ZARR\)\)', 1),
    ("param_seed_x", r'^#define SEED_X ', 1, 1, "pipeline9/parameters.h"),
    ("param_seed_y", r'^#define SEED_Y ', 1, 1, "pipeline9/parameters.h"),
    ("param_seed_z", r'^#define SEED_Z ', 1, 1, "pipeline9/parameters.h"),
    ("fm_score", r"float score = ScorePlacement\(am, patches, patchPositionsXYA,patchOrder, patchesToColour, manualGoodRel, patchesInvolved, maxDistanceThresh, 1\.0, true, true, false, compIndex\)", 1),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(S, "evidence", "derived", "simpaper10-lines.csv"))
    ap.add_argument("--repo", default="/data/repositories/scrollreading")
    a = ap.parse_args()
    cache = {}

    def source(path):
        if path not in cache:
            cache[path] = subprocess.check_output(["git", "-C", a.repo, "show", "%s:%s" % (COMMIT, path)]).decode().splitlines()
        return cache[path]
    rows = []
    for k in KEYS:
        key, pat, occ = k[:3]
        want = k[3] if len(k) > 3 else 1
        path = k[4] if len(k) > 4 else PATH
        src = source(path)
        hits = [i + 1 for i, l in enumerate(src) if re.search(pat, l)]
        if len(hits) < occ:
            sys.exit("mode_lines.py: %s: %d match(es) of %r, wanted occurrence %d" % (key, len(hits), pat, occ))
        if len(hits) != want:
            sys.exit("mode_lines.py: %s: %d matches of %r, expected %d" % (key, len(hits), pat, want))
        n = hits[occ - 1]
        rows.append({"key": key, "line": n, "text": src[n - 1].strip(), "commit": COMMIT, "path": path,
                     "matches": len(hits)})
    now = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        fh.write('"# written by src/tools/mode_lines.py at %s from scrollreading %s:%s (git show)"\n' % (now, COMMIT, PATH))
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print("  %-12s line %5d  %s" % (r["key"], r["line"], r["text"][:80]))


if __name__ == "__main__":
    main()
