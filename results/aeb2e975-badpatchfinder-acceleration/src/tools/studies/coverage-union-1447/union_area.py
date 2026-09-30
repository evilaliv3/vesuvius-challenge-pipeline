#!/usr/bin/env python3
"""The deduplicated union of the delivered cells of the measured PHerc1447 seeds, in cm2, certified beside.

Written 2026-09-24T07:4xZ for runs/rev1/coverage-union-1447 (PLAN 66), declared in DECLARATION.md before any
number. Stevens' measure on our sheets: «around 365 cm² of coverage on PHerc. 1667» (scrollprize.org/winners,
the quote is read from the saved page by this tool), different scroll, same family of tool.

DEFINITIONS (DECLARATION.md):
  local cell area a_c = |d_i x d_j| x (voxel mm)^2, d central differences on the sheet lattice, one sided at an
      edge, the sheet's median steps product where a cell has no neighbour along i or j (counted);
  bin = floor(p / 4) per voxel coordinate, side 4 voxels = one cell step (0.03456 mm at 8.64 um);
  union = sum over bins of max over sheets of (sum of a_c of that sheet's cells in the bin);
  summed bound = sum of every a_c of every sheet, every overlap counted;
  certified cells of a sheet, per mode asis and pitchband = certified-area's certified region (the largest
      piece the winding certificate leaves), computed here by certified_region.measure, imported unchanged.

    union_area.py --selftest
    union_area.py sheet <attempt> <k>          one sheet: cells, a_c, certified masks -> scratch/sheets/
    union_area.py combine                      every sheet -> evidence/union.csv, evidence/union-per-sheet.csv
    union_area.py list                         the sheets the v7 file names, one "<attempt> <k>" per line

Every mode runs the self test first and refuses to write anything if one case fails.
"""
import csv, glob, hashlib, html, json, os, re, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
R1 = "/data/scrollagent/runs/rev1"
TOOL = "coverage-union-1447/tools/union_area.py"
CA = os.path.join(R1, "certified-area")
SEEDS = os.path.join(R1, "seeds-at-scale-1447")
V7 = os.path.join(SEEDS, "evidence", "per-seed-queue-v7.csv")
OUT = os.path.join(SEEDS, "out")
SCR = os.path.join(STUDY, "scratch", "sheets")
EV = os.path.join(STUDY, "evidence")
NM = "not measurable"
SCROLL = "PHerc1447"
BIN = 4.0                  # voxels: one cell step (DECLARATION.md)
ROW_TEXT = "coverage by delivered sheets, deduplicated, on an eligible scroll, certified beside"
STEVENS_RE = r"around\s+(\d+)\s*cm²\s+of coverage on PHerc\.\s*1667"

sys.path.insert(0, os.path.join(CA, "tools"))
import certified_region as CR  # noqa: E402  (imports voxel.py and square.py itself)

SQ = CR.SQ
VOX_UM = CR.voxel_um(SCROLL)[0]
MM = VOX_UM * 1e-3


# ------------------------------------------------------------------------------------------------
# The measurement
# ------------------------------------------------------------------------------------------------

def local_area(px, py, pz, valid):
    """a_c in mm2 on the lattice, and the number of cells that fell back to the median steps."""
    P = np.stack([px, py, pz], -1)

    def diff(axis):
        n = valid.shape[axis]
        prev = np.zeros_like(valid); nxt = np.zeros_like(valid)
        Pp = np.zeros_like(P); Pn = np.zeros_like(P)
        if axis == 0:
            prev[1:] = valid[:-1]; nxt[:-1] = valid[1:]; Pp[1:] = P[:-1]; Pn[:-1] = P[1:]
        else:
            prev[:, 1:] = valid[:, :-1]; nxt[:, :-1] = valid[:, 1:]; Pp[:, 1:] = P[:, :-1]; Pn[:, :-1] = P[:, 1:]
        d = np.full(P.shape, np.nan)
        both = valid & prev & nxt
        d[both] = (Pn[both] - Pp[both]) / 2.0
        on = valid & nxt & ~prev
        d[on] = Pn[on] - P[on]
        op = valid & prev & ~nxt
        d[op] = P[op] - Pp[op]
        return d
    di, dj = diff(0), diff(1)
    a = np.linalg.norm(np.cross(di, dj), axis=-1) * MM * MM
    fb = valid & ~np.isfinite(a)
    if fb.any():
        si, _ = SQ.median_step(valid, px, py, pz, 0)
        sj, _ = SQ.median_step(valid, px, py, pz, 1)
        if not (np.isfinite(si) and np.isfinite(sj)):
            raise SystemExit("median steps not measurable and %d cells need them" % int(fb.sum()))
        a[fb] = si * sj * MM * MM
    return a, int(fb.sum())


def bin_keys(P, side, shift):
    """Packed int64 key of the cube floor((p + shift) / side), 21 bits per coordinate."""
    b = np.floor((P + shift) / side).astype(np.int64)
    if b.min() < 0 or b.max() >= (1 << 21):
        raise SystemExit("bin index outside 0 to 2^21: %d to %d" % (b.min(), b.max()))
    return (b[:, 2] << 42) | (b[:, 1] << 21) | b[:, 0]


def union_of(sheets, side=BIN, shift=0.0):
    """sheets: list of (P (n, 3) voxels, a (n,) mm2). Returns (union_mm2, summed_mm2, bins, pairs)."""
    keys, sums, summed = [], [], 0.0
    for P, a in sheets:
        if len(a) == 0:
            continue
        k = bin_keys(P, side, shift)
        u, inv = np.unique(k, return_inverse=True)
        keys.append(u); sums.append(np.bincount(inv.ravel(), weights=a, minlength=len(u)))
        summed += float(np.sum(a, dtype=np.float64))
    if not keys:
        return 0.0, 0.0, 0, 0
    K = np.concatenate(keys); S = np.concatenate(sums)
    del keys, sums
    o = np.argsort(K, kind="stable")
    K = K[o]; S = S[o]
    del o
    start = np.flatnonzero(np.r_[True, K[1:] != K[:-1]])
    mx = np.maximum.reduceat(S, start)
    return float(np.sum(mx, dtype=np.float64)), summed, int(len(start)), int(len(K))


# ------------------------------------------------------------------------------------------------
# The self test
# ------------------------------------------------------------------------------------------------

def plane(ni, nj, j0=0, normal_shift=0.0, jitter=0.0, seed=0):
    """A tilted flat lattice: rows i, columns j0..j0+nj-1 at 4 voxels along two orthonormal directions."""
    n = np.array([1.0, 0.7, 0.4]); n /= np.linalg.norm(n)
    u = np.cross(n, [0.0, 0.0, 1.0]); u /= np.linalg.norm(u)
    v = np.cross(n, u)
    O = np.array([3000.3, 2000.7, 10000.1]) + normal_shift * n
    I, J = np.meshgrid(np.arange(ni, dtype=np.float64), np.arange(j0, j0 + nj, dtype=np.float64), indexing="ij")
    P = O + 4.0 * I[..., None] * u + 4.0 * J[..., None] * v
    if jitter:
        P = P + np.random.default_rng(seed).uniform(-jitter, jitter, P.shape)
    return P


def as_sheet(P, via_file=None):
    """The lattice as certified_region reads it; through a patch file when via_file is given."""
    ni, nj = P.shape[:2]
    if via_file:
        rec = np.zeros(ni * nj, dtype=CR.POINT)
        I, J = np.meshgrid(np.arange(ni), np.arange(nj), indexing="ij")
        rec["x"], rec["y"] = I.ravel(), J.ravel()
        rec["px"], rec["py"], rec["pz"] = P[..., 0].ravel(), P[..., 1].ravel(), P[..., 2].ravel()
        rec.tofile(via_file)
        px, py, pz, valid, coll = CR.lattice_from_patch(via_file)
        if coll:
            raise SystemExit("self test lattice collisions %d" % coll)
    else:
        # the delivered sheets store float32 positions: identical copies must be identical after that rounding
        P = P.astype(np.float32).astype(np.float64)
        px, py, pz = P[..., 0], P[..., 1], P[..., 2]; valid = np.ones((ni, nj), bool)
    a, fb = local_area(px, py, pz, valid)
    Q = np.stack([px[valid], py[valid], pz[valid]], 1)
    return Q, a[valid], fb


def selftest(write=True):
    rows, ok_all = [], True
    cell = 16.0 * MM * MM                      # one cell, 4 x 4 voxels, in mm2

    def check(case, q, expected, got, ok):
        nonlocal ok_all
        rows.append([case, q, expected, got, "yes" if ok else "no"]); ok_all &= bool(ok)

    def rel(x, y):
        return abs(x - y) / y

    os.makedirs(SCR, exist_ok=True)
    tmp = os.path.join(STUDY, "scratch", "selftest_patch.bin")
    A = as_sheet(plane(100, 100), via_file=tmp)
    # (a)
    ea = 10000 * cell
    u, s, bins, _ = union_of([A[:2]])
    check("a", "sum of a_c mm2 (file round trip)", "%.9f" % ea, "%.9f" % s, rel(s, ea) <= 1e-6)
    check("a", "union mm2", "%.9f" % ea, "%.9f" % u, rel(u, ea) <= 1e-6)
    check("a", "fallback cells", 0, A[2], A[2] == 0)
    # (e) on (a): bin count times one bin face area is not the area
    cnt = bins * (BIN * MM) ** 2
    check("e", "bin count x bin face mm2 differs from area by > 5 per cent", "> 0.05",
          "%.4f" % rel(cnt, ea), rel(cnt, ea) > 0.05)
    # (b)
    u, s, _, _ = union_of([A[:2], A[:2]])
    check("b", "union mm2 of two identical copies", "%.9f" % ea, "%.9f" % u, rel(u, ea) <= 1e-6)
    check("b", "summed bound mm2", "%.9f" % (2 * ea), "%.9f" % s, rel(s, 2 * ea) <= 1e-6)
    # (c)
    B = as_sheet(plane(100, 100, j0=50))
    ec = 15000 * cell
    u, s, _, _ = union_of([A[:2], B[:2]])
    check("c", "union mm2, overlap 50 columns, within [0.98, 1.0] of exact", "%.9f" % ec, "%.9f" % u,
          0.98 * ec <= u <= ec * (1 + 1e-6))
    check("c", "union shortfall share (edge of the overlap)", "0 to 0.02", "%.6f" % (1 - u / ec), True)
    check("c", "summed bound mm2", "%.9f" % (2 * ea), "%.9f" % s, rel(s, 2 * ea) <= 1e-6)
    c_union = u
    # (d)
    D = as_sheet(plane(100, 100, normal_shift=14.0))
    u, s, _, _ = union_of([A[:2], D[:2]])
    check("d", "union mm2, parallel copy 14 voxels away", "%.9f" % (2 * ea), "%.9f" % u, rel(u, 2 * ea) <= 1e-6)
    # (f)
    F = as_sheet(plane(100, 100, j0=50, jitter=0.3, seed=7))
    u, s, _, _ = union_of([A[:2], F[:2]])
    check("f", "union within [exact (c) union, summed bound]", "%.9f to %.9f" % (c_union, s), "%.9f" % u,
          c_union * (1 - 1e-6) <= u <= s * (1 + 1e-6))
    check("f", "excess over the exact union, share (0.3 voxel jitter of the copy)", "characterisation",
          "%.6f" % (u / ec - 1), True)
    # the shifted grid and the 8 voxel grid obey the same identities on (a) and (b)
    for side, shift in ((BIN, BIN / 2), (2 * BIN, 0.0)):
        u, s, _, _ = union_of([A[:2], A[:2]], side, shift)
        check("b", "union mm2 of two copies, side %g shift %g" % (side, shift), "%.9f" % ea, "%.9f" % u,
              rel(u, ea) <= 1e-6)
    # the certificate's own self test, unchanged, not written into the other study
    okc, _ = CR.selftest(SCROLL, write=False)
    check("cert", "certified_region.selftest(PHerc1447) every case", "yes", "yes" if okc else "no", okc)
    if os.environ.get("SA_SELFTEST_BREAK") == "1":
        check("break", "planted failure (tests the refusal path only)", "yes", "no", False)
    try:
        os.remove(tmp)
    except OSError:
        pass
    if write:
        with open(os.path.join(EV, "union-selftest.csv"), "w", newline="") as fh:
            fh.write('"# written by %s: the self test on synthetic tilted sheets whose answers are fixed in '
                     'DECLARATION.md before any number (a one sheet, b two identical copies, c overlap of 50 columns, '
                     'd a parallel copy 14 voxels away, e bin count is not area, f a copy jittered by 0.3 voxel), plus '
                     'certified_region.py\'s own self test. voxel %s um. The tool refuses to write if one is no."\n'
                     % (TOOL, VOX_UM))
            w = csv.writer(fh)
            w.writerow(["case", "quantity", "expected", "got", "passed"])
            w.writerows(rows)
            w.writerow(["all", "every case", "yes", "yes" if ok_all else "no", "yes" if ok_all else "no"])
    return ok_all, rows


def require_selftest(write=False):
    ok, rows = selftest(write=write)
    if not ok:
        for r in rows:
            if r[-1] != "yes":
                print("SELF TEST FAILED:", r, file=sys.stderr)
        raise SystemExit("REFUSED: the self test failed; nothing written")
    print("self test passed (%d checks)" % len(rows), flush=True)


# ------------------------------------------------------------------------------------------------
# Inputs
# ------------------------------------------------------------------------------------------------

def read_rows(path):
    L = [l for l in open(path, newline="") if not l.lstrip('"').startswith("#")]
    return list(csv.DictReader(L))


def seeds():
    out = []
    for r in read_rows(V7):
        try:
            float(r["largest_square_mm_min_step"])
        except ValueError:
            continue
        if r["passes_rule"] != "yes":
            continue
        out.append((r["attempt"], int(r["delivered_sheets"])))
    return out


def sheet_list():
    L = []
    for a, n in seeds():
        for k in range(n):
            p = os.path.join(OUT, a, "C40", "patch_%d.bin" % k)
            if not os.path.isfile(p) or os.path.getsize(p) == 0:
                raise SystemExit("REFUSED: missing sheet %s" % p)
            L.append((a, k))
    return L


def label(a, k):
    return "%s-S%d" % (a, k)


def do_sheet(a, k):
    path = os.path.join(OUT, a, "C40", "patch_%d.bin" % k)
    px, py, pz, valid, coll = CR.lattice_from_patch(path)
    area, fb = local_area(px, py, pz, valid)
    si, _ = SQ.median_step(valid, px, py, pz, 0)
    sj, _ = SQ.median_step(valid, px, py, pz, 1)
    W = CR.certificate_module(SCROLL)
    rows, bands = W.axis_table(), W.pitch_bands()
    got, masks = CR.measure(W, rows, bands, px, py, pz, valid, VOX_UM, ("asis", "pitchband"))
    os.makedirs(SCR, exist_ok=True)
    L = label(a, k)
    tmp = os.path.join(SCR, L + ".tmp.npz")
    np.savez(tmp, P=np.stack([px[valid], py[valid], pz[valid]], 1).astype(np.float32),
             a=area[valid], asis=masks["asis"][valid], pitchband=masks["pitchband"][valid])
    n = int(valid.sum())
    info = dict(label=L, attempt=a, sheet=k, input=os.path.relpath(path, R1), cells=n, lattice_collisions=coll,
                sum_a_mm2=float(area[valid].sum()), cells_with_fallback_area=fb,
                step_i_mm=si * MM, step_j_mm=sj * MM, cells_x_steps_mm2=n * si * sj * MM * MM,
                certified_cells_asis=got["asis"]["certified_cells"],
                certified_cells_pitchband=got["pitchband"]["certified_cells"],
                sum_a_certified_asis_mm2=float(area[masks["asis"]].sum()),
                sum_a_certified_pitchband_mm2=float(area[masks["pitchband"]].sum()),
                sha256=hashlib.sha256(open(path, "rb").read()).hexdigest())
    os.replace(tmp, os.path.join(SCR, L + ".npz"))
    with open(os.path.join(SCR, L + ".json"), "w") as fh:
        json.dump(info, fh)
    print("%s: %d cells, %.3f cm2, certified asis %d pitchband %d" % (
        L, n, info["sum_a_mm2"] / 100, info["certified_cells_asis"], info["certified_cells_pitchband"]), flush=True)


# ------------------------------------------------------------------------------------------------
# The combination
# ------------------------------------------------------------------------------------------------

def stevens():
    pages = sorted(glob.glob(os.path.join(EV, "winners-*.html")))
    if not pages:
        raise SystemExit("REFUSED: no saved winners page in evidence/")
    p = pages[-1]
    t = html.unescape(re.sub(r"<[^>]+>", "", open(p, encoding="utf-8").read()))
    m = re.search(STEVENS_RE, t)
    if not m:
        raise SystemExit("REFUSED: Stevens' sentence not found in %s" % p)
    return m.group(0), float(m.group(1)), os.path.basename(p), hashlib.sha256(open(p, "rb").read()).hexdigest()


def squares_reference(attempts):
    """points x step_i_mm x step_j_mm over squares-*.csv rows: (cm2 over the given attempts, sheets, cm2 over all
    files, sheets, files, rows not numeric)."""
    mine = allc = 0.0; nm = na = bad = 0
    files = sorted(glob.glob(os.path.join(SEEDS, "evidence", "squares-PHerc1447-seed*.csv")))
    for f in files:
        for r in read_rows(f):
            try:
                v = int(r["points"]) * float(r["step_i_mm"]) * float(r["step_j_mm"]) / 100.0
            except (ValueError, KeyError):
                bad += 1
                continue
            allc += v; na += 1
            if r["point"] in attempts:
                mine += v; nm += 1
    return mine, nm, allc, na, len(files), bad


def combine():
    S = seeds()
    L = sheet_list()
    expected = sum(n for _, n in S)
    if len(L) != expected:
        raise SystemExit("REFUSED: %d sheets listed against %d delivered_sheets" % (len(L), expected))
    missing = [label(a, k) for a, k in L if not os.path.isfile(os.path.join(SCR, label(a, k) + ".json"))]
    if missing:
        raise SystemExit("REFUSED: %d sheets not measured yet, first %s" % (len(missing), missing[0]))
    infos = [json.load(open(os.path.join(SCR, label(a, k) + ".json"))) for a, k in L]

    # the known reference: certified-area's own rows on the sheets it measured
    ref = {}
    for r in read_rows(os.path.join(CA, "evidence", "certified-area.csv")):
        if r["label"].startswith("DELIV-"):
            ref[(r["label"], r["mode"])] = int(r["certified_cells"])
    compared = 0
    for i in infos:
        lab = "DELIV-%s-S%d" % (i["attempt"].replace("PHerc1447-", ""), i["sheet"])
        eq = []
        for mode in ("asis", "pitchband"):
            if (lab, mode) in ref:
                g = i["certified_cells_" + mode]
                if g != ref[(lab, mode)]:
                    raise SystemExit("REFUSED: %s %s certified cells %d here, %d in certified-area.csv"
                                     % (lab, mode, g, ref[(lab, mode)]))
                eq.append("yes")
                compared += 1
        i["certified_cells_equals_certified_area"] = ("yes, both modes" if len(eq) == 2 else
                                                      "not measured there (not its best sheet)")

    # per sheet CSV
    with open(os.path.join(EV, "union-per-sheet.csv"), "w", newline="") as fh:
        fh.write('"# written by %s: one row per delivered sheet of the seeds of per-seed-queue-v7.csv with a measured '
                 'square and passes_rule yes. sum_a_cm2 is the sum of the local cell areas |d_i x d_j| (central '
                 'differences on the lattice); sum_a_over_cells_x_steps checks it against cells x the median steps. '
                 'certified cells per mode are certified-area\'s certified region (largest piece) computed by '
                 'certified_region.measure; certified_cells_equals_certified_area compares with certified-area.csv '
                 'where that study measured the same sheet."\n' % TOOL)
        w = csv.writer(fh)
        cols = ["label", "input", "cells", "lattice_collisions", "sum_a_cm2", "cells_x_steps_cm2",
                "sum_a_over_cells_x_steps", "cells_with_fallback_area", "step_i_mm", "step_j_mm",
                "certified_cells_asis", "certified_cm2_asis", "certified_cells_pitchband", "certified_cm2_pitchband",
                "certified_cells_equals_certified_area", "sha256", "tool"]
        w.writerow(cols)
        for i in infos:
            w.writerow([i["label"], i["input"], i["cells"], i["lattice_collisions"], "%.6f" % (i["sum_a_mm2"] / 100),
                        "%.6f" % (i["cells_x_steps_mm2"] / 100), "%.6f" % (i["sum_a_mm2"] / i["cells_x_steps_mm2"]),
                        i["cells_with_fallback_area"], "%.6f" % i["step_i_mm"], "%.6f" % i["step_j_mm"],
                        i["certified_cells_asis"], "%.6f" % (i["sum_a_certified_asis_mm2"] / 100),
                        i["certified_cells_pitchband"], "%.6f" % (i["sum_a_certified_pitchband_mm2"] / 100),
                        i["certified_cells_equals_certified_area"], i["sha256"], TOOL])

    quote, snum, spage, ssha = stevens()
    attempts = {a for a, _ in S}
    sq_mine, sq_mine_n, sq_all, sq_all_n, sq_files, sq_bad = squares_reference(attempts)

    def load(sel):
        out = []
        for a, k in L:
            z = np.load(os.path.join(SCR, label(a, k) + ".npz"))
            P = z["P"].astype(np.float64); ar = z["a"]
            if sel != "all":
                m = z[sel]; P = P[m]; ar = ar[m]
            out.append((P, ar))
        return out

    results = {}
    for sel in ("all", "asis", "pitchband"):
        sh = load(sel)
        cells = sum(len(a) for _, a in sh)
        u, s, bins, pairs = union_of(sh, BIN, 0.0)
        u2, s2, _, _ = union_of(sh, BIN, BIN / 2)
        u8, s8, bins8, _ = union_of(sh, 2 * BIN, 0.0)
        if not (abs(s - s2) <= 1e-6 * s and abs(s - s8) <= 1e-6 * s):
            raise SystemExit("REFUSED: summed bound differs between grids")
        if u > s * (1 + 1e-9):
            raise SystemExit("REFUSED: union above the summed bound")
        results[sel] = dict(cells=cells, u=u, s=s, bins=bins, pairs=pairs, u2=u2, u8=u8, bins8=bins8)
        print("%s: %d cells, union %.3f cm2, summed %.3f cm2, shifted %.3f, side 8 %.3f" % (
            sel, cells, u / 100, s / 100, u2 / 100, u8 / 100), flush=True)
        del sh

    s_all = results["all"]["s"]
    with open(os.path.join(EV, "union.csv"), "w", newline="") as fh:
        fh.write('"# written by %s: the union of the delivered cells of PHerc1447, deduplicated at one cell: bins of '
                 'side %g voxels (%.5f mm at %s um), union = sum over bins of max over sheets of the sheet\'s summed '
                 'local cell area |d_i x d_j| in the bin; summed_bound_cm2 counts every overlap. cell_set all is every '
                 'delivered cell; asis and pitchband are the cells of certified-area\'s certified region per sheet in '
                 'that mode. certified_union_under_tenth_of_summed is the director\'s falsifier (07:36:15Z) on the '
                 'certified rows, with the summed bound of ALL delivered cells as denominator. Stevens\' number is on '
                 'PHerc1667, a different scroll, quoted from the saved page. The shifted and side 8 columns are '
                 'sensitivity, never the number. Self test: evidence/union-selftest.csv, passed, or no row is written."\n'
                 % (TOOL, BIN, BIN * MM, VOX_UM))
        w = csv.writer(fh)
        w.writerow(["row_text", "scroll", "cell_set", "seeds_counted", "sheets", "cells", "union_cm2",
                    "summed_bound_cm2", "union_over_summed", "summed_bound_all_cells_cm2",
                    "union_over_summed_all_cells", "certified_union_under_tenth_of_summed", "bins_occupied",
                    "sheet_bin_pairs", "union_shifted_half_bin_cm2", "union_bin_side_8_voxels_cm2",
                    "squares_points_x_steps_cm2_these_seeds", "squares_rows_these_seeds",
                    "squares_points_x_steps_cm2_all_34_files", "squares_rows_all_files", "squares_files",
                    "squares_rows_not_numeric", "stevens_quote", "stevens_cm2_as_stated", "stevens_scroll",
                    "stevens_source", "stevens_page_sha256", "union_over_stevens_365", "union_passes_stevens",
                    "bin_side_voxels", "bin_side_mm", "voxel_um", "certified_rows_compared_with_certified_area",
                    "selftest", "tool"])
        for sel in ("all", "asis", "pitchband"):
            r = results[sel]
            fals = "" if sel == "all" else ("yes" if r["u"] < 0.1 * s_all else "no")
            w.writerow([ROW_TEXT, SCROLL, sel if sel == "all" else "certified " + sel, len(S), len(L), r["cells"],
                        "%.4f" % (r["u"] / 100), "%.4f" % (r["s"] / 100), "%.6f" % (r["u"] / r["s"]) if r["s"] else NM,
                        "%.4f" % (s_all / 100), "%.6f" % (r["u"] / s_all), fals, r["bins"], r["pairs"],
                        "%.4f" % (r["u2"] / 100), "%.4f" % (r["u8"] / 100), "%.4f" % sq_mine, sq_mine_n,
                        "%.4f" % sq_all, sq_all_n, sq_files, sq_bad, quote, "%g" % snum, "PHerc1667",
                        "https://scrollprize.org/winners saved as evidence/%s" % spage, ssha,
                        "%.4f" % (r["u"] / 100 / snum), "yes" if r["u"] / 100 > snum else "no",
                        "%g" % BIN, "%.5f" % (BIN * MM), VOX_UM, compared,
                        "evidence/union-selftest.csv passed", TOOL])
    print("written evidence/union.csv and evidence/union-per-sheet.csv", flush=True)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cmd = sys.argv[1]
    if cmd == "list":
        for a, k in sheet_list():
            print(a, k)
        return
    if cmd == "--selftest":
        require_selftest(write=True)
        return
    if cmd == "sheet":
        require_selftest(write=False)
        do_sheet(sys.argv[2], int(sys.argv[3]))
    elif cmd == "combine":
        require_selftest(write=True)
        combine()
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
