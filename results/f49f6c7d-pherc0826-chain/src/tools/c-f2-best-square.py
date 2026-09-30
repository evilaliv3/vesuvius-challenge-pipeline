#!/usr/bin/env python3
"""Figure C2: the best square of every delivered PHerc. 0826 seed, as delivered and under the a2
cluster rule, seeds sorted by the delivered square.

What it reads. evidence/studies/chain-0826/per-seed-queue.csv (the delivered seeds: column
delivering_binary begins with «delivered»; column largest_square_mm_min_step; column
seed_rule_group, the wave) and evidence/studies/chain-0826/a2-cluster/<seed>.csv (column
a2_cluster_rule_square_mm, the largest over the seed's sheets). The two lines of the figure are
columns of the plotted table too: the fourth wave's source threshold, read from the header of
wave4-sources.csv, and the side of a 20 mm square, which is the definition of the
target and not a measurement.

What it writes. evidence/figures/c-f2-best-square.csv, one row per delivered seed in ascending order
of the delivered square, with x the rank, one y column per wave (nan in the other waves' columns,
so each wave has its own mark), the cluster rule square, and the check column
`cluster_not_above_delivered`: the cluster rule square cuts points from a sheet and so cannot
exceed the delivered square of the same seed; a row that says no stops the tool.

The stars (director 2026-09-30, the owner's question). The certified squares of the organisers' tracer grown from our
starts, route R2c of render-routes-0826, under the certificate with adjudicated crossings: column
c_certified_adjudicated_mm of src/inputs/render-routes-0826/square-three-definitions.csv, the copy the headline reads.
A star goes in the row of the seed whose certified square gave its start (r2c_star_mm), above that seed's x; a seed
that is not among the delivered seeds gets a row of its own at the right edge, x one past the last seed, with its
seed id in r2c_star_label. star_source_file and star_source_column say where each star's value was read.

Usage: c-f2-best-square.py [--out PATH]
"""
import argparse, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib  # noqa: E402

FIGURE = "c-f2-best-square"
WAVES = ["batch-1-400-0826", "batch-401-2400-0826", "batch-2401-6400-0826", "batch-6401-6712-0826",
         "batch-6713-6752-0826"]   # the figure has one mark per wave, five marks; a sixth wave stops the tool
TARGET_MM = 20.0   # the side of a 20 mm square, the target size: a definition, not a measurement
STARTS = "inputs/render-routes-0826/square-three-definitions.csv"
STAR_ROUTE, STAR_COLUMN = "R2cnative", "c_certified_adjudicated_mm"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = a.out or os.path.join(here, "evidence/figures/%s.csv" % FIGURE)
    C = os.path.join(here, "evidence/studies/chain-0826")
    _, _, q = figlib.read_study_csv(os.path.join(C, "per-seed-queue.csv"))
    head = open(os.path.join(C, "wave4-sources.csv")).readline()
    m = re.search(r"best >= ([0-9.]+) mm", head)
    if not m:
        sys.exit("wave4-sources.csv: no source threshold in the header")
    source = float(m.group(1))
    rows = []
    for r in q:
        if not r["delivering_binary"].startswith("delivered"):
            continue
        d = figlib.required_number(r, "largest_square_mm_min_step", r["attempt"])
        _, _, a2 = figlib.read_study_csv(os.path.join(C, "a2-cluster", r["attempt"] + ".csv"))
        cl = [float(s["a2_cluster_rule_square_mm"]) for s in a2
              if re.fullmatch(r"[0-9.]+", s["a2_cluster_rule_square_mm"])]
        if not cl:
            sys.exit("%s: no cluster rule square on any sheet" % r["attempt"])
        if r["seed_rule_group"] not in WAVES:
            sys.exit("%s: group %s is not a wave" % (r["attempt"], r["seed_rule_group"]))
        rows.append((d, max(cl), r["attempt"], r["seed_rule_group"]))
    rows.sort(key=lambda t: (t[0], t[2]))
    fields = ["x", "seed", "wave", "delivered_mm"] + ["delivered_wave%d_mm" % (i + 1) for i in range(len(WAVES))] + \
             ["cluster_rule_mm", "cluster_not_above_delivered", "source_threshold_mm", "target_mm",
              "source_file", "source_column", "r2c_star_mm", "r2c_star_label", "star_source_file", "star_source_column"]
    table = []
    for i, (d, c, seed, g) in enumerate(rows, 1):
        w = WAVES.index(g) + 1
        row = {"x": i, "seed": seed, "wave": w, "delivered_mm": "%.4f" % d,
               "cluster_rule_mm": "%.4f" % c,
               "cluster_not_above_delivered": "yes" if c <= d + 5e-5 else "no",
               "source_threshold_mm": source, "target_mm": TARGET_MM,
               "source_file": "chain-0826/per-seed-queue.csv; chain-0826/a2-cluster/<seed>.csv",
               "source_column": "largest_square_mm_min_step; a2_cluster_rule_square_mm (max over sheets)"}
        for k in range(1, len(WAVES) + 1):
            row["delivered_wave%d_mm" % k] = ("%.4f" % d) if k == w else figlib.NAN
        row.update({"r2c_star_mm": figlib.NAN, "r2c_star_label": "", "star_source_file": "", "star_source_column": ""})
        table.append(row)
    _, _, td = figlib.read_study_csv(os.path.join(here, STARTS))
    stars = [r for r in td if r["route"] == STAR_ROUTE]
    if not stars:
        sys.exit("%s: no %s row" % (STARTS, STAR_ROUTE))
    by_seed = {r["seed"]: r for r in table}
    for r in stars:
        m = re.fullmatch(r"(PHerc0826-seed\d+)-squarecentre", r["surface"])
        if not m:
            sys.exit("%s: %s is not a start at the centre of a certified square of a seed" % (STARTS, r["surface"]))
        v = figlib.required_number(r, STAR_COLUMN, r["surface"])
        src = {"star_source_file": STARTS + ", row route %s surface %s" % (STAR_ROUTE, r["surface"]),
               "star_source_column": STAR_COLUMN}
        if m.group(1) in by_seed:
            if by_seed[m.group(1)]["r2c_star_mm"] != figlib.NAN:
                sys.exit("%s: two stars for %s" % (STARTS, m.group(1)))
            by_seed[m.group(1)].update({"r2c_star_mm": r[STAR_COLUMN].strip()}, **src)
        else:
            edge = {f: figlib.NAN for f in fields}
            edge.update({"x": len(table) + 1, "seed": m.group(1), "wave": "", "cluster_not_above_delivered": "",
                         "source_file": "", "source_column": "", "r2c_star_mm": r[STAR_COLUMN].strip(),
                         "r2c_star_label": m.group(1).replace("PHerc0826-", ""), **src})
            table.append(edge)
    if any(r["cluster_not_above_delivered"] not in ("yes", "") for r in table) or \
            any(r["cluster_not_above_delivered"] == "" and r["r2c_star_label"] == "" for r in table):
        sys.exit("a cluster rule square exceeds its delivered square")
    comment = ("figure C2, the numbers plotted and nothing else, written by src/tools/%s.py at %s: "
               "%d delivered seeds of per-seed-queue.csv in ascending order of largest_square_mm_min_step; "
               "delivered_waveN_mm is that square in the column of the seed's wave and nan elsewhere; "
               "cluster_rule_mm is the largest a2_cluster_rule_square_mm over the seed's sheets; "
               "source_threshold_mm from the header of wave4-sources.csv; target_mm is the side of a 20 mm square; "
               "r2c_star_mm is the certified square of route %s grown from the centre of that seed's certified square, "
               "column %s of %s (a start whose seed is not delivered gets its own row at the right edge)"
               % (FIGURE, figlib.utc_now(), len(rows), STAR_ROUTE, STAR_COLUMN, STARTS))
    figlib.write_plotted(out, comment, fields, table)
    sys.stderr.write("%s: %d seeds\n" % (out, len(table)))


if __name__ == "__main__":
    main()
