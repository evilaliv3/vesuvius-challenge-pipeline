# This file is a copy of tools/cpp_gen24.py of the working tree and differs from it in three ways:
# the run folder of the working tree is this folder (the binaries under build/driver/, the
# estimates in evidence/ beside everything else, the scratch files under build/), the block
# labels are the English ones the files here carry, and the two phase names, the docstring and
# what it prints are in English. Nothing that computes is changed.
"""The twenty four scroll run and the exponent ablation, recomputed by calling the C++.

The rule was written before the runs: inputs/declaration-cpp-two-runs.md. The design (one seed per
slice in run A, twenty in run B), the guard, the order and the stopping rule come from there.

  python3 tools/cpp_gen24.py gen24      # 2,304 calls, 24 scrolls, needs inputs/grid23/
  python3 tools/cpp_gen24.py exponent   # 21,600 calls, p = 0.5, 1.5 and 2, needs inputs/grid15/

The estimates go to evidence/. The scoring is done by the existing tools, cpp_gen24_score.py and
cpp_exponent_score.py, which are not rewritten: so the only thing that differs between the two
arms is who produced x and y.
"""
import argparse
import csv
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L          # noqa: E402

BUILD = os.path.join(L.SRC, "build", "driver")     # where driver/build.sh puts the binaries
EV = L.EV                                          # the estimates live beside the other evidence
NG = L.NG
GUARD_S = 600                                  # declaration 2, section 4
SEEDS24 = (20260915, 7, 123456)                # those of the transcription's run, unchanged
TABLE_SEED = L.TABLE_SEED
K = 20
EXPONENTS = ("0.5", "1.5", "2.0")              # p = 1 and the weighted mean already exist in C++


def call(exe, scroll, z, seed, cache):
    """One estimate: one process, one slice, one seed, under the wall clock guard."""
    out = os.path.join(L.SRC, "build", "driver-tmp", f"{os.path.basename(exe)}-{scroll}-{z}-{seed}")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = [exe, "-i", os.path.join(NG, cache, scroll), "--slices", str(z),
           "--seed", str(seed), "--repeats", "1", "-o", out + ".json", "--csv", out + ".csv"]
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               OPENCV_FOR_THREADS_NUM="1", MKL_NUM_THREADS="1")
    t0 = time.perf_counter()
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=GUARD_S, check=True, env=env)
    except subprocess.TimeoutExpired:
        return None, round(time.perf_counter() - t0, 2), 1
    except subprocess.CalledProcessError:
        return None, round(time.perf_counter() - t0, 2), 0
    seconds = round(time.perf_counter() - t0, 2)
    try:
        with open(out + ".csv") as fh:
            row = next(csv.DictReader(fh))
    except (OSError, StopIteration):
        return None, seconds, 0
    finally:
        for suffix in (".csv", ".json"):
            try:
                os.remove(out + suffix)
            except OSError:
                pass
    return row, seconds, 0


# ----------------------------------------------------------------- run A, twenty four scrolls

def _gen24_task(t):
    scroll, z, variant, seed, tag = t
    exe = os.path.join(BUILD, f"vc_gen_umbilicus-{variant}")
    row, seconds, guard = call(exe, scroll, z, seed - z, "grid23")
    if guard or row is None:
        return dict(scroll=scroll, z=z, variant=variant, seed=seed, role=tag,
                    x="", y="", width="", height="", inside="", capped=0,
                    guard=guard, seconds=seconds)
    return dict(scroll=scroll, z=z, variant=variant, seed=seed, role=tag,
                x=round(float(row["grid_x"]), 2), y=round(float(row["grid_y"]), 2),
                width=float(row["grid_width"]), height=float(row["grid_height"]),
                inside=int(row["inside"]), capped=0, guard=0, seconds=seconds)


def gen24(workers):
    """576 slices by two variants at one seed, plus two more seeds on the weighted sum."""
    cols = ["scroll", "z", "variant", "seed", "role", "x", "y", "width", "height",
            "inside", "capped", "guard", "seconds"]
    raw = os.path.join(EV, "cpp-positions-24.csv")
    os.makedirs(EV, exist_ok=True)
    done = set()
    if os.path.exists(raw):
        for r in L.read_csv(raw):
            done.add((r["scroll"], int(r["z"]), r["variant"], int(r["seed"])))
    else:
        with open(raw, "w", newline="") as fh:
            csv.DictWriter(fh, cols).writeheader()

    tasks = []
    for scroll in sorted(os.listdir(os.path.join(NG, "grid23"))):
        d = os.path.join(NG, "grid23", scroll)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".grid") or not os.path.getsize(os.path.join(d, f)):
                continue
            z = int(f[:-5])
            for variant in ("as-is", "no-division"):
                t = (scroll, z, variant, SEEDS24[0] + z, "position")
                if (scroll, z, variant, SEEDS24[0] + z) not in done:
                    tasks.append(t)
            for s in SEEDS24[1:]:
                if (scroll, z, "no-division", s + z) not in done:
                    tasks.append((scroll, z, "no-division", s + z, "spread"))
    run(tasks, _gen24_task, raw, cols, workers)


# ------------------------------------------------------------------- run B, the exponent

def _exp_task(t):
    scroll, z, k, p = t
    exe = os.path.join(BUILD, f"vc_gen_umbilicus-p{p}")
    seed = TABLE_SEED + z + 1000 * k
    row, seconds, guard = call(exe, scroll, z, seed - z, "grid15")
    if guard or row is None:
        return dict(scroll=scroll, z=z, k=k, seed=seed, p=p, x="", y="", inside="",
                    capped=0, guard=guard, seconds=seconds)
    return dict(scroll=scroll, z=z, k=k, seed=seed, p=p,
                x=float(row["grid_x"]), y=float(row["grid_y"]),
                inside=int(row["inside"]), capped=0, guard=0, seconds=seconds)


def exponent(workers):
    cols = ["scroll", "z", "k", "seed", "p", "x", "y", "inside", "capped", "guard", "seconds"]
    raw = os.path.join(EV, "cpp-exponent-estimates.csv")
    os.makedirs(EV, exist_ok=True)
    done = set()
    if os.path.exists(raw):
        for r in L.read_csv(raw):
            done.add((r["scroll"], int(r["z"]), int(r["k"]), r["p"]))
    else:
        with open(raw, "w", newline="") as fh:
            csv.DictWriter(fh, cols).writeheader()

    scrolls = [s for s in L.CFG if L.CFG[s]["block"] == "primary"] + \
              [s for s in L.CFG if L.CFG[s]["block"] == "confirmation"]
    tasks = []
    for p in EXPONENTS:
        for scroll in scrolls:
            for z in L.heights(scroll):
                if not os.path.exists(os.path.join(NG, "grid15", scroll, f"{z:06d}.grid")):
                    continue
                for k in range(K):
                    if (scroll, z, k, p) not in done:
                        tasks.append((scroll, z, k, p))
    run(tasks, _exp_task, raw, cols, workers)


def run(tasks, fn, raw, cols, workers):
    print(f"{len(tasks)} estimates to make, {workers} processes", flush=True)
    t0 = time.perf_counter()
    written = 0
    with open(raw, "a", newline="") as fh:
        w = csv.DictWriter(fh, cols)
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for r in pool.map(fn, tasks, chunksize=4):
                if r is None:
                    continue
                w.writerow(r)
                written += 1
                if written % 200 == 0:
                    fh.flush()
                    el = time.perf_counter() - t0
                    rate = written / el
                    print(f"  {written}/{len(tasks)} in {el/60:.1f} min, {rate*60:.0f}/min, "
                          f"{(len(tasks)-written)/rate/60:.0f} min left", flush=True)
    print(f"written {raw} in {(time.perf_counter()-t0)/60:.1f} min", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["gen24", "exponent"])
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    (gen24 if a.phase == "gen24" else exponent)(a.workers)


if __name__ == "__main__":
    main()
