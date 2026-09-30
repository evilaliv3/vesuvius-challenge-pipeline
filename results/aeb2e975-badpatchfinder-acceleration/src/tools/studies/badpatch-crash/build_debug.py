#!/usr/bin/env python3
"""Rebuild PHerc1447-seed34's simpaper10 by the route of seed-search-1447/tools/build_binaries.py,
once as that route builds it (gate: sha256 equal to the binary that crashed) and once with -g
added to CFLAGS and nothing else changed (gate: differs from the plain build, same source).

Only CFLAGS changes between the two builds: -O3 is kept, -g is appended.
"""
import csv, hashlib, json, os, shlex, subprocess, sys, time

HERE = "/data/scrollagent/runs/rev1/badpatch-crash"
BUILD = os.path.join(HERE, "scratch", "src", "build", "corrected")
MANIFESTS = "/data/scrollagent/pipeline/datasets/manifests"
LADDER = "/data/scrollagent/runs/rev1/seed-ladder-1447/evidence/attempts.csv"
CRASHED = "/data/scrollagent/runs/rev1/seed-search-1447/scratch/bin/PHerc1447-seed34/simpaper10"
ATTEMPT = "PHerc1447-seed34"
JOBS = 4
CF_PLAIN = "-O3 -w -fopenmp -ffp-contract=off $(ARCHFLAGS) -I$(BLOSC2_PREFIX)/include -I$(LIBTIFF_PREFIX)/include"
CF_DEBUG = "-O3 -g -w -fopenmp -ffp-contract=off $(ARCHFLAGS) -I$(BLOSC2_PREFIX)/include -I$(LIBTIFF_PREFIX)/include"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def seed_row():
    with open(LADDER) as f:
        for r in csv.DictReader(f):
            if r["attempt"] == ATTEMPT and r["scroll"] == "PHerc1447":
                return r
    raise SystemExit("no ladder row for " + ATTEMPT)


def build(cflags, tag):
    log = os.path.join(HERE, "log", "build-%s.txt" % tag)
    subprocess.check_call("make -j%d clean_objects 2>/dev/null || rm -f *.o simpaper10" % JOBS,
                          shell=True, cwd=BUILD)
    t0 = time.monotonic()
    with open(log, "wb") as h:
        rc = subprocess.call(
            'python3 parse_parameters.py > /dev/null && make -j%d '
            'BLOSC2_PREFIX=/data/opt/blosc2 LIBTIFF_PREFIX=/data/opt/libtiff RPATH=1 '
            'CFLAGS=%s simpaper10' % (JOBS, shlex.quote(cflags)),
            shell=True, cwd=BUILD, stdout=h, stderr=subprocess.STDOUT)
    if rc != 0:
        raise SystemExit("build %s failed, see %s" % (tag, log))
    out = os.path.join(HERE, "scratch", "bin", tag)
    os.makedirs(out, exist_ok=True)
    dst = os.path.join(out, "simpaper10")
    subprocess.check_call(["cp", "-p", os.path.join(BUILD, "simpaper10"), dst])
    print("%s built in %.1f s" % (tag, time.monotonic() - t0), flush=True)
    return dst


def main():
    os.makedirs(os.path.join(HERE, "log"), exist_ok=True)
    shape = json.load(open(os.path.join(MANIFESTS, "PHerc1447.json")))["shape"]
    seed = seed_row()
    params = json.load(open(os.path.join(HERE, "scratch", "parameters-stock.json")))
    params["global"]["VOL_SIZE_X"] = shape[2]
    params["global"]["VOL_SIZE_Y"] = shape[1]
    params["global"]["VOL_SIZE_Z"] = shape[0]
    params["seed"]["SEED_X"] = int(seed["seed_x"])
    params["seed"]["SEED_Y"] = int(seed["seed_y"])
    params["seed"]["SEED_Z"] = int(seed["seed_z"])
    with open(os.path.join(BUILD, "parameters.json"), "w") as h:
        json.dump(params, h, indent=2)

    plain = build(CF_PLAIN, "plain")
    debug = build(CF_DEBUG, "debug")
    s_crash, s_plain, s_debug = sha256(CRASHED), sha256(plain), sha256(debug)
    rec = seed["build_sha256"]

    with open(os.path.join(HERE, "evidence", "binary-gate.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["binary", "path", "cflags", "sha256", "expectation", "expected_value",
                    "passes", "what_it_proves"])
        w.writerow(["crashed", CRASHED, CF_PLAIN, s_crash, "equals_the_ladder_record", rec,
                    "yes" if s_crash == rec else "no",
                    "the binary that crashed is the one seed-ladder-1447 recorded for seed34"])
        w.writerow(["plain", plain, CF_PLAIN, s_plain, "equals_the_crashed_binary", s_crash,
                    "yes" if s_plain == s_crash else "no",
                    "this tree and this route rebuild the binary that crashed, byte for byte"])
        w.writerow(["debug", debug, CF_DEBUG, s_debug, "differs_from_the_plain_build", s_plain,
                    "yes" if s_debug != s_plain else "no",
                    "the only change is -g appended to CFLAGS, so the difference is the symbols"])
    for n, s in (("crashed", s_crash), ("plain", s_plain), ("debug", s_debug)):
        print("%-8s %s" % (n, s))
    print("plain == crashed:", s_plain == s_crash)


if __name__ == "__main__":
    sys.exit(main())
