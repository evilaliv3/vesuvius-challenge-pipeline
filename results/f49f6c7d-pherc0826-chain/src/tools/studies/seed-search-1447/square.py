#!/usr/bin/env python3
"""The exact largest axis aligned fully covered square on a delivered sheet.

Rewritten for runs/rev1/reference-b40 after the original (quadrato.py) was deleted with the old
home on 2026-09-20. The recipe is the one the shipped study declares in the header line of
results/1f330280-delivered-surface/src/evidence/studies/delivered-square/squares-L212.csv, and
every column is reproduced under the name that file gives it. tools/square-notes.md says which
columns were read straight off that file and which were inferred, with the arithmetic.

What a delivered sheet is. A file patch_<n>.bin written by the fm stage of the chain: a flat
sequence of packed records of five little endian float32, "x, y, px, py, pz" (the struct
gridPointStruct of build/efficient/bin2tifxyz.cpp). (x, y) are the sheet's own parametrisation
coordinates, which bin2tifxyz maps onto an integer lattice with llround((x - xmin) / step) at
step 1, and (px, py, pz) are the volume coordinates in voxels. VOXEL_SIZE is 9, so one voxel is
0.009 mm.

What the square is. The occupancy mask is one cell per lattice site of the bounding box of the
sheet's own coordinates: covered where a point landed, uncovered elsewhere. Holes are NOT
filled: an uncovered cell is uncovered whatever surrounds it. The side reported in millimetres
is the number of cells times the SMALLER of the two measured cell steps of that sheet, which is
the conservative of the two.

Exactness. The search is the classic dynamic programme over the mask, which visits every corner:
dp[i, j] is the side of the largest fully covered square whose bottom right cell is (i, j), and
dp[i, j] = min(up[i, j], left[i, j], dp[i - 1, j - 1] + 1) on a covered cell, 0 elsewhere. A
measurer that steps its corners by a stride sells a lower bound as a maximum (righe.py stepped
by l // 8); tools/square_selftest.py checks this one against an independent brute force scan
that visits every corner, and the gate below refuses to measure a sheet until it has passed.

Tie break, declared here and not left to the machine: among the squares of the maximal side, the
one whose TOP LEFT corner comes first in row major order over (i, j). square_corner_i and
square_corner_j are that top left corner.

Usage:
  square.py <sheets dir> --point L212 --out evidence/squares-L212.csv
  square.py <sheets dir> --point L212 --out ... --selftest-summary evidence/square-selftest-summary.csv
"""

import argparse
import csv
import glob
import hashlib
import os
import re
import sys

import numpy as np

POINT = np.dtype([("x", "<f4"), ("y", "<f4"), ("px", "<f4"), ("py", "<f4"), ("pz", "<f4")])

VOXEL_UM = 9.0
MM_PER_VOXEL = VOXEL_UM * 1e-3

# A sheet whose own coordinates do not sit on the integer lattice within this many cells is not
# measurable: it comes out as "not measurable", never as a zero.
LATTICE_GATE = 0.01

# The side the prize asks for, in millimetres, used only for the limit and reaches_20mm columns.
TARGET_MM = 20.0

NOT_MEASURABLE = "not measurable"

COLUMNS = [
    "point", "sheet", "file", "points", "status", "cells_i", "cells_j", "fill_fraction",
    "lattice_residual_max", "step_samples_i", "step_samples_j", "step_i_voxel", "step_j_voxel",
    "step_i_mm", "step_j_mm", "axis_angle_deg_median", "square_cells", "square_corner_i",
    "square_corner_j", "square_mm_min_step", "square_mm_i_step", "square_mm_j_step",
    "size_ceiling_cells", "size_ceiling_mm", "square_cells_holes_filled",
    "square_mm_holes_filled", "enclosed_hole_cells", "limit", "reaches_20mm", "sha256",
]

HEADER_NOTE = (
    "# one row per delivered sheet. The square is the exact largest axis aligned square fully "
    "covered on the sheet own parametrisation grid, from tools/square.py, whose self test is "
    "evidence/square-selftest.csv. square_mm_min_step is the side in millimetres with the "
    "SMALLER of the two measured cell steps and is the number this study answers on; the two "
    "steps are measured per sheet and per axis from the 3D positions in the same file. limit is "
    "size when even a full bounding box would stay under 20 mm, enclosed_pores when filling the "
    "enclosed holes would reach 20 mm, outline otherwise. A sheet that fails the lattice gate "
    "comes out as not measurable, never as a zero."
)


# --------------------------------------------------------------------------------------------
# The square itself
# --------------------------------------------------------------------------------------------

def largest_square(mask):
    """Exact largest axis aligned square of covered cells.

    Returns (side, corner_i, corner_j). On an empty mask the side is 0 and the corner is
    (-1, -1), which is not a cell and cannot be mistaken for one.

    The classic dynamic programme, in the form dp = min(up, left, dp_diagonal + 1). up and left
    are the runs of covered cells ending at the cell going upward and leftward; both are exact
    prefix runs, so no corner is skipped. The equivalence with
    dp[i, j] = 1 + min(dp[i-1, j], dp[i, j-1], dp[i-1, j-1]) is checked against brute force on
    every case of tools/square_selftest.py.
    """
    mask = np.ascontiguousarray(mask, dtype=bool)
    if mask.ndim != 2:
        raise ValueError("mask must be two dimensional")
    ni, nj = mask.shape
    if ni == 0 or nj == 0 or not mask.any():
        return 0, -1, -1

    jj = np.arange(nj, dtype=np.int64)
    left = jj[None, :] - np.maximum.accumulate(np.where(mask, -1, jj[None, :]), axis=1)
    ii = np.arange(ni, dtype=np.int64)
    up = ii[:, None] - np.maximum.accumulate(np.where(mask, -1, ii[:, None]), axis=0)

    best = 0
    best_i = -1
    best_j = -1
    prev = np.zeros(nj, dtype=np.int64)
    diag = np.empty(nj, dtype=np.int64)
    for i in range(ni):
        diag[0] = 0
        diag[1:] = prev[:-1]
        row = np.minimum(np.minimum(up[i], left[i]), diag + 1)
        row[~mask[i]] = 0
        m = int(row.max())
        if m > best:
            best = m
            best_i = i
            best_j = int(np.argmax(row))
        prev = row

    return best, best_i - best + 1, best_j - best + 1


def enclosed_holes(mask):
    """The uncovered cells the covered cells enclose, as a boolean mask.

    A cell is enclosed when it is uncovered and cannot reach the outside of the bounding box by
    steps to its four side neighbours. Four connectivity on the background is the declared
    choice: a diagonal chain of covered cells closes a pore.
    """
    from scipy import ndimage

    mask = np.ascontiguousarray(mask, dtype=bool)
    if mask.size == 0:
        return np.zeros_like(mask)
    structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)
    filled = ndimage.binary_fill_holes(mask, structure=structure)
    return filled & ~mask


# --------------------------------------------------------------------------------------------
# Reading one sheet
# --------------------------------------------------------------------------------------------

def sheet_files(where):
    """The sheet files under a directory, ordered by their patch number."""
    d = where
    if os.path.isdir(os.path.join(where, "patches")):
        d = os.path.join(where, "patches")
    keyed = []
    for f in glob.glob(os.path.join(d, "patch_*.bin")):
        m = re.search(r"patch_(\d+)\.bin$", f)
        if m:
            keyed.append((int(m.group(1)), f))
    keyed.sort()
    return keyed


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def median_step(mask, px, py, pz, axis):
    """Median 3D distance in voxels between two covered cells one apart along `axis`.

    Returns (median_voxel, samples). The recipe is the one pipeline/tools/traced_area.py uses for
    the point spacing, median and not mean, applied here per axis and over every adjacent pair of
    the sheet rather than over a sample.
    """
    if axis == 0:
        pair = mask[:-1, :] & mask[1:, :]
        dx = px[1:, :] - px[:-1, :]
        dy = py[1:, :] - py[:-1, :]
        dz = pz[1:, :] - pz[:-1, :]
    else:
        pair = mask[:, :-1] & mask[:, 1:]
        dx = px[:, 1:] - px[:, :-1]
        dy = py[:, 1:] - py[:, :-1]
        dz = pz[:, 1:] - pz[:, :-1]
    n = int(pair.sum())
    if n == 0:
        return float("nan"), 0
    d = np.sqrt(dx[pair].astype(np.float64) ** 2
                + dy[pair].astype(np.float64) ** 2
                + dz[pair].astype(np.float64) ** 2)
    return float(np.median(d)), n


def median_axis_angle(mask, px, py, pz):
    """Median 3D angle in degrees between the two grid step vectors of a cell.

    Measured on every cell that is covered and whose neighbour one step along i and whose
    neighbour one step along j are both covered.
    """
    both = mask[:-1, :-1] & mask[1:, :-1] & mask[:-1, 1:]
    n = int(both.sum())
    if n == 0:
        return float("nan"), 0
    ax = (px[1:, :-1] - px[:-1, :-1])[both].astype(np.float64)
    ay = (py[1:, :-1] - py[:-1, :-1])[both].astype(np.float64)
    az = (pz[1:, :-1] - pz[:-1, :-1])[both].astype(np.float64)
    bx = (px[:-1, 1:] - px[:-1, :-1])[both].astype(np.float64)
    by = (py[:-1, 1:] - py[:-1, :-1])[both].astype(np.float64)
    bz = (pz[:-1, 1:] - pz[:-1, :-1])[both].astype(np.float64)
    na = np.sqrt(ax * ax + ay * ay + az * az)
    nb = np.sqrt(bx * bx + by * by + bz * bz)
    good = (na > 0) & (nb > 0)
    if not good.any():
        return float("nan"), 0
    cos = (ax * bx + ay * by + az * bz)[good] / (na[good] * nb[good])
    return float(np.median(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))), int(good.sum())


def not_measurable_row(point, sheet, path, points, digest, why, verbose=True):
    """Every quantity of a sheet that cannot be measured is the words "not measurable", never a
    zero: a zero here would be read as a sheet with no square. The reason goes to stderr, because
    the shipped table has no column for it."""
    if verbose:
        sys.stderr.write("%s sheet %s: not measurable, %s\n" % (point, sheet, why))
    row = {c: NOT_MEASURABLE for c in COLUMNS}
    row["point"] = point
    row["sheet"] = sheet
    row["file"] = os.path.basename(path)
    row["points"] = points
    row["status"] = NOT_MEASURABLE
    row["sha256"] = digest
    return row


def measure_sheet(point, sheet, path, target_mm=TARGET_MM, lattice_gate=LATTICE_GATE,
                  verbose=True):
    """One row of the table, for one delivered sheet."""
    digest = sha256_of(path)
    a = np.fromfile(path, dtype=POINT)
    points = int(a.size)
    if points == 0:
        return not_measurable_row(point, sheet, path, points, digest, "empty sheet", verbose)

    u = a["x"].astype(np.float64)
    v = a["y"].astype(np.float64)
    fu = u - u.min()
    fv = v - v.min()
    ci = np.rint(fu)
    cj = np.rint(fv)
    residual = float(max(np.abs(fu - ci).max(), np.abs(fv - cj).max()))
    if not np.isfinite(residual) or residual > lattice_gate:
        return not_measurable_row(point, sheet, path, points, digest,
                                  "lattice residual %g above the gate %g" % (residual, lattice_gate),
                                  verbose)

    ci = ci.astype(np.int64)
    cj = cj.astype(np.int64)
    cells_i = int(ci.max()) + 1
    cells_j = int(cj.max()) + 1

    mask = np.zeros((cells_i, cells_j), dtype=bool)
    mask[ci, cj] = True
    covered = int(mask.sum())
    if verbose and covered != points:
        sys.stderr.write("%s sheet %d: %d points land on %d cells, %d collisions\n"
                         % (point, sheet, points, covered, points - covered))

    px = np.zeros((cells_i, cells_j), dtype=np.float32)
    py = np.zeros((cells_i, cells_j), dtype=np.float32)
    pz = np.zeros((cells_i, cells_j), dtype=np.float32)
    px[ci, cj] = a["px"]
    py[ci, cj] = a["py"]
    pz[ci, cj] = a["pz"]

    step_i_voxel, samples_i = median_step(mask, px, py, pz, 0)
    step_j_voxel, samples_j = median_step(mask, px, py, pz, 1)
    angle, _ = median_axis_angle(mask, px, py, pz)
    if not (np.isfinite(step_i_voxel) and np.isfinite(step_j_voxel)):
        return not_measurable_row(point, sheet, path, points, digest,
                                  "no adjacent covered pair to measure a step on", verbose)

    step_i_mm = step_i_voxel * MM_PER_VOXEL
    step_j_mm = step_j_voxel * MM_PER_VOXEL
    step_min_mm = min(step_i_mm, step_j_mm)

    side, corner_i, corner_j = largest_square(mask)
    holes = enclosed_holes(mask)
    hole_cells = int(holes.sum())
    side_filled, _, _ = largest_square(mask | holes)

    size_ceiling_cells = min(cells_i, cells_j)
    size_ceiling_mm = size_ceiling_cells * step_min_mm
    square_mm_min = side * step_min_mm
    square_mm_holes = side_filled * step_min_mm

    if square_mm_min >= target_mm:
        limit = "none"
    elif size_ceiling_mm < target_mm:
        limit = "size"
    elif square_mm_holes >= target_mm:
        limit = "enclosed_pores"
    else:
        limit = "outline"

    return {
        "point": point,
        "sheet": sheet,
        "file": os.path.basename(path),
        "points": points,
        "status": "measured",
        "cells_i": cells_i,
        "cells_j": cells_j,
        "fill_fraction": round(covered / float(cells_i * cells_j), 6),
        "lattice_residual_max": round(residual, 6),
        "step_samples_i": samples_i,
        "step_samples_j": samples_j,
        "step_i_voxel": round(step_i_voxel, 4),
        "step_j_voxel": round(step_j_voxel, 4),
        "step_i_mm": round(step_i_mm, 6),
        "step_j_mm": round(step_j_mm, 6),
        "axis_angle_deg_median": (round(angle, 3) if np.isfinite(angle) else NOT_MEASURABLE),
        "square_cells": side,
        "square_corner_i": corner_i,
        "square_corner_j": corner_j,
        "square_mm_min_step": round(square_mm_min, 4),
        "square_mm_i_step": round(side * step_i_mm, 4),
        "square_mm_j_step": round(side * step_j_mm, 4),
        "size_ceiling_cells": size_ceiling_cells,
        "size_ceiling_mm": round(size_ceiling_mm, 4),
        "square_cells_holes_filled": side_filled,
        "square_mm_holes_filled": round(square_mm_holes, 4),
        "enclosed_hole_cells": hole_cells,
        "limit": limit,
        "reaches_20mm": "yes" if square_mm_min >= target_mm else "no",
        "sha256": digest,
    }


# --------------------------------------------------------------------------------------------
# The gate: no sheet is measured until the self test has passed
# --------------------------------------------------------------------------------------------

EXPECTED_SELFTEST = {"hand": 7, "random": 200, "stride": 1}


def check_selftest(path):
    """Refuse to measure unless the self test summary is there and every case agreed.

    Looks at the thing that could be wrong: the three kinds must all be present with the declared
    number of cases, and for each kind the number of cases, the number that agree, and the number
    where every implementation agrees must be the same number. A missing kind, a short count or
    one disagreement all stop the run.
    """
    if not os.path.exists(path):
        return False, "no self test summary at %s" % path
    with open(path, newline="") as fh:
        lines = [ln for ln in fh.read().splitlines() if ln and not ln.startswith('"#')]
    rows = list(csv.DictReader(lines))
    seen = {}
    for r in rows:
        kind = r.get("kind")
        try:
            cases = int(r["cases"])
            agree = int(r["cases_that_agree"])
            allagree = int(r["cases_where_the_two_implementations_and_brute_force_all_agree"])
        except (KeyError, TypeError, ValueError):
            return False, "self test summary row is not readable: %r" % (r,)
        if not (cases == agree == allagree):
            return False, "self test kind %s: %d cases, %d agree, %d all agree" % (
                kind, cases, agree, allagree)
        seen[kind] = cases
    for kind, n in EXPECTED_SELFTEST.items():
        if seen.get(kind) != n:
            return False, "self test kind %s has %r cases, %d declared" % (
                kind, seen.get(kind), n)
    return True, "self test passed: " + ", ".join(
        "%s %d" % (k, seen[k]) for k in sorted(seen))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default_summary = os.path.join(os.path.dirname(here), "evidence",
                                   "square-selftest-summary.csv")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sheets", help="the directory holding patch_<n>.bin, or its parent")
    ap.add_argument("--point", required=True, help="the label of the point, for example L212")
    ap.add_argument("--out", required=True, help="the CSV to write")
    ap.add_argument("--selftest-summary", default=default_summary,
                    help="the self test summary that must pass before anything is measured")
    ap.add_argument("--target-mm", type=float, default=TARGET_MM)
    ap.add_argument("--voxel-um", type=float, default=VOXEL_UM)
    a = ap.parse_args()

    global MM_PER_VOXEL
    MM_PER_VOXEL = a.voxel_um * 1e-3

    ok, why = check_selftest(a.selftest_summary)
    if not ok:
        sys.exit("refusing to measure: " + why)
    sys.stderr.write(why + "\n")

    files = sheet_files(a.sheets)
    if not files:
        sys.exit("no patch_<n>.bin under %s" % a.sheets)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        fh.write('"%s"\n' % HEADER_NOTE)
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        for n, path in files:
            row = measure_sheet(a.point, n, path, target_mm=a.target_mm)
            w.writerow(row)
            fh.flush()
            sys.stderr.write("sheet %d: %s, square %s cells, %s mm\n" % (
                n, row["status"], row["square_cells"], row["square_mm_min_step"]))
    sys.stderr.write("wrote %s, %d sheets\n" % (a.out, len(files)))


if __name__ == "__main__":
    main()
