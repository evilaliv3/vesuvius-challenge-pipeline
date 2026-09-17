# This file is a copy of tools/rev1_lib.py of the working tree and differs from it in one way
# only: the absolute paths of the machine the measurements ran on are replaced by paths inside
# this folder, resolved from the file's own location, with environment variables kept as
# overrides for the working tree (UMBILICUS_SRC, UMBILICUS_BENCH, VILLA_UPSTREAM). Nothing else
# is changed. Set none of them to run this folder: every default resolves inside it.
"""Shared pieces of the revision tools, so that no two of them can read two inputs.

Everything here reads the frozen run under inputs/ read-only: the transcription
villa_estimator.py, the cached grid slices of the fifteen scrolls (grid15/) and of the competition
set (grid23/), fifteen-config.json and the references. Nothing is written there.

The estimator is re-exposed with three knobs the frozen paper never turned: the constant of the
weight, 1/max(c, d) with c = 100 in the C++; its exponent, 1/max(c, d)^p with p = 1 in the C++,
added on 2026-09-18 for the exponent ablation; and the search, either villa's own walk
(cpp:119-142, transcribed in villa_estimator.estimate) or the pattern search rewritten for the
search ablation of Section VII. With c = 100, p = 1 and the original
search, `estimate` is villa_estimator.estimate to the bit, and rev1_selftest() asserts it.
"""
import csv
import json
import os
import sys

import numpy as np

SRC = os.environ.get("UMBILICUS_SRC") or os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))
NG = os.path.join(SRC, "inputs")
# the umbilicus bench, which only baselines() and errors() need. The frozen copy the article's
# numbers were measured against is archived in this folder at umbilicus-bench/, so this default
# resolves with nothing set and no clone; UMBILICUS_BENCH is the override the working tree uses
# to point at the living copy it keeps outside this repository.
BENCH = os.environ.get("UMBILICUS_BENCH") or os.path.join(SRC, "umbilicus-bench")
# a clone of ScrollPrize/villa, read for the commit the stand-in build compiled from
VILLA_UPSTREAM = os.environ.get("VILLA_UPSTREAM") or os.path.join(SRC, "villa")
# Where a figure tool puts what it draws. The rendered figures are delivered inside
# ../article.pdf, so this folder keeps no copy of them: build/ is written by a run and is
# not part of the source.
FIGURES = os.path.join(SRC, "build", "figures")
EV = os.path.join(SRC, "evidence")
LOGS = os.path.join(SRC, "logs")
sys.path.insert(0, BENCH)
sys.path.insert(0, NG)
import villa_estimator as ve                      # noqa: E402
from gridstore import read_grid, segments         # noqa: E402

CFG = json.load(open(os.path.join(NG, "fifteen-config.json")))
PRIMARY = [s for s in CFG if CFG[s]["block"] == "primary"]
CONFIRM = [s for s in CFG if CFG[s]["block"] == "confirmation"]
N_HEIGHTS = 24
TABLE_SEED = 20260915                             # seed of the frozen tables, plus z
THRESHOLD_MM = 0.30                               # preregistration-fifteen-references.md section 5


# ------------------------------------------------------------------ the estimator, with knobs

def weights(d, c=100.0, p=1.0):
    """The weight of cpp:112 with its exponent exposed: 1/max(c, d)^p. p=1 is the C++.

    p == 1.0 takes the original expression and not `** 1.0`, so that the default is the same
    computation to the bit and no existing number can move by an ULP.
    """
    m = np.maximum(c, d)
    return 1.0 / m if p == 1.0 else 1.0 / m ** p


def refine_score(cand, mid, nrm, divide, c=100.0, block=256, p=1.0):
    """cpp:98-117 with the constant and the exponent of the weight exposed. c=100, p=1 is the C++."""
    cand = np.atleast_2d(np.asarray(cand, float))
    out = np.empty(len(cand))
    for s in range(0, len(cand), block):
        cos2, d = ve._cos2(cand[s:s + block], mid, nrm)
        w = weights(d, c, p)
        num = (cos2 * w).sum(1)
        out[s:s + block] = num / w.sum(1) if divide else num
    return out


def sample(mid, nrm, seed):
    """cpp:52-55: N_SAMPLES draws with replacement, whatever the size of the pool.

    villa_estimator.sample capped the draw at the pool size (min(N_SAMPLES, len(mid))), which on
    a slice with fewer than 10000 segments is a different and noisier estimator than the C++
    (found by the numerical audit of 2026-09-16: 8 of the 360 table slices, 7 of them on
    PHerc0332). Everything under tools/ samples through this function.
    """
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(mid), ve.N_SAMPLES)
    return mid[idx].astype(float), nrm[idx].astype(float), rng


def estimate(mid, nrm, W, H, seed, divide, c=100.0, search="villa", max_sweeps=ve.MAX_SWEEPS,
             p=1.0):
    """The estimator with the weight constant c, its exponent p and the search selectable.

    search="villa"     cpp:45-142 as transcribed: seed from the unweighted sum, best updated inside
                       the 3 by 3 loop, no clamp to the grid, float64 like the transcription. The
                       C++ loop has no iteration limit; this one stops at max_sweeps and says so
                       through the second return value. See tools/search_cap.py for what that cap
                       does to the tables: only the weighted mean ever met it.
    search="rewritten" the rewritten search: seed and refinement on the same objective, probes
                       from a fixed centre, step halves when none improves, walk clipped to the
                       grid.
    Returns (xy, capped).
    """
    ms, ns, rng = sample(mid, nrm, seed)
    cand = np.stack([rng.uniform(0, W, ve.N_CANDIDATES), rng.uniform(0, H, ve.N_CANDIDATES)], 1)
    if search == "villa":
        best = cand[int(np.argmax(ve.seed_score(cand, ms, ns)))]
        bs = float(refine_score(best, ms, ns, divide, c, p=p)[0])
        step, sweeps, capped = ve.STEP0, 0, False
        while step >= ve.TOL:
            if sweeps >= max_sweeps:
                capped = True
                break
            sweeps += 1
            moved = False
            for d in ve.DIRS:
                q = best + step * d
                v = float(refine_score(q, ms, ns, divide, c, p=p)[0])
                if v > bs:
                    bs, best, moved = v, q, True
            if not moved:
                step /= 2.0
        return best, capped
    if search == "rewritten":
        lo, hi = np.array([0.0, 0.0]), np.array([W, H])
        best = cand[int(np.argmax(refine_score(cand, ms, ns, divide, c, p=p)))]
        bs = float(refine_score(best, ms, ns, divide, c, p=p)[0])
        step = ve.STEP0
        while step >= ve.TOL:
            probes = np.clip(best + step * ve.DIRS, lo, hi)
            vals = refine_score(probes, ms, ns, divide, c, p=p)
            k = int(np.argmax(vals))
            if vals[k] > bs:
                bs, best = float(vals[k]), probes[k]
            else:
                step /= 2.0
        return best, False
    raise ValueError(search)


def rev1_selftest(mid, nrm, W, H, seeds=(1, 2, 3)):
    """c=100 with villa's search must reproduce villa_estimator.estimate exactly, both variants,
    on a slice with at least N_SAMPLES segments (where the two sampling rules coincide)."""
    bad = []
    if len(mid) < ve.N_SAMPLES:
        return [("slice has fewer than N_SAMPLES segments: the frozen transcription differs by design",)]
    for s in seeds:
        for divide in (True, False):
            a, _ = ve.estimate(mid, nrm, W, H, s, divide)
            b, _ = estimate(mid, nrm, W, H, s, divide)
            if not (a[0] == b[0] and a[1] == b[1]):
                bad.append((s, divide, tuple(a), tuple(b)))
    return bad


# ------------------------------------------------------------------ the fifteen scrolls

def reference(scroll):
    """Control points of the scroll's reference, level 0 voxels, sorted by z."""
    p = CFG[scroll]["reference"]
    d = json.load(open(p if os.path.isabs(p) else os.path.join(NG, p)))
    pts = d["control_points"] if isinstance(d, dict) else d
    a = np.array([[p["x"], p["y"], p["z"]] for p in pts if not p.get("rejected")], float)
    return a[np.argsort(a[:, 2])]


def heights(scroll):
    """The 24 slice indices of the frozen tables, the same rule those tables used."""
    sc = CFG[scroll]["grid_scale"]
    ref = reference(scroll)
    lo, hi = ref[:, 2].min() / sc, ref[:, 2].max() / sc
    return [int(round(v)) for v in np.linspace(lo, hi, N_HEIGHTS)]


def grid15_slice(scroll, z):
    """One cached slice of the fifteen-scroll run as (mid, nrm, W, H), or None."""
    p = os.path.join(NG, "grid15", scroll, f"{z:06d}.grid")
    if not os.path.exists(p) or not os.path.getsize(p):
        return None
    h, paths, _ = read_grid(p)
    mid, nrm = segments(paths)
    if len(mid) < 100:
        return None
    return mid, nrm, float(h["bounds"][2]), float(h["bounds"][3])


def grid23_slices(scroll):
    """Every cached slice of the competition run, as [(z, mid, nrm, W, H)]."""
    d = os.path.join(NG, "grid23", scroll)
    out = []
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f)
        if not f.endswith(".grid") or not os.path.getsize(p):
            continue
        h, paths, _ = read_grid(p)
        mid, nrm = segments(paths)
        if len(mid) < 100:
            continue
        out.append((int(f[:-5]), mid, nrm, float(h["bounds"][2]), float(h["bounds"][3])))
    return out


def baselines(scroll, W):
    """The centroid baseline and the constant-axis control of the frozen tables, level 0 voxels."""
    import bench
    import data
    import estimators as est
    cfg = CFG[scroll]
    sc = cfg["grid_scale"]
    data.SCROLLS[scroll] = {"prediction": cfg["mask_pred"], "field_px": W * sc,
                            "voxel_um": cfg["voxel_um"], "store_scale": cfg["mask_scale"]}
    return {"centroid": bench.polylines(scroll, {"c": est.centroid}, 3, N_HEIGHTS)["c"],
            "fake_axis": bench.fake_axis(scroll, 3, N_HEIGHTS)}


def errors(truth, poly, mm):
    """bench.errors, the metric of the frozen tables."""
    import bench
    return bench.errors(truth, poly, mm)


# ------------------------------------------------------------------ small helpers

def write_csv(path, cols, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"written {path} ({len(rows)} rows)", flush=True)


def read_csv(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def villa_hash():
    """The commit of villa the stand-in build compiled from (real/build.sh: external/villa)."""
    import subprocess
    return subprocess.check_output(["git", "-C", VILLA_UPSTREAM,
                                    "rev-parse", "HEAD"], text=True).strip()


# The cache folder for a scroll's published xy normal grids. The folder is called `ngrid-9362` on
# every scroll, which is a name inherited from PHerc1203 and is WRONG on two of the three
# scrolls it was first used on: PHerc0800 and PHerc1447 are scanned at 8.640 um, not 9.362. The folders are
# not renamed, because tools and datasets in flight hold the path; instead every tool that reports
# this folder says the scroll's real voxel beside it, so nobody reads a resolution off a folder
# name. `grid_note` is what they print.
def grid_dir(scroll):
    return os.path.join(NG, "cache", scroll.lower(), "ngrid-9362", "xy")


def grid_note(scroll, voxel_um=None):
    v = voxel_um if voxel_um is not None else CFG.get(scroll, {}).get("voxel_um")
    if v is None:
        return ""
    return (f" (folder name says 9362; {scroll} is at {v:g} um)" if abs(v - 9.362) > 1e-9
            else "")
