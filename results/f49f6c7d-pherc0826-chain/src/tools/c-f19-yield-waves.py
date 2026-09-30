#!/usr/bin/env python3
"""Figure C19: seed yield per wave of the chain as run on PHerc. 0826, in the order the waves ran.

What it reads. evidence/derived/chain-summary.csv (rows wave<N>, quantities draws and delivered; the
counts of the article's table of waves) and evidence/studies/search-yield-0826/yield.csv (rows of arm
«ours (item 91 arm C)», scope «wave N alone», quantities «hole free» and «certified», columns
finds_per_seed and seeds_grown_to_end), so that this figure and the search yield paragraph count the
same finds. A find is a delivered seed with a square of 10 mm or more on one of its sheets, hole free
or certified, as search-yield-0826/DECLARATION.md defines it; the figure does not recount it.

What it draws. For each wave, finds per 100 seeds drawn, hole free and certified side by side, with
the counts behind each bar written above it. Waves 1 to 3 drew uniformly and are marked random; waves 4
and 5 drew near seeds that had already given a large square. A wave none of whose seeds had been grown
to the end at the chain's freeze is labelled so, not drawn as a zero.

What it writes. evidence/figures/c-f19-yield-waves.csv (key, panel, what, source, value; one row per
quantity drawn) and tools/c-f19-yield-waves-body.tex, the pgfplots body made from those rows.

Usage: c-f19-yield-waves.py [--out PATH] [--tex PATH]
"""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib  # noqa: E402

FIGURE = "c-f19-yield-waves"
FIELDS = ["key", "panel", "what", "source_file", "source_column", "value"]
ARM = "ours (item 91 arm C)"
RANDOM = (1, 2, 3)   # waves drawn uniformly (body.tex, The seeds; chain-0826 DECLARATION.md)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    ap.add_argument("--tex", default=None)
    a = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = a.out or os.path.join(here, "evidence/figures/%s.csv" % FIGURE)
    tex = a.tex or os.path.join(here, "tools/%s-body.tex" % FIGURE)
    _, _, cs = figlib.read_study_csv(os.path.join(here, "evidence/derived/chain-summary.csv"))
    _, _, yl = figlib.read_study_csv(os.path.join(here, "evidence/studies/search-yield-0826/yield.csv"))
    waves = sorted({int(r["scope"][4:]) for r in cs if r["scope"].startswith("wave") and r["scope"][4:].isdigit()})
    if not waves:
        sys.exit("chain-summary.csv: no wave rows")
    rows, W = [], []

    def put(key, what, src, col, value):
        rows.append(dict(key=key, panel="a", what=what, source_file=src, source_column=col, value=value))

    for w in waves:
        c = {r["quantity"]: r["value"] for r in cs if r["scope"] == "wave%d" % w}
        draws = int(figlib.required_number(c, "draws", "wave %d" % w))
        dl = int(figlib.required_number(c, "delivered", "wave %d" % w))
        f = {}
        grown = None
        for q in ("hole free", "certified"):
            r = [x for x in yl if x["arm"] == ARM and x["scope"] == "wave %d alone" % w and x["quantity"] == q]
            if len(r) != 1:
                sys.exit("yield.csv: %d rows for wave %d %s" % (len(r), w, q))
            f[q] = int(figlib.required_number(r[0], "finds_per_seed", "wave %d %s" % (w, q)))
            g = int(figlib.required_number(r[0], "seeds_grown_to_end", "wave %d" % w))
            if grown is not None and g != grown:
                sys.exit("yield.csv: wave %d grown to the end differs between quantities" % w)
            grown = g
        put("draws_w%d" % w, "wave %d seeds drawn" % w, "derived/chain-summary.csv", "wave%d draws" % w, draws)
        put("delivered_w%d" % w, "wave %d seeds delivered" % w, "derived/chain-summary.csv", "wave%d delivered" % w, dl)
        put("grown_w%d" % w, "wave %d seeds grown to the end" % w, "search-yield-0826/yield.csv", "seeds_grown_to_end", grown)
        for q, k in (("hole free", "hf"), ("certified", "cert")):
            put("finds_%s_w%d" % (k, w), "wave %d %s finds (seeds)" % (w, q), "search-yield-0826/yield.csv",
                "finds_per_seed; arm %s; scope wave %d alone" % (ARM, w), f[q])
            put("per100_%s_w%d" % (k, w), "wave %d %s finds per 100 seeds drawn" % (w, q), "this tool",
                "finds over draws times 100", ("%.2f" % (100.0 * f[q] / draws)) if grown else figlib.NOT_MEASURABLE)
        put("random_w%d" % w, "wave %d drawn uniformly" % w, "body.tex The seeds; chain-0826 DECLARATION.md", "",
            "yes" if w in RANDOM else "no")
        W.append((w, draws, dl, grown, f["hole free"], f["certified"]))
    comment = ("figure C19, what the bar chart drew, written by src/tools/%s.py: per wave of the chain as run, draws from "
               "derived/chain-summary.csv and finds (hole free and certified squares of 10 mm or more, one per seed) from "
               "search-yield-0826/yield.csv rows «%s», scope «wave N alone»; per100 = finds over draws times 100" % (FIGURE, ARM))
    figlib.write_plotted(out, comment, FIELDS, rows)

    top = max(100.0 * max(hf, ce) / d for (_, d, _, g, hf, ce) in W if g)
    ymax = top * 1.3
    L = ["%% Generated by src/tools/%s.py from evidence/figures/%s.csv. Do not edit." % (FIGURE, FIGURE)]
    L.append("\\begin{axis}[sa base, width=82mm, height=60mm, ybar=0pt, bar width=7pt, xmin=0.4, xmax=%g, ymin=0, ymax=%g,"
             " xtick={%s}, xticklabels={%s}, xticklabel style={align=center, font=\\footnotesize},"
             " ylabel={finds per 100 seeds drawn}, grid=none, ymajorgrids=true,"
             " sa legend below, legend style={at={(0.5,-0.3)}, legend columns=1, draw=none}, clip=false]"
             % (len(W) + 0.6, ymax, ",".join(str(w) for w, *_ in W),
                ", ".join("{wave %d\\\\%s}" % (w, "random" if w in RANDOM else "near") for w, *_ in W)))
    rw = [w for w, *_ in W if w in RANDOM]
    if rw:
        L.append("\\fill[sagrey!10] (axis cs:%g,0) rectangle (axis cs:%g,%g);" % (min(rw) - 0.45, max(rw) + 0.45, ymax))
    L.append("\\addplot[area legend, fill=saorange, draw=saorange!70!black] coordinates {%s};"
             % " ".join("(%d,%.4f)" % (w, 100.0 * hf / d) for (w, d, _, g, hf, ce) in W if g))
    L.append("\\addlegendentry{hole free square, 10 mm or more}")
    L.append("\\addplot[area legend, fill=sasky, draw=sasky!70!black] coordinates {%s};"
             % " ".join("(%d,%.4f)" % (w, 100.0 * ce / d) for (w, d, _, g, hf, ce) in W if g))
    L.append("\\addlegendentry{certified square, 10 mm or more}")
    for (w, d, dl, g, hf, ce) in W:
        if g:
            L.append("\\node[count, anchor=south] at (axis cs:%d,%.4f) {%d and %d\\\\of %s};"
                     % (w, 100.0 * max(hf, ce) / d, hf, ce, "{:,}".format(d)))
        else:
            L.append("\\node[count, anchor=south] at (axis cs:%d,0) {none grown\\\\to the end\\\\by the freeze};" % w)
    L.append("\\end{axis}")
    with open(tex, "w") as fh:
        fh.write("\n".join(L) + "\n")
    sys.stderr.write("%s: %d waves\n" % (out, len(W)))


if __name__ == "__main__":
    main()
