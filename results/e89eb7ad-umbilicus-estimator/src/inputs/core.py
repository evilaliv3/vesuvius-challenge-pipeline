# This file is a frozen copy of the module that split the estimator for the metamorphic battery
# of 2026-09-16, the run this folder's synthetic tables come from. It differs from the copy that
# produced them in one way only: the absolute path of that run is replaced by this folder,
# resolved from the file's own location, which needs one more import. Nothing else is changed.
"""The estimator split so that a metamorphic relation can act on its inputs.

`villa_estimator.estimate` draws its own samples and its own candidates inside the call and
hardcodes the candidate box to [0,W]x[0,H] with the origin at zero. A metamorphic test needs the
transformed run to see the IMAGE of the same samples and the IMAGE of the same candidates, not a
fresh draw: otherwise any difference is the draw and not the algorithm.

So the body is split in two. `draw` reproduces, line by line, what villa_estimator does to build
(samples, candidates); `climb` is the RANSAC pick plus the hill climb and takes them as arguments.
`fidelity` checks that draw + climb reproduces villa_estimator.estimate exactly, and every table
that uses this module runs it first.

villa_estimator.py is imported, never modified: another agent owns that folder.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import villa_estimator as ve

N_SAMPLES = ve.N_SAMPLES
N_CANDIDATES = ve.N_CANDIDATES
STEP0, TOL, MAX_SWEEPS = ve.STEP0, ve.TOL, ve.MAX_SWEEPS
DIRS = ve.DIRS


def draw(mid, nrm, W, H, seed):
    """villa_estimator.sample plus the two uniform draws of villa_estimator.estimate, in order."""
    ms, ns, rng = ve.sample(mid, nrm, seed)
    cand = np.stack([rng.uniform(0, W, N_CANDIDATES), rng.uniform(0, H, N_CANDIDATES)], 1)
    return ms, ns, cand


def climb(ms, ns, cand, divide, max_sweeps=MAX_SWEEPS):
    """cpp:78-142 on samples and candidates that are given, not drawn here."""
    best = cand[int(np.argmax(ve.seed_score(cand, ms, ns)))]
    bs = float(ve.refine_score(best, ms, ns, divide)[0])
    step, sweeps, capped = STEP0, 0, False
    while step >= TOL:
        if sweeps >= max_sweeps:
            capped = True
            break
        sweeps += 1
        moved = False
        for d in DIRS:
            c = best + step * d
            v = float(ve.refine_score(c, ms, ns, divide)[0])
            if v > bs:
                bs, best, moved = v, c, True
        if not moved:
            step /= 2.0
    return best, capped


def estimate(mid, nrm, W, H, seed, divide, max_sweeps=MAX_SWEEPS):
    ms, ns, cand = draw(mid, nrm, W, H, seed)
    return climb(ms, ns, cand, divide, max_sweeps)


def fidelity(mid, nrm, W, H, seeds, divides=(True, False)):
    """Must return 0 differences: otherwise the bench is broken, not the estimator."""
    bad = []
    for s in seeds:
        for d in divides:
            a, _ = ve.estimate(mid, nrm, W, H, s, d)
            b, _ = estimate(mid, nrm, W, H, s, d)
            if not (a[0] == b[0] and a[1] == b[1]):
                bad.append((s, d, tuple(a), tuple(b)))
    return bad


# ---------------------------------------------------------------- transforms

def affine(A, t):
    """A 2x2 matrix and a shift, acting on points, on normals and on candidates.

    Points and candidates map as p -> A p + t. Normals map as n -> A n renormalized, which is the
    correct push-forward only when A is a similarity; the relations tested here use nothing else.
    Under a reflection the pushed normal has the opposite sign to the one rebuilt from the
    transformed endpoints, and that is harmless: the objective uses cos^2.
    """
    A = np.asarray(A, float)
    t = np.asarray(t, float)

    def pts(p):
        return p @ A.T + t

    def nor(n):
        m = n @ A.T
        return m / np.linalg.norm(m, axis=1, keepdims=True)

    return pts, nor
