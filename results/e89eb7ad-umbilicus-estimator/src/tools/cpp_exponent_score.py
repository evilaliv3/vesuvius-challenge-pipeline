# This file is a copy of tools/cpp_exponent_score.py of the working tree and differs from it in
# two ways: the estimates of the compiled function are read from evidence/ here beside
# everything else, and the docstring and what it prints are in English. Nothing that computes
# is changed.
"""The exponent ablation scored from the C++ estimates, with the same code as before.

It computes nothing of its own: it imports `exponent_ablation` and feeds it the estimates of the
compiled binaries in place of the transcription's, so that metric, baselines, bootstrap and
bootstrap seeds are the same and the only difference is who produced x and y.

The rows p = 0.5, p = 1.5 and p = 2 come from the three binaries with the weight raised to the
exponent; the row p = 1 is NOT recompiled, it is the same estimates as the weighted sum of the main
run, that is the shipped expression `1.0f / std::max(100.0f, dist)` and not `pow(..., 1.0f)`.

    python3 tools/cpp_exponent_score.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L              # noqa: E402
import exponent_ablation as E     # noqa: E402

EV = L.EV


def raw():
    rows = []
    guarded = []
    for r in L.read_csv(os.path.join(EV, "cpp-exponent-estimates.csv")):
        if int(r["guard"]):
            guarded.append(r)
            continue
        rows.append(dict(scroll=r["scroll"], z=int(r["z"]), k=int(r["k"]), seed=int(r["seed"]),
                         p=r["p"], x=float(r["x"]), y=float(r["y"]),
                         inside=int(r["inside"]), capped=0))
    # p = 1 is the weighted sum of the main run, not a fourth binary
    for r in L.read_csv(os.path.join(EV, "cpp-k20-estimates.csv")):
        if r["variant"] != "no-division" or int(r["guard"]):
            continue
        rows.append(dict(scroll=r["scroll"], z=int(r["z"]), k=int(r["k"]), seed=int(r["seed"]),
                         p="1.0", x=float(r["x"]), y=float(r["y"]),
                         inside=int(r["inside"]), capped=0))
    return rows, guarded


def main():
    rows_raw, guarded = raw()
    if guarded:
        print(f"WARNING: {len(guarded)} estimates met the guard:")
        for r in guarded:
            print(f"  {r['scroll']} z {r['z']} k {r['k']} p {r['p']}")

    rows, spr = [], []
    for scroll in L.CFG:
        part = [r for r in rows_raw if r["scroll"] == scroll]
        if not part:
            continue
        rows.extend(E.score(scroll, part))
        spr.extend(E.spread(scroll, part))

    # known reference: the p = 1 row must reproduce the no-division row of the shipped tables,
    # because those are literally the same estimates scored by the same code
    old = {q["scroll"]: q for q in L.read_csv(os.path.join(L.EV, "cpp-k20.csv"))
           if q["variant"] == "no-division"}
    bad = []
    for r in rows:
        if r["p"] != "1.0":
            continue
        q = old.get(r["scroll"])
        if not q:
            continue
        for f in ("median_mm", "ci_lo_mm", "ci_hi_mm", "inside", "margin_vs_centroid_mm"):
            if str(r[f]) != str(q[f]):
                bad.append((r["scroll"], f, q[f], r[f]))
    print("  known reference (p = 1 against the no-division row of cpp-k20.csv):",
          "reproduced" if not bad else f"NOT reproduced: {bad}", flush=True)

    L.write_csv(os.path.join(EV, "cpp-exponent-fifteen-k20.csv"), list(rows[0]), rows)
    L.write_csv(os.path.join(EV, "cpp-exponent-seed-spread.csv"), list(spr[0]), spr)
    print(f"written cpp-exponent-fifteen-k20.csv: {len(rows)} rows")
    for p in ("0.5", "1.0", "1.5", "2.0"):
        part = [r for r in rows if r["p"] == p]
        if not part:
            continue
        import statistics
        med = statistics.median(float(r["median_mm"]) for r in part)
        out = sum(int(r["inside_of"]) - int(r["inside"]) for r in part)
        print(f"  p = {p}: median over scrolls {med:.2f} mm, outside {out}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
