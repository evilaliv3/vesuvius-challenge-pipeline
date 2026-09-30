#!/usr/bin/env python3
"""Squares of 10 mm or more found per machine hour on PHerc0826: Stevens' pipeline (item 91 arm A) against the
chain (item 91 arm C, every wave in the order it ran), counting the whole search. Formula, parts and models:
search-yield-0826/DECLARATION.md (declared 2026-09-28T18:24:40Z, addition 18:25:55Z). Zero CPU: reads CSVs only.

Writes evidence/yield.csv (one row per arm, quantity and wave scope, parts beside the result) and
evidence/yield-seeds.csv (one row per delivered seed of the chain as run: its wave and its best squares).
A value nobody measured is «not measurable», never a zero.
"""
import csv, hashlib, os, statistics, subprocess, sys

RUNS = "/data/scrollagent/runs/rev1"
ART = "/data/repositories/vesuvius-challenge-pipeline-private/results/f49f6c7d-pherc0826-chain/src/evidence"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = "search-yield-0826/tools/yield.py"
FREEZE = "2026-09-28T16:15:12Z"
THRESH = 10.0
K_O, K_C = 3, 7

IN = {
    "per_run": RUNS + "/stevens-changes-0826-91/evidence/per-run.csv",
    "arms": RUNS + "/stevens-changes-0826-91/evidence/arms.csv",
    "seed_rule": ART + "/studies/chain-0826/seed-rule.csv",
    "ladder": ART + "/studies/chain-0826/ladder.csv",
    "queue": ART + "/studies/chain-0826/per-seed-queue.csv",
    "chain_as_run": ART + "/derived/chain-as-run.csv",
    "chain_summary": ART + "/derived/chain-summary.csv",
    "refill": RUNS + "/chain-0826/evidence/refill.csv",
    "build": RUNS + "/nongrowth-profile-1447/evidence/build-objects-only.csv",
    "cert": RUNS + "/square20-0826-95/evidence/certified-squares.csv",
}
WAVES = ["batch-1-400-0826", "batch-401-2400-0826", "batch-2401-6400-0826", "batch-6401-6712-0826",
         "batch-6713-6752-0826"]
RANDOM = WAVES[:3]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rd(p):
    with open(p, newline="") as fh:
        return list(csv.DictReader(l for l in fh if not l.lstrip().startswith(('"#', "#"))))


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def f4(x):
    return "not measurable" if x is None else "%.4f" % x


def utc_s(t):
    return int(subprocess.check_output(["date", "-u", "-d", t, "+%s"]).decode())


def main():
    now = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    shas = {k: sha(p) for k, p in IN.items()}

    # item 91: per seed wall and cpu of arms A, C and X
    pr = rd(IN["per_run"])
    arm = {a: [r for r in pr if r["arm"] == a] for a in "ACX"}
    for a in "AC":
        bad = [r["attempt"] for r in arm[a] if r["outcome"] != "completed"]
        if bad or len(arm[a]) != 8:
            sys.exit("yield.py: arm %s has %d rows, not completed %s" % (a, len(arm[a]), bad))
    wall = {a: [float(r["wall_seconds"]) for r in arm[a]] for a in "AC"}
    cpu = {a: [float(r["cpu_seconds"]) for r in arm[a]] for a in "AC"}
    t = {a: statistics.mean(wall[a]) for a in "AC"}
    arms = {r["arm"]: r for r in rd(IN["arms"])}
    cpu_med_check = {a: "%.2f" % statistics.median(cpu[a]) for a in "AC"}
    cpu_med_arms = {a: "%.2f" % float(arms[a]["cpu_seconds"]) for a in "AC"}
    a10 = sum(float(r["best_square_mm"]) >= THRESH for r in arm["A"])
    x10 = sum(num(r["best_square_mm"]) is not None and float(r["best_square_mm"]) >= THRESH for r in arm["X"])

    b = [r for r in rd(IN["build"]) if r["series"] == "corrected"]
    b_full, b_obj = float(b[0]["full_rebuild_cpu_s"]), float(b[0]["partial_build_cpu_s"])

    # the chain as run
    sr = rd(IN["seed_rule"])
    draws = {w: sum(r["group"] == w for r in sr) for w in WAVES}
    lad = rd(IN["ladder"])
    q = rd(IN["queue"])
    car = {r["attempt"]: r["in_chain_as_run"] for r in rd(IN["chain_as_run"])}
    qw = {}
    for r in q:
        qw.setdefault(r["seed_rule_group"], []).append(r)
    deliv = {w: [r["attempt"] for r in qw.get(w, []) if r["delivering_binary"].startswith("delivered")] for w in WAVES}
    not_as_run = [s for w in WAVES for s in deliv[w] if car.get(s) != "yes"]
    if not_as_run:
        sys.exit("yield.py: delivered seeds of the snapshot not in the chain as run: %s" % not_as_run)

    # G_w: queued seeds that grew and were not delivered (DECLARATION addition 18:25:55Z)
    G, Gn = {}, {}
    for w in WAVES:
        G[w], Gn[w] = 0.0, 0
        for r in qw.get(w, []):
            if r["delivering_binary"].startswith("delivered") or r["growth_return_code"] == "not measurable":
                continue
            g = num(r["growth_wall_clock_seconds"])
            if g is None:
                sys.exit("yield.py: %s grew with no growth wall" % r["attempt"])
            p = os.path.join(RUNS, "chain-0826/evidence/runs", r["attempt"] + ".csv")
            if os.path.exists(p):
                g += sum(float(x["value"]) for x in rd(p) if x["quantity"].startswith("downstream_stage_")
                         and x["quantity"].endswith("_seconds") and num(x["value"]) is not None)
            G[w] += g
            Gn[w] += 1

    # S_w from refill.csv rows before the freeze
    rf = [r for r in rd(IN["refill"]) if r["utc"] < FREEZE]
    S, Snote = {}, {}
    for w in WAVES:
        lo, hi = w.split("-")[1], w.split("-")[2]
        dr = [r for r in rf if r["from"] == lo and r["to"] == hi and r["step"] == "draw"]
        ru = [r for r in rf if r["from"] == lo and r["to"] == hi and r["step"] == "seed-rule"]
        if len(dr) == 1 and len(ru) == 1:
            S[w] = float(utc_s(ru[0]["utc"]) - utc_s(dr[0]["utc"]))
            Snote[w] = "refill.csv seed-rule %s minus draw %s" % (ru[0]["utc"], dr[0]["utc"])
        else:
            S[w] = None
            Snote[w] = "%d draw and %d seed-rule rows" % (len(dr), len(ru))
    rate = max(S[w] / draws[w] for w in WAVES[1:] if S[w] is not None)
    for w in WAVES:
        if S[w] is None:
            S[w] = draws[w] * rate
            Snote[w] += "; declared model: %d draws x the largest per draw seconds of waves 2 to 5 (%.4f)" % (draws[w], rate)

    # finds per seed and per sheet, C40 only
    cert = [r for r in rd(IN["cert"]) if r["source"] == "C40"]
    by = {}
    for r in cert:
        by.setdefault(r["seed"], []).append(r)
    seeds_rows, finds = [], {}
    for wi, w in enumerate(WAVES, 1):
        for s in deliv[w]:
            rs = by.get(s)
            if not rs:
                seeds_rows.append({"seed": s, "wave": wi, "group": w, "c40_sheets": 0, "measured_sheets": 0,
                                   "best_hole_free_mm": "not measurable", "best_certified_mm": "not measurable",
                                   "hole_free_sheets_10mm": "not measurable", "certified_sheets_10mm": "not measurable"})
                continue
            m = [r for r in rs if r["status"] == "measured"]
            hf = [num(r["hole_free_square_mm"]) for r in m if num(r["hole_free_square_mm"]) is not None]
            ce = [num(r["certified_square_mm"]) for r in m if num(r["certified_square_mm"]) is not None]
            seeds_rows.append({"seed": s, "wave": wi, "group": w, "c40_sheets": len(rs), "measured_sheets": len(m),
                               "best_hole_free_mm": f4(max(hf)) if hf else "not measurable",
                               "best_certified_mm": f4(max(ce)) if ce else "not measurable",
                               "hole_free_sheets_10mm": sum(x >= THRESH for x in hf),
                               "certified_sheets_10mm": sum(x >= THRESH for x in ce)})
    missing = [r["seed"] for r in seeds_rows if r["c40_sheets"] == 0]

    def count(waves, qty):
        sel = [r for r in seeds_rows if r["group"] in waves and r["c40_sheets"]]
        col = "hole_free_sheets_10mm" if qty == "hole free" else "certified_sheets_10mm"
        return sum(r[col] > 0 for r in sel), sum(r[col] for r in sel)

    cs = {(r["scope"], r["quantity"]): r["value"] for r in rd(IN["chain_summary"])}
    seeds_ten = cs.get(("all", "seeds_square_at_least_source_mm"), "not measurable")
    hf_all = count(WAVES, "hole free")[0]
    check_ten = "per seed hole free %d, article SeedsTen %s: %s" % (hf_all, seeds_ten, "equal" if str(hf_all) == seeds_ten else "differ")
    check_cpu = "cpu median A %s C %s from per-run.csv, arms.csv A %s C %s: %s" % (
        cpu_med_check["A"], cpu_med_check["C"], cpu_med_arms["A"], cpu_med_arms["C"],
        "equal" if cpu_med_check == cpu_med_arms else "differ")

    out = []
    base = {"tool": TOOL}

    # ORIGINAL
    N_O = sum(len(deliv[w]) for w in RANDOM)
    H_O = N_O * (t["A"] + b_full) / (K_O * 3600.0)
    for qty in ("hole free", "certified"):
        F, Fs = count(RANDOM, qty)
        out.append(dict(base, arm="original (item 91 arm A)", quantity=qty, scope="random waves 1 to 3",
                        k=K_O, seeds_grown_to_end=N_O, finds_per_seed=F, finds_per_sheet=Fs,
                        yield_per_seed_grown=f4(F / N_O), t_delivered_wall_s=f4(t["A"]),
                        t_delivered_wall_median_s=f4(statistics.median(wall["A"])),
                        cpu_median_s=cpu_med_arms["A"], build_s=f4(b_full),
                        seed_rule_s="not counted (declared bound)", ladder_rows="not counted (declared bound)",
                        ladder_wall_s="not counted (declared bound)", ladder_build_s="not counted (declared bound)",
                        delivered_seeds=N_O, delivered_slot_s=f4(N_O * (t["A"] + b_full)),
                        undelivered_grown_seeds="not counted (declared bound)", undelivered_grown_s="not counted (declared bound)",
                        machine_hours=f4(H_O), finds_per_machine_hour=f4(F / H_O),
                        finds_per_sheet_per_machine_hour=f4(Fs / H_O),
                        formula="R_O = F_O / (N_O x (t_A + b_A) / (3 x 3600)); upper bound: dead attempts not charged",
                        check_seeds_ten=check_ten, check_cpu_medians=check_cpu,
                        note="item 91's 8 seeds, best square >= 10 mm: arm A %d of 8, chain as delivered (X) %d of 8" % (a10, x10)))

    # OURS, cumulative and per wave; and the as delivered information row
    runs_deliv = {}
    for w in WAVES:
        s_ = 0.0
        for sd in deliv[w]:
            rr = {x["quantity"]: x["value"] for x in rd(os.path.join(RUNS, "chain-0826/evidence/runs", sd + ".csv"))}
            g, d = num(rr.get("growth_wall_clock_seconds")), num(rr.get("downstream_wall_clock_seconds"))
            if g is None or d is None:
                s_ = None
                break
            s_ += g + d
        runs_deliv[w] = s_
    parts = {}
    for w in WAVES:
        lw = [r for r in lad if r["group"] == w]
        parts[w] = dict(S=S[w], P=len(lw), L=sum(float(r["wall_s"]) for r in lw), B=len(lw) * b_obj,
                        D=len(deliv[w]), G=G[w], Gn=Gn[w])
    for variant in ("order", "as delivered"):
        for wi, w in enumerate(WAVES, 1):
            for scope, ws in (("waves 1 to %d, cumulative" % wi, WAVES[:wi]), ("wave %d alone" % wi, [w])):
                if variant == "as delivered" and scope.startswith("wave ") and wi < 5:
                    continue
                Ssum = sum(parts[x]["S"] for x in ws)
                P = sum(parts[x]["P"] for x in ws)
                L = sum(parts[x]["L"] for x in ws)
                B = sum(parts[x]["B"] for x in ws)
                D = sum(parts[x]["D"] for x in ws)
                Gs = sum(parts[x]["G"] for x in ws)
                Gc = sum(parts[x]["Gn"] for x in ws)
                if variant == "order":
                    DS = D * t["C"]
                else:
                    DS = None if any(runs_deliv[x] is None for x in ws) else sum(runs_deliv[x] for x in ws)
                H = None if DS is None else Ssum / 3600.0 + (L + B + DS + Gs) / (K_C * 3600.0)
                for qty in ("hole free", "certified"):
                    F, Fs = count(ws, qty)
                    out.append(dict(base, arm="ours (item 91 arm C)" if variant == "order" else "ours as delivered (information)",
                                    quantity=qty, scope=scope, k=K_C, seeds_grown_to_end=D + Gc, finds_per_seed=F,
                                    finds_per_sheet=Fs, yield_per_seed_grown=f4(F / D) if D else "not measurable",
                                    t_delivered_wall_s=f4(t["C"]) if variant == "order" else "chain runs files",
                                    t_delivered_wall_median_s=f4(statistics.median(wall["C"])) if variant == "order" else "",
                                    cpu_median_s=cpu_med_arms["C"], build_s=f4(b_obj), seed_rule_s=f4(Ssum),
                                    ladder_rows=P, ladder_wall_s=f4(L), ladder_build_s=f4(B), delivered_seeds=D,
                                    delivered_slot_s=f4(DS), undelivered_grown_seeds=Gc, undelivered_grown_s=f4(Gs),
                                    machine_hours=f4(H), finds_per_machine_hour=f4(F / H) if H else "not measurable",
                                    finds_per_sheet_per_machine_hour=f4(Fs / H) if H else "not measurable",
                                    formula="R_C = F_C / (sum S_w / 3600 + sum (L_w + B_w + D_w x t_C + G_w) / (7 x 3600))"
                                    if variant == "order" else
                                    "as R_C with D_w x t_C replaced by the chain's growth plus downstream wall of its delivered seeds",
                                    check_seeds_ten=check_ten if scope == "waves 1 to 5, cumulative" else "",
                                    check_cpu_medians=check_cpu if variant == "order" else "",
                                    note="; ".join("wave %d S: %s" % (WAVES.index(x) + 1, Snote[x]) for x in ws)
                                    + ("; delivered seeds with no C40 row: %s" % (", ".join(missing) or "none"))))
    # the ratio rows
    for qty in ("hole free", "certified"):
        o = [r for r in out if r["arm"].startswith("original") and r["quantity"] == qty][0]
        c = [r for r in out if r["arm"] == "ours (item 91 arm C)" and r["quantity"] == qty
             and r["scope"] == "waves 1 to 5, cumulative"][0]
        ro, rc = num(o["finds_per_machine_hour"]), num(c["finds_per_machine_hour"])
        out.append(dict(base, arm="ratio ours / original", quantity=qty, scope="ours waves 1 to 5 against original waves 1 to 3",
                        finds_per_machine_hour=f4(rc / ro) if ro else "not measurable",
                        formula="R_C(5) / R_O; a lower bound of our advantage, since R_O is an upper bound",
                        note="R_C %s over R_O %s" % (c["finds_per_machine_hour"], o["finds_per_machine_hour"])))

    cols = ["tool", "arm", "quantity", "scope", "k", "seeds_grown_to_end", "finds_per_seed", "finds_per_sheet",
            "yield_per_seed_grown", "t_delivered_wall_s", "t_delivered_wall_median_s", "cpu_median_s", "build_s",
            "seed_rule_s", "ladder_rows", "ladder_wall_s", "ladder_build_s", "delivered_seeds", "delivered_slot_s",
            "undelivered_grown_seeds", "undelivered_grown_s", "machine_hours", "finds_per_machine_hour",
            "finds_per_sheet_per_machine_hour", "formula", "check_seeds_ten", "check_cpu_medians", "note"]
    hdr = "; ".join("%s %s sha256 %s" % (k, IN[k], shas[k][:16]) for k in IN)
    with open(os.path.join(HERE, "evidence", "yield.csv"), "w", newline="") as fh:
        fh.write('"# written by %s at %s: finds (square >= 10 mm on a delivered C40 sheet, hole free or certified, per '
                 'seed; per sheet a column) per machine hour, machine hours = slot seconds / (k x 3600) plus whole machine '
                 'seconds / 3600; formula and models in search-yield-0826/DECLARATION.md; chain as run frozen at %s; '
                 'inputs: %s"\n' % (TOOL, now, FREEZE, hdr))
        w_ = csv.DictWriter(fh, fieldnames=cols, restval="")
        w_.writeheader()
        w_.writerows(out)
    with open(os.path.join(HERE, "evidence", "yield-seeds.csv"), "w", newline="") as fh:
        fh.write('"# written by %s at %s: one row per delivered seed of the chain as run (article snapshot of '
                 'per-seed-queue.csv), its best hole free and certified square over its C40 sheets of %s"\n'
                 % (TOOL, now, IN["cert"]))
        w_ = csv.DictWriter(fh, fieldnames=["tool"] + list(seeds_rows[0]))
        w_.writeheader()
        for r in seeds_rows:
            w_.writerow(dict(r, tool=TOOL))
    print("yield.py: %d rows, %d seeds; %s; %s" % (len(out), len(seeds_rows), check_ten, check_cpu))
    return 0


if __name__ == "__main__":
    sys.exit(main())
