#!/usr/bin/env python3
"""Rebuild the ten per seed binaries of seed-ladder-1447, by the same route it used.

Why a rebuild. The declaration of this study says the ten are grown with the per seed binary the
ladder built and whose sha256 it recorded. That ladder removes each attempt's binary folder as
soon as the attempt ends (`reap` in its `run_ladder.py`), so `scratch/bin/` no longer exists and
the binaries are gone. The material that survives is the source tree, the stock
`parameters.json` and the recorded sha256 of every build, which is enough to rebuild by the same
route and to check the rebuild against what was recorded.

The route, copied from `seed-ladder-1447/tools/run_ladder.py` and not reinvented: `build.sh
corrected` lays down the patched working copy once, then for each seed `parameters.json` gets
that seed's SEED_X, SEED_Y, SEED_Z and the volume size of PHerc1447 read from its manifest,
`parse_parameters.py` turns it into `parameters.h`, and `make simpaper10` rebuilds. The binary is
copied out to `scratch/bin/<attempt>/simpaper10` and kept, because this study runs growths that
last hours and a binary that disappears cannot be re measured against.

Two gates, both written to `evidence/binary-gate.csv`:
  - `differs_from_stock`: the per seed build must differ from the stock build
    d59199492f4f33cb64e4ac6cb34a040484387b865b3028e3baa3775962b85e14, which is what proves the
    seed reached the compile. This is the ladder's gate SL0, unchanged.
  - `matches_ladder_sha256`: the rebuilt binary is compared with the sha256 the ladder recorded
    for that same attempt in its own `evidence/binary-gate.csv`. A mismatch is not a stop, it is
    a fact that goes in the outcome: the seed still reached the compile, but the binary is not
    byte for byte the one the ladder ran.
"""
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

S = "/data/scrollagent/runs/rev1/seed-search-1447"
LADDER = "/data/scrollagent/runs/rev1/seed-ladder-1447"
SRC = os.path.join(S, "scratch", "src")
BUILD = os.path.join(SRC, "build", "corrected")
MANIFESTS = "/data/scrollagent/pipeline/datasets/manifests"
STOCK_SHA = "d59199492f4f33cb64e4ac6cb34a040484387b865b3028e3baa3775962b85e14"
SCROLL = "PHerc1447"
JOBS = 12

# The ten of DECLARATION.md, read from the ladder's attempts.csv and checked against it below.
TEN = ["seed01", "seed11", "seed15", "seed26", "seed34", "seed35", "seed38", "seed40",
       "seed44", "seed48"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def ladder_rows():
    """The ten attempts of the ladder, with their coordinates and their recorded sha256."""
    rows = {}
    with open(os.path.join(LADDER, "evidence", "attempts.csv")) as f:
        for r in csv.DictReader(f):
            if r["scroll"] != SCROLL:
                continue
            if r["outcome"] != "still growing at the cap":
                continue
            rows[r["attempt"]] = r
    return rows


def gate_row(w, attempt, expectation, value, expected, passes, what):
    w.writerow([attempt, SCROLL, os.path.join(S, "scratch", "bin", attempt, "simpaper10"),
                value, expectation, expected, passes, what])


def main():
    rows = ladder_rows()
    want = ["%s-%s" % (SCROLL, s) for s in TEN]
    missing = [a for a in want if a not in rows]
    if missing:
        raise SystemExit("the ladder does not record these as still growing at the cap: %s" % missing)
    if sorted(rows) != sorted(want):
        raise SystemExit("the ladder's still growing set is %s, the declaration names %s"
                         % (sorted(rows), sorted(want)))

    shape = json.load(open(os.path.join(MANIFESTS, SCROLL + ".json")))["shape"]
    os.makedirs(os.path.join(S, "log"), exist_ok=True)

    if not os.path.exists(os.path.join(BUILD, "simpaper10")):
        print("laying down the patched working copy with build.sh corrected", flush=True)
        with open(os.path.join(S, "log", "build-corrected.txt"), "wb") as handle:
            rc = subprocess.call(["./build.sh", "corrected"], cwd=SRC,
                                 stdout=handle, stderr=subprocess.STDOUT,
                                 env=dict(os.environ, JOBS=str(JOBS)))
        if rc != 0:
            raise SystemExit("build.sh corrected failed, see log/build-corrected.txt")
    stock = sha256(os.path.join(BUILD, "simpaper10"))
    print("stock build sha %s, expected %s, %s"
          % (stock[:8], STOCK_SHA[:8], "equal" if stock == STOCK_SHA else "DIFFERENT"), flush=True)

    out = os.path.join(S, "evidence", "binary-gate.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["attempt", "scroll", "binary", "sha256", "expectation", "expected_value",
                    "passes", "what_it_proves"])
        gate_row(w, "stock", "equals_the_stock_build_of_the_ladder", stock, STOCK_SHA,
                 "yes" if stock == STOCK_SHA else "no",
                 "the source tree and the toolchain here rebuild the binary the ladder called stock")

        for attempt in want:
            seed = rows[attempt]
            params = json.load(open(os.path.join(S, "scratch", "parameters-stock.json")))
            params["global"]["VOL_SIZE_X"] = shape[2]
            params["global"]["VOL_SIZE_Y"] = shape[1]
            params["global"]["VOL_SIZE_Z"] = shape[0]
            params["seed"]["SEED_X"] = int(seed["seed_x"])
            params["seed"]["SEED_Y"] = int(seed["seed_y"])
            params["seed"]["SEED_Z"] = int(seed["seed_z"])
            with open(os.path.join(BUILD, "parameters.json"), "w") as handle:
                json.dump(params, handle, indent=2)
            t0 = time.monotonic()
            log = os.path.join(S, "log", "build-%s.txt" % attempt)
            with open(log, "wb") as handle:
                rc = subprocess.call(
                    "python3 parse_parameters.py > /dev/null && make -j%d "
                    "BLOSC2_PREFIX=/data/opt/blosc2 LIBTIFF_PREFIX=/data/opt/libtiff RPATH=1 "
                    "simpaper10" % JOBS,
                    shell=True, cwd=BUILD, stdout=handle, stderr=subprocess.STDOUT)
            if rc != 0:
                raise SystemExit("build failed for %s, see %s" % (attempt, log))
            sha = sha256(os.path.join(BUILD, "simpaper10"))
            binroot = os.path.join(S, "scratch", "bin", attempt)
            os.makedirs(binroot, exist_ok=True)
            shutil.copy2(os.path.join(BUILD, "simpaper10"), os.path.join(binroot, "simpaper10"))
            recorded = seed["build_sha256"]
            gate_row(w, attempt, "differs_from_stock", sha, STOCK_SHA,
                     "yes" if sha != STOCK_SHA else "no",
                     "the seed and volume parameters of this attempt reached the binary and changed it")
            gate_row(w, attempt, "matches_ladder_sha256", sha, recorded,
                     "yes" if sha == recorded else "no",
                     "this rebuild is byte for byte the binary seed-ladder-1447 ran for this seed")
            f.flush()
            print("%s built in %.1f s, sha %s, differs from stock %s, matches the ladder %s"
                  % (attempt, time.monotonic() - t0, sha[:8],
                     "yes" if sha != STOCK_SHA else "no",
                     "yes" if sha == recorded else "no"), flush=True)
    print("binary gate written to %s" % out, flush=True)


if __name__ == "__main__":
    sys.exit(main())
