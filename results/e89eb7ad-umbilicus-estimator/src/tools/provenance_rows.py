#!/usr/bin/env python3
"""Write src/paper/provenance-rows.tex, the rows of the appendix «Where each number comes from».

Added 2026-09-26, when the article was brought to the house template of the other works, whose
last appendix names, for every place in the text that prints a number, the file the number is
read from and the tool that writes that file. This article was published on 2026-09-17 with the
file named in each caption and in the prose; the appendix collects them in one table and adds the
files the prose reads through macros without naming them.

Every row is checked before anything is written, and the tool stops on the first failure:

  - each file exists under src/evidence;
  - each file is read by one of the three number writers of the article (src/paper/rev1_numbers.py,
    src/tools/paper_numbers.py) or named in src/paper/body.tex, so no row names a file the article
    does not use;
  - the tool named as the writer exists under src/tools and names the file in its own source,
    so no row names a writer that does not write it. The one file that no tool of this folder
    writes says so in the row, with the reason taken from src/evidence/README.md.

The first column is a LaTeX reference to the section, table or figure, so the numbering follows the
article and is never typed.

    python3 src/tools/provenance_rows.py
"""
import os
import sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(S, "evidence")
TOOLS = os.path.join(S, "tools")
PAPER = os.path.join(S, "paper")
OUT = os.path.join(PAPER, "provenance-rows.tex")

# (where, what, files, writer). writer None: no tool of this folder writes the file, and the
# row carries the reason instead, from src/evidence/README.md.
ROWS = [
    (r"Sec.~\ref{sec:line}", "the state upstream of pull request 1823, read again for the introduction",
     ["upstream-status-2026-09-28.csv"], "upstream_status.py"),
    (r"Sec.~\ref{sec:line}", "the defect line at the tip of the upstream default branch",
     ["upstream-check.csv"], "upstream_check.py"),
    (r"Sec.~\ref{sec:defect}, Fig.~\ref{fig:mechanism}", "the score against distance, sum and mean",
     ["mechanism-curve.csv"], "synthetic_density.py"),
    (r"Fig.~\ref{fig:exponent}", "the same score at each exponent",
     ["exponent-ablation-mechanism-curve.csv"], "figure_exponent.py"),
    (r"Fig.~\ref{fig:exponent}", "the rate each curve approaches or leaves the plateau",
     ["exponent-ablation-cancellation-rate.csv"], "exponent_ablation.py"),
    (r"Abstract, Sec.~\ref{sec:defect}, Table~\ref{tab:farfield}", "the far field bound against the runs, slice by slice",
     ["far-field-slices.csv", "far-field-prediction.csv"], "far_field_eigenvalue.py"),
    (r"Sec.~\ref{sec:defect}", "the far field limit on one slice and two synthetic sections",
     ["far-field-eigenvalue.csv"], "far_field_eigenvalue.py"),
    (r"Table~\ref{tab:farfieldscrolls}", "the same with the scroll as the unit, and its permutation test",
     ["far-field-per-scroll.csv", "far-field-permutation.csv"], "far_field_scrolls.py"),
    (r"Sec.~\ref{sec:fifteen}", "which scrolls were measured before the pre-registration",
     ["prereg-timeline.csv"], "prereg_timeline.py"),
    (r"Tables~\ref{tab:primary} and~\ref{tab:confirm}", "distances, intervals and the pre-registered verdicts",
     ["cpp-k20.csv", "cpp-k20-verdicts.json"], "cpp_k20.py"),
    (r"Sec.~\ref{sec:fifteen}", "every call of the compiled function",
     ["cpp-k20-estimates.csv"], "cpp_k20.py"),
    (r"Sec.~\ref{sec:fifteen}", "what those calls cost, summed from the seconds of each call",
     ["cpp-k20-estimates.csv"], "cpp_k20.py"),
    (r"Sec.~\ref{sec:fifteen}, Tables~\ref{tab:primary} and~\ref{tab:confirm}", "the margins before rounding, and the verdicts taken on them",
     ["cpp-k20-margins.csv", "cpp-k20-verdicts.json"], "cpp_k20_margins.py"),
    (r"Sec.~\ref{sec:fifteen}", "the cap of the transcription's hill climb",
     ["search-cap.csv"], "search_cap.py"),
    (r"Table~\ref{tab:baselines}", "the two rules scored after the fact",
     ["baselines-k20.csv"], "baselines_k20.py"),
    (r"Sec.~\ref{sec:baselines}", "the same question inside the umbilicus bench",
     ["bench-rules.csv"], "bench_rules.py"),
    (r"Sec.~\ref{sec:baselines}", "the rank tests and the Bland-Altman rows",
     ["inference-refit.json", "bland-altman-refit.csv"], "rev1_inference.py"),
    (r"Abstract, Sec.~\ref{sec:twentyfour}, Fig.~\ref{fig:gallery}", "the run on every scroll of the challenge",
     ["cpp-positions-24.csv"], "cpp_gen24.py"),
    (r"Sec.~\ref{sec:twentyfour}", "its per scroll summary",
     ["cpp-twentyfour.csv"], "cpp_gen24_score.py"),
    (r"Table~\ref{tab:density}", "the density bias on sections with a known centre",
     ["synthetic-density.csv"], "synthetic_density.py"),
    (r"Sec.~\ref{sec:density}", "one sidedness of the segments on the fifteen scrolls",
     ["density-asymmetry-fifteen.csv", "density-asymmetry-fifteen-summary.csv"], "density_asymmetry.py"),
    (r"Table~\ref{tab:ablation}", "the four cells of the ablation",
     ["ablation-search.csv"], "ablation_search.py"),
    (r"Sec.~\ref{sec:patch}", "what the merged squash of pull request 1823 touches",
     ["merged-patch.csv"], "merged_patch.py"),
    (r"Sec.~\ref{sec:patch}", "the regression test of the patch as built and run",
     ["regression-test-run.csv"], "regression_test_result.py"),
    (r"Table~\ref{tab:exponent}", "the exponent of the weight, compiled",
     ["cpp-exponent-fifteen-k20.csv", "cpp-exponent-seed-spread.csv"], "cpp_exponent_score.py"),
    (r"Sec.~\ref{sec:exponent}", "the transcription's p = 1 against its own estimates",
     ["exponent-ablation-k20-estimates.csv"], "exponent_ablation.py"),
    (r"Table~\ref{tab:exponent}", "the interval and the paired count of its aggregate row",
     ["cpp-exponent-aggregate.csv"], "exponent_intervals.py"),
    (r"Sec.~\ref{sec:notdone}", "what the second umbilicus of PHerc.\\ 1218 is",
     ["second-reference.csv"], "second_reference.py"),
]

# Why no tool of this folder writes this one, in the words of src/evidence/README.md.
NO_WRITER = {
    "cpp-k20-cost.csv": "by hand from the log of the run, one quantity per row",
}


# A file whose name the writer takes from its --out argument rather than from its own source: the
# writer must instead name the option that gives the file its shape, and the file must carry it.
WRITTEN_AS = {
    "upstream-status-2026-09-26.csv": ("--merged-at", "merged_at"),
    "upstream-status-2026-09-28.csv": ("--merged-at", "merged_at"),
}


def tt(name):
    # \path of the url package, so a long file name breaks at the end of a narrow column instead of
    # running into the next one; it takes the name as typed, underscores included.
    return "\\path{%s}" % name


def main():
    readers = "".join(open(p, errors="replace").read() for p in
                      (os.path.join(PAPER, "rev1_numbers.py"), os.path.join(TOOLS, "paper_numbers.py"),
                       os.path.join(PAPER, "body.tex")))
    out = []
    for where, what, files, writer in ROWS:
        for f in files:
            if not os.path.exists(os.path.join(EV, f)):
                sys.exit("provenance_rows.py: no src/evidence/%s" % f)
            if f not in readers:
                sys.exit("provenance_rows.py: %s is read by no number writer and named nowhere in the body" % f)
            if writer is None:
                if f not in NO_WRITER:
                    sys.exit("provenance_rows.py: %s has no writer and no reason given" % f)
                continue
            p = os.path.join(TOOLS, writer)
            if not os.path.exists(p):
                sys.exit("provenance_rows.py: no src/tools/%s" % writer)
            src = open(p, errors="replace").read()
            if f in WRITTEN_AS:
                opt, col = WRITTEN_AS[f]
                if opt not in src or col not in open(os.path.join(EV, f)).readline().strip().split(","):
                    sys.exit("provenance_rows.py: %s is not written by src/tools/%s %s" % (f, writer, opt))
                continue
            if f not in src:
                sys.exit("provenance_rows.py: src/tools/%s does not name %s" % (writer, f))
        opts = sorted({WRITTEN_AS[f][0] for f in files if f in WRITTEN_AS})
        by = (tt(writer) + "".join(" " + tt(o) for o in opts)) if writer else "; ".join(NO_WRITER[f] for f in files)
        out.append("%s & %s & %s & %s \\\\" % (where, what, ", ".join(tt(f) for f in files), by))
    with open(OUT, "w") as fh:
        fh.write("%% Generated by src/tools/provenance_rows.py. Do not edit.\n")
        fh.write("\n".join(out) + "\n")
    print("provenance_rows.py: wrote %s, %d rows" % (OUT, len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
