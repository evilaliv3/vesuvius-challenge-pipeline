# This file is a copy of tools/cpp_k20.py of the working tree and differs from it in three ways:
# the run folder of the working tree is this folder (the binaries under build/driver/, the
# estimates in evidence/ beside everything else, the scratch files under build/), the block
# labels are the English ones the files here carry, and the three phase names, the docstring
# and what it prints are in English. Nothing that computes is changed.
"""Tables III and IV recomputed by calling the compiled C++, not the transcription.

The rule was written before the run: inputs/declaration-cpp-comparison.md. The seeds, the guard,
the order of the scrolls, the criterion of agreement and what stops everything come from there.

Three phases, kept apart on purpose.

  python3 tools/cpp_k20.py estimates   # 14,400 calls to align_and_extract_umbilicus
  python3 tools/cpp_k20.py scores      # the estimates through the SAME code as fifteen_k20.score
  python3 tools/cpp_k20.py compare     # row by row against the frozen tables

The first phase needs nothing beyond the two binaries of driver/build.sh and the cut slices in
inputs/grid15/. The second and the third read the umbilicus bench archived at umbilicus-bench/,
because the score reloads the bench's masks for the centroid baseline; nothing has to be set.

The second phase computes nothing of its own: it imports `fifteen_k20` and feeds it the C++
estimates in place of the Python ones, so that metric, baselines, bootstrap, threshold and
verdicts are the same code on both arms and the only difference is who produced x and y.
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L          # noqa: E402

BUILD = os.path.join(L.SRC, "build", "driver")     # where driver/build.sh puts the binaries
EV = L.EV                                          # the estimates live beside the other evidence
RAW = os.path.join(EV, "cpp-k20-estimates.csv")
RAW_COLS = ["scroll", "z", "k", "seed", "variant", "x", "y", "inside", "capped",
            "guard", "seconds"]

K = 20
TABLE_SEED = L.TABLE_SEED          # 20260915, the same number as the frozen tables
GUARD_S = 600                      # declaration, section 5
GRID15 = os.path.join(L.NG, "grid15")
VARIANTS = ("as-is", "no-division")

# Order fixed in the declaration: the primary block first, then the confirmation block, each in
# the order of fifteen-config.json.
SCROLLS = [s for s in L.CFG if L.CFG[s]["block"] == "primary"] + \
          [s for s in L.CFG if L.CFG[s]["block"] == "confirmation"]


def one(task):
    """One estimate: one process, one slice, one seed, one variant, under the wall clock guard."""
    scroll, z, k, variant = task
    seed = TABLE_SEED + 1000 * k          # the driver adds z, so the seed is TABLE_SEED+z+1000k
    exe = os.path.join(BUILD, f"vc_gen_umbilicus-{variant}")
    out = os.path.join(L.SRC, "build", "driver-tmp", f"{scroll}-{z}-{k}-{variant}")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = [exe, "-i", os.path.join(GRID15, scroll), "--slices", str(z),
           "--seed", str(seed), "--repeats", "1",
           "-o", out + ".json", "--csv", out + ".csv"]
    # One thread per estimate: OpenCV and OpenBLAS otherwise open a pool the size of the machine,
    # and six processes reach eleven cores. The computation, which is scalar, is untouched.
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               OPENCV_FOR_THREADS_NUM="1", MKL_NUM_THREADS="1")
    t0 = time.perf_counter()
    guard = 0
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=GUARD_S, check=True, env=env)
    except subprocess.TimeoutExpired:
        guard = 1
    except subprocess.CalledProcessError:
        return None
    seconds = time.perf_counter() - t0
    if guard:
        return dict(scroll=scroll, z=z, k=k, seed=TABLE_SEED + z + 1000 * k, variant=variant,
                    x="", y="", inside="", capped=0, guard=1, seconds=round(seconds, 2))
    try:
        with open(out + ".csv") as fh:
            row = next(csv.DictReader(fh))
    except (OSError, StopIteration):
        return None
    finally:
        for suffix in (".csv", ".json"):
            try:
                os.remove(out + suffix)
            except OSError:
                pass
    return dict(scroll=scroll, z=z, k=k, seed=int(row["seed"]), variant=variant,
                x=float(row["grid_x"]), y=float(row["grid_y"]),
                inside=int(row["inside"]), capped=0, guard=0, seconds=round(seconds, 2))


def estimates(workers):
    os.makedirs(EV, exist_ok=True)
    done = set()
    if os.path.exists(RAW):
        with open(RAW) as fh:
            for r in csv.DictReader(fh):
                done.add((r["scroll"], int(r["z"]), int(r["k"]), r["variant"]))
    else:
        with open(RAW, "w", newline="") as fh:
            csv.DictWriter(fh, RAW_COLS).writeheader()

    tasks = []
    for scroll in SCROLLS:
        for z in L.heights(scroll):
            if not os.path.exists(os.path.join(GRID15, scroll, f"{z:06d}.grid")):
                continue
            for k in range(K):
                for variant in VARIANTS:
                    if (scroll, z, k, variant) not in done:
                        tasks.append((scroll, z, k, variant))
    print(f"{len(tasks)} estimates to make, {len(done)} already made, {workers} processes", flush=True)

    t0 = time.perf_counter()
    written = 0
    with open(RAW, "a", newline="") as fh:
        w = csv.DictWriter(fh, RAW_COLS)
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for r in pool.map(one, tasks, chunksize=4):
                if r is None:
                    continue
                w.writerow(r)
                written += 1
                if written % 200 == 0:
                    fh.flush()
                    el = time.perf_counter() - t0
                    rate = written / el
                    print(f"  {written}/{len(tasks)} in {el/60:.1f} min, "
                          f"{rate*60:.0f}/min, {(len(tasks)-written)/rate/60:.0f} min left",
                          flush=True)
    print(f"written {RAW} in {(time.perf_counter()-t0)/60:.1f} min", flush=True)


def scores():
    import fifteen_k20 as F

    raw_all = []
    with open(RAW) as fh:
        for r in csv.DictReader(fh):
            if int(r["guard"]):
                raw_all.append(dict(scroll=r["scroll"], z=int(r["z"]), k=int(r["k"]),
                                    variant=r["variant"], guard=1))
                continue
            raw_all.append(dict(scroll=r["scroll"], z=int(r["z"]), k=int(r["k"]),
                                seed=int(r["seed"]), variant=r["variant"],
                                x=float(r["x"]), y=float(r["y"]),
                                inside=int(r["inside"]), capped=0, guard=0))

    guarded = [r for r in raw_all if r.get("guard")]
    if guarded:
        by = {}
        for r in guarded:
            by.setdefault((r["scroll"], r["variant"]), []).append(r["z"])
        print("ESTIMATES THAT MET THE GUARD (rows that do not reproduce, declaration section 5):")
        for key, zs in sorted(by.items()):
            print(f"  {key[0]} {key[1]}: {len(zs)} estimates, slices {sorted(set(zs))}")

    rows = []
    incomplete = []
    for scroll in SCROLLS:
        raw = [r for r in raw_all if r["scroll"] == scroll and not r.get("guard")]
        if not raw:
            continue
        # A slice enters the score only with all twenty estimates of both variants: a half done
        # slice would leave zeros in the polyline fifteen_k20.score builds.
        have = {}
        for r in raw:
            have[(r["z"], r["variant"])] = have.get((r["z"], r["variant"]), 0) + 1
        full = {z for z in {r["z"] for r in raw}
                if all(have.get((z, v), 0) == K for v in VARIANTS)}
        dropped = sorted({r["z"] for r in raw} - full)
        if dropped:
            incomplete.append((scroll, "incomplete slices", dropped))
        raw = [r for r in raw if r["z"] in full]
        if not raw:
            continue
        rows += F.score(scroll, raw)

    os.makedirs(EV, exist_ok=True)
    out = os.path.join(EV, "cpp-k20.csv")
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"written {out}: {len(rows)} rows")

    verdicts = {"primary": F.verdict(rows, "primary", 4, 3),
                "confirmation": F.verdict(rows, "confirmation", 8, 6)}
    with open(os.path.join(EV, "cpp-k20-verdicts.json"), "w") as fh:
        json.dump(verdicts, fh, indent=1)

    if incomplete:
        print("INCOMPLETE ARMS (scroll, what, slices):", incomplete)
    return rows, verdicts


FROZEN = os.path.join(L.EV, "fifteen-k20.csv")
FROZEN_VERDICTS = os.path.join(L.EV, "fifteen-k20-verdicts.json")


def compare():
    """Row by row, the C++ against the transcription, by the criterion of declaration section 4."""
    py = {(r["scroll"], r["variant"]): r for r in L.read_csv(FROZEN)}
    cpp = {(r["scroll"], r["variant"]): r for r in L.read_csv(os.path.join(EV, "cpp-k20.csv"))}
    frozen_v = json.load(open(FROZEN_VERDICTS))
    cpp_v = json.load(open(os.path.join(EV, "cpp-k20-verdicts.json")))

    out = []
    stop = []
    for key in sorted(cpp):
        if key not in py:
            continue
        a, b = py[key], cpp[key]
        med_py, med_cpp = float(a["median_mm"]), float(b["median_mm"])
        in_py = float(a["ci_lo_mm"]) <= med_cpp <= float(a["ci_hi_mm"])
        in_cpp = float(b["ci_lo_mm"]) <= med_py <= float(b["ci_hi_mm"])
        flags = all(a[f] == b[f] for f in ("margin_ci_includes_zero", "margin_ci_below_threshold"))
        full_py = int(a["inside"]) == int(a["inside_of"])
        full_cpp = int(b["inside"]) == int(b["inside_of"])
        agree = in_py and in_cpp and flags and full_py == full_cpp

        mpy, mcpp = float(a["margin_vs_centroid_mm"]), float(b["margin_vs_centroid_mm"])
        moves = []
        if (mpy > 0) != (mcpp > 0):
            moves.append("the margin changes sign")
        if (mpy >= L.THRESHOLD_MM) != (mcpp >= L.THRESHOLD_MM):
            moves.append("the margin crosses the threshold upwards")
        # The threshold has two sides: -0.30 mm is the one that decides `loses`. The first draft of
        # this check looked only at the positive side and would have missed a real crossing; added
        # on 2026-09-18 after the run, and it makes the check stricter, not looser.
        if (mpy <= -L.THRESHOLD_MM) != (mcpp <= -L.THRESHOLD_MM):
            moves.append("the margin crosses the threshold downwards")
        if a["margin_ci_includes_zero"] == "0" and b["margin_ci_includes_zero"] == "1":
            moves.append("the interval of the margin comes to include zero")
        if key[1] == "no-division" and full_py and not full_cpp:
            moves.append("inside on every slice no longer holds")
        if moves:
            stop.append((key, moves))

        out.append(dict(scroll=key[0], variant=key[1],
                        median_py_mm=med_py, median_cpp_mm=med_cpp,
                        delta_mm=round(med_cpp - med_py, 2),
                        ci_py=f"{a['ci_lo_mm']}..{a['ci_hi_mm']}",
                        ci_cpp=f"{b['ci_lo_mm']}..{b['ci_hi_mm']}",
                        cpp_in_py_ci=int(in_py), py_in_cpp_ci=int(in_cpp),
                        flags_equal=int(flags),
                        inside_transcription=f"{a['inside']}/{a['inside_of']}",
                        inside_shipped=f"{b['inside']}/{b['inside_of']}",
                        margin_py_mm=mpy, margin_cpp_mm=mcpp,
                        agree=int(agree), moves_a_verdict="; ".join(moves)))

    L.write_csv(os.path.join(EV, "cpp-vs-transcription.csv"), list(out[0]), out)
    n_agree = sum(r["agree"] for r in out)
    print(f"rows compared: {len(out)}, in agreement: {n_agree}")
    for r in out:
        if not r["agree"]:
            print(f"  DIFFERS {r['scroll']:12s} {r['variant']:12s} "
                  f"{r['median_py_mm']:8.2f} -> {r['median_cpp_mm']:8.2f} mm "
                  f"(delta {r['delta_mm']:+.2f}) ci_py {r['ci_py']} ci_cpp {r['ci_cpp']} "
                  f"inside {r['inside_transcription']} -> {r['inside_shipped']}")

    # Inside the grid, by OBJECTIVE and not by implementation. The word "arm" names two different
    # axes in this work (transcription against shipped function on one, weighted mean against
    # weighted sum on the other) and a sentence that does not say which axis it describes can hand
    # one the number of the other: it happened on 2026-09-18. Here the objective is written into
    # the printed line.
    for variant, objective in (("as-is", "weighted mean, as published"),
                               ("no-division", "weighted sum, this patch")):
        tot_in = sum(int(cpp[k]["inside"]) for k in cpp if k[1] == variant)
        tot_of = sum(int(cpp[k]["inside_of"]) for k in cpp if k[1] == variant)
        print(f"inside the grid, {objective} ({variant}): {tot_in} of {tot_of}, "
              f"outside {tot_of - tot_in}")

    same_verdicts = True
    for block in ("primary", "confirmation"):
        for field in ("repair", "beat", "repaired", "beats", "loses", "zero_outside",
                      "never_double", "beats_scrolls"):
            if frozen_v[block][field] != cpp_v[block][field]:
                same_verdicts = False
                print(f"  VERDICT {block}.{field}: {frozen_v[block][field]} -> {cpp_v[block][field]}")
    print("verdicts identical" if same_verdicts else "VERDICTS CHANGED")

    if stop or not same_verdicts:
        print("\nOUTCOME C of the declaration: something moves a verdict, everything stops.")
        for key, moves in stop:
            print(f"  {key[0]} {key[1]}: {'; '.join(moves)}")
    elif n_agree == len(out):
        print("\nOUTCOME A: every row in agreement, the transcription was faithful.")
    else:
        print("\nOUTCOME B: some rows differ, no verdict moves.")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["estimates", "scores", "compare"])
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    if a.phase == "estimates":
        estimates(a.workers)
    elif a.phase == "scores":
        scores()
    else:
        compare()


if __name__ == "__main__":
    main()
