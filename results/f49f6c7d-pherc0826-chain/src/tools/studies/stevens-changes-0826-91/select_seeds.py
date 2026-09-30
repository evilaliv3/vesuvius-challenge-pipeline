#!/usr/bin/env python3
"""select_seeds.py: the 8 PHerc0826 seeds of stevens-changes-0826-91 by the rule of DECLARATION.md («The seeds»).
Writes evidence/seeds.csv (csv.writer, first line names the tool)."""
import csv, datetime, os
import numpy as np

R1 = "/data/scrollagent/runs/rev1"
M = R1 + "/stevens-changes-0826-91"
CH = R1 + "/chain-0826"
TOOL = "stevens-changes-0826-91/tools/select_seeds.py"
RNG = 20260928


def rows(p):
    ls = [l for l in open(p) if not l.startswith('"#') and not l.startswith("#")]
    return list(csv.DictReader(ls))


def num(x):
    try:
        return float(x)
    except ValueError:
        return None


def main():
    road1b = {r["attempt"] for r in rows(R1 + "/area-0826-90/evidence/road1b-seeds.csv")}
    assert len(road1b) == 12, len(road1b)
    excl = road1b | {"PHerc0826-seed2019", "PHerc0826-seed5630", "PHerc0826-seed6365"}
    pop = []
    for r in rows(CH + "/evidence/per-seed-queue.csv"):
        sq, gp, sh = num(r["largest_square_mm_min_step"]), num(r["growth_patches"]), num(r["pred_chunk_share_255"])
        if not r["delivering_binary"].startswith("delivered") or sq is None or gp is None or sh is None or gp > 10000:
            continue
        if r["attempt"] in excl:
            continue
        if not os.path.isfile(CH + "/out/%s/growth/rel.csv" % r["attempt"]):
            continue
        pop.append(dict(attempt=r["attempt"], share=sh, square=sq, patches=int(gp)))
    pop.sort(key=lambda d: int(d["attempt"].split("seed")[1]))
    shares = np.array([d["share"] for d in pop])
    med = float(np.median(shares))
    halves = {"low": [d for d in pop if d["share"] <= med], "high": [d for d in pop if d["share"] > med]}
    rng = np.random.default_rng(RNG)
    out = []
    for h in ("low", "high"):
        H = halves[h]
        q = np.percentile([d["square"] for d in H], [25, 50, 75])
        cells = [[], [], [], []]
        for d in H:
            b = int(np.searchsorted(q, d["square"], side="left"))
            cells[b].append(d)
        taken = set()
        for b in range(4):
            c = [d for d in cells[b] if d["attempt"] not in taken]
            note = ""
            if not c:
                for nb in sorted(range(4), key=lambda x: (abs(x - b), x)):
                    c = [d for d in cells[nb] if d["attempt"] not in taken]
                    if c:
                        note = "cell empty, drawn from bin %d" % (nb + 1)
                        break
            i = int(rng.integers(0, len(c)))
            d = c[i]
            taken.add(d["attempt"])
            out.append([TOOL, h, b + 1, "%.4f" % med, ";".join("%.4f" % x for x in q), len(H), len(c), i, d["attempt"],
                        "%.4f" % d["share"], "%.4f" % d["square"], d["patches"], note])
    t = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(M + "/evidence/seeds.csv", "w", newline="") as f:
        f.write('"# written by %s at %s: rule of DECLARATION.md (population %d delivered 0826 seeds with a square, growth '
                'patches <= 10000, delivered growth tree on disk, road 1b 12 and road 2 3 excluded); rng %d"\n' % (TOOL, t, len(pop), RNG))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["tool", "share_half", "square_bin", "share_median", "square_quartiles_of_half", "half_size", "cell_size",
                    "draw_index", "attempt", "pred_chunk_share_255", "largest_square_mm_min_step", "growth_patches", "note"])
        w.writerows(out)
    for r in out:
        print(r[1:])


if __name__ == "__main__":
    main()
