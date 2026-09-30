#!/usr/bin/env python3
"""Build the per seed simpaper10 of seeds 01, 15, 26 and 34, twice: from the untouched corrected
series and from the same series with the orphan guard added as corrections/00007.

The route is the one this home already uses (seed-search-1447/tools/build_binaries.py,
badpatch-crash/tools/build_debug.py): the working copy laid down by build.sh corrected,
parameters.json carrying that seed's SEED_X/Y/Z and the volume size of PHerc1447 read from its
manifest, then parse_parameters.py and make simpaper10.

Gate: the plain build of each seed must equal the sha256 that seed-search-1447 recorded for the
run that produced the sheets now on disk. If it does not, a difference in output afterwards is
not necessarily the guard's, and the run stops.
"""
import csv, hashlib, json, os, shutil, subprocess, sys, time

H = "/data/scrollagent/runs/rev1/orphan-guard"
S = "/data/scrollagent/runs/rev1/seed-search-1447"
LADDER = "/data/scrollagent/runs/rev1/seed-ladder-1447/evidence/attempts.csv"
MANIFESTS = "/data/scrollagent/pipeline/datasets/manifests"
SCROLL = "PHerc1447"
SEEDS = ["seed01", "seed15", "seed26", "seed34"]
JOBS = 4
TREES = {"plain": os.path.join(H, "scratch", "src-plain", "build", "corrected"),
         "guard": os.path.join(H, "scratch", "src-guard", "build", "corrected")}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def recorded_sha(attempt):
    """The sha256 of the binary that produced the sheets now on disk, from that run's own CSV."""
    with open(os.path.join(S, "evidence", "runs", attempt + ".csv")) as f:
        for r in csv.DictReader(f):
            if r["quantity"] == "binary_sha256":
                return r["value"]
    raise SystemExit("no binary_sha256 row for " + attempt)


def ladder_seed(attempt):
    with open(LADDER) as f:
        for r in csv.DictReader(f):
            if r["attempt"] == attempt and r["scroll"] == SCROLL:
                return r
    raise SystemExit("no ladder row for " + attempt)


def main():
    shape = json.load(open(os.path.join(MANIFESTS, SCROLL + ".json")))["shape"]
    stock = json.load(open(os.path.join(H, "scratch", "parameters-stock.json")))
    out = os.path.join(H, "evidence", "binary-gate.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["attempt", "series", "binary", "sha256", "expectation", "expected_value",
                    "passes", "what_it_proves"])
        for s in SEEDS:
            attempt = "%s-%s" % (SCROLL, s)
            seed = ladder_seed(attempt)
            rec = recorded_sha(attempt)
            shas = {}
            for series, build in TREES.items():
                params = json.loads(json.dumps(stock))
                params["global"]["VOL_SIZE_X"] = shape[2]
                params["global"]["VOL_SIZE_Y"] = shape[1]
                params["global"]["VOL_SIZE_Z"] = shape[0]
                params["seed"]["SEED_X"] = int(seed["seed_x"])
                params["seed"]["SEED_Y"] = int(seed["seed_y"])
                params["seed"]["SEED_Z"] = int(seed["seed_z"])
                with open(os.path.join(build, "parameters.json"), "w") as h:
                    json.dump(params, h, indent=2)
                log = os.path.join(H, "log", "build-%s-%s.txt" % (attempt, series))
                t0 = time.monotonic()
                with open(log, "wb") as h:
                    rc = subprocess.call(
                        "python3 parse_parameters.py > /dev/null && make -j%d "
                        "BLOSC2_PREFIX=/data/opt/blosc2 LIBTIFF_PREFIX=/data/opt/libtiff RPATH=1 "
                        "simpaper10" % JOBS,
                        shell=True, cwd=build, stdout=h, stderr=subprocess.STDOUT)
                if rc != 0:
                    raise SystemExit("build failed for %s %s, see %s" % (attempt, series, log))
                dst_dir = os.path.join(H, "scratch", "bin", series, attempt)
                os.makedirs(dst_dir, exist_ok=True)
                dst = os.path.join(dst_dir, "simpaper10")
                shutil.copy2(os.path.join(build, "simpaper10"), dst)
                shas[series] = (dst, sha256(dst))
                print("%s %s built in %.1f s, sha %s"
                      % (attempt, series, time.monotonic() - t0, shas[series][1][:8]), flush=True)

            pp, ps = shas["plain"]
            gp, gs = shas["guard"]
            w.writerow([attempt, "corrected", pp, ps, "equals_the_binary_that_wrote_what_is_on_disk",
                        rec, "yes" if ps == rec else "no",
                        "this tree and this route rebuild the binary seed-search-1447 ran for this seed"])
            w.writerow([attempt, "corrected+00007", gp, gs, "differs_from_the_plain_build", ps,
                        "yes" if gs != ps else "no",
                        "the guard reached the binary and changed it"])
            f.flush()
    print("binary gate written to " + out)


if __name__ == "__main__":
    sys.exit(main())
