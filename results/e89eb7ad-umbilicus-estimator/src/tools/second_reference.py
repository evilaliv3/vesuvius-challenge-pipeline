# This file is a copy of tools/second_reference.py of the working tree. It differs from it in the
# paths and in the column and field names, and in nothing that computes: the working copy reads
# the run folder and the fifteen scroll configuration where they live on the machine the
# measurement ran on, while this one reads the same numbers from this folder. The two compute the
# same quantities, and two rows of the CSV differ only in the note that names the file each read.
# This copy writes the evidence file and stops there: turning those rows into the macros the
# article prints is typesetting and is not done in this folder.
"""What the second reference of PHerc1218 is, and how far the same construction sits from a hand
on every scroll that has one.

The article used to call the distance between the two umbilici of PHerc1218 the distance between
two independent annotations. It is not one. The second umbilicus is produced by
`make_umbilicus.py` of `vesuvius-sheet-tools`, whose own header says it takes the papyrus centroid
of each slice as the umbilicus position: it reads the instance labels as a mask, thresholded at
`labels > 0`, and never which sheet is which. The second reference is therefore a per slice
centroid of the papyrus mask, which is the construction this paper already scores as the centroid
baseline, and the published number is a hand against a mask centroid.

Because only the support of the labels matters, the same derivation runs from the masked scan and
the surface prediction the challenge publishes, so the comparison can be made on every scroll that
carries a hand umbilicus and not only on the two that carry published instance labels. That run
was closed on 2026-09-18 and is not in this folder; its per scroll table is here as
`inputs/second-reference/hand-vs-mask-centroid.csv`, with its provenance beside it. This tool reads that table, and `inputs/fifteen-config.json` for who
annotated what, and writes the summary the article quotes.

Inputs:  inputs/second-reference/hand-vs-mask-centroid.csv, inputs/fifteen-config.json,
         evidence/reference-uncertainty.csv (for the published number, which is not retyped here)
Output:  evidence/second-reference.csv, one row per quantity

    python3 tools/second_reference.py
"""
import csv
import json
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
IN = os.path.join(SRC, "inputs")
EV = os.path.join(SRC, "evidence")


def read_csv(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def pearson(xs, ys):
    """Plain Pearson correlation. scipy is a dependency of this folder, but a two line formula
    read by a referee is worth more here than an import."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / (sxx * syy) ** 0.5


def main():
    rows = read_csv(os.path.join(IN, "second-reference", "hand-vs-mask-centroid.csv"))
    # one row per scroll: the published Dopico file is kept in the table as the guard that the
    # derivation reproduces it, and is dropped here so that PHerc1218 is not counted twice.
    derived = [r for r in rows if r["second_reference"] == "mask centroid, derived here"]
    published = next(r for r in rows if r["second_reference"] == "Dopico, published")
    assert len({r["scroll"] for r in derived}) == len(derived), "a scroll appears twice"

    cfg = json.load(open(os.path.join(IN, "fifteen-config.json")))
    hands = {}
    for scroll, v in cfg.items():
        hands.setdefault("challenge" if v["source"] == "challenge" else "third party",
                         []).append(scroll)
    assert not set(hands["challenge"]) & set(hands["third party"]), "a scroll has two hands"

    # the published number, read from the evidence file the frozen run wrote, not retyped
    unc = read_csv(os.path.join(EV, "reference-uncertainty.csv"))
    spread = next(float(r["median_mm"]) for r in unc
                  if r["window"] == "common coverage" and r["direction"] == "A against B")

    gaps = [(r["scroll"], abs(float(r["mean_both_directions_mm"]) - float(r["centroid_baseline_mm"])))
            for r in derived]
    dist = sorted((float(r["mean_both_directions_mm"]), r["scroll"]) for r in derived)
    values = [d for d, _ in dist]
    rank = [s for _, s in dist].index("PHerc1218") + 1
    q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
    corr = pearson([float(r["mean_both_directions_mm"]) for r in derived],
                   [float(r["centroid_baseline_mm"]) for r in derived])
    worst_gap = max(gaps, key=lambda g: g[1])
    pherc1218 = next(g for g in gaps if g[0] == "PHerc1218")
    # the published number against the centroid column of the article's own table, on the scroll
    # the published number was measured on: the two are the same kind of quantity, the distance
    # from that scroll's hand annotation to a mask centroid, measured by two different chains.
    published_vs_centroid = abs(
        spread - float(next(r for r in derived if r["scroll"] == "PHerc1218")["centroid_baseline_mm"]))

    out = [
        ("scrolls with a hand umbilicus", len(cfg),
         "inputs/fifteen-config.json, one entry per scroll"),
        ("hand umbilici published by the challenge", len(hands["challenge"]),
         "field source = challenge"),
        ("hand umbilici clicked by the third party", len(hands["third party"]),
         "field source = drobkov"),
        ("scrolls carrying two independent hand umbilici", 0,
         "the two sets are disjoint, so no scroll has a second hand"),
        ("scrolls with a derived second reference", len(derived),
         "hand against a per slice centroid of the papyrus mask"),
        ("smallest distance mm", f"{values[0]:.3f}", dist[0][1]),
        ("largest distance mm", f"{values[-1]:.3f}", dist[-1][1]),
        ("median distance mm", f"{statistics.median(values):.3f}", "over the scrolls"),
        ("first quartile mm", f"{q1:.3f}", "over the scrolls"),
        ("third quartile mm", f"{q3:.3f}", "over the scrolls"),
        ("largest over smallest", f"{values[-1] / values[0]:.2f}",
         f"{dist[-1][1]} against {dist[0][1]}"),
        ("rank of PHerc1218 ascending", rank, f"of {len(derived)} scrolls"),
        ("scrolls above the published number", sum(v > spread for v in values),
         f"published number {spread:.3f} mm, evidence/reference-uncertainty.csv"),
        ("published number mm", f"{spread:.3f}",
         "hand against the published mask centroid of PHerc1218"),
        ("derived number on PHerc1218 mm", f"{float(published['mean_both_directions_mm']):.3f}",
         "mean of the two directions of the published row, the guard"),
        ("Pearson against the centroid baseline", f"{corr:.4f}",
         "mean_both_directions_mm against centroid_baseline_mm"),
        ("median difference against the centroid baseline mm",
         f"{statistics.median(g for _, g in gaps):.3f}", "over the scrolls"),
        ("largest difference against the centroid baseline mm", f"{worst_gap[1]:.3f}",
         worst_gap[0]),
        ("difference on PHerc1218 mm", f"{pherc1218[1]:.3f}",
         "the scroll the published number was measured on"),
        ("published number against the centroid column mm", f"{published_vs_centroid:.3f}",
         "both are the distance from the hand annotation of PHerc1218 to a mask centroid"),
    ]
    path = os.path.join(EV, "second-reference.csv")
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["quantity", "value", "note"])
        w.writerows(out)
    print("wrote", path, len(out), "rows")


if __name__ == "__main__":
    main()
