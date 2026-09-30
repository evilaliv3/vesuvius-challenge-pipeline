#!/usr/bin/env python3
"""aggregate91.py: the tables of stevens-changes-0826-91 (DECLARATION.md, «Aggregate»), read from the files the tools wrote.
  1. manifest91.py compare for the pairs (A,B), (B,C), (C,D), (C,X) of every seed whose manifests exist (appended to
     evidence/identity.csv).
  2. evidence/per-run.csv: one row per arm and seed: outcome, cpu and wall seconds, growth patches, peak, sheets, and from
     evidence/measures/collection-<arm>-<seed>.csv's total row: Stevens' formula cm2, best square mm, a2 share, v2 cells,
     clean cm2; not run rows from evidence/not-run.csv; a run with no row yet is «pending».
  3. evidence/aggregate.csv: per arm the median of each measure over the seeds measured, their count and the deaths; then
     the paired differences B-A, C-B, D-C, X-C per seed and their median over the seeds where both arms have the measure,
     with the growth and sheets identity of the pair beside («identical» pairs are written so, never «better»)."""
import csv, datetime, os, statistics, subprocess, sys

M = "/data/scrollagent/runs/rev1/stevens-changes-0826-91"
TOOL = "stevens-changes-0826-91/tools/aggregate91.py"
ARMS = ["A", "B", "C", "D", "X"]
PAIRS = [("A", "B"), ("B", "C"), ("C", "D"), ("C", "X")]
MEAS = ["cpu_seconds", "wall_seconds", "growth_patches", "growth_peak_vmhwm_kb", "sheets", "stevens_formula_cm2",
        "best_square_mm", "a2_share", "v2_cells", "clean_cm2"]


def rows(p):
    return list(csv.DictReader(l for l in open(p) if not l.startswith('"#')))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    seeds = [r["attempt"] for r in rows(M + "/evidence/seeds.csv")]
    for a1, a2 in PAIRS:
        for s in seeds:
            ok = all(os.path.exists(M + "/evidence/manifests/%s-%s-growth.csv" % (a, s)) for a in (a1, a2) if a != "X")
            if ok:
                subprocess.run([sys.executable, M + "/tools/manifest91.py", "compare", a1, a2, s], stdout=subprocess.DEVNULL)
    ident = {}
    if os.path.exists(M + "/evidence/identity.csv"):
        for r in rows(M + "/evidence/identity.csv"):
            ident[(r["attempt"], r["against"], r["arm"], r["kind"])] = r["value"]
    notrun = {}
    if os.path.exists(M + "/evidence/not-run.csv"):
        for r in rows(M + "/evidence/not-run.csv"):
            notrun[(r["arm"], r["attempt"])] = r["outcome"] + ": " + r["reason"]
    per = {}
    for arm in ARMS:
        for s in seeds:
            d = {m: "" for m in MEAS}
            p = M + "/evidence/runs/%s-%s.csv" % (arm, s)
            if (arm, s) in notrun:
                d["outcome"] = notrun[(arm, s)]
            elif not os.path.exists(p):
                d["outcome"] = "pending"
            else:
                kv = {r["quantity"]: r["value"] for r in rows(p)}
                if arm == "X":
                    d["outcome"] = "delivered by the chain (no run here)"
                    d["wall_seconds"] = str(num(kv.get("growth_wall_clock_seconds")) + num(kv.get("downstream_wall_clock_seconds"))) \
                        if num(kv.get("growth_wall_clock_seconds")) is not None and num(kv.get("downstream_wall_clock_seconds")) is not None else ""
                    d["cpu_seconds"] = kv.get("cpu_seconds", "")
                    d["growth_patches"] = kv.get("growth_patches", "")
                else:
                    d["outcome"] = kv.get("outcome", "running")
                    for m in ("cpu_seconds", "wall_seconds", "growth_patches", "growth_peak_vmhwm_kb"):
                        d[m] = kv.get(m, "")
                d["sheets"] = kv.get("sheets", "")
            c = M + "/evidence/measures/collection-%s-%s.csv" % (arm, s)
            if os.path.exists(c):
                tot = [r for r in rows(c) if r["sheet"].startswith("all ")]
                if tot:
                    t = tot[0]
                    d["stevens_formula_cm2"], d["best_square_mm"] = t["stevens_formula_cm2"], t["square_mm_delivered"]
                    d["a2_share"], d["v2_cells"], d["clean_cm2"] = t["a2_share"], t["v2_cells"], t["clean_cm2"]
            per[(arm, s)] = d
    t = utc()
    with open(M + "/evidence/per-run.csv", "w", newline="") as f:
        f.write('"# written by %s at %s: one row per arm and seed, from evidence/runs, evidence/measures (the total row of '
                'measure91.py) and evidence/not-run.csv; X is the chain as delivered (C plus the corrections), no run here, '
                'its wall read from chain-0826 (machine shared)"\n' % (TOOL, t))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["tool", "arm", "attempt", "outcome"] + MEAS)
        for arm in ARMS:
            for s in seeds:
                d = per[(arm, s)]
                w.writerow([TOOL, arm, s, d["outcome"]] + [d[m] for m in MEAS])
    out = []
    for arm in ARMS:
        deaths = sum(1 for s in seeds if per[(arm, s)]["outcome"].startswith(("stopped", "crashed")))
        nr = sum(1 for s in seeds if per[(arm, s)]["outcome"].startswith("not run"))
        pend = sum(1 for s in seeds if per[(arm, s)]["outcome"] in ("pending", "running"))
        for m in MEAS:
            v = [num(per[(arm, s)][m]) for s in seeds if num(per[(arm, s)][m]) is not None]
            out.append([TOOL, "arm", arm, "", m, len(v), "%.4f" % statistics.median(v) if v else "not measurable",
                        "deaths %d, not run %d, pending %d" % (deaths, nr, pend)])
    for a1, a2 in PAIRS:
        for m in MEAS:
            diffs = []
            for s in seeds:
                x, y = num(per[(a1, s)][m]), num(per[(a2, s)][m])
                if x is not None and y is not None:
                    diffs.append(y - x)
                    out.append([TOOL, "pair %s-%s" % (a2, a1), a2 + "-" + a1, s, m, 1, "%.4f" % (y - x),
                                "growth %s; sheets %s" % (ident.get((s, a1, a2, "growth"), "not compared"),
                                                         ident.get((s, a1, a2, "sheets"), "not compared"))])
            out.append([TOOL, "pair median", a2 + "-" + a1, "", m, len(diffs),
                        "%.4f" % statistics.median(diffs) if diffs else "not measurable", "median over seeds with both"])
    with open(M + "/evidence/aggregate.csv", "w", newline="") as f:
        f.write('"# written by %s at %s: per arm medians over the seeds measured and the paired differences (second arm '
                'minus first) per seed and their median; identity of the pair from evidence/identity.csv"\n' % (TOOL, t))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["tool", "kind", "arm_or_pair", "attempt", "measure", "n", "value", "note"])
        w.writerows(out)
    arms_csv(seeds, per, t)
    for r in out:
        if r[1] in ("arm", "pair median"):
            print(r[2], r[4], r[5], r[6], r[7])


def arms_csv(seeds, per, t):
    """evidence/arms.csv in the form the fifth work asks (results/f49f6c7d-pherc0826-chain/src/paper/PLACEHOLDERS.md):
    one row per arm A to E. A to D: medians over the seeds whose run completed; deaths = runs stopped at the ceiling or
    crashed; seeds = completed runs; every cell «not run» when no run completed and at least one is «not run: would not
    finish»; «pending» while runs remain. E: seeds_per_draw = delivered seeds over draws, all four waves (e-yield.csv)."""
    cols = [("cpu_seconds", "cpu_seconds"), ("wall_seconds", "wall_seconds"), ("sheets", "sheets"),
            ("stevens_formula_cm2", "stevens_formula_cm2"), ("largest_square_mm", "best_square_mm"),
            ("a2_share", "a2_share"), ("v2_cells", "v2_cells")]
    rows_out = []
    for arm in ["A", "B", "C", "D"]:
        oc = [per[(arm, s)]["outcome"] for s in seeds]
        done = [s for s in seeds if per[(arm, s)]["outcome"] == "completed"]
        deaths = sum(1 for o in oc if o.startswith(("stopped", "crashed")))
        nr = sum(1 for o in oc if o.startswith("not run"))
        pend = sum(1 for o in oc if o in ("pending", "running"))
        note = "completed %d, deaths %d, not run %d, pending %d of %d seeds" % (len(done), deaths, nr, pend, len(seeds))
        if not done:
            fill = "not run" if nr and not pend else "pending"
            rows_out.append([TOOL, arm] + [fill] * len(cols) + [deaths if fill != "pending" else "pending", "not measurable", len(done), note])
            continue
        cells = []
        for _, m in cols:
            v = [num(per[(arm, s)][m]) for s in done if num(per[(arm, s)][m]) is not None]
            cells.append("%.4f" % statistics.median(v) if v else "not measurable")
        rows_out.append([TOOL, arm] + cells + [deaths, "not measurable", len(done), note])
    e = [r for r in rows(M + "/evidence/e-yield.csv") if r["group"] == "all waves"][0]
    spd = int(e["delivered_seeds"]) / int(e["draws"])
    rows_out.append([TOOL, "E"] + ["not measurable"] * len(cols) + ["not measurable", "%.4f" % spd, e["delivered_seeds"],
                     "seed selection, no growth: %s delivered seeds of %s draws, four waves (e-yield.csv; survivors per draw %s)"
                     % (e["delivered_seeds"], e["draws"], e["survivors_per_draw"])])
    with open(M + "/evidence/arms.csv", "w", newline="") as f:
        f.write('"# written by %s at %s: one row per arm A to E for the fifth work (PLACEHOLDERS.md of f49f6c7d); A to D medians '
                'over the seeds whose run completed (evidence/per-run.csv), largest_square_mm = the run\'s best '
                'square_mm_min_step; E from evidence/e-yield.csv"\n' % (TOOL, t))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["tool", "arm"] + [c for c, _ in cols] + ["deaths", "seeds_per_draw", "seeds", "note"])
        w.writerows(rows_out)


if __name__ == "__main__":
    main()
