#!/usr/bin/env python3
"""The self test of the exact largest square, which runs and passes before any sheet is measured.

Three independent measurers are compared on every case:

  1. square.largest_square, the dynamic programme the tool uses;
  2. sat_largest_square, a second implementation over a summed area table with a binary search on
     the side, which shares no line of code with the first;
  3. brute_force_largest_square, an exhaustive scan that visits EVERY top left corner and every
     side and reads every cell of every candidate square, with no prefix sum and no recurrence.

The third is the honest arbiter: it is slow and stupid on purpose. The defect this whole file
exists for is the one righe.py shipped, a scan that stepped its corners by l // 8 and sold the
lower bound it found as a maximum; the stride case below is built to make exactly that defect
visible, and --negative runs the suite against a deliberately broken copy to show that it does.

All three break a tie the same declared way: among the squares of the maximal side, the one whose
TOP LEFT corner comes first in row major order over (i, j). On an empty mask the side is 0 and
the corner is (-1, -1).

  square_selftest.py                 writes evidence/square-selftest.csv and the summary
  square_selftest.py --negative      writes evidence/square-selftest-negative.csv
"""

import argparse
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import square  # noqa: E402

SEED = 20260920
RANDOM_CASES = 200

CASE_COLUMNS = [
    "kind", "case", "seed", "rows", "cols", "covered_cells", "what_the_case_is",
    "dp_side", "dp_corner_i", "dp_corner_j",
    "sat_side", "sat_corner_i", "sat_corner_j",
    "brute_side", "brute_corner_i", "brute_corner_j",
    "expected_side", "expected_corner_i", "expected_corner_j",
    "enclosed_hole_cells", "expected_enclosed_hole_cells",
    "side_holes_filled", "expected_side_holes_filled",
    "agrees_with_brute_force", "all_three_agree", "matches_the_hand_answer", "ok",
]

SUMMARY_COLUMNS = [
    "kind", "what_the_case_is", "cases", "cases_that_agree",
    "cases_where_the_two_implementations_and_brute_force_all_agree",
]

SUMMARY_NOTE = (
    "# the self test of the exact largest fully covered square, summarised by kind of case from "
    "the row by row table beside it, evidence/square-selftest.csv, written by "
    "tools/square_selftest.py. cases_that_agree counts the cases where the dynamic programme of "
    "tools/square.py and the independent brute force scan return the same side; the last column "
    "counts the cases where the dynamic programme, the second implementation and the brute force "
    "scan all return the same side AND the same corner. The random seed is in every random row "
    "of the table."
)

CASE_NOTE = (
    "# one row per case of the self test of tools/square.py. dp_ is the dynamic programme under "
    "test, sat_ the second implementation over a summed area table, brute_ the exhaustive scan "
    "that visits every corner. expected_ is filled only for the cases worked out by hand. A side "
    "of 0 with a corner of -1 is the empty mask, which has no square: it is not a cell."
)


# --------------------------------------------------------------------------------------------
# The two measurers that are not the one under test
# --------------------------------------------------------------------------------------------

def brute_force_largest_square(mask):
    """Exhaustive: every top left corner, every side, every cell of every candidate.

    No prefix sum, no recurrence, no stride. Deliberately the slowest possible statement of what
    the answer is, so that it cannot share a defect with the dynamic programme.
    """
    m = [[bool(x) for x in row] for row in np.asarray(mask, dtype=bool)]
    ni = len(m)
    nj = len(m[0]) if ni else 0
    best = 0
    best_i = -1
    best_j = -1
    for i in range(ni):
        for j in range(nj):
            s = 1
            while i + s <= ni and j + s <= nj:
                full = True
                for r in range(i, i + s):
                    for c in range(j, j + s):
                        if not m[r][c]:
                            full = False
                            break
                    if not full:
                        break
                if not full:
                    break
                if s > best:
                    best = s
                    best_i = i
                    best_j = j
                s += 1
    return best, best_i, best_j


def sat_largest_square(mask):
    """Second implementation: summed area table plus a binary search on the side.

    A square of side s exists only if one of side s - 1 exists, so the predicate is monotone and
    the binary search is exact. The corner is the first window of the winning side in row major
    order, the same tie break the other two use.
    """
    a = np.asarray(mask, dtype=bool)
    ni, nj = a.shape if a.ndim == 2 else (0, 0)
    if ni == 0 or nj == 0 or not a.any():
        return 0, -1, -1
    sat = np.zeros((ni + 1, nj + 1), dtype=np.int64)
    sat[1:, 1:] = np.cumsum(np.cumsum(a.astype(np.int64), axis=0), axis=1)

    def first_corner(s):
        if s <= 0 or s > ni or s > nj:
            return None
        tot = (sat[s:, s:] - sat[:-s, s:] - sat[s:, :-s] + sat[:-s, :-s])
        hit = np.flatnonzero(tot.ravel() == s * s)
        if hit.size == 0:
            return None
        k = int(hit[0])
        return divmod(k, tot.shape[1])

    lo, hi, best = 1, min(ni, nj), 0
    corner = (-1, -1)
    while lo <= hi:
        mid = (lo + hi) // 2
        c = first_corner(mid)
        if c is None:
            hi = mid - 1
        else:
            best, corner = mid, c
            lo = mid + 1
    return best, corner[0], corner[1]


def broken_stride_largest_square(mask, stride=8):
    """The defect, on purpose: the same scan, but stepping the top left corners by a stride.

    This is the shape of the routine righe.py shipped (it stepped by l // 8). It is never used to
    measure anything: --negative runs the suite against it to show the suite catches it.
    """
    a = np.asarray(mask, dtype=bool)
    ni, nj = a.shape if a.ndim == 2 else (0, 0)
    best, best_i, best_j = 0, -1, -1
    for i in range(0, ni, stride):
        for j in range(0, nj, stride):
            s = 1
            while i + s <= ni and j + s <= nj and a[i:i + s, j:j + s].all():
                if s > best:
                    best, best_i, best_j = s, i, j
                s += 1
    return best, best_i, best_j


# --------------------------------------------------------------------------------------------
# The cases
# --------------------------------------------------------------------------------------------

def hand_cases():
    """Seven masks and the answers worked out by hand, written down here with their reasoning."""
    cases = []

    # 1. the empty mask: no square at all, and a corner that is not a cell.
    m = np.zeros((4, 4), dtype=bool)
    cases.append(("empty mask, 4 by 4", m, 0, -1, -1, 0, 0))

    # 2. the full mask: the square is the whole thing, corner at the origin.
    m = np.ones((5, 5), dtype=bool)
    cases.append(("full mask, 5 by 5", m, 5, 0, 0, 0, 5))

    # 3. one covered cell at (1, 2): side 1 there and nowhere else.
    m = np.zeros((3, 3), dtype=bool)
    m[1, 2] = True
    cases.append(("one covered cell at (1, 2)", m, 1, 1, 2, 0, 1))

    # 4. an L: columns 0 and 1 down the whole height, rows 3 and 4 across the whole width. A 2 by
    #    2 fits at (0, 0); a 3 by 3 would need three covered columns in three rows and the arms
    #    are two wide, so 2 is the maximum and (0, 0) is the first corner in row major order.
    m = np.zeros((5, 5), dtype=bool)
    m[:, 0:2] = True
    m[3:5, :] = True
    cases.append(("an L with arms two cells wide", m, 2, 0, 0, 0, 2))

    # 5. the largest square touches the bottom and the right edge: a 3 by 3 block at rows 3 to 5
    #    and columns 3 to 5 of a 6 by 6, with one lone cell at (0, 0) so the mask is not just the
    #    block. Side 3 at (3, 3), and it runs into both edges.
    m = np.zeros((6, 6), dtype=bool)
    m[3:6, 3:6] = True
    m[0, 0] = True
    cases.append(("largest square touching the bottom and right edge", m, 3, 3, 3, 0, 3))

    # 6. a hole in the middle of the only big square: 7 by 7 full but for (3, 3). Every 4 by 4
    #    window of a 7 by 7 spans rows 0 to 3, 1 to 4, 2 to 5 or 3 to 6, so every one of them
    #    contains row 3, and likewise column 3; so every 4 by 4 contains (3, 3) and the maximum
    #    is 3, first at (0, 0). The single uncovered cell is enclosed, and with it closed the
    #    square is the whole 7.
    m = np.ones((7, 7), dtype=bool)
    m[3, 3] = False
    cases.append(("a hole in the middle of the only big square", m, 3, 0, 0, 1, 7))

    # 7. two squares of equal side, the tie broken by the declared scan order: a 3 by 3 block at
    #    rows 1 to 3 columns 0 to 2, and another at rows 0 to 2 columns 6 to 8. Both give side 3.
    #    Row major order over the TOP LEFT corner puts (0, 6) before (1, 0), so the second block
    #    wins. A measurer that reported the first block would be scanning by something else.
    m = np.zeros((5, 10), dtype=bool)
    m[1:4, 0:3] = True
    m[0:3, 6:9] = True
    cases.append(("two squares of equal side, tie broken by row major on the top left corner",
                  m, 3, 0, 6, 0, 3))

    return cases


def random_cases(n=RANDOM_CASES, seed=SEED):
    rng = np.random.default_rng(seed)
    out = []
    for k in range(n):
        ni = int(rng.integers(1, 15))
        nj = int(rng.integers(1, 15))
        density = float(rng.uniform(0.10, 0.95))
        m = rng.random((ni, nj)) < density
        out.append(("random %d by %d at density %.2f" % (ni, nj, density), m))
    return out


def stride_case():
    """A mask built to catch a measurer that steps over corners.

    A 48 by 48 grid, empty but for one 20 by 20 block whose top left corner is (3, 5). Neither 3
    nor 5 is a multiple of 8, so a scan that steps its corners by 8 never stands on the real
    corner: the best it can do is start at (8, 8) and run to the far edge of the block at row 22
    and column 24, which is a square of side 15. It would report 15 where the answer is 20.
    """
    m = np.zeros((48, 48), dtype=bool)
    m[3:23, 5:25] = True
    return "a 20 by 20 block at (3, 5) on a 48 by 48 grid, missed by a stride of 8", m, 20, 3, 5


# --------------------------------------------------------------------------------------------
# Running them
# --------------------------------------------------------------------------------------------

def run_case(kind, name, what, mask, expected, seed, measurer):
    dp = measurer(mask)
    sat = sat_largest_square(mask)
    brute = brute_force_largest_square(mask)
    holes = square.enclosed_holes(mask)
    hole_cells = int(holes.sum())
    filled = square.largest_square(np.asarray(mask, dtype=bool) | holes)[0]

    agrees = dp[0] == brute[0]
    all_three = (dp == sat == brute)
    if expected is None:
        hand_ok = ""
        ok = bool(agrees and all_three)
    else:
        exp_side, exp_i, exp_j, exp_holes, exp_filled = expected
        hand_ok = bool(dp == (exp_side, exp_i, exp_j)
                       and brute == (exp_side, exp_i, exp_j)
                       and sat == (exp_side, exp_i, exp_j)
                       and hole_cells == exp_holes
                       and filled == exp_filled)
        ok = bool(agrees and all_three and hand_ok)

    a = np.asarray(mask, dtype=bool)
    return {
        "kind": kind, "case": name, "seed": seed,
        "rows": a.shape[0], "cols": a.shape[1], "covered_cells": int(a.sum()),
        "what_the_case_is": what,
        "dp_side": dp[0], "dp_corner_i": dp[1], "dp_corner_j": dp[2],
        "sat_side": sat[0], "sat_corner_i": sat[1], "sat_corner_j": sat[2],
        "brute_side": brute[0], "brute_corner_i": brute[1], "brute_corner_j": brute[2],
        "expected_side": "" if expected is None else expected[0],
        "expected_corner_i": "" if expected is None else expected[1],
        "expected_corner_j": "" if expected is None else expected[2],
        "enclosed_hole_cells": hole_cells,
        "expected_enclosed_hole_cells": "" if expected is None else expected[3],
        "side_holes_filled": filled,
        "expected_side_holes_filled": "" if expected is None else expected[4],
        "agrees_with_brute_force": "yes" if agrees else "no",
        "all_three_agree": "yes" if all_three else "no",
        "matches_the_hand_answer": "" if hand_ok == "" else ("yes" if hand_ok else "no"),
        "ok": "yes" if ok else "no",
    }


def build_rows(measurer):
    rows = []
    for k, (what, m, side, ci, cj, holes, filled) in enumerate(hand_cases()):
        rows.append(run_case("hand", "hand_%d" % (k + 1), what, m,
                             (side, ci, cj, holes, filled), "", measurer))
    for k, (what, m) in enumerate(random_cases()):
        rows.append(run_case("random", "random_%d" % (k + 1), what, m, None, SEED, measurer))
    what, m, side, ci, cj = stride_case()
    rows.append(run_case("stride", "stride_1", what, m, (side, ci, cj, 0, side), "", measurer))
    return rows


KIND_WHAT = {
    "hand": "worked out by hand",
    "random": "random mask against an independent brute force scan",
    "stride": "a mask built to catch a measurer that steps over corners",
}


def summarise(rows):
    out = []
    for kind in ("hand", "random", "stride"):
        these = [r for r in rows if r["kind"] == kind]
        out.append({
            "kind": kind,
            "what_the_case_is": KIND_WHAT[kind],
            "cases": len(these),
            "cases_that_agree": sum(1 for r in these if r["agrees_with_brute_force"] == "yes"),
            "cases_where_the_two_implementations_and_brute_force_all_agree":
                sum(1 for r in these if r["all_three_agree"] == "yes"),
        })
    return out


def write_csv(path, note, columns, rows):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="") as fh:
        fh.write('"%s"\n' % note)
        w = csv.DictWriter(fh, fieldnames=columns)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ev = os.path.join(os.path.dirname(here), "evidence")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--negative", action="store_true",
                    help="run the same suite against a deliberately broken measurer that steps "
                         "its corners by 8, to show the suite catches it")
    ap.add_argument("--evidence", default=ev)
    a = ap.parse_args()

    if a.negative:
        rows = build_rows(lambda m: broken_stride_largest_square(m, 8))
        write_csv(os.path.join(a.evidence, "square-selftest-negative.csv"),
                  "# the SAME suite run against broken_stride_largest_square of "
                  "tools/square_selftest.py, which steps its top left corners by 8 instead of "
                  "visiting every one. Every row where agrees_with_brute_force is no is a case "
                  "the suite catches. If this file ever showed every case agreeing, the suite "
                  "would be worthless and the measurer unguarded.",
                  CASE_COLUMNS, rows)
        summary = summarise(rows)
        caught = {s["kind"]: s["cases"] - s["cases_that_agree"] for s in summary}
        for s in summary:
            print("negative %-7s cases %3d, agree %3d, caught %3d"
                  % (s["kind"], s["cases"], s["cases_that_agree"],
                     s["cases"] - s["cases_that_agree"]))
        if caught.get("stride", 0) < 1:
            sys.exit("the negative check did not catch the stride case: the suite is worthless")
        if sum(caught.values()) < 2:
            sys.exit("the negative check caught only the stride case")
        print("negative check: the broken measurer is caught on %d cases of %d"
              % (sum(caught.values()), len(rows)))
        return

    rows = build_rows(square.largest_square)
    write_csv(os.path.join(a.evidence, "square-selftest.csv"), CASE_NOTE, CASE_COLUMNS, rows)
    summary = summarise(rows)
    write_csv(os.path.join(a.evidence, "square-selftest-summary.csv"), SUMMARY_NOTE,
              SUMMARY_COLUMNS, summary)

    for s in summary:
        print("%-7s cases %3d, agree %3d, all three agree %3d"
              % (s["kind"], s["cases"], s["cases_that_agree"],
                 s["cases_where_the_two_implementations_and_brute_force_all_agree"]))
    failed = [r["case"] for r in rows if r["ok"] != "yes"]
    if failed:
        sys.exit("self test FAILED on %d cases: %s" % (len(failed), ", ".join(failed[:10])))
    expected = {"hand": 7, "random": RANDOM_CASES, "stride": 1}
    for s in summary:
        if s["cases"] != expected[s["kind"]]:
            sys.exit("kind %s ran %d cases, %d declared"
                     % (s["kind"], s["cases"], expected[s["kind"]]))
    print("self test passed, %d cases, seed %d" % (len(rows), SEED))


if __name__ == "__main__":
    main()
