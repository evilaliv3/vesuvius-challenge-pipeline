#!/usr/bin/env python3
"""Write src/paper/numbers.tex from src/evidence. No number in the article is typed by hand.

The shape is the one paper/00001 uses: every numeric value in the .tex expands a macro defined
here, and this file is generated. `rev1-numbers.tex` of that folder is the model, down to the
`\\xspace` after each value.

Two rules this generator keeps and states, because both have cost this laboratory a correction:

  1. A macro is written only if the cell it comes from is there. A missing cell stops the tool
     with the file and the column named; it is never a default and never a zero.
  2. The tool says how many macros it expected to write and how many it wrote, which is the rule
     of 2026-09-22T04:17:45Z applied to a generator.
"""
import csv, os, re, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(S, "evidence", "studies")
OUT = os.path.join(S, "paper", "numbers.tex")


def rows(rel):
    p = os.path.join(EV, rel)
    if not os.path.exists(p):
        sys.exit("paper_numbers.py: no %s" % p)
    lines = open(p).read().splitlines(True)
    lines = [l for l in lines
             if not l.lstrip().startswith('"#') and not l.lstrip().startswith("#")]
    return list(csv.DictReader(lines))


def group(v):
    """The value as the ARTICLE prints it, which is not always as the CSV holds it.

    A CSV holds 1548.2 and 94962; an article prints 1,548.2 and 94,962. The macro has to carry
    the typeset form, or the number in the prose and the number in the macro are different
    strings and the one in the prose stays a literal. That is exactly what happened on the first
    run of macroise.py: nine macros of twenty one found nothing in the body, every one of them a
    value of four digits or more.

    Only a plain number is grouped. Anything with a letter, a sign or a second dot is left
    exactly as the file has it, because it is not a quantity this rule is about.
    """
    if not re.fullmatch(r"\d+(?:\.\d+)?", v):
        return v
    whole, _, frac = v.partition(".")
    if len(whole) < 4:
        return v
    out = "{:,}".format(int(whole))
    return out + ("." + frac if frac else "")


def series(v):
    """A semicolon list from a CSV as the ARTICLE prints it: commas, and each element grouped.

    c-stage-summary.csv holds every second that finished as «47.4; 48.6; 48.3» and the article
    prints «47.4, 48.6, 48.3». Same reason group() exists: a macro has to carry the typeset form
    or the prose keeps its literal. The middle run of a series had no macro at all until
    2026-09-22T18:45Z, so a reader met two macros and one literal inside one list.
    """
    return ", ".join(group(x.strip()) for x in v.split(";") if x.strip())


def pick(rs, where, col, rel):
    """One cell, or a stop that names what was looked for."""
    hit = [r for r in rs if all(r.get(k) == v for k, v in where.items())]
    if len(hit) != 1:
        sys.exit("paper_numbers.py: %s, %s: expected 1 row, found %d"
                 % (rel, ", ".join("%s=%s" % kv for kv in where.items()), len(hit)))
    if col not in hit[0] or hit[0][col] == "":
        sys.exit("paper_numbers.py: %s has no cell in column %s for %s" % (rel, col, where))
    return hit[0][col]


def main():
    M = {}

    # the quiet bench: the seconds behind every factor of this work
    rel = "quiet-bench/c-stage-summary.csv"
    b = rows(rel)
    for arm, seed, tag in (("c2", "PHerc1447-seed26", "BothSeedTwentySix"),
                           ("c2", "PHerc1447-seed40", "BothSeedForty"),
                           ("c2", "PHerc1447-seed38", "BothSeedThirtyEight"),
                           ("plain", "PHerc1447-seed26", "PlainSeedTwentySix"),
                           ("plain", "PHerc1447-seed40", "PlainSeedForty"),
                           ("plain", "PHerc1447-seed38", "PlainSeedThirtyEight"),
                           ("noA8", "PHerc1447-seed26", "NoAEightSeedTwentySix")):
        w = {"arm": arm, "attempt": seed}
        M["Bench" + tag + "Min"] = pick(b, w, "seconds_min", rel)
        M["Bench" + tag + "Max"] = pick(b, w, "seconds_max", rel)
        M["Bench" + tag + "Runs"] = pick(b, w, "runs_that_finished", rel)


    # The factors. The two files are keyed differently and that is not cosmetic: the medians file
    # is one row per RATIO and the other one row per ATTEMPT, and they answer different questions
    # about the same five runs, a median against a median and a smallest against a smallest. The
    # work names both wherever either is used, so both are generated here.
    rel = "quiet-bench/a8-factor-medians.csv"
    med = rows(rel)
    M["EarlierPatchFactorMedian"] = pick(med, {"ratio": "A8's four changes"}, "factor", rel)
    M["BothChangesFactor"] = pick(med, {"ratio": "corrections 00008 and 00009"}, "factor", rel)
    M["AllSixFactor"] = pick(med, {"ratio": "all six changes together"}, "factor", rel)
    rel = "quiet-bench/a8-factor.csv"
    M["EarlierPatchFactorSmallest"] = pick(rows(rel), {"attempt": "PHerc1447-seed26"},
                                           "factor", rel)

    # The MEDIAN of each arm on the ribbon, which the prose quotes as a value in its own right
    # and not only inside a list: «50.6 over 48.3» is the factor's own two operands. They are
    # shipped, in a8-factor-medians.csv, as the numerator and denominator of the two ratios, so
    # nothing is computed here. A series macro was tried first and cannot work: the smallest and
    # largest of the same three runs are already macros in the body, so the literal list is no
    # longer contiguous text for anything to match.
    rel = "quiet-bench/a8-factor-medians.csv"
    med = rows(rel)
    M["BenchNoAEightSeedTwentySixMedian"] = pick(
        med, {"ratio": "A8's four changes"}, "numerator_median_seconds", rel)
    M["BenchPlainSeedTwentySixMedian"] = pick(
        med, {"ratio": "A8's four changes"}, "denominator_median_seconds", rel)
    M["BenchBothSeedTwentySixMedian"] = pick(
        med, {"ratio": "corrections 00008 and 00009"}, "denominator_median_seconds", rel)

    # the identity of the earlier performance patch, measured 2026-09-22
    rel = "a8-identity/identity-totals.csv"
    if os.path.exists(os.path.join(EV, rel)):
        i = rows(rel)
        M["EarlierPatchFilesCompared"] = pick(i, {"tree": "both trees"}, "files_compared", rel)
        M["EarlierPatchFilesDiffering"] = pick(i, {"tree": "both trees"}, "files_differing", rel)
        M["EarlierPatchFilesFourteenFortySeven"] = pick(i, {"scroll": "PHerc1447"},
                                                        "files_compared", rel)
        M["EarlierPatchFilesZeroOneThreeNine"] = pick(i, {"scroll": "PHerc0139"},
                                                      "files_compared", rel)
    else:
        sys.exit("paper_numbers.py: %s is not shipped yet. The identity of the earlier patch is in the "
                 "draft, so its file has to travel with the article: copy "
                 "runs/rev1/a8-identity/evidence/identity-totals.csv into src/evidence/studies/"
                 "a8-identity/ and run check_shipped_copies.py." % rel)

    # The ten seeds of the search: the square each delivered, and the size of the tree it grew.
    # These are the numbers the prose meets most often outside the bench, and seed11's square
    # reads «not measurable» in the file, which travels into the macro as it stands: the article
    # prints what the evidence says and not a blank.
    rel = "seed-search-1447/per-seed.csv"
    seeds = rows(rel)
    words = {"01": "One", "11": "Eleven", "15": "Fifteen", "26": "TwentySix", "34": "ThirtyFour",
             "35": "ThirtyFive", "38": "ThirtyEight", "40": "Forty", "44": "FortyFour",
             "48": "FortyEight"}
    for num, word in words.items():
        w = {"attempt": "PHerc1447-seed" + num}
        M["SeedSquare" + word] = pick(seeds, w, "largest_square_mm_min_step", rel)
        M["SeedPatches" + word] = pick(seeds, w, "growth_patches", rel)
        M["SeedRelLines" + word] = pick(seeds, w, "growth_rel_csv_lines", rel)

    # The bookkeeping of the tree grown twice into one folder. These are the numbers the prose
    # repeats most: 104 appears nine times in the body, 413 and 202 seven each. A number a text
    # says nine times is the one that must not be a literal, because a literal has to be found
    # nine times when the measurement moves, and the ninth is the one that is missed.
    rel = "growth-bookkeeping/id-inventory-seed34.csv"
    inv = rows(rel)
    M["MixedOrphanIds"] = pick(inv, {"quantity": "orphan ids of badpatch-crash"}, "value", rel)
    M["MixedImpossibleIds"] = pick(
        inv, {"quantity": "ids the log says cannot be this run's"}, "value", rel)
    M["MixedImpossibleNoFile"] = pick(inv, {"quantity": "of those, with no patch file"},
                                      "value", rel)
    M["MixedImpossibleWithFile"] = pick(inv, {"quantity": "of those, with a patch file"},
                                        "value", rel)
    M["MixedHighestOrphanId"] = pick(inv, {"quantity": "highest orphan id"}, "value", rel)

    # What the guard refuses on that tree, at the two chain lengths the prose gives, and the
    # prediction made from rel.csv alone before the guard existed. The prediction and the count
    # are two different measurements of one thing and the work prints both, so both are here.
    rel = "orphan-guard/refused-chains.csv"
    ref = rows(rel)
    for length, word in (("2", "Two"), ("3", "Three")):
        w = {"attempt": "PHerc1447-seed34", "chain_length": length}
        M["RefusedChains" + word] = pick(ref, w, "chains_refused", rel)
        M["RefusedPatches" + word] = pick(ref, w, "patches_involved", rel)

    # The check that kept a rule from becoming a bar. A rule was built to make two segmentation
    # tools comparable: a cell counts only where the prediction the seeds grew from holds surface
    # within a voxel. It drops 38.5 per cent of the cells of the sheet that carries this work's
    # bar, so the question of whether those cells are papyrus was put to the owner as forty
    # unlabelled cutouts of the raw scan, twenty on kept cells and twenty on dropped ones, the
    # answer key held outside the folder that was published. They do not separate.
    rel = "tracer-against-the-chain/cutout-score-seed26-patch2.csv"
    cut = rows(rel)
    M["CutoutCoveredSheet"] = pick(cut, {}, "covered_yes", rel)
    M["CutoutCoveredNot"] = pick(cut, {}, "covered_no", rel)
    M["CutoutUncoveredSheet"] = pick(cut, {}, "uncovered_yes", rel)
    M["CutoutUncoveredNot"] = pick(cut, {}, "uncovered_no", rel)
    M["CutoutSheetRateCovered"] = pick(cut, {}, "sheet_rate_covered", rel)
    M["CutoutSheetRateUncovered"] = pick(cut, {}, "sheet_rate_uncovered", rel)
    M["CutoutFisherP"] = pick(cut, {}, "fisher_p_one_sided", rel)

    # How much of the chain's own delivery sits on the marked prediction, which is the column the
    # rule leaves behind now that it decides nothing.
    rel = "tracer-against-the-chain/coverage-selftest-chain.csv"
    cov = rows(rel)
    M["CoverShareBarSeed"] = pick(cov, {"seed": "26"}, "covered_share", rel)
    M["CoverShareAllSeeds"] = pick(cov, {"seed": "ALL"}, "covered_share", rel)

    # The bounded worklist of 2026-09-23 (the owner's bound, the director's ruling of 15:42:35Z):
    # every literal of runs/rev1/worklist-aeb2e975.csv of the house was read against its sentence
    # and its decision is a row of runs/rev1/macro-aeb2e975-conversion.csv. The ones converted
    # are below, one cell each, grouped by the file they are read from. A literal left out is
    # there for a reason written in that log: two meanings in the body, a sentence that names two
    # cells at once, a maximum no cell stores, or digits that only coincide with a cell.
    BOUNDED = [
        # c-stage-cost/totals.csv
        ("StepsModelTotalSeedForty", "c-stage-cost/totals.csv", {'quantity': 'odometer steps, all four rounds, model', 'attempt': 'PHerc1447-seed40'}, "value"),
        ("StepsPrunedTotalSeedForty", "c-stage-cost/totals.csv", {'quantity': 'odometer steps, all four rounds, measured, pruned', 'attempt': 'PHerc1447-seed40'}, "value"),
        ("StepsFactorSeedForty", "c-stage-cost/totals.csv", {'quantity': 'factor between the unpruned model and the pruned counter', 'attempt': 'PHerc1447-seed40'}, "value"),
        ("TimersOdometerSecondsCOne", "c-stage-cost/totals.csv", {'quantity': 'odometer_seconds summed over the four rounds, arm c1', 'attempt': 'PHerc1447-seed40'}, "value"),
        ("TimersCoverSecondsCOne", "c-stage-cost/totals.csv", {'quantity': 'cover_seconds summed over the four rounds, arm c1', 'attempt': 'PHerc1447-seed40'}, "value"),
        ("StepsShareLengthFiveSeedForty", "c-stage-cost/totals.csv", {'quantity': 'share of the steps that are the round at length 5, per cent', 'attempt': 'PHerc1447-seed40'}, "value"),
        ("TimersSetupSecondsCOne", "c-stage-cost/totals.csv", {'quantity': 'setup_seconds summed over the four rounds, arm c1', 'attempt': 'PHerc1447-seed40'}, "value"),
        ("TimersSequencesSecondsCOne", "c-stage-cost/totals.csv", {'quantity': 'sequences_seconds summed over the four rounds, arm c1', 'attempt': 'PHerc1447-seed40'}, "value"),
        ("TimersSetupSecondsCTwo", "c-stage-cost/totals.csv", {'quantity': 'setup_seconds summed over the four rounds, arm c2', 'attempt': 'PHerc1447-seed40'}, "value"),
        ("TimersOdometerSecondsCTwo", "c-stage-cost/totals.csv", {'quantity': 'odometer_seconds summed over the four rounds, arm c2', 'attempt': 'PHerc1447-seed40'}, "value"),
        ("TimersSequencesSecondsCTwo", "c-stage-cost/totals.csv", {'quantity': 'sequences_seconds summed over the four rounds, arm c2', 'attempt': 'PHerc1447-seed40'}, "value"),
        ("TimersCoverSecondsCTwo", "c-stage-cost/totals.csv", {'quantity': 'cover_seconds summed over the four rounds, arm c2', 'attempt': 'PHerc1447-seed40'}, "value"),
        # published-segments-eligible/segments-eligible.csv
        ("VoxelZeroOneThreeNine", "published-segments-eligible/segments-eligible.csv", {'scroll': 'PHerc0139', 'segment': 'ours-C40-sheet-1'}, "voxel_um"),
        ("SheetLatticeI", "published-segments-eligible/segments-eligible.csv", {'scroll': 'PHerc0139', 'segment': 'ours-C40-sheet-1'}, "cells_i"),
        ("SheetLatticeJ", "published-segments-eligible/segments-eligible.csv", {'scroll': 'PHerc0139', 'segment': 'ours-C40-sheet-1'}, "cells_j"),
        ("SheetSquareBase", "published-segments-eligible/segments-eligible.csv", {'scroll': 'PHerc0139', 'segment': 'ours-C40-sheet-1'}, "square_mm_min_step"),
        # seed-search-1447/alignment-fanout.csv
        ("FanOutSeedTwentySix", "seed-search-1447/alignment-fanout.csv", {'attempt': 'PHerc1447-seed26'}, "fan_out"),
        ("FanOutSeedThirtyEight", "seed-search-1447/alignment-fanout.csv", {'attempt': 'PHerc1447-seed38'}, "fan_out"),
        ("FanOutSeedForty", "seed-search-1447/alignment-fanout.csv", {'attempt': 'PHerc1447-seed40'}, "fan_out"),
        ("FanOutSeedOne", "seed-search-1447/alignment-fanout.csv", {'attempt': 'PHerc1447-seed01'}, "fan_out"),
        ("FanOutSeedFifteen", "seed-search-1447/alignment-fanout.csv", {'attempt': 'PHerc1447-seed15'}, "fan_out"),
        ("FanOutSeedFortyEight", "seed-search-1447/alignment-fanout.csv", {'attempt': 'PHerc1447-seed48'}, "fan_out"),
        ("FanOutSeedEleven", "seed-search-1447/alignment-fanout.csv", {'attempt': 'PHerc1447-seed11'}, "fan_out"),
        ("FanOutSeedThirtyFour", "seed-search-1447/alignment-fanout.csv", {'attempt': 'PHerc1447-seed34'}, "fan_out"),
        ("FanOutSeedThirtyFive", "seed-search-1447/alignment-fanout.csv", {'attempt': 'PHerc1447-seed35'}, "fan_out"),
        # c-stage-cost/profile-baseline.csv
        ("ProfileShareLeftChild", "c-stage-cost/profile-baseline.csv", {'tag': 'baseline', 'sort': 'srcline', 'what': 'stl_tree.h:1425'}, "share_percent"),
        ("ProfileShareFindBadPatches", "c-stage-cost/profile-baseline.csv", {'tag': 'baseline', 'sort': 'symbol', 'rank': '1'}, "share_percent"),
        ("ProfileShareRightChild", "c-stage-cost/profile-baseline.csv", {'tag': 'baseline', 'sort': 'srcline', 'what': 'stl_tree.h:1437'}, "share_percent"),
        ("ProfileShareLowerBoundOne", "c-stage-cost/profile-baseline.csv", {'tag': 'baseline', 'sort': 'srcline', 'what': 'stl_tree.h:2604'}, "share_percent"),
        ("ProfileShareLowerBoundTwo", "c-stage-cost/profile-baseline.csv", {'tag': 'baseline', 'sort': 'srcline', 'what': 'stl_tree.h:2605'}, "share_percent"),
        ("ProfileShareLowerBoundThree", "c-stage-cost/profile-baseline.csv", {'tag': 'baseline', 'sort': 'srcline', 'what': 'stl_tree.h:2603'}, "share_percent"),
        ("ProfileShareLowerBoundFour", "c-stage-cost/profile-baseline.csv", {'tag': 'baseline', 'sort': 'srcline', 'what': 'stl_tree.h:2607'}, "share_percent"),
        ("ProfileShareOdometerWalk", "c-stage-cost/profile-baseline.csv", {'tag': 'baseline', 'sort': 'srcline', 'what': 'badpatchfinder.cpp:426'}, "share_percent"),
        # c-stage-on-0139/trees.csv
        ("ZeroOneThreeNinePatchesS", "c-stage-on-0139/trees.csv", {'tree': 'S'}, "patch_files"),
        ("ZeroOneThreeNinePatchesDFourFifty", "c-stage-on-0139/trees.csv", {'tree': 'D450'}, "patch_files"),
        ("ZeroOneThreeNinePatchesC", "c-stage-on-0139/trees.csv", {'tree': 'C'}, "patch_files"),
        ("ZeroOneThreeNinePatchesDOneFifty", "c-stage-on-0139/trees.csv", {'tree': 'D150'}, "patch_files"),
        ("ZeroOneThreeNinePatchesPTwo", "c-stage-on-0139/trees.csv", {'tree': 'P2'}, "patch_files"),
        ("ZeroOneThreeNineFanOutC", "c-stage-on-0139/trees.csv", {'tree': 'C'}, "fan_out"),
        ("ZeroOneThreeNineFanOutA", "c-stage-on-0139/trees.csv", {'tree': 'A'}, "fan_out"),
        # c-stage-on-0139/c-stage-ratios.csv
        ("RatioGuardOverBothC", "c-stage-on-0139/c-stage-ratios.csv", {'tree': 'C', 'baseline_arm': 'guarded', 'arm': 'c2'}, "ratio_median_over_median"),
        ("RatioGuardOverBothPTwo", "c-stage-on-0139/c-stage-ratios.csv", {'tree': 'P2', 'baseline_arm': 'guarded', 'arm': 'c2'}, "ratio_median_over_median"),
        ("RatioPlainOverGuardRepeat", "c-stage-on-0139/c-stage-ratios.csv", {'tree': 'repeat', 'baseline_arm': 'plain', 'arm': 'guarded'}, "ratio_median_over_median"),
        ("RatioGuardOverBothRepeat", "c-stage-on-0139/c-stage-ratios.csv", {'tree': 'repeat', 'baseline_arm': 'guarded', 'arm': 'c2'}, "ratio_median_over_median"),
        ("RatioPlainOverGuardS", "c-stage-on-0139/c-stage-ratios.csv", {'tree': 'S', 'baseline_arm': 'plain', 'arm': 'guarded'}, "ratio_median_over_median"),
        ("RatioGuardOverBothS", "c-stage-on-0139/c-stage-ratios.csv", {'tree': 'S', 'baseline_arm': 'guarded', 'arm': 'c2'}, "ratio_median_over_median"),
        ("RatioPlainOverGuardDFourFifty", "c-stage-on-0139/c-stage-ratios.csv", {'tree': 'D450', 'baseline_arm': 'plain', 'arm': 'guarded'}, "ratio_median_over_median"),
        ("RatioGuardOverBothDFourFifty", "c-stage-on-0139/c-stage-ratios.csv", {'tree': 'D450', 'baseline_arm': 'guarded', 'arm': 'c2'}, "ratio_median_over_median"),
        ("RatioPlainOverGuardC", "c-stage-on-0139/c-stage-ratios.csv", {'tree': 'C', 'baseline_arm': 'plain', 'arm': 'guarded'}, "ratio_median_over_median"),
        ("RatioPlainOverGuardDOneFifty", "c-stage-on-0139/c-stage-ratios.csv", {'tree': 'D150', 'baseline_arm': 'plain', 'arm': 'guarded'}, "ratio_median_over_median"),
        ("RatioPlainOverGuardPTwo", "c-stage-on-0139/c-stage-ratios.csv", {'tree': 'P2', 'baseline_arm': 'plain', 'arm': 'guarded'}, "ratio_median_over_median"),
        # c-stage-cost/small-tree-cost.csv
        ("SpreadBothMin", "c-stage-cost/small-tree-cost.csv", {'series': '00007, 00008 and 00009'}, "min_seconds"),
        ("SpreadBothMax", "c-stage-cost/small-tree-cost.csv", {'series': '00007, 00008 and 00009'}, "max_seconds"),
        ("SpreadBothMedian", "c-stage-cost/small-tree-cost.csv", {'series': '00007, 00008 and 00009'}, "median_seconds"),
        ("SpreadGuardMax", "c-stage-cost/small-tree-cost.csv", {'series': 'guarded (00007 only)'}, "max_seconds"),
        # seed-search-1447/cost-per-ribbon-quiet.csv
        ("CostAfterSeedOne", "seed-search-1447/cost-per-ribbon-quiet.csv", {'attempt': 'PHerc1447-seed01'}, "growth_plus_c_after"),
        ("CostAfterSeedFifteen", "seed-search-1447/cost-per-ribbon-quiet.csv", {'attempt': 'PHerc1447-seed15'}, "growth_plus_c_after"),
        ("CostAfterSeedTwentySix", "seed-search-1447/cost-per-ribbon-quiet.csv", {'attempt': 'PHerc1447-seed26'}, "growth_plus_c_after"),
        ("CostBeforeSeedOne", "seed-search-1447/cost-per-ribbon-quiet.csv", {'attempt': 'PHerc1447-seed01'}, "growth_plus_c_before"),
        ("CostBeforeSeedFifteen", "seed-search-1447/cost-per-ribbon-quiet.csv", {'attempt': 'PHerc1447-seed15'}, "growth_plus_c_before"),
        ("CostBeforeSeedTwentySix", "seed-search-1447/cost-per-ribbon-quiet.csv", {'attempt': 'PHerc1447-seed26'}, "growth_plus_c_before"),
        ("CostBeforeSeedThirtyEight", "seed-search-1447/cost-per-ribbon-quiet.csv", {'attempt': 'PHerc1447-seed38'}, "growth_plus_c_before"),
        ("CostBeforeSeedForty", "seed-search-1447/cost-per-ribbon-quiet.csv", {'attempt': 'PHerc1447-seed40'}, "growth_plus_c_before"),
        ("CostBeforeSeedFortyEight", "seed-search-1447/cost-per-ribbon-quiet.csv", {'attempt': 'PHerc1447-seed48'}, "growth_plus_c_before"),
        ("CostAfterSeedThirtyEight", "seed-search-1447/cost-per-ribbon-quiet.csv", {'attempt': 'PHerc1447-seed38'}, "growth_plus_c_after"),
        ("CostAfterSeedForty", "seed-search-1447/cost-per-ribbon-quiet.csv", {'attempt': 'PHerc1447-seed40'}, "growth_plus_c_after"),
        ("CostAfterSeedFortyEight", "seed-search-1447/cost-per-ribbon-quiet.csv", {'attempt': 'PHerc1447-seed48'}, "growth_plus_c_after"),
        ("CostBeforeTotal", "seed-search-1447/cost-per-ribbon-quiet.csv", {'attempt': 'total all six'}, "growth_plus_c_before"),
        ("CostAfterTotal", "seed-search-1447/cost-per-ribbon-quiet.csv", {'attempt': 'total all six'}, "growth_plus_c_after"),
        # seed-search-1447/summary.csv
        ("BestPublishedSquare", "seed-search-1447/summary.csv", {'quantity': 'comparison', 'statistic': 'best_published_segment_of_PHerc1447'}, "value"),
        ("RepeatSpreadSquare", "seed-search-1447/summary.csv", {'quantity': 'comparison', 'statistic': 'director_rule_spread'}, "value"),
        # c-stage-cost/runs.csv
        ("StageFmSecondsSeedTwentySix", "c-stage-cost/runs.csv", {'tag': 'c2', 'attempt': 'PHerc1447-seed26', 'stage': 'fm 30 10'}, "seconds"),
        # the load of the shared machine during the stages l to fm of the first table (2026-09-30, the owner's order):
        # cores busy at the start of the l stage of seed40 (the lower) and of seed26 (the higher), tag c2
        ("StageLoadLow", "c-stage-cost/runs.csv", {'tag': 'c2', 'attempt': 'PHerc1447-seed40', 'stage': 'l'}, "cores_busy_at_start"),
        ("StageLoadHigh", "c-stage-cost/runs.csv", {'tag': 'c2', 'attempt': 'PHerc1447-seed26', 'stage': 'l'}, "cores_busy_at_start"),
        ("ProfileBaselineSeconds", "c-stage-cost/runs.csv", {'tag': 'baseline-profile', 'stage': 'c'}, "seconds"),
        ("TimersStageSecondsCOne", "c-stage-cost/runs.csv", {'tag': 'timers-c1', 'stage': 'c'}, "seconds"),
        ("TimersStageSecondsCTwo", "c-stage-cost/runs.csv", {'tag': 'timers-c2', 'stage': 'c'}, "seconds"),
        ("ChangedSecondsSeedEleven", "c-stage-cost/runs.csv", {'tag': 'c2-11-35', 'attempt': 'PHerc1447-seed11', 'stage': 'c'}, "seconds"),
        ("SpreadPlainRunOne", "c-stage-cost/runs.csv", {'tag': 'spread-plain-1', 'stage': 'c'}, "seconds"),
        # seed-search-1447/per-seed.csv
        ("SeedTracedAreaFortyFour", "seed-search-1447/per-seed.csv", {'attempt': 'PHerc1447-seed44'}, "traced_area_mm2"),
        # c-stage-cost/step-counts-model.csv
        ("StepsModelSeedTwentySixLengthTwo", "c-stage-cost/step-counts-model.csv", {'attempt': 'PHerc1447-seed26', 'length': '2'}, "odometer_steps"),
        ("StepsModelSeedTwentySixLengthThree", "c-stage-cost/step-counts-model.csv", {'attempt': 'PHerc1447-seed26', 'length': '3'}, "odometer_steps"),
        ("StepsModelSeedTwentySixLengthFour", "c-stage-cost/step-counts-model.csv", {'attempt': 'PHerc1447-seed26', 'length': '4'}, "odometer_steps"),
        ("StepsModelSeedTwentySixLengthFive", "c-stage-cost/step-counts-model.csv", {'attempt': 'PHerc1447-seed26', 'length': '5'}, "odometer_steps"),
        ("StepsModelSeedFortyLengthThree", "c-stage-cost/step-counts-model.csv", {'attempt': 'PHerc1447-seed40', 'length': '3'}, "odometer_steps"),
        ("StepsModelSeedFortyLengthFour", "c-stage-cost/step-counts-model.csv", {'attempt': 'PHerc1447-seed40', 'length': '4'}, "odometer_steps"),
        ("StepsModelSeedFortyLengthFive", "c-stage-cost/step-counts-model.csv", {'attempt': 'PHerc1447-seed40', 'length': '5'}, "odometer_steps"),
        # c-stage-cost/step-counts-measured.csv
        ("StepsPrunedSeedFortyLengthThree", "c-stage-cost/step-counts-measured.csv", {'variant': 'pruned', 'attempt': 'PHerc1447-seed40', 'length': '3'}, "odometer_steps"),
        ("StepsPrunedSeedFortyLengthFour", "c-stage-cost/step-counts-measured.csv", {'variant': 'pruned', 'attempt': 'PHerc1447-seed40', 'length': '4'}, "odometer_steps"),
        ("StepsPrunedSeedFortyLengthFive", "c-stage-cost/step-counts-measured.csv", {'variant': 'pruned', 'attempt': 'PHerc1447-seed40', 'length': '5'}, "odometer_steps"),
        # c-stage-cost/c-stage-times.csv
        ("CStageCOneSeedOne", "c-stage-cost/c-stage-times.csv", {'arm': 'c1', 'attempt': 'PHerc1447-seed01'}, "arm_seconds"),
        ("CStageCTwoSeedOne", "c-stage-cost/c-stage-times.csv", {'arm': 'c2', 'attempt': 'PHerc1447-seed01'}, "arm_seconds"),
        ("CStageCOneSeedFifteen", "c-stage-cost/c-stage-times.csv", {'arm': 'c1', 'attempt': 'PHerc1447-seed15'}, "arm_seconds"),
        ("CStageCTwoSeedFifteen", "c-stage-cost/c-stage-times.csv", {'arm': 'c2', 'attempt': 'PHerc1447-seed15'}, "arm_seconds"),
        ("CStageCOneSeedTwentySix", "c-stage-cost/c-stage-times.csv", {'arm': 'c1', 'attempt': 'PHerc1447-seed26'}, "arm_seconds"),
        # 2026-09-23 (coordinator): the two cells below hold 51.8 like BenchPlainSeedTwentySixMax, which an
        # earlier placement by value had put in their place in the text; each now has its own macro.
        ("CStageCTwoSeedTwentySix", "c-stage-cost/c-stage-times.csv", {'arm': 'c2', 'attempt': 'PHerc1447-seed26'}, "arm_seconds"),
        ("ZeroOneThreeNineMedianPlainRepeat", "c-stage-on-0139/c-stage-diff.csv", {'tree': 'repeat', 'arm_a': 'plain', 'arm_b': 'c2'}, "median_a"),
        ("CStageCOneSeedThirtyEight", "c-stage-cost/c-stage-times.csv", {'arm': 'c1', 'attempt': 'PHerc1447-seed38'}, "arm_seconds"),
        ("CStageCTwoSeedThirtyEight", "c-stage-cost/c-stage-times.csv", {'arm': 'c2', 'attempt': 'PHerc1447-seed38'}, "arm_seconds"),
        ("CStageCOneSeedForty", "c-stage-cost/c-stage-times.csv", {'arm': 'c1', 'attempt': 'PHerc1447-seed40'}, "arm_seconds"),
        ("CStageCOneSeedFortyEight", "c-stage-cost/c-stage-times.csv", {'arm': 'c1', 'attempt': 'PHerc1447-seed48'}, "arm_seconds"),
        ("CStageCTwoSeedFortyEight", "c-stage-cost/c-stage-times.csv", {'arm': 'c2', 'attempt': 'PHerc1447-seed48'}, "arm_seconds"),
        ("CStageReferenceSeedThirtyEight", "c-stage-cost/c-stage-times.csv", {'arm': 'c1', 'attempt': 'PHerc1447-seed38'}, "reference_seconds"),
        ("CStageReferenceSeedFortyEight", "c-stage-cost/c-stage-times.csv", {'arm': 'c1', 'attempt': 'PHerc1447-seed48'}, "reference_seconds"),
        # seed-search-1447/untouched-seed11-downstream.csv
        ("UntouchedSecondsSeedEleven", "seed-search-1447/untouched-seed11-downstream.csv", {'attempt': 'PHerc1447-seed11', 'stage': 'c'}, "seconds"),
        # c-stage-on-0139/c-stage-diff.csv
        ("ZeroOneThreeNineMedianBothRepeat", "c-stage-on-0139/c-stage-diff.csv", {'tree': 'repeat', 'arm_a': 'plain', 'arm_b': 'c2'}, "median_b"),
        ("ZeroOneThreeNineMedianPlainS", "c-stage-on-0139/c-stage-diff.csv", {'tree': 'S', 'arm_a': 'plain', 'arm_b': 'c2'}, "median_a"),
        ("ZeroOneThreeNineMedianBothS", "c-stage-on-0139/c-stage-diff.csv", {'tree': 'S', 'arm_a': 'plain', 'arm_b': 'c2'}, "median_b"),
        ("ZeroOneThreeNineMedianPlainDFourFifty", "c-stage-on-0139/c-stage-diff.csv", {'tree': 'D450', 'arm_a': 'plain', 'arm_b': 'c2'}, "median_a"),
        ("ZeroOneThreeNineMedianBothDFourFifty", "c-stage-on-0139/c-stage-diff.csv", {'tree': 'D450', 'arm_a': 'plain', 'arm_b': 'c2'}, "median_b"),
        ("ZeroOneThreeNineMedianPlainC", "c-stage-on-0139/c-stage-diff.csv", {'tree': 'C', 'arm_a': 'plain', 'arm_b': 'c2'}, "median_a"),
        ("ZeroOneThreeNineMedianBothC", "c-stage-on-0139/c-stage-diff.csv", {'tree': 'C', 'arm_a': 'plain', 'arm_b': 'c2'}, "median_b"),
        ("ZeroOneThreeNineMedianPlainDOneFifty", "c-stage-on-0139/c-stage-diff.csv", {'tree': 'D150', 'arm_a': 'plain', 'arm_b': 'c2'}, "median_a"),
        ("ZeroOneThreeNineMedianBothDOneFifty", "c-stage-on-0139/c-stage-diff.csv", {'tree': 'D150', 'arm_a': 'plain', 'arm_b': 'c2'}, "median_b"),
        ("ZeroOneThreeNineMedianPlainPTwo", "c-stage-on-0139/c-stage-diff.csv", {'tree': 'P2', 'arm_a': 'plain', 'arm_b': 'c2'}, "median_a"),
        ("ZeroOneThreeNineMedianBothPTwo", "c-stage-on-0139/c-stage-diff.csv", {'tree': 'P2', 'arm_a': 'plain', 'arm_b': 'c2'}, "median_b"),
        # growth-bookkeeping/log-compare.csv
        ("MixedImpossibleMentions", "growth-bookkeeping/log-compare.csv", {'log': 'growth-PHerc1447-seed34.txt'}, "impossible_mentions"),
        # growth-bookkeeping/tree-freshness.csv
        ("MixedChunkFiles", "growth-bookkeeping/tree-freshness.csv", {'attempt': 'PHerc1447-seed34'}, "chunk_files"),
        # growth-bookkeeping/orphan-rows.csv
        ("MixedRowsImpossible", "growth-bookkeeping/orphan-rows.csv", {'population': 'impossible_ids_413'}, "rows"),
        ("MixedRowsOrphan", "growth-bookkeeping/orphan-rows.csv", {'population': 'orphan_ids_104'}, "rows"),
    ]
    cache = {}
    for name, rel, where, col in BOUNDED:
        if rel not in cache:
            cache[rel] = rows(rel)
        M[name] = pick(cache[rel], where, col, rel)

    # 2026-09-24, director 08:52:23Z point 3: the coverage of the delivered sheets of PHerc. 1447,
    # deduplicated, from the renamed copy of union.csv (numbers by union_area.py, names by
    # accepted_names.py). The prose rounds to whole cm2, so the macro does, from the cell; the bin
    # side is read from the file, never typed, and the tool stops if the row is not at 4 voxels.
    # 2026-09-24T10:16:29Z verdict on the stitched test: the copy is now union-renamed-v3.csv, written
    # by accepted_names_v3.py with the label of that verdict, worded «winding» on the ruling of 2026-09-24T10:54:00Z; the numbers are the same cells.
    rel = "coverage-union-1447/union-renamed-v3.csv"
    u = rows(rel)
    if pick(u, {"cell_set": "all"}, "bin_side_voxels", rel) != "4":
        sys.exit("paper_numbers.py: %s row all is not at a bin of 4 voxels" % rel)
    M["CoverageUnionOneCell"] = str(int(round(float(pick(u, {"cell_set": "all"}, "union_cm2", rel)))))
    M["CoverageUnionTwoCells"] = str(int(round(float(
        pick(u, {"cell_set": "all"}, "union_bin_side_8_voxels_cm2", rel)))))
    M["CoverageSeeds"] = pick(u, {"cell_set": "all"}, "seeds_counted", rel)
    M["CoverageBinVoxels"] = pick(u, {"cell_set": "all"}, "bin_side_voxels", rel)
    M["StevensCoverageQuote"] = pick(u, {"cell_set": "all"}, "stevens_quote", rel)

    # 2026-09-24, director 10:16:29Z point 4: Stevens' ten published components of PHerc. 1667 measured
    # by this laboratory's tool, summed with every overlap counted. From the renamed copy of
    # field-sums.csv (numbers by field_table.py, names by accepted_names_v3.py). The count is printed
    # as a word, so the word is taken from the cell and the tool stops on a count it has no word for;
    # the sentence says «every overlap counted», so the tool stops unless the row's own column says so.
    rel = "field-0826-0800/field-sums-renamed-v3.csv"
    fs = rows(rel)
    how = pick(fs, {"scroll": "PHerc1667"}, "how", rel)
    if "every overlap counted" not in how:
        sys.exit("paper_numbers.py: %s row PHerc1667 does not say every overlap counted: %r" % (rel, how))
    words = {"10": "ten"}
    n = pick(fs, {"scroll": "PHerc1667"}, "surfaces", rel)
    if n not in words:
        sys.exit("paper_numbers.py: %s row PHerc1667 has %s surfaces, no word for it" % (rel, n))
    M["StevensComponentsWord"] = words[n]
    M["StevensComponentsSum"] = pick(fs, {"scroll": "PHerc1667"}, "delivered_area_cm2_sum", rel)

    # 2026-09-24, director 17:22:24Z and 18:24:03Z: the ink sentence of Limits. From the shipped
    # ink-detector-0139/descriptive-row.csv (tool descriptive_row.py), rows of our two sheets only,
    # seed376 S0 and seed316 S1; any other PHerc1447 row (seed325's sheet only row) is left out by
    # name and said so. Every word of the sentence that states an order is checked on the cells:
    # «between» (the no ink maximum below our minimum, our maximum below the ink minimum), the two
    # component ranges, «no ink is evident» (our largest component count below the smallest on the
    # labelled ink), and «our two largest sheets» (the top two of union-per-sheet-renamed-v3.csv by
    # the area accepted by the uncalibrated certificate, in both of its modes).
    rel = "ink-detector-0139/descriptive-row.csv"
    ink = rows(rel)
    OURS = {"FILL-SEED376-S0-pitchband": "PHerc1447-seed376-S0",
            "FILL-SEED316-S1-pitchband": "PHerc1447-seed316-S1"}
    ours = [r for r in ink if r["scroll"] == "PHerc1447" and r["sheet_or_segment"] in OURS]
    left = sorted({r["sheet_or_segment"] for r in ink
                   if r["scroll"] == "PHerc1447" and r["sheet_or_segment"] not in OURS})
    lab = [r for r in ink if r["scroll"] == "PHerc0139" and r["what"] == "labelled ink"]
    nol = [r for r in ink if r["scroll"] == "PHerc0139" and r["what"] == "labelled no ink"]
    for name, rs in (("our sheets", ours), ("labelled ink", lab), ("labelled no ink", nol)):
        if len(rs) != 4 or sorted(r["checkpoint"] for r in rs) != ["seed42", "seed42", "seed43", "seed43"]:
            sys.exit("paper_numbers.py: %s: %s is not four rows over seed42 and seed43" % (rel, name))
    if left:
        print("  %s: left out of the ink sentence by name: %s" % (rel, ", ".join(left)))

    def col(rs, c, cast=float):
        out = []
        for r in rs:
            try:
                out.append(cast(r[c]))
            except (KeyError, ValueError):
                sys.exit("paper_numbers.py: %s has no number in column %s for %s %s"
                         % (rel, c, r.get("sheet_or_segment"), r.get("checkpoint")))
        return out

    def cell_of(rs, c, v):
        return [r[c] for r in rs if float(r[c]) == v][0]

    so, sn, sl = col(ours, "c_sheet"), col(nol, "c_sheet"), col(lab, "c_sheet")
    if not (max(sn) < min(so) and max(so) < min(sl)):
        sys.exit("paper_numbers.py: %s: our coherent share is not between the no ink and the ink" % rel)
    M["InkOursShareMin"], M["InkOursShareMax"] = cell_of(ours, "c_sheet", min(so)), cell_of(ours, "c_sheet", max(so))
    M["InkNoInkShareMin"], M["InkNoInkShareMax"] = cell_of(nol, "c_sheet", min(sn)), cell_of(nol, "c_sheet", max(sn))
    M["InkLabelledShareMin"], M["InkLabelledShareMax"] = cell_of(lab, "c_sheet", min(sl)), cell_of(lab, "c_sheet", max(sl))
    co, cl = col(ours, "ext_floor_components_sheet", int), col(lab, "ext_floor_components_sheet", int)
    if not max(co) < min(cl):
        sys.exit("paper_numbers.py: %s: our component counts reach those of the labelled ink" % rel)
    small = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
    if min(co) not in small or max(co) not in small:
        sys.exit("paper_numbers.py: %s: no word for our component range %d to %d" % (rel, min(co), max(co)))
    M["InkOursComponentsMinWord"], M["InkOursComponentsMaxWord"] = small[min(co)], small[max(co)]
    M["InkLabelledComponentsMin"], M["InkLabelledComponentsMax"] = str(min(cl)), str(max(cl))
    for c, name in (("ext_threshold_u8", "InkExtThreshold"), ("ext_floor_mm", "InkExtFloorMm")):
        vals = {r[c] for r in ours + lab + nol}
        if len(vals) != 1:
            sys.exit("paper_numbers.py: %s: column %s differs between rows: %s" % (rel, c, sorted(vals)))
        M[name] = vals.pop()
    M["InkOursSheetsWord"] = small[len({r["sheet_or_segment"] for r in ours})]
    rel2 = "coverage-union-1447/union-per-sheet-renamed-v3.csv"
    ps = rows(rel2)
    for mode in ("pitchband", "asis"):
        c = "accepted_uncalibrated_cm2_" + mode
        top = sorted(ps, key=lambda r: -float(r[c]))[:2]
        if {r["label"] for r in top} != set(OURS.values()):
            sys.exit("paper_numbers.py: %s: the two largest by %s are %s, not our two sheets"
                     % (rel2, c, [r["label"] for r in top]))

    # The precedent beside it: TAUIL Abd Elilah's survey, quoted from its README through
    # tauil-quotes.csv (tool tauil_quotes.py, each quotation checked verbatim). The headline is never
    # printed without the correction, so the tool stops unless both rows are there and verbatim.
    rel = "ink-detector-0139/tauil-quotes.csv"
    tq = rows(rel)
    for r in tq:
        if r["verbatim_in_readme"] != "yes":
            sys.exit("paper_numbers.py: %s: %s is not verbatim in the README" % (rel, r["quantity"]))
    for q, name in (("headline", "TauilHeadlineQuote"), ("segments_word", "TauilSegmentsWord"),
                    ("area_cm2_approx", "TauilAreaCm"), ("best_window_score", "TauilBestWindow"),
                    ("control_median", "TauilControlMedian"), ("correction_dates", "TauilCorrectionDates"),
                    ("oblique_median", "TauilObliqueQuote"), ("half_off", "TauilHalfOffQuote"),
                    ("correction", "TauilCorrectionQuote")):
        M[name] = pick(tq, {"quantity": q}, "value", rel)

    # Section 9, added 2026-09-26: the author's remedy as this laboratory automated it, read from the
    # shipped copies of runs/rev1/stevens-remedy-half-on/evidence (tools in tools/studies/ of the same
    # name). Every state the prose asserts is checked here, so a changed CSV stops the build.
    words = {"0": "Zero", "1": "One", "2": "Two", "3": "Three", "4": "Four", "5": "Five",
             "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine"}

    def seedname(s):
        return "Seed" + "".join(words[c] for c in s.split("seed")[1])

    rel = "stevens-remedy-half-on/remedy-parts.csv"
    rp = rows(rel)
    part = {r["part"]: r for r in rp}
    want = {"M1a pairs and chains 2 to 5": "on", "M1a length 5": "on", "M1d consumption": "on",
            "M2a bridge detection": "on (detection only)", "M2b bridge output not consumed": "off (as a drop)",
            "M3 simulated annealing, several components": "off", "M3b annealing result read": "on (reads nothing)",
            "M3c annealing random stream": "property"}
    for p, state in want.items():
        if pick(rp, {"part": p}, "default_in_chain", rel) != state:
            sys.exit("paper_numbers.py: %s: part %s is no longer %r" % (rel, p, state))
        if not part[p]["house_delivered_source"].startswith("yes"):
            sys.exit("paper_numbers.py: %s: part %s is not in the house's delivered source" % (rel, p))
    for p, name in (("M1a pairs and chains 2 to 5", "RemedyChainMin"), ("M1a length 5", "RemedyChainMax")):
        m = re.search(r"patches,(\d+),badPatches", part[p]["quote"])
        if not m:
            sys.exit("paper_numbers.py: %s: no chain length in the quote of %s" % (rel, p))
        M[name] = m.group(1)
    for p, name in (("M1a pairs and chains 2 to 5", "RemedyLineChainFirst"), ("M1a length 5", "RemedyLineChainLast"),
                    ("M1d consumption", "RemedyLineConsume"), ("M2a bridge detection", "RemedyLineBridgeDetect"),
                    ("M2b bridge output not consumed", "RemedyLineBridgeNote"),
                    ("M3 simulated annealing, several components", "RemedyLineAnneal"),
                    ("M3b annealing result read", "RemedyLineManualRead"),
                    ("M3c annealing random stream", "RemedyLineRandom")):
        M[name] = pick(rp, {"part": p}, "line_62cbc21", rel)
    if "random_device" not in part["M3c annealing random stream"]["quote"] or \
            part["M3c annealing random stream"]["file"] != "pipeline9/anneal.cpp":
        sys.exit("paper_numbers.py: %s: the random stream is no longer std::random_device in anneal.cpp" % rel)

    # The ten seed arm: the recipe with the annealing changes the delivered sheets on how many seeds.
    rel = "stevens-remedy-half-on/per-seed.csv"
    ps10 = [r for r in rows(rel) if r["seed"] != "BAR"]
    measured = [r for r in ps10 if r["status"] == "measured"]
    if len(measured) != len(ps10):
        sys.exit("paper_numbers.py: %s: a seed of the arm is not measured" % rel)
    M["RemedySeedsMeasured"] = str(len(measured))
    M["RemedySeedsChanged"] = str(sum(r["delivered_sheets_changed"] == "yes" for r in measured))
    # the identity with the annealing left out, on the first seed of the ten
    rel = "stevens-remedy-half-on/identity-off-PHerc1447-seed262.csv"
    v = pick(rows(rel), {"kind": "verdict"}, "delivered", rel)
    m = re.fullmatch(r"sheets sha equal (\d+) of (\d+)", v)
    if not m or m.group(1) != m.group(2):
        sys.exit("paper_numbers.py: %s: the identity verdict is %r" % (rel, v))
    M["RemedyIdentityOffSheets"] = m.group(1)

    # Three draws more on three seeds: the best square per draw and its spread.
    rel = "stevens-remedy-half-on/draws-per-seed.csv"
    dr = rows(rel)
    DSEEDS = ["PHerc1447-seed355", "PHerc1447-seed262", "PHerc1447-seed664"]
    if sorted(r["seed"] for r in dr) != sorted(DSEEDS):
        sys.exit("paper_numbers.py: %s: the seeds are not the three of the order" % rel)
    lower = higher = 0
    for s in DSEEDS:
        n = "Remedy" + seedname(s)
        before = pick(dr, {"seed": s}, "best_square_mm_before", rel)
        M[n + "Before"] = before
        for d, dn in (("d0", "DZero"), ("d1", "DOne"), ("d2", "DTwo"), ("d3", "DThree")):
            v = pick(dr, {"seed": s}, "best_square_mm_" + d, rel)
            M[n + dn] = v
            lower += float(v) < float(before)
            higher += float(v) > float(before)
        M[n + "Spread"] = pick(dr, {"seed": s}, "best_square_mm_spread_d0_d3", rel)
    if not (lower and higher):
        sys.exit("paper_numbers.py: %s: the draws no longer fall on both sides of the delivery" % rel)
    top = max(dr, key=lambda r: float(r["best_square_mm_spread_d0_d3"]))
    if top["seed"] != "PHerc1447-seed262":
        sys.exit("paper_numbers.py: %s: the largest spread is no longer seed262's" % rel)
    jac = [float(pick(dr, {"seed": s}, "excluded_jaccard_mean_d1_d3", rel)) for s in DSEEDS]
    M["RemedyJaccardMin"] = cell_of(dr, "excluded_jaccard_mean_d1_d3", min(jac))
    M["RemedyJaccardMax"] = cell_of(dr, "excluded_jaccard_mean_d1_d3", max(jac))

    # The overlap class of each draw, the enrichment E, and the declared rule the classes follow.
    rel = "stevens-remedy-half-on/overlap-per-seed.csv"
    op = rows(rel)
    for s in DSEEDS:
        n = "Remedy" + seedname(s)
        seen = set()
        for d, dn in (("d0", "DZero"), ("d1", "DOne"), ("d2", "DTwo"), ("d3", "DThree")):
            k = pick(op, {"seed": s, "draw": d}, "klass", rel)
            if k not in ("R", "P", "I", "H"):
                sys.exit("paper_numbers.py: %s: %s %s has class %r" % (rel, s, d, k))
            seen.add(k)
            M[n + dn + "Class"] = k
            M[n + dn + "E"] = pick(op, {"seed": s, "draw": d}, "E", rel)
        if "R" in seen:
            sys.exit("paper_numbers.py: %s: %s has a draw of class R, which the caption says none has" % (rel, s))
        if len(seen) < 2 or pick(op, {"seed": s, "draw": "SEED"}, "klass", rel) != "unstable across draws":
            sys.exit("paper_numbers.py: %s: %s is no longer unstable across draws" % (rel, s))
    head = [l for l in open(os.path.join(EV, rel)) if l.startswith("#")][0]
    m = re.search(r"R E>=(\S+) and A>=(\S+), P E>=\1 and A<\2, I (\S+)<E<\1, H E<=\3", head)
    if not m:
        sys.exit("paper_numbers.py: %s: the rule is not in the header as expected" % rel)
    M["RemedyRuleE"], M["RemedyRuleA"], M["RemedyRuleEIndet"] = m.group(1), m.group(2), m.group(3)

    # One sentence on the growth: the chunk store cap, memory and identity only (the clocks are not
    # measurable under the declared rule, so none is read here).
    rel = "growth-memory-1447/summary-cap.csv"
    gc = rows(rel)
    if pick(gc, {"quantity": "cap128_bar_verdict"}, "value", rel) != "pass":
        sys.exit("paper_numbers.py: %s: the cap 128 bar is not passed" % rel)
    M["GrowthCapPeakRatio"] = pick(gc, {"quantity": "cap128_peak_ratio_over_unchanged"}, "value", rel)
    M["GrowthCapChunks"] = pick(gc, {"quantity": "unchanged-cap128_shared_chunks_cap"}, "value", rel)
    rel = "growth-memory-1447/growth-unchanged-cap128.csv"
    g1 = rows(rel)
    for q, name in (("growth_identity", "GrowthCapTreeFiles"), ("sheets_identity", "GrowthCapSheets")):
        v = pick(g1, {"quantity": q, "attempt": "PHerc1447-seed1111"}, "value", rel)
        m = re.fullmatch(r"identical (\d+) of (\d+)", v)
        if not m or m.group(1) != m.group(2):
            sys.exit("paper_numbers.py: %s: %s is %r" % (rel, q, v))
        M[name] = m.group(1)

    # The clocks of that growth work: the prose says they are not measurable under the declared rule, so
    # every rule row of the quiet window's summary must say so; nothing of it is printed.
    rel = "quiet-window-2026-09-26/summary.csv"
    qr = [r for r in rows(rel) if r["quantity"].startswith("rule_")]
    # «not applicable» is an arm against itself (U against U), which the rule does not compare
    if not any(r["value"] == "not measurable" for r in qr) or \
            any(r["value"] not in ("not measurable", "not applicable") for r in qr):
        sys.exit("paper_numbers.py: %s: a rule row of the quiet window is measurable now; the growth sentence is out of date" % rel)

    # ... + 7 + 2 from 2026-09-23T12:2xZ: the cutout result and the coverage column beside it.
    # ... + 116 from 2026-09-23T16Z: the rows of macro-aeb2e975-conversion.csv whose decision is converted.
    # ... + 5 from 2026-09-24: the coverage paragraph of section 8.
    # ... + 2 from 2026-09-24T10:16:29Z: Stevens' ten components measured by this laboratory's tool.
    # ... + 13 + 9 from 2026-09-24T18:24:03Z: the ink sentence of Limits (six shares, four component
    # bounds, threshold, floor, the count of sheets) and the nine quotations of the precedent.
    # ... + 64 from 2026-09-26: section 9, the remedy (10 from the parts, 3 from the arm and its identity,
    # 18 squares and 2 overlaps of the draws, 24 classes and enrichments, 3 of the rule) and 4 of the growth.
    # 2026-09-26 (writing agent, on the director's note of that day): PHerc1447 left the First
    # Letters list with villa pull request 1887. From the shipped copy of
    # prize-eligibility/evidence/prize-eligibility.csv, written by read_prize_eligibility.py from
    # the GitHub API. The text says 1447 is off the First Letters list and on the Grand Prize list,
    # and that the published segments measured here are of PHerc1447 and PHerc0800, both on the
    # Grand Prize list; the tool stops unless the files say so.
    rel = "prize-eligibility/prize-eligibility.csv"
    pe = rows(rel)
    k = {"pr": "1887"}
    for c, want in (("merged", "yes"), ("PHerc1447_on_first_letters_main", "no"),
                    ("PHerc1447_on_grand_prize_main", "yes"), ("PHerc0139_on_either_main", "no"),
                    ("removed_scroll", "PHerc1447"),
                    ("merged_month", "September")):
        if pick(pe, k, c, rel) != want:
            sys.exit("paper_numbers.py: %s, %s is not %s, and the text says it is" % (rel, c, want))
    gp = set(pick(pe, k, "grand_prize_scrolls_main", rel).split())
    seg = rows("published-segments-eligible/segments-eligible.csv")
    pub = {r["scroll"] for r in seg if r["source"] == "published"}
    if pub != {"PHerc1447", "PHerc0800"} or not pub <= gp:
        sys.exit("paper_numbers.py: the published segments measured are of %s, not PHerc1447 and "
                 "PHerc0800 both on the Grand Prize list, as the text says" % sorted(pub))
    M["FirstLettersRemovalPR"] = pick(pe, k, "pr", rel)
    M["FirstLettersRemovedDay"] = pick(pe, k, "merged_day", rel)
    # ... + 2 from 2026-09-26: the pull request that took PHerc1447 off the First Letters list and its day.
    # 2026-09-30 (the referee's pass on the lean S): literals the text quoted from a cell become
    # macros of that cell. The medians of the changed arm on the two tangles of the quiet bench,
    # the two quiet factors of the figure's plotted table, the smallest-run factor on seed40, the
    # two shared machine ratios, seed44's fan out and the spreads of the seed38 pair.
    rel = "seed-search-1447/cost-per-ribbon-quiet.csv"
    cq = rows(rel)
    M["BenchBothSeedFortyMedian"] = pick(cq, {"attempt": "PHerc1447-seed40"}, "c_stage_after", rel)
    M["BenchBothSeedThirtyEightMedian"] = pick(cq, {"attempt": "PHerc1447-seed38"}, "c_stage_after", rel)
    fp = os.path.join(S, "evidence", "figures", "s-f1-c-stage-before-after.csv")
    fl = [l for l in open(fp) if not l.lstrip().startswith("#") and not l.lstrip().startswith('"#')]
    fr = list(csv.DictReader(fl))
    M["QuietFactorSeedFortyMedian"] = pick(fr, {"seed_1447": "PHerc1447-seed40"}, "quiet_factor_plain_over_c2", fp)
    M["QuietFactorSeedThirtyEightMedian"] = pick(fr, {"seed_1447": "PHerc1447-seed38"}, "quiet_factor_plain_over_c2", fp)
    rel = "quiet-bench/c2-factor.csv"
    M["QuietFactorSeedFortySmallest"] = pick(rows(rel), {"attempt": "PHerc1447-seed40"}, "factor", rel)
    rel = "c-stage-cost/c-stage-times.csv"
    ct = rows(rel)
    M["SharedRatioSeedFortyEight"] = pick(ct, {"arm": "c2", "attempt": "PHerc1447-seed48"}, "speedup", rel)
    M["SharedRatioSeedThirtyEight"] = pick(ct, {"arm": "c2", "attempt": "PHerc1447-seed38"}, "speedup", rel)
    rel = "seed-search-1447/alignment-fanout.csv"
    M["FanOutSeedFortyFour"] = pick(rows(rel), {"attempt": "PHerc1447-seed44"}, "fan_out", rel)
    rel = "quiet-bench/c-stage-summary.csv"
    M["BenchBothSeedThirtyEightSpread"] = pick(rows(rel), {"arm": "c2", "attempt": "PHerc1447-seed38"}, "spread_seconds", rel)
    M["BenchBothSeedThirtyEightSpreadPct"] = pick(rows(rel), {"arm": "c2", "attempt": "PHerc1447-seed38"}, "spread_pct", rel)
    # ... + 10 from 2026-09-30: the block above.
    # ... + 2 from 2026-09-30 later: StageLoadLow and StageLoadHigh, the load during the stages l to fm of the first table.
    expected = 10 + 7 * 3 + 4 + 4 + 10 * 3 + 5 + 2 * 2 + 3 + 7 + 2 + 116 + 2 + 5 + 2 + 13 + 9 + 64 + 2 + 2
    with open(OUT, "w") as fh:
        fh.write("%% Generated by src/tools/paper_numbers.py from src/evidence. Do not edit.\n")
        for k in sorted(M):
            # a line number of source code, and a pull request number, is printed as the source
            # counts it, never grouped
            fh.write("\\newcommand{\\%s}{%s\\xspace}\n" % (k, M[k] if k.startswith("RemedyLine") or k == "FirstLettersRemovalPR" else group(M[k])))
    print("wrote %s: %d macro(s) of the %d expected" % (OUT, len(M), expected))
    if len(M) != expected:
        print("  the count and the expectation disagree, which is the thing to look at")


if __name__ == "__main__":
    main()
