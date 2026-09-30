#!/usr/bin/env python3
"""Build one simpaper10 for this study, one arm, configured for PHerc0139.

Adapted from runs/rev1/c-stage-cost/tools/build_one.py. What was adapted, and nothing else:

  * the source tree is scratch/src-<arm>, one per arm, so that a build never depends on a patch
    being moved in or out between two builds (that script had one tree and edited its groups);
  * parameters.json is read from /data/scrollagent/pipeline/build/efficient/parameters.json, the
    file that configured the binary which grew every tree of this study
    (reference-b40/DECLARATION.md), instead of seed-search-1447's stock parameters plus a
    PHerc1447 seed from seed-ladder-1447. It carries the PHerc0139 volume and the PHerc0139 seed;
  * the volume shape in it is checked against pipeline/datasets/manifests/PHerc0139.json, the
    published metadata, and a mismatch stops the build. No constant is typed in this file;
  * the CSV it appends to is this study's evidence/binaries.csv.

The compile route, the CFLAGS and the JOBS are those of c-stage-cost, unchanged, so that the
three arms differ by nothing but the patches in their corrections group.

Usage:  build_one.py <arm>        with <arm> one of plain, guarded, c2
"""
import csv, hashlib, json, os, shutil, subprocess, sys, time

S = "/data/scrollagent/runs/rev1/c-stage-on-0139"
STOCK_PARAMS = "/data/scrollagent/pipeline/build/efficient/parameters.json"
MANIFEST = "/data/scrollagent/pipeline/datasets/manifests/PHerc0139.json"
SERIES = "corrected"
JOBS = 8
CSV = os.path.join(S, "evidence", "binaries.csv")
HEADER = [
    "arm",                    # plain, guarded or c2
    "corrections_present",    # the patch numbers of the corrections group in that arm's tree
    "series",                 # the build.sh group list it was laid down from
    "sha256",                 # sha256 of the binary as built
    "sha256_stripped",        # sha256 after `strip`, which removes the debug sections only
    "build_seconds",          # wall clock of parse_parameters.py plus make
    "source_tree",            # the tree it was laid down from
    "how_it_was_measured",    # in prose
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    arm = sys.argv[1]
    src = os.path.join(S, "scratch", "src-%s" % arm)
    out = os.path.join(src, "build", SERIES)
    if not os.path.isdir(src):
        raise SystemExit("no source tree at %s: run tools/lay_source.sh" % src)

    params = json.load(open(STOCK_PARAMS))
    shape = json.load(open(MANIFEST))["shape"]          # z, y, x as the manifest publishes it
    got = [params["global"]["VOL_SIZE_Z"], params["global"]["VOL_SIZE_Y"],
           params["global"]["VOL_SIZE_X"]]
    if got != shape:
        raise SystemExit("volume shape %r in %s is not the published %r of %s"
                         % (got, STOCK_PARAMS, shape, MANIFEST))

    env = dict(os.environ, JOBS=str(JOBS), BLOSC2_PREFIX="/data/opt/blosc2",
               LIBTIFF_PREFIX="/data/opt/libtiff", RPATH="1", TMPDIR="/data/tmp")
    log = os.path.join(S, "log", "build-%s.txt" % arm)
    with open(log, "wb") as h:
        rc = subprocess.call(["./build.sh", SERIES], cwd=src, stdout=h,
                             stderr=subprocess.STDOUT, env=env)
    if rc != 0:
        raise SystemExit("build.sh %s failed for arm %s, see %s" % (SERIES, arm, log))

    shutil.copy2(STOCK_PARAMS, os.path.join(out, "parameters.json"))

    cflags = ("-O3 -w -fopenmp -ffp-contract=off -I/data/opt/blosc2/include "
              "-I/data/opt/libtiff/include")
    cmd = ("python3 parse_parameters.py > /dev/null && make -j%d "
           "BLOSC2_PREFIX=/data/opt/blosc2 LIBTIFF_PREFIX=/data/opt/libtiff RPATH=1 "
           "CFLAGS='%s' simpaper10" % (JOBS, cflags))
    # every object is rebuilt, because CFLAGS changed and make does not know it
    for f in os.listdir(out):
        if f.endswith(".o"):
            os.remove(os.path.join(out, f))
    t0 = time.monotonic()
    with open(log, "ab") as h:
        rc = subprocess.call(cmd, shell=True, cwd=out, stdout=h, stderr=subprocess.STDOUT)
    secs = time.monotonic() - t0
    if rc != 0:
        raise SystemExit("make failed for arm %s, see %s" % (arm, log))

    binroot = os.path.join(S, "scratch", "bin", arm)
    os.makedirs(binroot, exist_ok=True)
    binary = os.path.join(binroot, "simpaper10")
    shutil.copy2(os.path.join(out, "simpaper10"), binary)
    stripped = binary + ".stripped"
    shutil.copy2(binary, stripped)
    subprocess.check_call(["strip", stripped])
    sh, shs = sha256(binary), sha256(stripped)
    os.remove(stripped)

    present = " ".join(sorted(n.split("-")[0] for n in
                              os.listdir(os.path.join(src, "patches", "corrections"))
                              if n.endswith(".patch")))
    new = not os.path.exists(CSV)
    with open(CSV, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            f.write("# one row per binary this study built, one per arm. sha256 is of the file as "
                    "built; sha256_stripped is of a copy passed through `strip`. corrections_present "
                    "is the patch numbers found in that arm's patches/corrections folder, which is "
                    "what makes the arms differ. The volume shape and the seed come from "
                    "/data/scrollagent/pipeline/build/efficient/parameters.json and the shape is "
                    "checked against pipeline/datasets/manifests/PHerc0139.json before the build; "
                    "no constant is typed in the tool.\n")
            w.writerow(HEADER)
        w.writerow([arm, present, SERIES, sh, shs, "%.1f" % secs, src,
                    "built by tools/build_one.py, the route of c-stage-cost/tools/build_one.py "
                    "with the PHerc0139 parameters of pipeline/build/efficient"])
    print("%s: sha %s stripped %s in %.1f s" % (arm, sh, shs, secs))


if __name__ == "__main__":
    main()
