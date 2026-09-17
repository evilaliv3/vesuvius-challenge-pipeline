# This file is a copy of tools/search_cap.py of the working tree and differs from it in one way
# only: the four saved slices are read from inputs/ here, through the module that carries them
# under its name here, and the file it writes is named as it is named here. Nothing else is
# changed.
#!/usr/bin/env python3
"""The cap on the hill climb: what it is, which runs met it, and what it does to the tables.

Written on 2026-09-18 for point 1 of the villa maintainer's review of pull request 1823, which
asks for the runner, the value of the cap, which variants used it, and how a capped run enters the
error and convergence statistics.

The cap is villa_estimator.MAX_SWEEPS = 2000 sweeps of the eight probes. It is not in the C++: the
loop at normalgridtools.cpp:119-142 halves the step only when no probe improves, so it has no
iteration limit. A capped run is not dropped and is not recorded as a failure: the position the
walk had reached is returned and scored like any other estimate, with a flag beside it.

Three things are measured here.

  1. How many estimates of each run met the cap, by variant.
  2. How the walk grows with the cap on the one slice the compiled binary was also run on. The
     published objective does not converge there, so the distance is proportional to the cap, and
     the ratio measured here is what licenses the rescoring of step 3.
  3. What Tables II and III would say with the cap raised by that factor, every capped estimate
     moved out along its own ray by the ratio of step 2 and the rows rescored by the tool that
     wrote them. This bounds the effect of the cap on every published number.

Writes evidence/search-cap.csv. Reads the frozen run read-only.
"""
import os
import sys

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np                                    # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L                                  # noqa: E402
import villa_estimator as ve                          # noqa: E402
import fifteen_k20 as F                               # noqa: E402

OUT = os.path.join(L.EV, "search-cap.csv")
COLS = ["quantity", "run", "variant", "scroll", "value", "unit", "note"]
CAPS = (2000, 8000, 32000)
GROWTH_SCROLL, GROWTH_Z = "PHerc0125", 6891           # the dump the compiled binary also ran on


def counts(rows, run, of_note):
    """Capped estimates by variant in one raw run."""
    out = []
    for variant in sorted({r["variant"] for r in rows}):
        v = [r for r in rows if r["variant"] == variant]
        cap = [r for r in v if int(r["capped"])]
        out.append(dict(quantity="capped_estimates", run=run, variant=variant, scroll="",
                        value=len(cap), unit="estimates", note=f"of {len(v)} {of_note}"))
        out.append(dict(quantity="capped_scrolls", run=run, variant=variant, scroll="",
                        value=len({r["scroll"] for r in cap}), unit="scrolls",
                        note=", ".join(sorted({r["scroll"] for r in cap})) or "none"))
        out.append(dict(quantity="capped_outside", run=run, variant=variant, scroll="",
                        value=sum(1 for r in cap if not int(r["inside"])), unit="estimates",
                        note="capped estimates already outside the grid when the walk was stopped"))
    return out


def growth():
    """How far the published walk travels as the cap is raised, on one saved slice."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "inputs"))
    import slices
    rows, dist = [], {}
    for scroll, z, mid, nrm, W, H, mm in slices.saved():
        if (scroll, z) != (GROWTH_SCROLL, GROWTH_Z):
            continue
        for ms in CAPS:
            xy, cap = L.estimate(mid, nrm, W, H, L.TABLE_SEED + z, True, max_sweeps=ms)
            dist[ms] = float(np.hypot(xy[0] - W / 2.0, xy[1] - H / 2.0))
            rows.append(dict(quantity="walk_distance", run=f"cap {ms}", variant="as-is",
                             scroll=f"{scroll} z{z}", value=round(dist[ms], 1), unit="grid units",
                             note=f"stopped by the cap: {bool(cap)}"))
    # The same slice was run 20 times by the compiled binary. Its median answer says how far the
    # published walk really travels when nothing stops it, against how far the cap let it travel.
    cpp = {r["dump"]: r for r in L.read_csv(os.path.join(L.EV, "cpp-runs.csv"))
           if r["variant"] == "as-is"}
    key = f"d-{GROWTH_SCROLL[-4:]}-{GROWTH_Z}"
    if key in cpp:
        W = H = 8387.0                                    # the grid of PHerc0125, as in the run
        dc = float(np.hypot(float(cpp[key]["median_x"]) - W / 2.0,
                            float(cpp[key]["median_y"]) - H / 2.0))
        rows.append(dict(quantity="walk_distance", run="compiled binary", variant="as-is",
                         scroll=f"{GROWTH_SCROLL} z{GROWTH_Z}", value=round(dc, 1),
                         unit="grid units",
                         note=f"median of {cpp[key]['repeats']} repeats, evidence/cpp-runs.csv; "
                              "the C++ walk is not capped and stops on its own"))
        rows.append(dict(quantity="cap_shortfall", run=f"cap {CAPS[0]}", variant="as-is",
                         scroll=f"{GROWTH_SCROLL} z{GROWTH_Z}",
                         value=round(dc / dist[CAPS[0]], 2), unit="times",
                         note="the compiled binary travels this many times further than the "
                              "capped transcription, so the cap flatters the published version"))
    ratios = [dist[b] / dist[a] for a, b in zip(CAPS, CAPS[1:])]
    caps = [b / a for a, b in zip(CAPS, CAPS[1:])]
    rows.append(dict(quantity="growth_ratio", run="", variant="as-is",
                     scroll=f"{GROWTH_SCROLL} z{GROWTH_Z}",
                     value=round(float(np.mean(ratios)), 2), unit="times",
                     note="distance multiplied when the cap is multiplied by "
                          f"{caps[0]:.0f}: {', '.join(f'{r:.2f}' for r in ratios)}"))
    return rows, float(CAPS[-1]) / CAPS[0]


def table_sensitivity(raw, factor):
    """Tables II and III rescored with every capped estimate pushed out by `factor`."""
    centre = {}

    def mid_of(scroll):
        if scroll not in centre:
            for zz in L.heights(scroll):
                g = L.grid15_slice(scroll, zz)
                if g:
                    centre[scroll] = (g[2] / 2.0, g[3] / 2.0)
                    break
        return centre[scroll]

    pushed = []
    for r in raw:
        q = dict(r)
        if q["capped"]:
            cx, cy = mid_of(q["scroll"])
            q["x"] = cx + (q["x"] - cx) * factor
            q["y"] = cy + (q["y"] - cy) * factor
        pushed.append(q)

    fields = ["median_k0_mm", "median_mm", "iqr_mm", "min_mm", "max_mm", "ci_lo_mm", "ci_hi_mm",
              "inside", "centroid_mm", "margin_vs_centroid_mm", "margin_ci_lo_mm",
              "margin_ci_hi_mm", "margin_ci_includes_zero", "margin_ci_below_threshold"]
    rows, a_all, b_all, worst = [], [], [], (0.0, "")
    for scroll in L.CFG:
        a = F.score(scroll, [r for r in raw if r["scroll"] == scroll])
        b = F.score(scroll, [r for r in pushed if r["scroll"] == scroll])
        a_all += a
        b_all += b
        for ra, rb in zip(a, b):
            moved = [f for f in fields if ra[f] != rb[f]]
            if not moved:
                continue
            d = abs(float(rb["median_mm"]) - float(ra["median_mm"]))
            if d > worst[0]:
                worst = (d, scroll)
            rows.append(dict(quantity="row_moved", run=f"cap {int(factor)}x", variant=ra["variant"],
                             scroll=scroll, value=round(d, 2), unit="mm",
                             note=f"median {ra['median_mm']} to {rb['median_mm']} mm; "
                                  f"fields moved: {', '.join(moved)}"))
    va = {"primary": F.verdict(a_all, "primary", 4, 3),
          "confirmation": F.verdict(a_all, "confirmation", 8, 6)}
    vb = {"primary": F.verdict(b_all, "primary", 4, 3),
          "confirmation": F.verdict(b_all, "confirmation", 8, 6)}
    changed = [f"{k} {q}" for k in va for q in ("repair", "beat") if va[k][q] != vb[k][q]]
    rows.append(dict(quantity="rows_moved", run=f"cap {int(factor)}x", variant="", scroll="",
                     value=len(rows), unit="rows",
                     note=f"of {len(a_all)} rows of Tables II and III"))
    rows.append(dict(quantity="worst_row_move", run=f"cap {int(factor)}x", variant="as-is",
                     scroll=worst[1], value=round(worst[0], 2), unit="mm",
                     note="largest change of any median in either table"))
    rows.append(dict(quantity="verdicts_changed", run=f"cap {int(factor)}x", variant="", scroll="",
                     value=len(changed), unit="verdicts", note="; ".join(changed) or "none"))
    return rows


def main():
    rows = [dict(quantity="cap", run="every run of the revision", variant="", scroll="",
                 value=ve.MAX_SWEEPS, unit="sweeps",
                 note="villa_estimator.MAX_SWEEPS; not in the C++, whose loop at "
                      "normalgridtools.cpp:119-142 at commit 23adee047 has no iteration limit")]

    raw = [dict(r, z=int(r["z"]), k=int(r["k"]), seed=int(r["seed"]), x=float(r["x"]),
                y=float(r["y"]), inside=int(r["inside"]), capped=int(r["capped"]))
           for r in L.read_csv(os.path.join(L.EV, "k20-estimates.csv"))]
    rows += counts(raw, "k20-estimates", "(15 scrolls, 24 slices, 20 seeds)")
    rows += counts(L.read_csv(os.path.join(L.EV, "positions-24-refit.csv")),
                   "positions-24-refit", "(24 scrolls, 24 slices, 1 seed)")

    g, factor = growth()
    rows += g
    rows += table_sensitivity(raw, factor)

    L.write_csv(OUT, COLS, rows)
    for r in rows:
        print(f"  {r['quantity']:18s} {r['run']:18s} {r['variant']:12s} "
              f"{r['value']!s:>10s} {r['unit']:12s} {r['note']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
