#!/usr/bin/env python3
"""cuts-2715/tools/headline.py: the void test and eye cuts on the article's headline square, R2c seed6273 squarecentre, adjudicated
certified square 28.1285 mm (DECLARATION addition 09:18Z). Reuses cuts.py's cut, profiles and drawings and sheetrun.py's void test
unchanged, with the module globals pointed at this square. -> evidence/headline-cuts.csv, evidence/headline-air.csv,
scratch/png/headline-*.png. Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran."""
import csv, os, sys
import numpy as np
H = "/data/scrollagent/runs/rev1/cuts-2715"
sys.path.insert(0, H + "/tools")
import cuts as C  # noqa: E402
import sheetrun as SR  # noqa: E402
TOOL = "cuts-2715/tools/headline.py"
ROUTE, NAME = "R2cnative", "PHerc0826-seed6273-squarecentre"
adj = [r for r in C.rows(C.RR + "/evidence/square-checks-adjudicated.csv") if r["route"] == ROUTE and r["surface"] == NAME][-1]
b = int(adj["certified_adjudicated_cells"]); i0, j0 = map(int, adj["certified_adjudicated_corner"].split())
STEP = float(adj["step_mm"])
if (b, i0, j0, adj["certified_adjudicated_mm"], STEP) != (748, 392, 374, "28.1285", 0.037605):
    raise SystemExit("refuse: adjudicated row differs from the declaration: %r" % adj)
if abs(SR.T_AIR - 63.0) > 1e-9:
    raise SystemExit("refuse: T_air")
P, V = C.RT.surface(ROUTE, NAME)[:2]
if not V[i0:i0 + b, j0:j0 + b].all():
    raise SystemExit("refuse: invalid nodes inside the square")
C.SQP = P[i0:i0 + b, j0:j0 + b].astype(np.float64); C.ZS = C.SQP[..., 2]; C.b = b
if not (np.diff(C.ZS, axis=0) < 0).all():
    raise SystemExit("refuse: z not strictly decreasing along i")
C.PARTNERS = []


def main():
    zv = np.load(C.RR + "/scratch/values-%s-%s.npz" % (ROUTE, NAME))
    VAL = zv["VAL"].astype(np.float64)[i0:i0 + b, j0:j0 + b]
    meas = np.isfinite(VAL)
    zmin, zmax = float(C.ZS.min()), float(C.ZS.max())
    cuts = [("even%d" % k, int(round(zmin + (k + 0.5) / 7.0 * (zmax - zmin))), "") for k in range(7)]
    rm = np.array([np.mean(VAL[i][meas[i]]) if meas[i].any() else np.inf for i in range(b)])
    r1 = int(np.argmin(rm)); rm2 = rm.copy(); rm2[max(0, r1 - 50):r1 + 51] = np.inf; r2 = int(np.argmin(rm2))
    for n_, r in ((1, r1), (2, r2)):
        cuts.append(("dark-row%d" % n_, int(round(float(np.median(C.ZS[r])))), "row %d mean grey %.1f" % (r, rm[r])))
    rows_out = []
    for tag, zc, note in cuts:
        name = "headline-%s-%d" % (tag, zc)
        js, ist, pts, t, nrm = C.cut_nodes(zc)
        n = len(js)
        raw = C.profiles(pts, nrm, np.zeros(n))
        v, vr = SR.void_runs(raw)
        longest = max(vr, key=lambda r: r[1] - r[0]) if vr else None
        L = (longest[1] - longest[0] + 1) if longest else 0
        k0 = (longest[0] + longest[1]) // 2 if longest else n // 2
        O, _ = C.ours_near(pts[:, :2], zc); Q2 = np.zeros((0, 3), np.float32)
        s0 = C.score(raw)
        sp = C.strip_png(name, zc, js, raw, dict(d=np.full(n, np.nan), flips=[], gaps=[(a, e, "", 0, 0) for a, e in vr if e - a + 1 >= 25]),
                         C.to_strip(O, pts, t, nrm), np.zeros((0, 2)),
                         "%s %s: axial cut z %d inside the adjudicated square (columns %d..%d of 748), %d nodes; blue bars void runs 25+ "
                         "(T_air 63)" % (ROUTE, NAME, zc, js[0], js[-1], n))
        C.HALF, C.MAG = 320, 2
        bp = C.box_png(name, pts[k0], zc, pts, O, Q2, "%s: z %d, centre node %d (column %d), %s" % (
            name, zc, k0, js[k0], "middle of the longest void run (%d nodes)" % L if longest else "middle node, no void node"))
        C.HALF, C.MAG = 128, 5
        zp = C.box_png(name + "-zoom", pts[k0], zc, pts, O, Q2, "%s: z %d, 2.4 mm at 5 x, centre node %d (column %d)" % (name, zc, k0, js[k0]))
        row = dict(utc=C.utc(), cut=name, zc=zc, kind=tag, note=note, nodes=n, first_column=int(js[0]), last_column=int(js[-1]),
                   void_nodes=int(v.sum()), void_runs_25plus=sum(1 for a, e in vr if e - a + 1 >= 25),
                   longest_void_run_nodes=L, longest_void_run_mm="%.3f" % (L * STEP),
                   longest_void_run_columns=("%d..%d" % (js[longest[0]], js[longest[1]])) if longest else "none",
                   inside_square="yes (only the square's columns are cut)", median_centre_value="%.1f" % np.nanmedian(s0["sm"][:, C.OFF == 0]),
                   strip_png=sp, box_png=bp, zoom_png=zp)
        rows_out.append(row)
        print(row, flush=True)
    with open(H + "/evidence/headline-cuts.csv", "w", newline="") as f:
        f.write("# written by %s at %s: void test (T_air 63.0, runs of 25+ nodes) on 9 axial cuts of the headline square %s %s, adjudicated "
                "28.1285 mm (DECLARATION addition 09:18Z)\n" % (TOOL, C.utc(), ROUTE, NAME))
        w = csv.DictWriter(f, list(rows_out[0]), lineterminator="\n"); w.writeheader(); w.writerows(rows_out)
    air = dict(utc=C.utc(), route=ROUTE, surface=NAME, square_mm=adj["certified_adjudicated_mm"], cells=b * b,
               cells_measurable=int(meas.sum()), cells_not_measurable=int((~meas).sum()),
               cells_le_57=int((VAL[meas] <= 57).sum()), share_le_57_of_measurable="%.4f" % float((VAL[meas] <= 57).mean()),
               square_median="%.1f" % float(np.median(VAL[meas])), zmin="%.1f" % zmin, zmax="%.1f" % zmax,
               lowest_rows="%d %d" % (r1, r2), lowest_row_means="%.1f %.1f" % (rm[r1], rm[r2]))
    with open(H + "/evidence/headline-air.csv", "w", newline="") as f:
        f.write("# written by %s at %s: air proxy on the headline square, VAL <= 57 (routes.py values npz, nearest voxel, raw scan); "
                "not measurable counted apart\n" % (TOOL, C.utc()))
        w = csv.DictWriter(f, list(air), lineterminator="\n"); w.writeheader(); w.writerow(air)
    print(air)


if __name__ == "__main__":
    main()
