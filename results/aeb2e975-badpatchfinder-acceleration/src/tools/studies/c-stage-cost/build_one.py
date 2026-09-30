#!/usr/bin/env python3
"""Build one simpaper10 for this study, by the route seed-search-1447/tools/build_binaries.py used.

The route, unchanged: `build.sh <series>` lays down a working copy from the pinned upstream plus
the patch groups, then parameters.json gets seed40's SEED_X/Y/Z and the PHerc1447 volume shape read
from the dataset manifest, parse_parameters.py turns it into parameters.h, and `make simpaper10`
rebuilds. Nothing here carries a typed constant: the seed comes from seed-ladder-1447's attempts.csv
and the shape from pipeline/datasets/manifests/PHerc1447.json.

Usage:  build_one.py <series> <label> [--debug]

  <series>  a group list for build.sh (corrected, or a name this study added)
  <label>   the name the binary is kept under in scratch/bin/<label>/simpaper10
  --debug   add -g to CFLAGS. -g changes no instruction: the check below strips both binaries and
            compares them, and the row it writes says whether they were equal.

Writes one row per build into evidence/binaries.csv.
"""
import csv, hashlib, json, os, shutil, subprocess, sys, time

S = "/data/scrollagent/runs/rev1/c-stage-cost"
SRC = os.path.join(S, "scratch", "src")
LADDER = "/data/scrollagent/runs/rev1/seed-ladder-1447/evidence/attempts.csv"
MANIFEST = "/data/scrollagent/pipeline/datasets/manifests/PHerc1447.json"
STOCK_PARAMS = "/data/scrollagent/runs/rev1/seed-search-1447/scratch/parameters-stock.json"
ATTEMPT = "PHerc1447-seed40"
JOBS = 8
CSV = os.path.join(S, "evidence", "binaries.csv")
HEADER = [
    "label",                  # the name this study calls the build
    "series",                 # the build.sh group list it was laid down from
    "debug_flag",             # yes when -g was added to CFLAGS, no otherwise
    "sha256",                 # sha256 of the binary as built
    "sha256_stripped",        # sha256 after `strip`, which removes the debug sections only
    "build_seconds",          # wall clock of parse_parameters.py plus make
    "how_it_was_measured",    # in prose
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def seed_row():
    with open(LADDER) as f:
        for r in csv.DictReader(f):
            if r["attempt"] == ATTEMPT:
                return r
    raise SystemExit("no row for %s in %s" % (ATTEMPT, LADDER))


def main():
    series, label = sys.argv[1], sys.argv[2]
    debug = "--debug" in sys.argv[3:]
    out = os.path.join(SRC, "build", series)
    seed = seed_row()
    shape = json.load(open(MANIFEST))["shape"]

    env = dict(os.environ, JOBS=str(JOBS), BLOSC2_PREFIX="/data/opt/blosc2",
               LIBTIFF_PREFIX="/data/opt/libtiff", RPATH="1", TMPDIR="/data/tmp")
    log = os.path.join(S, "log", "build-%s.txt" % label)
    with open(log, "wb") as h:
        rc = subprocess.call(["./build.sh", series], cwd=SRC, stdout=h,
                             stderr=subprocess.STDOUT, env=env)
    if rc != 0:
        raise SystemExit("build.sh %s failed, see %s" % (series, log))

    params = json.load(open(STOCK_PARAMS))
    params["global"]["VOL_SIZE_X"] = shape[2]
    params["global"]["VOL_SIZE_Y"] = shape[1]
    params["global"]["VOL_SIZE_Z"] = shape[0]
    params["seed"]["SEED_X"] = int(seed["seed_x"])
    params["seed"]["SEED_Y"] = int(seed["seed_y"])
    params["seed"]["SEED_Z"] = int(seed["seed_z"])
    with open(os.path.join(out, "parameters.json"), "w") as h:
        json.dump(params, h, indent=2)

    cflags = ("-O3 -w -fopenmp -ffp-contract=off -I/data/opt/blosc2/include "
              "-I/data/opt/libtiff/include")
    if debug:
        cflags += " -g"
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
        raise SystemExit("make failed for %s, see %s" % (label, log))

    binroot = os.path.join(S, "scratch", "bin", label)
    os.makedirs(binroot, exist_ok=True)
    binary = os.path.join(binroot, "simpaper10")
    shutil.copy2(os.path.join(out, "simpaper10"), binary)
    stripped = binary + ".stripped"
    shutil.copy2(binary, stripped)
    subprocess.check_call(["strip", stripped])
    sh, shs = sha256(binary), sha256(stripped)
    os.remove(stripped)

    new = not os.path.exists(CSV)
    with open(CSV, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            f.write("# one row per binary this study built. sha256 is of the file as built; "
                    "sha256_stripped is of a copy passed through `strip`, which removes the debug "
                    "sections and nothing else, so two builds that differ only by -g have equal "
                    "sha256_stripped. Seed and volume shape come from seed-ladder-1447/evidence/"
                    "attempts.csv and pipeline/datasets/manifests/PHerc1447.json, never typed here.\n")
            w.writerow(HEADER)
        w.writerow([label, series, "yes" if debug else "no", sh, shs, "%.1f" % secs,
                    "built by tools/build_one.py, the route of seed-search-1447/tools/build_binaries.py"])
    print("%s: sha %s stripped %s in %.1f s" % (label, sh, shs, secs))


if __name__ == "__main__":
    main()
