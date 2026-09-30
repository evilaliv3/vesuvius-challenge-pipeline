#!/usr/bin/env python3
"""cuts-2715/tools/sheetrun.py: rule C (surface against our 800 sheets) and the post hoc void test of cuts-2715/DECLARATION.md
(addition 09:13Z). -> evidence/sheet-runs.csv, evidence/rule-c.csv, evidence/verdict.csv (rules A, B, C side by side, eye column,
final = rule C). Released on 2026-09-30 by the owner's decision; this output was kept private while the study ran."""
import csv, os, sys
import numpy as np
from scipy import ndimage
H = "/data/scrollagent/runs/rev1/cuts-2715"
sys.path.insert(0, H + "/tools")
import cuts as C  # noqa: E402
import drift as DR  # noqa: E402
TOOL = "cuts-2715/tools/sheetrun.py"
OFF = C.OFF
MED = float(C.rows(C.RR + "/evidence/candidate-2715.csv")[-1]["square_median"])
T_AIR = 0.6 * MED
if abs(T_AIR - 63.0) > 1e-9:
    raise SystemExit("refuse: T_air %.3f differs from the declared 63.0" % T_AIR)


def runs_of(marks, shift=None):
    out = []
    for M, mk in sorted(marks.items()):
        per = {}
        for k, o in mk:
            k = int(k)
            per.setdefault(k, []).append(o - (shift[k] if shift is not None else 0.0))
        ks = sorted(per)
        groups, cur = [], [ks[0]]
        for k in ks[1:]:
            if k - cur[-1] <= 4:
                cur.append(k)
            else:
                groups.append(cur); cur = [k]
        groups.append(cur)
        for g in groups:
            if g[-1] - g[0] + 1 < 25:
                continue
            o = np.array([np.median(per[k]) for k in g])
            of = ndimage.median_filter(o, size=5, mode="nearest")
            out.append(dict(sheet=M, first=g[0], last=g[-1], nodes_with_marks=len(g), o_first=float(of[0]), o_last=float(of[-1]),
                            o_min=float(of.min()), o_max=float(of.max()), X=float(of.max() - of.min())))
    return out


def void_runs(raw):
    meas8 = np.isfinite(raw[:, C.W8]).all(1)
    sm = ndimage.gaussian_filter1d(np.nan_to_num(raw), 1.0, axis=1)
    sm = ndimage.uniform_filter1d(sm, 3, axis=0, mode="nearest")
    w3 = (OFF >= -3) & (OFF <= 3)
    v = meas8 & (sm[:, w3].max(1) < T_AIR)
    runs, k, n = [], 0, len(v)
    while k < n:
        if v[k]:
            e = k
            while e + 1 < n and v[e + 1]:
                e += 1
            runs.append((k, e)); k = e + 1
        else:
            k += 1
    return v, runs


def main():
    A_rows = {r["cut"]: r for r in C.rows(H + "/evidence/cuts.csv")}
    B_rows = {r["cut"]: r for r in C.rows(H + "/evidence/drift.csv")}
    run_rows, c_rows = [], {}
    for name, ra in A_rows.items():
        z = np.load(H + "/scratch/profiles-%s.npz" % name)
        js, pts, nrm, raw = z["js"], z["pts"], z["nrm"], z["raw"].astype(np.float64)
        zc = int(ra["zc"]); n = len(js)
        t = np.stack([nrm[:, 1], -nrm[:, 0]], 1)
        marks = DR.sheet_marks(pts, t, nrm, zc)
        R0 = runs_of(marks) if marks else []
        m = n // 2
        ramp = 12.0 * np.clip((np.arange(n) - (m - 5)) / 10.0, 0, 1)
        RR = runs_of(marks, ramp) if marks else []
        span = [r for r in RR if r["first"] <= m - 5 and r["last"] >= m + 5]
        ref_ok = bool(span) and all(r["X"] >= 8 for r in span)
        cov = np.zeros(n, bool)
        for r in R0:
            cov[r["first"]:r["last"] + 1] = True
        v, vr = void_runs(raw)
        long_void = [(a, e) for a, e in vr if e - a + 1 >= 25]
        pv = B_rows[name]["pitch_vox"]
        p = float(pv) if pv != C.NM else None
        Xmax = max([r["X"] for r in R0], default=None)
        reasons = []
        if p is None:
            verdict = "undecided"; reasons.append("pitch not measurable")
        else:
            big = [r for r in R0 if r["X"] >= p]
            if big or long_void:
                verdict = "no"
                if big:
                    reasons.append("%d run(s) with X >= p %.1f: %s" % (len(big), p, "; ".join(
                        "%s nodes %d..%d (columns %d..%d) X %.1f" % (r["sheet"], r["first"], r["last"], js[r["first"]], js[r["last"]], r["X"])
                        for r in big)))
                if long_void:
                    reasons.append("%d void run(s) of 25+ nodes (post hoc T_air 63): %s" % (len(long_void), "; ".join(
                        "nodes %d..%d (columns %d..%d, %d voxels)" % (a, e, js[a], js[e], 4 * (e - a + 1)) for a, e in long_void)))
            else:
                if cov.mean() < 0.80:
                    reasons.append("coverage %.4f < 0.80" % cov.mean())
                if any(r["X"] >= p / 2 for r in R0):
                    reasons.append("a run with p/2 <= X < p")
                verdict = "undecided" if reasons else "yes"
            if not ref_ok:
                reasons.append("ramp reference: %s" % ("no run spans the ramp" if not span else "a spanning run has X < 8"))
                if verdict == "yes":
                    verdict = "undecided"
        for r in R0:
            run_rows.append(dict(cut=name, zc=zc, sheet=r["sheet"], first_node=r["first"], last_node=r["last"],
                                 first_column=int(js[r["first"]]), last_column=int(js[r["last"]]), nodes_with_marks=r["nodes_with_marks"],
                                 o_first="%.1f" % r["o_first"], o_last="%.1f" % r["o_last"], o_min="%.1f" % r["o_min"], o_max="%.1f" % r["o_max"],
                                 X_vox="%.1f" % r["X"], X_ge_p=("yes" if p is not None and r["X"] >= p else "no")))
        c_rows[name] = dict(utc=C.utc(), cut=name, zc=zc, nodes=n, runs=len(R0), coverage="%.4f" % cov.mean(),
                            max_X_vox="%.1f" % Xmax if Xmax is not None else C.NM, pitch_vox=pv,
                            runs_X_ge_p=sum(1 for r in R0 if p is not None and r["X"] >= p),
                            runs_X_ge_half_p=sum(1 for r in R0 if p is not None and r["X"] >= p / 2),
                            void_nodes_post_hoc=int(v.sum()), void_runs_25plus_post_hoc=len(long_void),
                            longest_void_run_nodes=max([e - a + 1 for a, e in vr], default=0),
                            void_runs_detail="; ".join("%d..%d (columns %d..%d)" % (a, e, js[a], js[e]) for a, e in long_void),
                            ref_ramp_spanning_runs=len(span), ref_ramp_spanning_X=" ".join("%.1f" % r["X"] for r in span),
                            ref_ramp_ok="yes" if ref_ok else "no", verdict_c=verdict,
                            reason_c="; ".join(reasons) if reasons else "coverage >= 0.80, every run X < p/2, no void run, reference passed")
        print(name, verdict, c_rows[name]["reason_c"][:300], flush=True)

    def write(p, head, rows):
        with open(p, "w", newline="") as f:
            f.write(head + "\n")
            w = csv.DictWriter(f, list(rows[0]), lineterminator="\n"); w.writeheader(); w.writerows(rows)
    write(H + "/evidence/sheet-runs.csv", "# written by %s at %s: rule C runs (our 800 sheets against the surface, |o| <= 15, 25+ nodes)" % (TOOL, C.utc()), run_rows)
    write(H + "/evidence/rule-c.csv", "# written by %s at %s: rule C per cut (DECLARATION addition 09:13Z); the void test is post hoc "
          "(T_air 63.0)" % (TOOL, C.utc()), list(c_rows.values()))
    eye = {}
    ep = H + "/evidence/eye.csv"
    if os.path.exists(ep):
        eye = {r["cut"]: r["eye"] for r in C.rows(ep)}
    va = [A_rows[k]["verdict"] for k in A_rows]; vb = [B_rows[k]["verdict_b"] for k in A_rows]; vc = [c_rows[k]["verdict_c"] for k in A_rows]

    def ov(vs):
        return "no" if "no" in vs else ("yes" if all(v == "yes" for v in vs) else "undecided")
    with open(H + "/evidence/verdict.csv", "w", newline="") as f:
        f.write("# written by %s at %s: verdict per cut and overall; rules A (declaration 08:59:43Z), B (addition 09:06:20Z), C (addition "
                "09:13Z) side by side; A and B fail their references (see DECLARATION additions); final_one_layer = rule C; eye from "
                "evidence/eye.csv, the agent's look at every PNG, never changes a verdict\n" % (TOOL, C.utc()))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["cut", "zc", "rule_a_share_on_layer", "rule_a_null_share", "rule_a_verdict", "rule_b_max_E_vox", "rule_b_ref_ramp_seen",
                    "rule_b_verdict", "rule_c_coverage", "rule_c_max_X_vox", "rule_c_pitch_vox", "rule_c_void_runs_25plus_post_hoc",
                    "rule_c_ref_ramp_ok", "rule_c_verdict", "final_one_layer", "reason", "eye"])
        for k in A_rows:
            a, b, c = A_rows[k], B_rows[k], c_rows[k]
            w.writerow([k, a["zc"], a["share_on_layer"], a["null_shift6_share_on_layer"], a["verdict"], b["max_excursion_E_vox"],
                        b["ref_ramp_seen"], b["verdict_b"], c["coverage"], c["max_X_vox"], c["pitch_vox"], c["void_runs_25plus_post_hoc"],
                        c["ref_ramp_ok"], c["verdict_c"], c["verdict_c"], c["reason_c"], eye.get(k, "")])
        w.writerow(["overall", "", "", "", ov(va), "", "", ov(vb), "", "", "", "", "", ov(vc), ov(vc),
                    "rule C: yes %d, no %d, undecided %d of %d; rule B: no %d; rule A: no %d (A and B do not discriminate)" % (
                        vc.count("yes"), vc.count("no"), vc.count("undecided"), len(vc), vb.count("no"), va.count("no")), eye.get("overall", "")])
    print("overall C", ov(vc))


if __name__ == "__main__":
    main()
