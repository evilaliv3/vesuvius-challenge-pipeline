#!/usr/bin/env python3
"""wave_sizing.py <target_survivors> <from>: sizes a draw wave under seed rule v2 from the second wave's actual yield so far
(director 22:17:19Z). v2 passers per draw from evidence/seed-rule.csv group batch-401-2400-0826; survivors per classified
passer from evidence/ladder.csv of that group at the time of the run; batch 1 beside it. Draws needed = target / (passers per
draw x survivors per passer), rounded up to a multiple of 400. Writes evidence/wave-sizing.csv (appends one block per run)."""
import csv, math, os, subprocess, sys
S = "/data/scrollagent/runs/rev1/chain-0826"
target, frm = int(sys.argv[1]), int(sys.argv[2])
def rows(p):
    return list(csv.DictReader(l for l in open(p, newline="") if not l.lstrip().startswith('"#')))
rule, lad = rows(S + "/evidence/seed-rule.csv"), rows(S + "/evidence/ladder.csv")
t = subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip()
out = []
for g in ("batch-1-400-0826", "batch-401-2400-0826"):
    R = [r for r in rule if r["group"] == g]
    P = [r for r in R if r["passes_rule"] == "yes"]
    L = [r for r in lad if r["group"] == g]
    sv = sum(r["outcome"] == "still growing at the cap" for r in L)
    out.append(dict(utc=t, group=g, draws=len(R), rule_passers=len(P), classified=len(L), survivors=sv,
                    passers_per_draw="%.4f" % (len(P) / len(R)), survivors_per_classified="%.4f" % (sv / len(L)),
                    survivors_per_draw="%.4f" % (len(P) / len(R) * sv / len(L)), target="", draws_needed="", draw_range=""))
b = out[1]
y = float(b["survivors_per_draw"])
need = int(math.ceil(target / y / 400.0) * 400)
out.append(dict(utc=t, group="wave sizing on batch-401-2400-0826", draws="", rule_passers="", classified="", survivors="",
                passers_per_draw=b["passers_per_draw"], survivors_per_classified=b["survivors_per_classified"],
                survivors_per_draw=b["survivors_per_draw"], target=target, draws_needed=need, draw_range="%d..%d" % (frm, frm + need - 1)))
p = S + "/evidence/wave-sizing.csv"
new = not os.path.exists(p)
with open(p, "a", newline="") as h:
    if new:
        h.write('"# written by chain-0826/tools/wave_sizing.py: yield of the v2 waves and the draws a target needs; batch 1 was judged by rule v1 (its rule_passers are v1 passers)"\n')
    w = csv.DictWriter(h, fieldnames=list(out[0].keys()))
    if new:
        w.writeheader()
    for r in out:
        w.writerow(r)
for r in out:
    print(r)
