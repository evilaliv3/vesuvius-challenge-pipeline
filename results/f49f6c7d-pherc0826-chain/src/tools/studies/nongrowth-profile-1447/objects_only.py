#!/usr/bin/env python3
"""objects_only.py <series corrected|delivered>: nongrowth-profile-1447 (DECLARATION.md), the check behind saving 2.

1. Counts the object files of this study's full per seed rebuild (scratch/src-<series>-cpu, built for seed1111 by
   tools/replay_build.py) that are byte for byte those of seeds-at-scale-1447/scratch/src/build/<series> (built last for
   whatever seed the chain built last): an object equal across two seeds does not depend on the seed.
2. In a fresh cp -a copy of seeds-at-scale-1447/scratch/src, writes seed1111's parameters.json exactly as
   replay_build.py does, runs parse_parameters.py, then compiles ONLY the objects that differed in 1 with the build's
   own flags and links with the makefile's link line; the binary's sha256 is compared with the delivered per seed
   binary. CPU of this partial build (user + sys of the children) beside the full rebuild's from evidence/cpu-runs.csv.
Writes evidence/build-objects-only.csv (one row per series; rows of other series are kept).
"""
import csv, filecmp, glob, hashlib, json, os, resource, shutil, subprocess, sys

TOOL = "nongrowth-profile-1447/tools/objects_only.py"
ST = "/data/scrollagent/runs/rev1/nongrowth-profile-1447"
F = "/data/scrollagent/runs/rev1/seeds-at-scale-1447"
A = "PHerc1447-seed1111"
FLAGS = "-O3 -w -fopenmp -ffp-contract=off  -I/data/opt/blosc2/include -I/data/opt/libtiff/include"
LINK = ("-lblosc2 -ltiff -L/data/opt/blosc2/lib -L/data/opt/libtiff/lib -Wl,-rpath,/data/opt/blosc2/lib "
        "-Wl,-rpath,/data/opt/libtiff/lib")
OUT = ST + "/evidence/build-objects-only.csv"
COLS = ["tool", "series", "objects", "objects_equal_across_seeds", "objects_recompiled", "partial_build_cpu_s",
        "full_rebuild_cpu_s", "binary_sha256", "delivered_binary_sha256", "binary_identical"]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    series = sys.argv[1]
    full = "%s/scratch/src-%s-cpu/build/%s" % (ST, series, series)
    shared = "%s/scratch/src/build/%s" % (F, series)
    objs = sorted(os.path.basename(p) for p in glob.glob(full + "/*.o"))
    diff = [o for o in objs if not filecmp.cmp(os.path.join(full, o), os.path.join(shared, o), shallow=False)]
    copy = "%s/scratch/src-%s-objonly" % (ST, series)
    shutil.rmtree(copy, ignore_errors=True)
    subprocess.run(["cp", "-a", F + "/scratch/src", copy], check=True)
    b = "%s/build/%s" % (copy, series)
    sys.path.insert(0, ST + "/tools")
    # parameters exactly as replay_build.py writes them
    L = [l for l in open(F + "/evidence/seeds-PHerc1447-draw1500.csv") if not l.lstrip('"').startswith("#")]
    seed = [r for r in csv.DictReader(L) if r["attempt"] == A][0]
    shape = json.load(open("/data/scrollagent/pipeline/datasets/manifests/PHerc1447.json"))["shape"]
    params = json.load(open(F + "/scratch/parameters-stock.json"))
    params["global"]["VOL_SIZE_X"], params["global"]["VOL_SIZE_Y"], params["global"]["VOL_SIZE_Z"] = shape[2], shape[1], shape[0]
    params["seed"]["SEED_X"], params["seed"]["SEED_Y"], params["seed"]["SEED_Z"] = (int(seed["seed_x"]), int(seed["seed_y"]), int(seed["seed_z"]))
    with open(b + "/parameters.json", "w") as h:
        json.dump(params, h, indent=2)
    r0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    cmds = ["python3 parse_parameters.py > /dev/null"]
    cmds += ["g++ -c %s %s" % (o[:-2] + (".c" if os.path.exists(os.path.join(b, o[:-2] + ".c")) else ".cpp"), FLAGS) for o in diff]
    link = [l for l in open(b + "/makefile") if l.startswith("simpaper10:")][0].split(":", 1)[1].split()
    cmds.append("g++ -o simpaper10 %s %s %s" % (" ".join(link), FLAGS, LINK))
    for c in cmds:
        subprocess.run(c, shell=True, cwd=b, check=True)
    r1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (r1.ru_utime - r0.ru_utime) + (r1.ru_stime - r0.ru_stime)
    got = sha(b + "/simpaper10")
    ref = sha("%s/scratch/%s/%s/simpaper10" % (F, "bin" if series == "corrected" else "bin-delivered", A))
    fr = [x for x in csv.DictReader([l for l in open(ST + "/evidence/cpu-runs.csv") if not l.startswith('"#')])
          if x["stage"] == "build_" + series]
    row = [TOOL, series, len(objs), len(objs) - len(diff), " ".join(diff), "%.2f" % cpu, fr[-1]["cpu_s"], got, ref,
           "yes" if got == ref else "no"]
    keep = []
    if os.path.exists(OUT):
        keep = [x for x in csv.reader([l for l in open(OUT) if not l.startswith('"#')])][1:]
        keep = [x for x in keep if x[1] != series]
    with open(OUT, "w", newline="") as f:
        f.write('"# written by %s: per seed build with only the objects that differ across seeds recompiled"\n' % TOOL)
        w = csv.writer(f, lineterminator="\n")
        w.writerow(COLS); w.writerows(keep + [row])
    print(dict(zip(COLS, row)))
    shutil.rmtree(copy)


if __name__ == "__main__":
    main()
