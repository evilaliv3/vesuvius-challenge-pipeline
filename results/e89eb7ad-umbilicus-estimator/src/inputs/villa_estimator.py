"""villa's `align_and_extract_umbilicus`, transcribed once and used by every table.

One module so that no two tables can rest on two different algorithms under the same name. On
2026-09-15 they nearly did: an earlier version of the twenty-four scroll run seeded the hill climb
from the refinement score instead of from the unweighted sum of cpp:78-88, which is a different
estimator from the published one, and its column was still called "as published".

The transcription, from volume-cartographer/core/src/normalgridtools.cpp:15-147:

  cpp:45-56   sample 10000 segments, draw 1000 uniform candidates over the store bounds
  cpp:78-88   seed score: UNWEIGHTED sum of cos^2. This is what picks the seed, in both variants.
  cpp:98-117  refinement score: cos^2 weighted by 1/max(100, dist), then divided by the sum of the
              weights at line 116. `divide=False` is the one line under test and nothing else.
  cpp:119-142 hill climb from 1024, best updated inside the 3 by 3 loop, walk unbounded.

`max_sweeps` is not in the C++. The C++ loop has no bound on how far it may walk, so a slice can
run for minutes. A slice that hits the cap is not dropped and is not counted as a failure: the
position the walk had reached is returned, flagged in the `capped` column of the raw estimate file,
and scored with every other estimate. It therefore enters the tables. Since every walk that has met
this cap had already left the grid, it counts as outside in the convergence tally, which is what it
is; and it enters the error medians nearer the section than an uncapped walk would be, so the cap
flatters the variant that meets it, which is only ever the published one. `search_cap.py` measures
how much. It is the same bound, 2000, used by every run in this folder.
"""
import numpy as np

N_SAMPLES = 10000        # cpp:23
N_CANDIDATES = 1000      # cpp:22
STEP0, TOL = 1024.0, 1.0
MAX_SWEEPS = 2000
DIRS = np.array([(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if (a, b) != (0, 0)], float)


def _cos2(cand, mid, nrm):
    """cos^2 between each segment normal and the direction from candidate to segment."""
    vx = mid[None, :, 0] - cand[:, 0, None]
    vy = mid[None, :, 1] - cand[:, 1, None]
    d = np.hypot(vx, vy)
    d = np.where(d < 1e-6, np.inf, d)                    # cpp:107
    return ((vx / d) * nrm[None, :, 0] + (vy / d) * nrm[None, :, 1]) ** 2, d


def seed_score(cand, mid, nrm, block=256):
    """cpp:78-88. Unweighted sum of cos^2, the function that picks the RANSAC seed."""
    cand = np.atleast_2d(np.asarray(cand, float))
    out = np.empty(len(cand))
    for s in range(0, len(cand), block):
        cos2, _ = _cos2(cand[s:s + block], mid, nrm)
        out[s:s + block] = cos2.sum(1)
    return out


def refine_score(cand, mid, nrm, divide, block=256):
    """cpp:98-117. divide=True is the function as it stands, False removes line 116's division."""
    cand = np.atleast_2d(np.asarray(cand, float))
    out = np.empty(len(cand))
    for s in range(0, len(cand), block):
        cos2, d = _cos2(cand[s:s + block], mid, nrm)
        w = 1.0 / np.maximum(100.0, d)                   # cpp:112
        num = (cos2 * w).sum(1)
        out[s:s + block] = num / w.sum(1) if divide else num
    return out


def sample(mid, nrm, seed):
    """cpp:45-50, with a seeded generator so that a measurement can be repeated."""
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(mid), min(N_SAMPLES, len(mid)))
    return mid[idx].astype(float), nrm[idx].astype(float), rng


def estimate(mid, nrm, W, H, seed, divide, max_sweeps=MAX_SWEEPS, trace=None):
    """The published estimator, or the published estimator with the division removed.

    `trace`, when a list is passed, collects the seed and every position the climb accepts, so a
    figure can draw the walk. It is appended to and never read, so the estimate is the same
    whether it is passed or not.
    """
    ms, ns, rng = sample(mid, nrm, seed)
    cand = np.stack([rng.uniform(0, W, N_CANDIDATES), rng.uniform(0, H, N_CANDIDATES)], 1)
    best = cand[int(np.argmax(seed_score(cand, ms, ns)))]          # cpp:78-88, both variants
    bs = float(refine_score(best, ms, ns, divide)[0])
    if trace is not None:
        trace.append(tuple(best))
    step, sweeps, capped = STEP0, 0, False
    while step >= TOL:
        if sweeps >= max_sweeps:
            capped = True
            break
        sweeps += 1
        moved = False
        for d in DIRS:                                             # cpp:124-137
            c = best + step * d
            v = float(refine_score(c, ms, ns, divide)[0])
            if v > bs:
                bs, best, moved = v, c, True                       # best updated inside the loop
                if trace is not None:
                    trace.append(tuple(best))
        if not moved:
            step /= 2.0
    return best, capped


def interior_max(ms, ns, centre, divide, half=200.0, step=4.0):
    """Is there a maximum of the objective inside a window around this point?

    The probe uses the SAME sampled segments the estimate used: a different draw would be a
    slightly different function, and the answer would be about the draw and not about the shape.
    """
    g = np.arange(-half, half + 1, step)
    LX, LY = np.meshgrid(centre[0] + g, centre[1] + g)
    L = np.stack([LX.ravel(), LY.ravel()], 1)
    m = L[int(np.argmax(refine_score(L, ms, ns, divide)))]
    return bool(abs(m[0] - centre[0]) < half - 1 and abs(m[1] - centre[1]) < half - 1)
