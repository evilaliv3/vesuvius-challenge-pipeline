#!/usr/bin/env python3
"""Write src/paper/numbers.tex from src/evidence. No number in the article is typed by hand.

The two rules of the sister tools of results/aeb2e975 and results/f211b3cf, kept:

  1. A macro is written only if the ONE cell it comes from is there. A missing cell stops the tool
     with the file and the column named; it is never a default and never a zero. A cell that reads
     «not measurable» or «not run» travels into its macro as it stands.
  2. The tool says how many macros it expected and how many it wrote, and exits non zero when they
     differ.

And one rule of this work, which was written while its measurements ran. A macro whose file is not
there yet is PENDING: it is declared below with the file and the column that will fill it, it is
never written into numbers.tex, and the tool exits 3 and lists it. «Pending» is not a value: no
macro ever expands to it, so a pending number cannot reach a page. The build refuses the article
on exit 3; only its preview mode, which never writes article.pdf, goes on, and it removes the
paragraphs that use pending macros before it typesets.

Form only, nothing rounded: a plain number of four or more digits before the point is grouped
(1386.3267 prints as 1,386.3267). Names in NO_GROUP are identifiers and are never grouped.

Usage: paper_numbers.py [--dry-run] [--list-pending]
"""
import csv, os, re, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(S, "evidence")
OUT = os.path.join(S, "paper", "numbers.tex")
PENDING_OUT = os.path.join(S, "paper", "pending.txt")
NO_GROUP = ("Volume", "Line", "SeedId")   # a volume id, a source line and a seed number are identifiers, never grouped


class Pending(Exception):
    pass


CACHE = {}


def rows(rel):
    if rel not in CACHE:
        p = os.path.join(EV, rel)
        if not os.path.exists(p):
            raise Pending(rel)
        with open(p, newline="") as fh:
            lines = [l for l in fh if not l.lstrip().startswith(('"#', "#"))]
        CACHE[rel] = list(csv.DictReader(lines))
    return CACHE[rel]


CUT = {}


def cutoff():
    """The decisions of src/tools/cutoff.py, or {} when it has not run."""
    p = os.path.join(EV, "derived", "cutoff.csv")
    if not CUT and os.path.exists(p):
        with open(p, newline="") as fh:
            for r in csv.DictReader(l for l in fh if not l.lstrip().startswith(('"#', "#"))):
                CUT[r["item"]] = r
    return CUT


def pick(rel, where, col, accept_partial=False):
    rs = rows(rel)
    hit = [r for r in rs if all((v(r.get(k, "")) if callable(v) else r.get(k) == v) for k, v in where.items())]
    if len(hit) != 1:
        sys.exit("paper_numbers.py: %s, %s: expected 1 row, found %d" % (rel, where, len(hit)))
    v = hit[0].get(col)
    if v is None or v == "":
        sys.exit("paper_numbers.py: %s has no cell in column %s for %s" % (rel, col, where))
    # A study may write its file before its runs end. A cell that says «pending», or a row whose
    # note says some of its seeds are still pending («pending 6 of 8 seeds»), is not a value yet:
    # it is treated exactly like a missing file, so the word never reaches a page and a median
    # over the seeds done so far never passes for the arm's result.
    if v.strip().lower() == "pending":
        raise Pending(rel)
    m = re.search(r"pending (\d+) of \d+", hit[0].get("note", "") or "")
    if m and int(m.group(1)) > 0 and not accept_partial:
        raise Pending(rel)
    return v


def group(v):
    if not re.fullmatch(r"\d+(?:\.\d+)?", v):
        return v
    whole, _, frac = v.partition(".")
    if len(whole) < 4:
        return v
    return "{:,}".format(int(whole)) + ("." + frac if frac else "")


# Printed precision (director 2026-09-29T04:22:11Z: no number that reads as machine output). By rule, never
# by hand, and never changing a value the facts gate compares numerically:
#   1. a decimal whose fraction is all zeros is an integer (10.0000 sheets, 257.0000 s, 15.0000 mm, 10.0 mm);
#   2. a duration in seconds is rounded to one decimal, then rule 1 (5,187.48 s to 5,187.5; 615.70 to 615.7);
#   3. except the medians of item 91's arms (Arm*, Pair*): a median of an even count of one decimal seconds has two,
#      and ArmACpu and ArmDCpu are values of results/facts, so they keep their source precision (rule 1 only).
# Ratios, shares, areas and mm measures keep their source decimals.
SECONDS = re.compile(r"^(Clk\w+(Cpu|Wall)(Med|Min)|Fac\w+(Cpu|Wall)(Old|New)|Obj(Partial|Full)Cpu|"
                     r"Yield\w*(Time|Build|SelectSteps|LadderWall|UndeliveredWall))$")
KEEP_SECONDS = re.compile(r"^(Arm[A-D](Cpu|Wall)|Pair\w+Cpu(Old|New))$")


def precision(name, v):
    if not re.fullmatch(r"\d+\.\d+", v):
        return v
    if SECONDS.match(name) and not KEEP_SECONDS.match(name):
        v = "%.1f" % float(v)
    whole, _, frac = v.partition(".")
    if set(frac) == {"0"} and name not in KEEP_DECIMALS:
        return whole
    if KEEP_SECONDS.match(name):
        return v.rstrip("0")
    return v


# A value whose decimals say how it was measured keeps them even when they are all zeros (the referee, 2026-09-30:
# a normalised cross correlation of 1.0000 printed as 1 reads as a count).
KEEP_DECIMALS = {"RefNcc"}


def tex(v):
    return v.replace("_", "\\_").replace("%", "\\%")


CS = "derived/chain-summary.csv"
AS = "derived/area-summary.csv"
EL = "derived/eligibility.csv"
ST = "studies/"


def spec():
    """(macro, file, where, column). Everything the article uses, in the order it uses it."""
    L = []
    # Eligibility, the raw JSON.
    for lst, tag in (("grand-prize-2027", "Grand"), ("first-letters-2027", "First")):
        L += [("Elig%sListed" % tag, EL, {"list": lst}, "pherc0826_listed"),
              ("Elig%sScrolls" % tag, EL, {"list": lst}, "scrolls"),
              ("Elig%sVolume" % tag, EL, {"list": lst}, "pherc0826_volume")]
    L += [("EligCommitSha", EL, {"list": "grand-prize-2027"}, "commit"),
          ("EligCommitDate", EL, {"list": "grand-prize-2027"}, "commit_date")]
    # The chain, per wave and in all.
    names = {"wave1": "WaveOne", "wave2": "WaveTwo", "wave3": "WaveThree", "wave4": "WaveFour",
             "wave5": "WaveFive", "all": "All"}
    qs = {"draws": "Draws", "rule_passers": "Passers", "ladder_survivors": "Survivors",
          "survivors_per_rule_passer": "Yield", "delivered": "Delivered", "growth_crashed": "Crashed",
          "waiting": "Waiting", "not_delivered_other": "NotDeliveredOther",
          "best_square_median_mm": "SquareMedian", "best_square_max_mm": "SquareMax",
          "seeds_square_at_least_source_mm": "SeedsTen", "seeds_square_at_least_20mm": "SeedsTwenty",
          "cluster_rule_best_median_mm": "ClusterMedian", "cluster_rule_best_max_mm": "ClusterMax",
          "seeds_cluster_rule_at_least_source_mm": "ClusterSeedsTen", "a2_flagged_share": "AtwoShare",
          "a2_sheets": "Sheets", "sheets_delivered_at_least_20mm": "SheetsTwenty",
          "sheets_both_at_least_20mm": "SheetsBothTwenty"}
    for sc, n in names.items():
        for q, m in qs.items():
            L.append((n + m, CS, {"scope": sc, "quantity": q}, "value"))
    L += [("SquareCheckAll", CS, {"scope": "all", "quantity": "best_square_seeds"}, "check_value"),
          ("NearSources", CS, {"scope": "wave4", "quantity": "near_sources"}, "value"),
          ("NearDraws", CS, {"scope": "wave4", "quantity": "near_draws_made"}, "value"),
          ("NearPerSource", CS, {"scope": "wave4", "quantity": "near_draws_per_source_max"}, "value"),
          ("NearShellMin", CS, {"scope": "wave4", "quantity": "near_shell_min_vox"}, "value"),
          ("NearShellMax", CS, {"scope": "wave4", "quantity": "near_shell_max_vox"}, "value"),
          ("NearFiveSources", CS, {"scope": "wave5", "quantity": "near_sources"}, "value"),
          ("NearFiveDraws", CS, {"scope": "wave5", "quantity": "near_draws_made"}, "value"),
          ("NearFivePerSource", CS, {"scope": "wave5", "quantity": "near_draws_per_source_max"}, "value"),
          ("NearFiveShellMax", CS, {"scope": "wave5", "quantity": "near_shell_max_vox"}, "value"),
          ("NearFiveThreshold", CS, {"scope": "wave5", "quantity": "source_threshold_mm"}, "value"),
          ("WavesLadderFinished", CS, {"scope": "all", "quantity": "waves_with_finished_ladder"}, "value"),
          ("AtwoTstar", CS, {"scope": "rule", "quantity": "a2_T_star_deg"}, "value"),
          ("AtwoS", CS, {"scope": "rule", "quantity": "a2_S"}, "value"),
          ("SourceThreshold", CS, {"scope": "rule", "quantity": "source_threshold_mm"}, "value")]
    # Identity of the builds against unchanged, three seeds each.
    for seed, tag in (("PHerc0826-seed109", "OneOhNine"), ("PHerc0826-seed300", "ThreeHundred"),
                      ("PHerc0826-seed237", "TwoThirtySeven")):
        for col, m in (("growth_identity", "Growth"), ("sheets_identity", "Sheets"), ("stage_files_identity", "Stages"), ("holds", "Holds")):
            L.append(("IdMlp%s%s" % (tag, m), ST + "growth-lto-pgo-1447/identity-0826-mlp.csv", {"seed": seed}, col))
            L.append(("IdHv%s%s" % (tag, m), ST + "chain-0826/identity-0826-all.csv", {"seed": seed}, col))
    L += [("IdMlpHolds", ST + "growth-lto-pgo-1447/identity-0826-summary.csv", {"build": lambda b: b.endswith("(MLP)")}, "identity_holds"),
          ("IdHvHolds", ST + "chain-0826/identity-0826-summary.csv", {"build": "flathash+avx512"}, "identity_holds"),
          ("IdHvReplaced", ST + "chain-0826/identity-0826-summary.csv", {"build": "flathash+avx512"}, "seeds_replaced")]
    # Quiet clocks on PHerc0826-seed237.
    F = ST + "growth-exact-fixes-88/clock-summary-PHerc0826-seed237.csv"
    H = ST + "hot-lines-88/clock-summary.csv"
    for f, arm, tag in ((F, "HV3", "ClkHv"), (F, "STACK", "ClkMlp"), (H, "Z", "ClkZ"), (H, "L", "ClkL")):
        for q, m in (("runs_started", "Started"), ("runs_counted", "Counted"),
                     ("run_cpu_seconds_median", "CpuMed"), ("run_cpu_seconds_min", "CpuMin"),
                     ("wall_clock_seconds_median", "WallMed"), ("wall_clock_seconds_min", "WallMin"),
                     ("cores_busy_others_over_run_max", "OthersMax")):
            L.append((tag + m, f, {"arm": arm, "quantity": q}, "value"))
    L += [("ClkMlpRuleCpu", F, {"arm": "STACK", "quantity": "rule_cpu_median_below_HV3_min"}, "value"),
          ("ClkMlpRuleWall", F, {"arm": "STACK", "quantity": "rule_wall_median_below_HV3_min"}, "value"),
          ("ClkLRuleCpu", H, {"arm": "L", "quantity": "rule_cpu_median_below_Z_min"}, "value"),
          ("ClkLRuleWall", H, {"arm": "L", "quantity": "rule_wall_median_below_Z_min"}, "value")]
    I = ST + "hot-lines-88/identity-l-summary.csv"
    L += [("LzChunks", I, {"quantity": "chunks_checked"}, "value"),
          ("LzIdentical", I, {"quantity": "decoded_byte_identical"}, "value"),
          ("LzDiffering", I, {"quantity": "differing_or_error"}, "value"),
          ("LzComplib", I, {"quantity": "copy_complib"}, "value")]
    # Area.
    for q, m in (("area_seeds", "AreaSeeds"), ("union_one_step_cm2", "UnionOneStep"),
                 ("union_half_step_cm2", "UnionHalfStep"), ("union_bin_max_cm2", "UnionBinMax"),
                 ("union_sheets", "UnionSheets"), ("union_clean_summed_cm2", "UnionCleanSummed"),
                 ("union_all_cells_summed_cm2", "UnionAllSummed"), ("union_largest_piece_cm2", "UnionPiece"),
                 ("union_largest_piece_sheet", "UnionPieceSheet"), ("stevens_quoted_cm2", "StevensQuoted"),
                 ("lamina_group_cm2", "LaminaGroup"), ("lamina_group_sheets", "LaminaGroupSheets"),
                 ("lamina_group_seeds", "LaminaGroupSeeds"), ("lamina_group_square_mm", "LaminaGroupSquare"),
                 ("lamina_group_conflicts_inside", "LaminaGroupConflicts"), ("lamina_groups_listed", "LaminaGroupsListed"),
                 ("lamina_piece_cm2", "LaminaPiece"), ("lamina_piece_sheet", "LaminaPieceSheet"),
                 ("lamina_pitch_vox", "LaminaPitch"), ("lamina_refusals", "LaminaRefusals"),
                 ("lamina_wrapping_sheets", "LaminaWrapping"), ("lamina_conflict_area_sq_vox", "LaminaConflictArea"),
                 ("lamina_conflict_pitches", "LaminaConflictPitches"),
                 ("stevens_reproduced_cm2", "StevensRepro"), ("stevens_components", "StevensComponents"),
                 ("stevens_formula_best_run_cm2", "FormulaBestRun"), ("stevens_formula_best_run", "FormulaBestRunSeed"),
                 ("stevens_formula_runs", "FormulaRuns"), ("stevens_formula_sum_runs_cm2", "FormulaSumRuns"),
                 ("road1b_seeds", "RoadOneBSeeds"), ("road1b_qualified", "RoadOneBQualified"),
                 ("road1b_min_square_mm", "RoadOneBMinSquare"),
                 ("road1b_seeds_used", "RoadOneBSeedsUsed"), ("road1b_patches_used", "RoadOneBPatches"),
                 ("road1b_used_min_square_mm", "RoadOneBUsedMinSquare"),
                 ("road1b_used_max_distance_vox", "RoadOneBUsedMaxDistance")):
        L.append((m, AS, {"quantity": q}, "value"))
    # Fibre (director 2026-09-29T02:21:36Z): the fibre score of the certified pieces, certified-piece-0826.
    FS = "derived/fibre-summary.csv"
    for q, m in (("fibre_bar", "FibreBar"), ("fibre_bar_factor", "FibreBarFactor"),
                 ("fibre_reference_score", "FibreReference"), ("fibre_reference_sheet", "FibreReferenceSheet"),
                 ("fibre_white_noise", "FibreWhiteNoise"), ("fibre_window_cells", "FibreWindowCells"),
                 ("fibre_period_min_mm", "FibrePeriodMin"), ("fibre_period_max_mm", "FibrePeriodMax"),
                 ("fibre_windows", "FibreWindows"), ("fibre_pieces_fewer_windows", "FibrePiecesFewerWindows"),
                 ("fibre_pieces_not_measurable", "FibrePiecesNotMeasurable"), ("fibre_pieces_ranked", "FibrePiecesRanked"),
                 ("fibre_pieces_passing", "FibrePiecesPassing"), ("fibre_population_min_cm2", "FibrePopulationMin"),
                 ("fibre_best_piece_cm2", "FibreBestPiece"), ("fibre_best_piece_sheet", "FibreBestPieceSheet"),
                 ("fibre_best_piece_source", "FibreBestPieceSource"), ("fibre_best_piece_score", "FibreBestPieceScore"),
                 ("fibre_best_other_piece_cm2", "FibreBestOtherPiece"), ("fibre_best_other_piece_sheet", "FibreBestOtherPieceSheet"),
                 ("fibre_best_other_piece_source", "FibreBestOtherPieceSource"), ("fibre_best_other_piece_score", "FibreBestOtherPieceScore"),
                 ("fibre_best_square_mm", "FibreBestSquare"), ("fibre_best_square_sheet", "FibreBestSquareSheet"),
                 ("fibre_best_square_score", "FibreBestSquareScore"),
                 ("fibre_union_piece_score", "FibreUnionPiece"), ("fibre_union_piece_certified_cm2", "FibreUnionPieceCertified"),
                 ("fibre_lamina_piece_score", "FibreLaminaPiece"), ("fibre_lamina_piece_certified_cm2", "FibreLaminaPieceCertified"),
                 ("fibre_group_members_scored", "FibreGroupScored"), ("fibre_group_member_sheet", "FibreGroupMemberSheet"),
                 ("fibre_group_member_score", "FibreGroupMember"),
                 ("fibre_coll_four_seeds", "FibreCollFourSeeds"), ("fibre_coll_four_seeds_ranked", "FibreCollFourSeedsRanked"),
                 ("fibre_coll_four_pieces_ranked", "FibreCollFourPiecesRanked"),
                 # the reframe around the checks (director 2026-09-29T06:54:31Z): the largest pieces that fail the fibre test
                 ("fibre_top_failing_count", "FibreTopFailCount"), ("fibre_top_failing_score_min", "FibreTopFailScoreMin"),
                 ("fibre_top_failing_score_max", "FibreTopFailScoreMax"), ("fibre_top_failing_piece_min_cm2", "FibreTopFailPieceMin"),
                 ("fibre_top_failing_piece_max_cm2", "FibreTopFailPieceMax"), ("fibre_top_failing_sheets", "FibreTopFailSeeds"),
                 ("fibre_top_failing_square_max_mm", "FibreTopFailSquareMax")):
        L.append((m, FS, {"quantity": q}, "value"))
    # The checks as a tool (director 2026-09-29T06:54:31Z): best-windows-0826, through src/tools/checks_summary.py.
    CH = "derived/checks-summary.csv"
    for q, m in (("windows_side_mm", "WinSide"), ("windows_area_cm2", "WinArea"), ("windows_covered_bar", "WinCoveredBar"),
                 ("windows_flagged_bar", "WinFlaggedBar"), ("windows_fibre_bar", "WinFibreBar"),
                 ("windows_tile_cells", "WinTileCells"), ("windows_sheets_searched", "WinSheets"),
                 ("windows_seeds_searched", "WinSeedsSearched"), ("windows_with_candidate", "WinCandidates"),
                 ("windows_no_candidate", "WinNoCandidate"), ("windows_clean", "WinClean"),
                 ("windows_clean_seeds", "WinCleanSeeds"), ("windows_clean_sheets", "WinCleanSheets"),
                 ("windows_sheets_distinct", "WinSheetsDistinct"), ("windows_candidate_sheets", "WinCandidateSheets"),
                 ("windows_candidate_sheets_not_clean", "WinCandidateNotClean"), ("windows_no_clean", "WinNoClean"),
                 ("windows_best_covered", "WinBestCovered"), ("windows_best_hole", "WinBestHole"),
                 ("windows_best_flagged", "WinBestFlagged"), ("windows_best_fibre", "WinBestFibre"),
                 ("windows_best_tiles", "WinBestTiles"), ("windows_best_sheet", "WinBestSheet"),
                 ("windows_best_seed", "WinBestSeedId"), ("windows_best_source", "WinBestSource"),
                 ("windows_best3_seeds", "WinBestThreeSeeds"), ("windows_best3_flagged_max", "WinBestThreeFlaggedMax"),
                 ("windows_best3_covered_min", "WinBestThreeCoveredMin"), ("windows_clean_tiles_min", "WinTilesMin"),
                 ("windows_clean_tiles_max", "WinTilesMax"), ("windows_tiles_per_window", "WinTilesPer"),
                 ("windows_selftests_passing", "WinSelfTests"), ("windows_best3_angle_min_deg", "WinAngleMin"),
                 ("windows_best3_angle_max_deg", "WinAngleMax"),
                 ("straight_peak_window_vox", "StraightWindow"), ("straight_random_median_vox", "StraightRandomMedian"),
                 ("straight_random_share", "StraightRandomShare"), ("straight_near_vox", "StraightNear"),
                 ("straight_bw1_i_median_vox", "StraightOneIMedian"), ("straight_bw1_j_median_vox", "StraightOneJMedian"),
                 ("straight_bw1_i_share", "StraightOneIShare"), ("straight_bw1_j_share", "StraightOneJShare"),
                 ("straight_best3_separating", "StraightSeparating"), ("straight_separating_seed", "StraightSepSeedId"),
                 ("straight_separating_median_min_vox", "StraightSepMedMin"),
                 ("straight_separating_median_max_vox", "StraightSepMedMax"),
                 ("straight_other_median_min_vox", "StraightOtherMedMin"),
                 ("straight_other_median_max_vox", "StraightOtherMedMax")):
        L.append((m, CH, {"quantity": q}, "value"))
    # The positive control of positive-control-0139 (w016 of PHerc. 0139, labelled): PENDING until its verdict is written
    # and copied; the text that carries it waits in two PENDING blocks of body.tex.
    for q, m in (("pc_a_ours_ba", "PcOursABa"), ("pc_a_theirs_ba", "PcTheirsABa"), ("pc_a_null_best", "PcNullA"),
                 ("pc_a_null_reads", "PcNullReadsA"), ("pc_a_ours_reads", "PcReadsA"), ("pc_a_common", "PcCommonA"),
                 ("pc_b_ours_ba", "PcOursBBa"), ("pc_b_theirs_ba", "PcTheirsBBa"), ("pc_b_null_best", "PcNullB"),
                 ("pc_b_null_reads", "PcNullReadsB"), ("pc_b_ours_reads", "PcReadsB"), ("pc_b_common", "PcCommonB"),
                 ("pc_labelfree_rows", "PcLabelFreeRows"), ("pc_labelfree_yes", "PcLabelFreeYes"),
                 ("pc_labelfree_square_mm", "PcLabelFreeSquare"), ("pc_ink_0826_reading", "PcInkReading"),
                 ("pc_region_cm2", "PcRegion"), ("pc_match_vox", "PcMatch")):
        L.append((m, CH, {"quantity": q}, "value"))
    # The headline (render-routes-0826 route R2c, director 12:52:52Z and 15:38:23Z) and the renderer check (ink-finetune-k2).
    names = {"seed": "SeedId", "square_mm": "Square", "strict_mm": "Strict", "pairwise_mm": "Pairwise",
             "sec_i_share": "SecIShare", "sec_j_share": "SecJShare", "on_ours_share": "OnOurs", "sec_i_median": "SecIMedian",
             "sec_j_median": "SecJMedian", "our_sheet": "OurSheet", "flags": "Flags", "fibre": "Fibre",
             "fibre_tiles": "FibreTiles", "window": "Window", "rotation_deg": "Rotation", "generations": "Generations"}
    for k, K in (("one", "One"), ("two", "Two")):
        for q, n in names.items():
            if q == "square_mm":
                continue                   # the headline square: definition c below, never square-checks' column
            L.append(("Rc%s%s" % (K, n), CH, {"quantity": "r2c_%s_%s" % (k, q)}, "value"))
    # The headline square under the certificate with adjudicated crossings (director rule 2026-09-29T23:59:34Z,
    # decision of 2026-09-30): column c of render-routes-0826's square-three-definitions.csv, copied to
    # src/inputs/render-routes-0826/ with its sha256 in SHA256SUMS there. RcOneSquareBefore is column a of the same row,
    # the square before the adjudication, which Figure C21 draws.
    TD = "../inputs/render-routes-0826/square-three-definitions.csv"
    for sf, K in (("PHerc0826-seed6273-squarecentre", "One"), ("PHerc0826-seed5364-squarecentre", "Two")):
        L.append(("Rc%sSquare" % K, TD, {"route": "R2cnative", "surface": sf}, "c_certified_adjudicated_mm"))
    L.append(("RcOneSquareBefore", TD, {"route": "R2cnative", "surface": "PHerc0826-seed6273-squarecentre"},
              "a_certified_this_study_mm"))
    for q, m in (("r2c_crop_mm", "RcCrop"), ("r2c_old_square_mm", "RcOldSquare"), ("r2c_old_other_flags", "RcOldOtherFlags"),
                 ("regrid_first_fail_value", "RegridFailValue"), ("regrid_first_fail_bar", "RegridFailBar"),
                 ("refcheck_ncc_min", "RefNcc"), ("refcheck_segments", "RefSegments")):
        L.append((m, CH, {"quantity": q}, "value"))
    # Youssef Nader's v8-in (owner's order of 2026-09-30): derived/v8in-summary.csv, written by src/tools/v8in_summary.py.
    VS = "derived/v8in-summary.csv"
    for q, m in (("order_w016_ba_chosen", "VeinOrderBa"), ("order_w016_ba_other", "VeinOrderBaOther"),
                 ("order_w016_pixels", "VeinOrderPixels"), ("threshold", "VeinThreshold"),
                 ("s6273_w016order_sheet_share", "VeinSixSheet"), ("s6273_w016order_plus_share", "VeinSixPlus"),
                 ("s6273_w016order_minus_share", "VeinSixMinus"), ("s6273_otherorder_sheet_share", "VeinSixSheetOther"),
                 ("s6273_otherorder_plus_share", "VeinSixPlusOther"), ("s6273_otherorder_minus_share", "VeinSixMinusOther"),
                 ("s5364_w016order_sheet_share", "VeinFiveSheet"), ("s5364_w016order_plus_share", "VeinFivePlus"),
                 ("s5364_w016order_minus_share", "VeinFiveMinus"), ("s5364_otherorder_sheet_share", "VeinFiveSheetOther"),
                 ("s5364_otherorder_plus_share", "VeinFivePlusOther"), ("s5364_otherorder_minus_share", "VeinFiveMinusOther"),
                 ("face_offset_vox", "VeinFaceOffset"), ("s6273_faceplus_w016order_share", "VeinFacePlus"),
                 ("s6273_faceminus_w016order_share", "VeinFaceMinus"), ("ratio_known_min", "VeinRatioMin"),
                 ("ratio_known_max", "VeinRatioMax"), ("ratio_s6273", "VeinRatioSix"), ("ratio_s5364", "VeinRatioFive"),
                 ("null_layers_shared_min", "VeinNullSharedMin"), ("null_layers_shared_max", "VeinNullSharedMax"),
                 ("null_layers_total", "VeinNullLayers")):
        L.append((m, VS, {"quantity": q}, "value"))
    # The factor of item 91's arms A to C as Figure 1 and the arms figure print it (c-f18-arms-steps.py's table).
    # The whole R2d surface of seed 2715 read by v8-in (derived/v8in-reads.csv, src/tools/v8in_reads.py).
    VR = "derived/v8in-reads.csv"
    L.append(("VeinRdPixels", VR, {"read": "R2d-seed2715-S0-whole-surface-w016"}, "pixels"))
    L.append(("VeinRdShare", VR, {"read": "R2d-seed2715-S0-whole-surface-w016"}, "sheet_share"))
    L.append(("VeinRdShareOther", VR, {"read": "R2d-seed2715-S0-whole-surface-other"}, "sheet_share"))
    # Figure C25, the headline square at full resolution (owner's word of 2026-09-30): its plotted table, written by
    # src/tools/c-f25-square-full.py plot and pinned in src/tools/c-f25-square-full-pins.csv.
    FS = "figures/c-f25-square-full.csv"
    for k, m in (("grid", "FullSquareGrid"), ("voxel_um", "FullSquareVoxel"), ("missing", "FullSquareMissing"),
                 ("stretch_lo_pct", "FullSquareLo"), ("stretch_hi_pct", "FullSquareHi"), ("bar_mm", "FullSquareBar")):
        L.append((m, FS, {"key": k}, "value"))
    L.append(("ArmFactorAC", "figures/c-f18-arms-steps.csv", {"key": "factor_ac"}, "value"))
    L.append(("ArmFactorBC", "figures/c-f18-arms-steps.csv", {"key": "factor_bc"}, "value"))
    # What the chain as delivered ran beyond arm C (the referee, 2026-09-30): derived/corrections.csv, written by
    # src/tools/corrections_list.py from the patches shipped under src/inputs/chain-0826-corrections.
    CO = "derived/corrections.csv"
    for k, m in (("count_changes_output", "CorrOutput"), ("count_inert", "CorrInert"), ("x_c_seeds", "CorrSeeds"),
                 ("x_c_seeds_growth_differs", "CorrSeedsDiffer"), ("median_growth_patches_x", "CorrPatchesX"),
                 ("median_growth_patches_c", "CorrPatchesC"), ("median_formula_cm2_x", "CorrFormulaX"),
                 ("median_formula_cm2_c", "CorrFormulaC"), ("median_square_mm_x", "CorrSquareX"),
                 ("median_square_mm_c", "CorrSquareC")):
        L.append((m, CO, {"key": k}, "value"))
    # Route R2d's larger square on seed 2715 (the referee, 2026-09-30): column c of the same shipped file, and its dark
    # share from candidate-2715.csv (render-routes-0826/tools/cand2715.py), shipped beside it.
    L.append(("RdSquare", TD, {"route": "R2dnative", "surface": "PHerc0826-seed2715-S0-sq"}, "c_certified_adjudicated_mm"))
    L.append(("RdDark", "../inputs/render-routes-0826/candidate-2715.csv", {"route": "R2dnative"}, "dark_share_in_square"))
    # The axial cuts of study cuts-2715 (director 2026-09-30): derived/cuts-summary.csv, written by src/tools/cuts_summary.py.
    CU = "derived/cuts-summary.csv"
    for q, m in (("rd_cuts", "CutsRd"), ("rd_crack_cuts", "CutsRdCrack"), ("rd_air_cuts", "CutsRdAir"),
                 ("rd_air_cuts_not_crack", "CutsRdAirOther"), ("rd_controls", "CutsRdControls"), ("rd_streaks", "CutsRdStreaks"),
                 ("void_run_nodes", "CutsVoidRun"), ("dark_threshold", "CutsDarkT"), ("head_cuts", "CutsHead"),
                 ("head_void_runs_bar", "CutsHeadRuns"), ("head_longest_nodes", "CutsHeadLongest"),
                 ("head_longest_mm", "CutsHeadLongestMm"), ("air_bar", "CutsAirBar"), ("air_head", "CutsAirHead"),
                 ("air_rd", "CutsAirRd"), ("air_rd_corner", "CutsAirCorner")):
        L.append((m, CU, {"quantity": q}, "value"))
    for tag, m in (("four", "CollFour"), ("control", "CollControl"), ("setseed6365", "SetSeedA"),
                   ("setseed2019", "SetSeedB"), ("setseed5630", "SetSeedC")):
        for q, n in (("formula_cm2", "Formula"), ("a2_share", "Atwo"), ("v2_cells", "Vtwo"),
                     ("clean_cm2", "Clean"), ("square_mm", "Square"), ("union_cm2", "Union"), ("sheets", "Sheets")):
            L.append((m + n, AS, {"quantity": "coll_%s_%s" % (tag, q)}, "value"))
    SM = ST + "area-0826-90/stevens-method-0826.csv"
    L += [("DeliveredSixThreeSixFive", SM, {"run": "PHerc0826-seed6365"}, "sum_components_cm2"),
          ("DeliveredTwoOhOneNine", SM, {"run": "PHerc0826-seed2019"}, "sum_components_cm2"),
          ("DeliveredFiveSixThreeOh", SM, {"run": "PHerc0826-seed5630"}, "sum_components_cm2")]
    # The module sections (director 2026-09-28T06:40:45Z, PLAN 93 spine 07:53:42Z).
    SF = "derived/speed-factors.csv"
    for step, tag in (("hash and AVX-512 to MLP", "Mlp"), ("zstd copy to LZ4HC copy, MLP", "Lz")):
        for clock, c in (("cpu", "Cpu"), ("wall", "Wall")):
            w = {"step": step, "seed": "PHerc0826-seed237", "clock": clock}
            L += [("Fac%s%s" % (tag, c), SF, w, "factor"), ("Fac%s%sOld" % (tag, c), SF, w, "old_median_s"),
                  ("Fac%s%sNew" % (tag, c), SF, w, "new_median_s")]
    ML = "derived/simpaper10-lines.csv"
    for key, m in (("usage_g", "LineUsageG"), ("mode_g", "LineG"), ("g_generate", "LineGGenerate"),
                   ("mode_l", "LineL"), ("l_centre", "LineLCentre"), ("mode_c", "LineC"),
                   ("c_round_2", "LineCRoundTwo"), ("c_round_5", "LineCRoundFive"), ("mode_vm", "LineVm"),
                   ("vm_orders", "LineVmOrders"), ("vm_bridges", "LineVmBridges"), ("mode_hm", "LineHm"),
                   ("hm_springs", "LineHmSprings"), ("hm_run", "LineHmRun"), ("mode_fm", "LineFm"),
                   ("fm_score", "LineFmScore")):
        L.append((m, ML, {"key": key}, "line"))
    L.append(("SrCommit", ML, {"key": "mode_g"}, "commit"))
    UP = "derived/upstream.csv"
    for repo, num, m in (("WillStevens/scrollreading", "2", "UpSrTwo"), ("WillStevens/scrollreading", "3", "UpSrThree"),
                         ("WillStevens/scrollreading", "4", "UpSrFour"), ("ScrollPrize/villa", "1875", "UpVillaBlocks"),
                         ("ScrollPrize/villa", "1877", "UpVillaSeedCheck"), ("ScrollPrize/villa", "1885", "UpVillaTracer"),
                         ("Hob3rMallow/scrollfiesta_public", "17", "UpSfSeventeen"), ("Hob3rMallow/scrollfiesta_public", "18", "UpSfEighteen"),
                         ("Hob3rMallow/scrollfiesta_public", "19", "UpSfNineteen"), ("Hob3rMallow/scrollfiesta_public", "20", "UpSfTwenty"),
                         ("Hob3rMallow/scrollfiesta_public", "21", "UpSfTwentyOne")):
        L.append((m + "State", UP, {"repo": repo, "number": num}, "state"))
    # 2026-09-28 (director 12:12:31Z): villa 1885 is closed, not merged; its seed correction is now
    # pull request 1915 and the cost its other commit changed is described in issue 1914, as the
    # owner's closing comment on 1885 says. The sentence prints the merge cell of 1885 too.
    L += [("UpVillaTracerMerged", UP, {"repo": "ScrollPrize/villa", "number": "1885"}, "merged_at"),
          ("UpVillaSeedZeroState", UP, {"repo": "ScrollPrize/villa", "number": "1915"}, "state"),
          ("UpVillaRayIssueState", UP, {"repo": "ScrollPrize/villa", "number": "1914"}, "state")]
    L += [("UpReadAt", UP, {"repo": "ScrollPrize/villa", "number": "1875"}, "read_at")]
    I5 = ST + "chain-0826/inputs/i5-coverage.csv"
    L += [("PredInMask", I5, {"scroll": "PHerc0826"}, "predicted_in_mask_share"),
          ("PredInMaskRef", I5, {"scroll": "PHerc1447"}, "predicted_in_mask_share")]
    for key, m in (("param_surface_zarr", "LineSurfaceZarr"), ("surface_zarr_open", "LineSurfaceOpen"), ("param_seed_x", "LineSeedX"),
                   ("param_seed_y", "LineSeedY"), ("param_seed_z", "LineSeedZ")):
        L.append((m, ML, {"key": key}, "line"))
    BO = ST + "nongrowth-profile-1447/build-objects-only.csv"
    L += [("ObjPartialCpu", BO, {"series": "corrected"}, "partial_build_cpu_s"),
          ("ObjFullCpu", BO, {"series": "corrected"}, "full_rebuild_cpu_s"),
          ("ObjIdentical", BO, {"series": "corrected"}, "binary_identical"),
          ("ObjObjects", BO, {"series": "corrected"}, "objects"),
          ("ObjEqualAcross", BO, {"series": "corrected"}, "objects_equal_across_seeds"),
          ("ObjCheckBuilds", CS, {"scope": "build", "quantity": "objects_only_builds"}, "value"),
          ("ObjCheckEqual", CS, {"scope": "build", "quantity": "objects_only_builds"}, "check_value"),
          ("ObjCheckVariants", CS, {"scope": "build", "quantity": "objects_check_variants"}, "value")]
    # Item 96: NOT pending. The text switches on \ifRuntimeParamsDone, true only when the summary is in
    # the snapshot and its identity_holds reads yes; its macros are written only then.
    RP = ST + "runtime-params-96/identity-summary.csv"
    for col, m in (("seeds_holding", "RuntimeSeeds"), ("identity_holds", "RuntimeHolds"), ("build", "RuntimeBuild")):
        L.append((m, RP, {"against": lambda v: True}, col))
    SQ = "derived/square95.csv"
    for scope, q, m in (("all", "seeds", "RegrowSeeds"), ("all", "seeds_at_cap", "RegrowAtCap"),
                        ("all", "seeds_ended_by_itself", "RegrowEnded"), ("all", "g72000_best_mm", "RegrowBest"),
                        ("all", "g72000_best_seed", "RegrowBestSeed"), ("all", "seeds_20mm", "RegrowSeedsTwenty"),
                        ("all", "others_min_mm", "RegrowOthersMin"), ("all", "others_max_mm", "RegrowOthersMax"),
                        ("PHerc0826-seed2604", "g36000_best_mm", "RegrowBestBefore"),
                        ("PHerc0826-seed2604", "g72000_best_sheet", "RegrowBestSheet"),
                        ("PHerc0826-seed2604", "g72000_best_cells", "RegrowBestCells"),
                        ("PHerc0826-seed2604", "g72000_cluster_rule_mm", "RegrowBestCluster"),
                        ("PHerc0826-seed2604", "g72000_best_sheet_a2_share", "RegrowBestAtwo"),
                        ("PHerc0826-seed2604", "g72000_highest_generation", "RegrowBestGeneration"),
                        ("PHerc0826-seed2604", "identity_to_36000_as_sets", "RegrowIdentity"),
                        # item 95 (f), director 2026-09-28T21:22:13Z: the ten next capped seeds, and the
                        # largest change among the four other seeds of the five
                        ("next10", "seeds", "RegrowNextSeeds"),
                        ("next10", "largest_abs_change_mm", "RegrowNextChange"),
                        ("next10", "largest_abs_change_seed", "RegrowNextChangeSeed"),
                        ("next10", "largest_abs_change_before_mm", "RegrowNextChangeBefore"),
                        ("next10", "largest_abs_change_after_mm", "RegrowNextChangeAfter"),
                        ("next10", "seeds_20mm", "RegrowNextSeedsTwenty"),
                        ("all", "others_largest_abs_change_mm", "RegrowOthersChange"),
                        ("all", "others_largest_abs_change_seed", "RegrowOthersChangeSeed")):
        L.append((m, SQ, {"scope": scope, "quantity": q}, "value"))
    # The two caps, never pooled (director 2026-09-28T16:50:23Z): each parsed from the shipped tool that
    # ran it, and the freeze of the chain at its relaunch (tools/caps.py).
    CP = "derived/caps.csv"
    for scope, q, m in (("chain_as_run", "generation_cap", "ChainGenCap"), ("chain_as_run", "patch_limit", "ChainPatchLimit"),
                        ("g72000_regrowth", "generation_cap", "RegrowGenCap"),
                        ("g72000_regrowth", "patch_limit", "RegrowPatchLimit"),
                        ("freeze", "freeze_utc", "ChainFreezeTime"), ("freeze", "seeds_out_at_g72000", "ChainSeedsAfterFreeze")):
        L.append((m, CP, {"scope": scope, "quantity": q}, "value"))
    CK = ST + "square20-0826-95/checks-PHerc0826-seed2604.csv"
    L += [("CheckLaminaAvoid", CK, {"check": "one_lamina"}, "largest_square_avoiding_flagged_mm"),

          ("CheckVtwoAvoid", CK, {"check": "v2_crossing"}, "largest_square_avoiding_flagged_mm"),

]
    L.append(("RuntimeAgainst", ST + "runtime-params-96/identity-summary.csv", {"against": lambda v: True}, "against"))
    # PENDING, road 1b: the eight nearest seeds of road1b-seeds.csv pooled as one run, same tool
    # (collection-eight-6365.csv, the columns of collection-four-6365.csv).
    R = ST + "area-0826-90/collection-eight-6365.csv"
    allrow = {"sheet": lambda s: s.startswith("all ")}
    L += [("RoadOneBFormula", R, allrow, "stevens_formula_cm2"),
          ("RoadOneBAtwo", R, allrow, "a2_share"),
          ("RoadOneBVtwo", R, allrow, "v2_cells"),
          ("RoadOneBSquare", R, allrow, "square_mm_delivered")]
    # Road 1b closed by the director 2026-09-28T15:50:25Z, not rerun: its two stage c runs, stopped by
    # their RSS bounds in pass 3 (area-0826-90/tools/road1b_memory.py).
    RM = ST + "area-0826-90/road1b-memory.csv"
    second = {"run": "second"}
    L += [("RoadOneBBound", RM, second, "rss_bound_gb"),
          ("RoadOneBStopPatches", RM, second, "patches"),
          ("RoadOneBPassThreeGB", RM, second, "pass3_first_rss_gb"),
          ("RoadOneBStopGB", RM, second, "stop_rss_gb"),
          ("RoadOneBStopMinutes", RM, second, "pass3_first_to_stop_min"),
          ("RoadOneBFirstBound", RM, {"run": "first"}, "rss_bound_gb")]
    # PENDING, item 91: one row per arm, «not run» written by the study where an arm did not finish
    # by 2026-09-30T12:00Z.
    A = ST + "stevens-changes-0826-91/arms.csv"
    for arm in "ABCD":
        for col, n in (("cpu_seconds", "Cpu"), ("wall_seconds", "Wall"), ("sheets", "Sheets"),
                       ("stevens_formula_cm2", "Formula"), ("largest_square_mm", "Square"),
                       ("a2_share", "Atwo"), ("v2_cells", "Vtwo"), ("deaths", "Deaths")):
            L.append(("Arm%s%s" % (arm, n), A, {"arm": arm}, col))
    L += [("ArmESeedsPerDraw", A, {"arm": "E"}, "seeds_per_draw")]
    # Search yield (director 2026-09-28T18:20:15Z): finds per machine hour, whole search cost, one row
    # per arm, quantity and scope of search-yield-0826/yield.csv; the parts beside the result.
    Y = ST + "search-yield-0826/yield.csv"
    O = "original (item 91 arm A)"
    C = ("ours (item 91 arm C)", "waves 1 to 5, cumulative")
    for q, t in (("hole free", "Hf"), ("certified", "Cert")):
        o = {"arm": O, "quantity": q}
        c = {"arm": C[0], "quantity": q, "scope": C[1]}
        L += [("YieldOrigFinds" + t, Y, o, "finds_per_seed"), ("YieldOrigYield" + t, Y, o, "yield_per_seed_grown"),
              ("YieldOrigRate" + t, Y, o, "finds_per_machine_hour"),
              ("YieldOursFinds" + t, Y, c, "finds_per_seed"), ("YieldOursRate" + t, Y, c, "finds_per_machine_hour"),
              ("YieldOursRandomRate" + t, Y, {"arm": C[0], "quantity": q, "scope": "waves 1 to 3, cumulative"},
               "finds_per_machine_hour"),
              ("YieldDeliveredRate" + t, Y, {"arm": "ours as delivered (information)", "quantity": q, "scope": C[1]},
               "finds_per_machine_hour"),
              ("YieldRatio" + t, Y, {"arm": "ratio ours / original", "quantity": q}, "finds_per_machine_hour")]
    o = {"arm": O, "quantity": "hole free"}
    c = {"arm": C[0], "quantity": "hole free", "scope": C[1]}
    L += [("YieldOrigSeeds", Y, o, "seeds_grown_to_end"), ("YieldOrigTime", Y, o, "t_delivered_wall_s"),
          ("YieldOrigBuild", Y, o, "build_s"), ("YieldOrigK", Y, o, "k"), ("YieldOrigHours", Y, o, "machine_hours"),
          ("YieldOursK", Y, c, "k"), ("YieldOursSelectSteps", Y, c, "seed_rule_s"), ("YieldOursLadderRows", Y, c, "ladder_rows"),
          ("YieldOursLadderWall", Y, c, "ladder_wall_s"), ("YieldOursLadderBuild", Y, c, "ladder_build_s"),
          ("YieldOursDelivered", Y, c, "delivered_seeds"), ("YieldOursTime", Y, c, "t_delivered_wall_s"),
          ("YieldOursUndelivered", Y, c, "undelivered_grown_seeds"),
          ("YieldOursUndeliveredWall", Y, c, "undelivered_grown_s"), ("YieldOursHours", Y, c, "machine_hours")]
    CO = "derived/cutoff.csv"
    for arm in "ABCD":
        L.append(("Arm%sDone" % arm, CO, {"item": "arm" + arm}, "completed"))
    L.append(("ArmSeeds", CO, {"item": "armC"}, "of"))
    L.append(("CutoffTime", CO, {"item": "road1b"}, "cutoff"))
    AP = "derived/arms-paired.csv"
    for pair, pn in (("AB", "AB"), ("BC", "BC"), ("CD", "CD")):
        L.append(("Pair%sShared" % pn, AP, {"pair": pair, "measure": "cpu_seconds"}, "shared_seeds"))
        for meas, mn in (("cpu_seconds", "Cpu"), ("stevens_formula_cm2", "Formula"), ("best_square_mm", "Square")):
            L += [("Pair%s%sOld" % (pn, mn), AP, {"pair": pair, "measure": meas}, "old_median"),
                  ("Pair%s%sNew" % (pn, mn), AP, {"pair": pair, "measure": meas}, "new_median")]
    return L


def reads_rows():
    """The body of the table «v8-in reads on PHerc. 0826», from derived/v8in-reads.csv, each cell as the macros print it."""
    out = []
    for r in rows("derived/v8in-reads.csv"):
        cell = lambda k: tex(group(precision("VeinReads", r[k]))) if re.fullmatch(r"\d+(\.\d+)?", r[k]) else tex(r[k])
        order = "measured on w016" if r["order"] == "w016" else "the other"
        out.append("%s & %s & %s & %s & %s & %s & %s & %s \\\\\n" % (
            tex(r["surface"]), tex(r["extent"]), order, cell("pixels"), cell("sheet_share"), cell("plus_share"),
            cell("minus_share"), cell("sheet_over_larger_copy")))
    return "".join(out)


def main():
    L = spec()
    names = [m for m, *_ in L]
    dup = sorted({n for n in names if names.count(n) > 1})
    if dup:
        sys.exit("paper_numbers.py: macro names repeated: %s" % dup)
    bad = [n for n in names if not re.fullmatch(r"[A-Za-z]+", n)]
    if bad:
        sys.exit("paper_numbers.py: macro names with a character TeX will not take: %s" % bad)
    M, pending, skipped = {}, [], []
    for name, rel, where, col in L:
        cut = cutoff()
        arm = re.match(r"Arm([ABCD])", name)
        dec = cut.get("arm" + arm.group(1), {}).get("decision", "open") if arm and rel.endswith("arms.csv") else None
        if name.startswith("RoadOneB") and "collection-eight" in rel and \
                cut.get("road1b", {}).get("decision", "open").startswith("four seed"):
            skipped.append(name)          # the declared fallback: the text does not use these
            continue
        if name.startswith("Check") and not os.path.exists(os.path.join(EV, rel)):
            skipped.append(name)          # the checks file is not in: the text prints «not complete»
            continue
        if name.startswith("Runtime") and not os.path.exists(os.path.join(EV, rel)):
            skipped.append(name)          # item 96 not in: the text prints the proposed next step
            continue
        try:
            if dec == "not run in time":
                v = "no run"          # the table's caption says: no seed of the arm completed by the cut off
            else:
                decided = rel.endswith("cutoff.csv") and cut.get(where.get("item"), {}).get("decision", "open") != "open"
                v = pick(rel, where, col, accept_partial=(dec == "row as written, completed seeds beside it") or decided)
        except Pending:
            pending.append((name, rel, col))
            continue
        if "Rule" in name:
            # A verdict cell reads «pass (median X, Z min Y)»: its numbers are macros of their own,
            # so only the verdict word is kept, and it must be one of the two a rule can give.
            v = v.split()[0]
            if v not in ("pass", "fail"):
                sys.exit("paper_numbers.py: %s reads %r, not a verdict" % (name, v))
        v = precision(name, v)
        if not any(name.startswith(p) or p in name for p in NO_GROUP):
            v = group(v)
        M[name] = tex(v)
    expected = len(L) - len(pending) - len(skipped)
    road = cutoff().get("road1b", {}).get("decision", "open")
    print("paper_numbers.py: %d macros declared, %d written, %d pending, %d not used by the declared fallback"
          % (len(L), len(M), len(pending), len(skipped)))
    if len(M) != expected:
        sys.exit("paper_numbers.py: wrote %d of %d" % (len(M), expected))
    if "--dry-run" not in sys.argv:
        with open(OUT, "w") as fh:
            fh.write("%% Written by src/tools/paper_numbers.py from src/evidence. Do not edit.\n")
            fh.write("%% %d macros; %d pending macros are declared in the tool and NOT defined here.\n"
                     % (len(M), len(pending)))
            for k in names:
                if k in M:
                    fh.write("\\newcommand{\\%s}{%s\\xspace}\n" % (k, M[k]))
            # Which road 1b paragraph the text prints: decided by cutoff.py, never here. Undecided and
            # absent, the switch is not defined, the paragraph stays pending and the build refuses.
            r95 = cutoff().get("square95", {})
            sq = r95.get("decision", "open")
            if sq == "open":
                sq = r95.get("state_now", "open")   # what the checks file says now; decided at the cut off
            fh.write("\\newif\\ifSquareChecksClean\n\\SquareChecksClean%s\n\\newif\\ifSquareChecksCrossing\n"
                     "\\SquareChecksCrossing%s\n" % ("true" if sq == "clean" else "false",
                                                   "true" if sq == "crossing found" else "false"))
            fh.write("\\newif\\ifRuntimeParamsDone\n\\RuntimeParamsDone%s\n"
                     % ("true" if M.get("RuntimeHolds") == "yes" else "false"))
            if road != "open" or "RoadOneBFormula" in M:
                fh.write("\\newif\\ifRoadOneBRun\n\\RoadOneBRun%s\n"
                         % ("false" if road.startswith("four seed") else "true"))
            # The table «v8-in reads on PHerc. 0826» (owner's order of 2026-09-30): one row per row of
            # derived/v8in-reads.csv, written by src/tools/v8in_reads.py; a read added later is a rerun of that tool.
            fh.write("\\newcommand{\\VeinReadsRows}{%%\n%s}\n" % reads_rows())
            fh.write("\\newcommand{\\VeinReadsCount}{%d\\xspace}\n" % len(rows("derived/v8in-reads.csv")))
        with open(PENDING_OUT, "w") as fh:
            for name, rel, col in pending:
                fh.write("%s\t%s\t%s\n" % (name, rel, col))
    if pending:
        files = sorted({r for _, r, _ in pending})
        print("paper_numbers.py: PENDING, %d macros wait for %s" % (len(pending), ", ".join(files)))
        if "--list-pending" in sys.argv:
            for name, rel, col in pending:
                print("  %s  %s  %s" % (name, rel, col))
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
