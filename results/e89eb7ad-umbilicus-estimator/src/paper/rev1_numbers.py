# This file is a copy of paper/00001/tools/rev1_numbers.py of the private repository, which is
# frozen, brought into this work on 2026-09-23 beside the macro files it writes. It differs from
# that copy in two ways only: it reads the evidence and writes the macro files of this work
# (src/evidence/, src/paper/), and the four git commits the frozen copy asked of moving clones are
# constants below, each with the place it comes from. Nothing else is changed.
#
# Run on this work on 2026-09-23 it wrote 762 macros, each equal line for line and in order to the
# carried rev1-numbers.tex, which has 987: the other 225 expand from CSVs of the frozen run that
# this work does not carry (removal-cache, sensitivity-c-*, spiral-downstream, axis-identifiability,
# the mincap pair, the noise floor) and no source of this article uses them. So the carried file
# stays the one the build reads, and a run of this file is a check on it, not a replacement:
#     VILLA_UPSTREAM=<villa clone> python3 src/paper/rev1_numbers.py   in a copy of this folder
"""One source for every number of the revision: the CSVs of evidence/, nothing typed.

The frozen paper takes its macros from its own generator, which is not in this folder and is not
touched. This writes a second macro file, rev1-numbers.tex, and the generated table bodies the
revised paper inputs, from the evidence the revision produced. A CSV that is not there yet is
skipped, so the paper can be built while a run is still going, and a macro that is then missing
fails the LaTeX build rather than printing a stale figure.

Every macro name starts with Rev so that it cannot collide with the Umb macros.
"""
import json
import os
import re
import subprocess
import sys

# Where the article's sources live: src/paper/ of this work, flat, which is where this file is.
REV1 = os.path.dirname(os.path.abspath(__file__))
PAPERS = REV1
# rev1_lib is in src/tools/. It goes at the end of the path and not the front: until 2026-09-23 a
# file there was named numbers.py and stood in for the standard library module numpy imports, and
# it was renamed paper_numbers.py for that reason; the end of the path stays the safe place.
sys.path.append(os.path.join(os.path.dirname(REV1), "tools"))
import rev1_lib as L  # noqa: E402

# The commits the published text names. The frozen copy read each of them from the HEAD of a clone
# at build time, and a clone moves (on 2026-09-23 the villa clone's upstream/main was 33b0b91b7 and
# its HEAD a pull request branch), so a rebuild would have printed a different article. Each is
# the value the article published on 2026-09-17 prints, in rev1-numbers.tex as carried byte for
# byte from it.
#
# The tip of ScrollPrize/villa the text says the defect was still in: \RevUpstreamTip 2dcfaf6a0,
# \RevUpstreamDate 2026-09-17 (commit time 2026-09-17T12:45:19+02:00, "(#1815)"). It is read here
# only as a check: the macros come from evidence/upstream-check.csv, which tools/upstream_check.py
# writes against the same pinned tip, and a CSV taken at another tip is refused.
UPSTREAM_TIP = "2dcfaf6a08c3bc796fde726c4fa32050c8fc90e7"
# The villa commit the stand-in build compiled from: \RevVillaCommit, the same as PIN in
# tools/upstream_check.py.
VILLA_BUILT = "23adee047dea06526151d3a152a7d85de8da478b"
# The commit of the public repository the revision's evidence was written against:
# \RevPublicRepoCommit, the first twelve characters, which is all the text prints.
PUBLIC_REPO_COMMIT = "1cdad5a29a80"
# The patch commit, pull request 1823 of ScrollPrize/villa before it was squashed: \RevPatchCommit.
# Its tree, test file and line counts are still read from a clone (VILLA_FORK, else VILLA_UPSTREAM,
# else /data/repositories/villa), because a commit does not change once it exists.
PATCH_COMMIT = "7a4129a1dd21d867dba4f276d21c2fa27cf86287"
CNAME = {25: "TwentyFive", 50: "Fifty", 100: "Hundred", 200: "TwoHundred", 400: "FourHundred",
         800: "EightHundred"}
SEC = {"circle 1:1": "CircleOne", "ellipse 1.4": "Ellipse", "half circle": "Half",
       "density 1:2": "DensTwo", "density 1:5": "DensFive", "density 1:10": "DensTen"}
SCROLL_KEY = {s: s.replace("PHerc", "").replace("Paris4", "ParisFour")
              .replace("0", "Zero").replace("1", "One").replace("2", "Two").replace("3", "Three")
              .replace("4", "Four").replace("5", "Five").replace("6", "Six").replace("7", "Seven")
              .replace("8", "Eight").replace("9", "Nine") for s in L.CFG}


RULE_NAME = {"centroid": "the centroid", "argmax": "the maximum of the distance transform",
             "plateau_centroid": "the centroid of the plateau",
             "plateau_nearest_centroid": "the plateau point nearest the centroid",
             "argmax + hampel": "the maximum of the distance transform with jumps rejected"}


def and_list(items):
    """A list a person reads: one item, two joined by and, more with commas and a final and."""
    xs = [str(x) for x in items]
    if not xs:
        return "none"
    return xs[0] if len(xs) < 2 else ", ".join(xs[:-1]) + " and " + xs[-1]


TENS_MM = 10.0   # what "tens of millimetres" means when the paper counts rows, declared once here
# The day the two post hoc baselines and the bench run were declared post hoc in the paper. It is
# written here and not taken from the clock or from SOURCE_DATE_EPOCH, because it is the date of a
# declaration and must not move when the paper is rebuilt.
BASELINES_DECLARED = "18 September 2026"


def umb(name):
    """The value of an Umb macro of the frozen run, read from its own macro file.

    The revision compares against numbers the September run computed, the reference spread of
    PHerc1218 above all. Reading the macro keeps the comparison value
    in one place, papers/umbilicus-numbers.tex, instead of repeating it here.
    """
    src = open(os.path.join(PAPERS, "umbilicus-numbers.tex")).read()
    m = re.search(r"\\newcommand\{\\" + name + r"\}\{([0-9.]+)\\xspace\}", src)
    if not m:
        raise SystemExit(f"rev1_numbers: no \\{name} in umbilicus-numbers.tex")
    return float(m.group(1))


def num(x):
    if isinstance(x, str):
        return x
    s = f"{x:,.2f}" if isinstance(x, float) else f"{x:,}"
    return s.replace(",", "{,}")


def body(name, lines):
    p = os.path.join(PAPERS, name)
    open(p, "w").write("% Generated by tools/rev1_numbers.py. Do not edit by hand.\n"
                       + "\n".join(lines) + "\n")
    print(f"written {p} ({len(lines)} rows)")


def csv(name):
    p = os.path.join(L.EV, name)
    return L.read_csv(p) if os.path.exists(p) else None


def main():
    M = []
    h = VILLA_BUILT
    M += [("RevVillaCommit", h), ("RevVillaShort", h[:9])]
    M.append(("RevPublicRepoCommit", PUBLIC_REPO_COMMIT))

    # Whether the defect is still in the published code, asked of the clone by
    # tools/upstream_check.py rather than remembered. A referee asks this first.
    u = csv("upstream-check.csv")
    if u:
        tips = {r["tip"] for r in u}
        if tips != {UPSTREAM_TIP[:9]}:
            raise SystemExit("rev1_numbers: upstream-check.csv was taken at tip %s, not at the "
                             "pinned %s: run tools/upstream_check.py" % (", ".join(sorted(tips)),
                                                                         UPSTREAM_TIP[:9]))
        r = u[0]
        M += [("RevUpstreamTip", r["tip"]), ("RevUpstreamAhead", r["commits_ahead"]),
              ("RevUpstreamDate", r["tip_date"]),
              ("RevUpstreamTouching", r["commits_touching_file"]),
              ("RevUpstreamDefectLine", r["defect_line_at_tip"])]

    # ---- Meta E: the counts behind the captions
    # The counts the captions state, recounted here from the files they come from. Until
    # 2026-09-30 they were read from consistency.csv, whose writer rev1_consistency.py is not in
    # this folder (referee 2026-09-30, finding 14); the values must be the ones that file carried.
    fif = csv("fifteen.csv")
    pos24 = csv("cpp-positions-24.csv")
    noise = csv("search-noise.csv")
    if fif and pos24 and noise:
        import json as _json
        s24 = _json.load(open(os.path.join(os.path.dirname(REV1), "inputs", "scrolls-24.json")))
        outside = [k for k, q in s24.items()
                   if q.get("note", "").startswith("not one of the twenty-three in the competition")]
        if len(outside) != 1:
            raise SystemExit("rev1_numbers.py: scrolls-24.json marks %d scrolls outside the competition" % len(outside))
        run_scrolls = {q["scroll"] for q in pos24}
        if run_scrolls != set(s24):
            raise SystemExit("rev1_numbers.py: cpp-positions-24.csv and scrolls-24.json name different scrolls")
        cps = [int(q["scored_on"]) for q in fif]
        M += [("RevFifteenSlices", max(int(q["heights_used"]) for q in fif)),
              ("RevFifteenCpMin", min(cps)), ("RevFifteenCpMax", max(cps)),
              ("RevFifteenCpTotal", sum(cps)),
              ("RevRunScrolls", len(run_scrolls)),
              ("RevRunInCompetition", len(run_scrolls) - len(outside)),
              ("RevRunNotInCompetition", outside[0]),
              ("RevRunSlices", len({(q["scroll"], q["z"]) for q in pos24 if q["role"] == "position"})),
              ("RevNoiseSlices", sum(q["variant"] == "no-division" for q in noise)),
              ("RevNoiseScrolls", len({q["scroll"] for q in noise if q["variant"] == "no-division"}))]
    # the saved slices of the stand-in build: how many the published objective left on every
    # repeat (referee 2026-09-30, finding 8: the text named one where there are two)
    runs = csv("cpp-runs.csv")
    if runs:
        leave = [q for q in runs if q["variant"] == "as-is" and int(q["outside"]) == int(q["repeats"])]
        M += [("RevNoiseAsIsLeaving", len(leave)),
              ("RevNoiseAsIsLeavingSlices", " and ".join(q["dump"][2:] for q in leave)),
              ("RevNoiseFixedOutside", sum(int(q["outside"]) for q in runs if q["variant"] == "no-division"))]
    # the lines of the function the project's own suite runs, from function-coverage.csv
    # (finding 14: the frozen macro printed 20.50 where 17 of 83 is 20.48)
    fc = csv("function-coverage.csv")
    if fc:
        ran = sum(int(q["runs_suite"]) > 0 for q in fc)
        M += [("RevCoverageLines", len(fc)), ("RevCoverageRun", ran),
              ("RevCoveragePct", f"{100.0 * ran / len(fc):.2f}")]
    vl = csv("villa-lines.csv")
    if vl:
        M += [("RevVillaLinesChecked", len([r for r in vl if r["expected_token"]])),
              ("RevVillaLinesFound", sum(int(r["present"] or 0) for r in vl))]

    # Table I without the reference column
    sn = csv("search-noise.csv")
    if sn:
        body("rev1-search-noise.tex",
             [f"{r['scroll']} & {r['slice_z']} & {float(r['spread_median_mm']):.2f} & "
              f"{float(r['spread_p90_mm']):.2f} & {float(r['spread_worst_mm']):.2f} \\\\"
              for r in sn if r["variant"] == "no-division"])

    # ---- Meta E: cache misses of the indexed removal
    rc = csv("removal-cache.csv")
    if rc:
        idx = sorted([r for r in rc if r["strategy"] == "indexed"], key=lambda r: int(r["n"]))
        lin = sorted([r for r in rc if r["strategy"] == "linear"], key=lambda r: int(r["n"]))
        col = "net_misses_per_removal" if idx[0].get("net_misses_per_removal") else "misses_per_removal"
        mpr = [float(r[col]) for r in idx]
        M += [("RevCacheSmallN", int(idx[0]["n"])), ("RevCacheLargeN", int(idx[-1]["n"])),
              ("RevCacheIndexedMissesSmall", mpr[0]), ("RevCacheIndexedMissesLarge", mpr[-1]),
              ("RevCacheIndexedRatio", f"{mpr[-1] / mpr[0]:.0f}" if mpr[0] else "n/a"),
              ("RevCacheLinearMissesSmall", float(lin[0][col])),
              ("RevCacheLinearMissesLarge", float(lin[-1][col])),
              ("RevCacheNetted", "net of the setup" if col.startswith("net") else "including the setup"),
              ("RevCacheSizes", len(idx)),
              ("RevCacheIndexedInstrSmall", int(round(float(idx[0].get("net_instructions_per_removal") or float(idx[0]["instructions"]) / int(idx[0]["n"]))))),
              ("RevCacheIndexedInstrLarge", int(round(float(idx[-1].get("net_instructions_per_removal") or float(idx[-1]["instructions"]) / int(idx[-1]["n"]))))),
              ("RevCacheIndexedMissesMid", float(idx[3][col])),
              ("RevCacheMidN", int(idx[3]["n"]))]
        body("rev1-removal-cache.tex",
             [f"{int(r['n']):,} & {float(r[col]):.1f} & {float(l[col]):.1f} \\\\".replace(",", "{,}")
              for r, l in zip(idx, lin)])

    # ---- the frozen run's own measurements, recomputed with the faithful sample (audit 2026-09-16)
    # The twenty four scroll run moved to the shipped function on 2026-09-18, called through
    # vc_gen_umbilicus with no cap; its summary has the same schema, so only the file changes.
    # The transcription's stays beside it and its counts are printed as the difference.
    for name, key in (("cpp-twentyfour.csv", "Gen"), ("synthetic-sections-refit.csv", "Syn"),
                      ("noise-by-variant-refit.csv", "Noi")):
        rows = csv(name) or (csv("twentythree-refit.csv") if key == "Gen" else None)
        if not rows:
            continue
        if key == "Gen":
            t24 = csv("twentythree-refit.csv")
            if t24:
                M += [("RevGenInsideAsIsTranscription",
                       sum(int(r["inside_as_is"]) for r in t24)),
                      ("RevGenInsideFixedTranscription",
                       sum(int(r["inside_fixed"]) for r in t24))]
        if key == "Gen":
            # One seed per slice, and the paper says so wherever it states the count: 576 of 576
            # is a count over 576 slices, not over 576 by however many seeds. Counted from the
            # raw positions rather than asserted, so it cannot go stale if the design changes.
            pos = csv("cpp-positions-24.csv") or csv("positions-24-refit.csv")
            pos = [q for q in pos if q.get("role", "position") == "position"] if pos else pos
            if pos:
                per = {}
                for q in pos:
                    per[(q["scroll"], q["z"], q["variant"])] = per.get(
                        (q["scroll"], q["z"], q["variant"]), 0) + 1
                M += [("RevGenSeedsPerSlice", max(per.values()) if per else 1)]
            M += [("RevGenScrolls", len(rows)),
                  ("RevGenInsideAsIs", sum(int(r["inside_as_is"]) for r in rows)),
                  ("RevGenInsideFixed", sum(int(r["inside_fixed"]) for r in rows)),
                  ("RevGenSlices", sum(int(r["slices"]) for r in rows)),
                  ("RevGenAllInside", sum(int(r["inside_fixed"]) == int(r["slices"]) for r in rows)),
                  ("RevGenAllInsideAsIs", sum(int(r["inside_as_is"]) == int(r["slices"]) for r in rows)),
                  ("RevGenUnderSixteen", sum(int(r["inside_as_is"]) < 16 for r in rows)),
                  ("RevGenSeedWorst", round(max(float(r["seed_spread_pct"]) for r in rows), 2)),
                  ("RevGenCentroidWorst", round(max(float(r["centroid_med_pct"]) for r in rows), 2)),
                  ("RevGenSmoother", sum(float(r["jump_med_fixed_pct"]) < float(r["jump_med_as_is_pct"]) for r in rows)),
                  ("RevGenInterior", sum(r["interior_max"] == "True" for r in rows)),
                  ("RevGenInteriorPct", f'{100.0 * sum(r["interior_max"] == "True" for r in rows) / len(rows):.1f}'),
                  ("RevGenContinuityPass", sum(float(r["jump_med_fixed_pct"]) < 2.0 for r in rows))]
            # The four criteria of inputs/preregistration-twenty-four-scrolls.md, lines 25 to 44, each
            # with its count (referee 2026-09-30, finding 1): 1, at least 23 of 24 slices inside on
            # every scroll and 99 % over the total; 2, median seed spread below 1 % of the grid width
            # on every scroll; 3, median jump along z below 2 % on every scroll; 4, an interior
            # maximum on at least 90 % of the scrolls. The thresholds are those of the text.
            seedw = max(rows, key=lambda r: float(r["seed_spread_pct"]))
            jumpw = max(rows, key=lambda r: float(r["jump_med_fixed_pct"]))
            c1 = sum(int(r["inside_fixed"]) >= int(r["slices"]) - 1 for r in rows)
            c1pct = 100.0 * sum(int(r["inside_fixed"]) for r in rows) / sum(int(r["slices"]) for r in rows)
            c2 = sum(float(r["seed_spread_pct"]) < 1.0 for r in rows)
            c3 = sum(float(r["jump_med_fixed_pct"]) < 2.0 for r in rows)
            c4 = sum(r["interior_max"] == "True" for r in rows)
            crit = [c1 == len(rows) and c1pct >= 99.0, c2 == len(rows), c3 == len(rows),
                    c4 >= 0.9 * len(rows)]
            M += [("RevGenCritOneScrolls", c1), ("RevGenCritOnePass", "passes" if crit[0] else "fails"),
                  ("RevGenCritTwoPass", "passes" if crit[1] else "fails"),
                  ("RevGenCritTwoFail", len(rows) - c2),
                  ("RevGenSeedWorstScroll", seedw["scroll"]),
                  ("RevGenCritThreePass", "passes" if crit[2] else "fails"),
                  ("RevGenCritThreeFail", len(rows) - c3),
                  ("RevGenJumpWorst", f'{float(jumpw["jump_med_fixed_pct"]):.2f}'),
                  ("RevGenJumpWorstScroll", jumpw["scroll"]),
                  ("RevGenCritFourPass", "passes" if crit[3] else "fails"),
                  ("RevGenCritPassed", sum(crit)),
                  ("RevGenGeneralises", "does" if all(crit) else "does not")]
            posall = csv("cpp-positions-24.csv") or []
            spreadseeds = {}
            for q in posall:
                if q["variant"] == "no-division":
                    spreadseeds.setdefault((q["scroll"], q["z"]), set()).add(q["seed"])
            if posall:
                M += [("RevGenSpreadSeeds", max(len(v) for v in spreadseeds.values())),
                      ("RevGenSpreadSeedsMin", min(len(v) for v in spreadseeds.values()))]
            # the seeds per slice of that run are a constant of the tool that made it
            # (rev1_recompute.SEEDS), not a column of its CSV
            import rev1_recompute
            M += [("RevGenSeeds", len(rev1_recompute.SEEDS)),
                  ("RevGenEstimatesPerSeed", 2 * sum(int(r["slices"]) for r in rows))]
        if key == "Syn":
            a = {r["family"] + "|" + str(r["value"]): r for r in rows}
            c = a.get("A concentric circles|0.0")
            if c:
                M += [("RevSynCircleAsIs", f'{float(c["median_mm_as_is"]):.3f}'),
                      ("RevSynCircleFixed", f'{float(c["median_mm_no_division"]):.3f}'),
                      ("RevSynCircleAsIsUnits", float(c["median_units_as_is"])),
                      ("RevSynCircleFixedUnits", float(c["median_units_no_division"])),
                      ("RevSynSeeds", int(c["n_seeds"]))]
            half = a.get("D partial arcs|0.5")
            if half:
                M += [("RevSynHalfAsIs", float(half["median_units_as_is"])),
                      ("RevSynHalfFixed", float(half["median_units_no_division"]))]
            M.append(("RevSynConfigs", len(rows)))
        if key == "Noi":
            steadier = [r for r in rows if float(r["a12_as_is_vs_no_division"]) < 0.5]
            sig = [r for r in steadier if float(r["p"]) < 0.05]
            M += [("RevNoiseSlicesCompared", len(rows)), ("RevNoiseAsIsSteadier", len(steadier)),
                  ("RevNoiseAsIsSteadierSig", len(sig)), ("RevNoiseRepeats", int(rows[0]["n_per_group"]))]
            worst = max(rows, key=lambda q: float(q["median_as_is_mm"]))
            M.append(("RevNoiseRunawaySlice", f'{float(worst["median_as_is_mm"]):.0f}'))
            for i, r in enumerate(sorted(sig, key=lambda q: float(q["p"]))[:2]):
                M += [(f"RevNoiseSigA{'One' if i == 0 else 'Two'}", float(r["a12_as_is_vs_no_division"])),
                      (f"RevNoiseSigP{'One' if i == 0 else 'Two'}", f'{float(r["p"]):.3f}')]

    # ---- the inference of Section V-B, on the twenty-seed medians
    pi = os.path.join(L.EV, "inference-refit.json")
    if os.path.exists(pi):
        inf = json.load(open(pi))
        fr, ne, to = inf["friedman"], inf["nemenyi"], inf["tost"]
        key = "no-division vs centroid"
        M += [("RevInfScrolls", inf["n_scrolls"]), ("RevInfMethods", inf["k_methods"]),
              ("RevInfChi", round(fr["chi2"], 2)), ("RevInfP", f'{fr["p"]:.1e}'.replace("e-0", "e-")),
              ("RevInfRankFixed", fr["mean_ranks"]["no-division"]),
              ("RevInfRankCentroid", fr["mean_ranks"]["centroid"]),
              ("RevInfRankFakeAxis", fr["mean_ranks"]["fake_axis"]),
              ("RevInfRankAsIs", fr["mean_ranks"]["as-is"]),
              ("RevInfHolmVsCentroid", f'{inf["wilcoxon_holm"][key]["p_holm"]:.4f}'),
              ("RevInfNemenyiCD", ne["critical_difference"]), ("RevInfNemenyiGap", ne["gap_fixed_vs_centroid"]),
              ("RevInfNemenyiVerdict", "separates" if ne["separates"] else "does not separate"),
              ("RevInfTostLimit", to["bound_mm"]), ("RevInfTostP", f'{to["p"]:.3f}'), ("RevInfTostN", to["n"]),
              ("RevInfTostVerdict", "equivalent" if to["equivalent"] else "not equivalent"),
              ("RevInfNonDiscriminating", ", ".join(inf["non_discriminating"]) or "none"),
              ("RevInfWorstPrimary", inf["worst"]["primary"]),
              ("RevInfWorstConfirm", inf["worst"]["confirmation"])]
    # ---- 2026-09-18, referee: the scroll where the constant axis wins is a property of the
    # scroll. The control's distance from the reference IS the distance from the reference to the
    # centre of the field, so these numbers say how much a rule has to know to beat it.
    # The constant axis control belongs to Tables II and III, so it is read from the same file
    # they are: the shipped function since 2026-09-18. The axis itself is deterministic and does
    # not move with the instrument, but the count of scrolls the estimator beats it on does, and
    # a control read from another file than the table it controls is how two instruments end up
    # on one page.
    fk = csv("cpp-k20.csv") or csv("fifteen-k20.csv")
    if fk:
        nd0 = [r for r in fk if r["variant"] == "no-division"]
        fa = sorted((float(r["fake_axis_mm"]), r["scroll"]) for r in nd0)
        dead = [s2 for v, s2 in fa
                if all(v < float(r[k]) for r in nd0 if r["scroll"] == s2
                       for k in ("median_mm", "centroid_mm"))]
        rest = [v for v, s2 in fa if s2 not in dead]
        beaten = sum(1 for r in nd0 if r["scroll"] not in dead
                     and float(r["median_mm"]) < float(r["fake_axis_mm"]))
        import statistics as _s
        M += [("RevFakeAxisMin", f"{fa[0][0]:.2f}"), ("RevFakeAxisMinScroll", fa[0][1]),
              ("RevFakeAxisMedian", f"{_s.median(v for v, _ in fa):.2f}"),
              ("RevFakeAxisSecond", f"{min(rest):.2f}"), ("RevFakeAxisMax", f"{max(rest):.2f}"),
              ("RevFakeAxisOthers", len(rest)), ("RevFakeAxisSumCloser", beaten)]

    ba = csv("bland-altman-refit.csv")
    if ba:
        r = [q for q in ba if q["scroll"] == "PHerc1218" and q["axis"] == "y"]
        if r:
            M += [("RevLoaFixedLow", f'{float(r[0]["loa_low_mm"]):.2f}'),
                  ("RevLoaFixedHigh", f'{float(r[0]["loa_high_mm"]):.2f}')]

    # ---- Meta A: density bias on synthetic sections
    sd = csv("synthetic-density.csv")
    if sd:
        for r in sd:
            k = SEC[r["section"]] + ("Sum" if r["objective"] == "sum" else "Mean")
            M += [(f"RevDens{k}FieldErr", f"{float(r['fieldmax_err_median_units']):.0f}"),
                  (f"RevDens{k}FieldErrMm", f"{float(r['fieldmax_err_median_mm']):.2f}"),
                  (f"RevDens{k}FieldDx", f"{float(r['fieldmax_dx_median_units']):+.0f}"),
                  (f"RevDens{k}EstErr", f"{float(r['estimate_err_median_units']):.0f}"),
                  (f"RevDens{k}EstErrMm", f"{float(r['estimate_err_median_mm']):.2f}"),
                  (f"RevDens{k}EstDx", f"{float(r['estimate_dx_median_units']):+.0f}")]
        M.append(("RevDensSeeds", int(sd[0]["n_seeds"])))
        ten = {r["objective"]: r for r in sd if r["section"] == "density 1:10"}
        dx = float(ten["sum"]["fieldmax_dx_median_units"])
        M.append(("RevDensPredictionSum", "held" if 50 <= dx <= 250 else "failed"))
        M.append(("RevDensPredictionMean",
                  "held" if abs(float(ten["mean"]["fieldmax_dx_median_units"])) < 10 else "failed"))
        rows = []
        for sec in SEC:
            s = {r["objective"]: r for r in sd if r["section"] == sec}
            if len(s) < 2:
                continue
            rows.append(f"{sec} & {float(s['sum']['fieldmax_err_median_units']):.0f} & "
                        f"{float(s['sum']['fieldmax_dx_median_units']):+.0f} & "
                        f"{float(s['mean']['fieldmax_err_median_units']):.0f} & "
                        f"{float(s['mean']['fieldmax_dx_median_units']):+.0f} & "
                        f"{float(s['sum']['estimate_err_median_units']):.0f} & "
                        f"{float(s['mean']['estimate_err_median_units']):.0f} \\\\")
        body("rev1-density.tex", rows)
    mc = csv("mechanism-curve.csv")
    if mc:
        for sec, key in (("f1 spiral", "Spiral"), ("circle 1:1", "Circle")):
            rr = [r for r in mc if r["section"] == sec]
            s = [float(r["weighted_sum"]) for r in rr]
            m = [float(r["weighted_mean"]) for r in rr]
            M += [(f"RevMech{key}SumFar", f"{s[-1] / max(s):.1e}".replace("e-0", "e-")),
                  (f"RevMech{key}MeanFar", f"{m[-1] / max(m):.2f}")]

    # ---- Meta A: density asymmetry on the real slices
    da = csv("density-asymmetry.csv")
    if da:
        worst = max(da, key=lambda r: float(r["sector_ratio_median"]))
        others = [float(r["sector_ratio_median"]) for r in da if r is not worst]
        M += [("RevAsymWorstScroll", worst["scroll"]),
              ("RevAsymWorstRatio", float(worst["sector_ratio_median"])),
              ("RevAsymWorstHalf", f"{float(worst['dominant_half_fraction_median']):.2f}"),
              ("RevAsymWorstSameHalf", f"{100 * float(worst['same_half_plane_fraction']):.0f}"),
              ("RevAsymWorstCos", f"{float(worst['cosine_median']):.2f}"),
              ("RevAsymOthersRatioLow", min(others)), ("RevAsymOthersRatioHigh", max(others)),
              ("RevAsymSameHalfLow", f"{100 * min(float(r['same_half_plane_fraction']) for r in da):.0f}"),
              ("RevAsymSameHalfHigh", f"{100 * max(float(r['same_half_plane_fraction']) for r in da):.0f}"),
              ("RevAsymScrolls", len(da)), ("RevAsymSlices", int(da[0]["slices"]))]
        body("rev1-asymmetry.tex",
             [f"{r['scroll']} & {float(r['sector_ratio_median']):.2f} & "
              f"{float(r['dominant_half_fraction_median']):.2f} & "
              f"{float(r['centroid_minus_ref_median_mm']):.2f} & "
              f"{float(r['estimate_minus_ref_median_mm']):.2f} & "
              f"{float(r['cosine_median']):.2f} & "
              f"{100 * float(r['same_half_plane_fraction']):.0f} \\\\" for r in da])

    # ---- reviewer's point 1 (2026-09-17): the far field limit of the mean as an eigenvalue
    ff = csv("far-field-eigenvalue.csv")
    if ff:
        by = {r["section"]: r for r in ff}
        for sec, key in ((f"PHerc0826 xy 8000", "Slice"), ("circle 1:1", "Circle"), ("half circle", "Half")):
            r = by[sec]
            M += [(f"RevFar{key}Lambda", f"{float(r['lambda_max']):.2f}"),
                  (f"RevFar{key}LambdaMin", f"{float(r['lambda_min']):.2f}"),
                  (f"RevFar{key}Centre", f"{float(r['mean_at_centre']):.2f}"),
                  (f"RevFar{key}Ratio", f"{float(r['far_over_centre']):.2f}")]
        M += [("RevFarSliceScroll", "PHerc0826"), ("RevFarSliceZ", 8000),
              ("RevFarSamples", int(ff[0]["n_samples"]))]

    # The two sizes of the search, taken from the transcription's own constants (cpp:22-23) so
    # that the text cannot drift from the estimator every number here was computed with.
    M += [("RevSeedCandidates", L.ve.N_CANDIDATES), ("RevSampleDraws", L.ve.N_SAMPLES)]

    # ---- second round, point 4: equation (1) tested on every slice of the fifteen scrolls
    fp = csv("far-field-prediction.csv")
    fs = csv("far-field-slices.csv")
    if fp and fs:
        maj = next(r for r in fp if r["rule"].startswith("majority"))
        k0 = next(r for r in fp if r["rule"].startswith("seed"))
        tp, fpos = int(maj["predicted_yes_observed_yes"]), int(maj["predicted_yes_observed_no"])
        fn, tn = int(maj["predicted_no_observed_yes"]), int(maj["predicted_no_observed_no"])
        M += [("RevFarSlicesTotal", int(maj["n"])), ("RevFarScrolls", len({r["scroll"] for r in fs})),
              ("RevFarPredictedYes", tp + fpos), ("RevFarPredictedNo", fn + tn),
              ("RevFarRunaways", tp + fn), ("RevFarStayed", fpos + tn),
              ("RevFarTruePos", tp), ("RevFarFalsePos", fpos),
              ("RevFarFalseNeg", fn), ("RevFarTrueNeg", tn),
              ("RevFarSensitivity", f"{float(maj['sensitivity']):.2f}"),
              ("RevFarSpecificity", f"{float(maj['specificity']):.2f}"),
              ("RevFarPrecision", f"{float(maj['precision']):.2f}"),
              # No macro for the pooled Fisher test of this CSV. Two reviews of 2026-09-18 made
              # the same point and it is right: the 360 slices are 24 from each of 15 scrolls and
              # are not independent, so a pooled test inflates its own p value. The CSV keeps the
              # number as a record of what was computed; the paper uses the per scroll table and
              # the within-scroll permutation of far_field_scrolls.py instead.
              ("RevFarSeedZeroFalseNeg", int(k0["predicted_no_observed_yes"])),
              # Said from the numbers whatever they are: with no miss the condition is necessary;
              # with a miss it is necessary on all but that many, and the miss is named below.
              ("RevFarNecessity", "necessary and not sufficient" if fn == 0 else
               f"necessary on all but {fn} of the {tp + fn} slices that leave, and not sufficient"),
              ("RevFarSliceSeedRule", "more than half of the " + str(int(fs[0]["seeds"])) + " seeds")]
        # The outcomes of Table I are the shipped walk's since 2026-09-18 13:03 UTC. The slices
        # whose side changed against the transcription's outcomes are named from the two files,
        # and the missed slices, if any, are named with their seed counts under both instruments.
        fst = csv("far-field-slices-transcription.csv")
        if fst:
            a = {(r["scroll"], r["z"]): r for r in fst}
            b = {(r["scroll"], r["z"]): r for r in fs}
            changed = sorted(k for k in b if k in a and a[k]["outside_majority"] != b[k]["outside_majority"])
            misses = sorted(k for k in b if int(b[k]["outside_majority"]) and not int(b[k]["predicts_runaway"]))
            misses_t = sorted(k for k in a if int(a[k]["outside_majority"]) and not int(a[k]["predicts_runaway"]))
            def _nm(k):
                return f"{k[0].replace('PHerc', 'PHerc. ')} z {k[1]}"
            M += [("RevFarSidesChanged", len(changed)),
                  ("RevFarSidesChangedSlices", ", ".join(_nm(k) for k in changed) or "none"),
                  ("RevFarMissCount", len(misses)),
                  ("RevFarMissCountTranscription", len(misses_t)),
                  ("RevFarMissSlices", ", ".join(_nm(k) for k in misses) or "none")]
            if misses:
                k = misses[0]
                M += [("RevFarMissSlice", _nm(k)),
                      ("RevFarMissSeedsShipped", int(b[k]["seeds_outside"])),
                      ("RevFarMissSeedsTranscription", int(a[k]["seeds_outside"])),
                      ("RevFarMissSeedsOf", int(b[k]["seeds"])),
                      ("RevFarMissRatio", f"{float(b[k]['lambda_over_mean']):.3f}")]
            # Whole sentences, built only when there is something to say: a sentence assembled
            # around a value that can be empty prints a blank in a published page, so the
            # sentence is empty instead, as in the gallery caption.
            if misses:
                k = misses[0]
                M += [("RevFarMissSentence",
                       f"One of them is the miss. On {_nm(k)} the bound is "
                       f"{float(b[k]['lambda_over_mean']):.3f} of the score on the axis, so the "
                       f"condition does not fire, and the published walk leaves the grid on "
                       f"{int(b[k]['seeds_outside'])} of {int(b[k]['seeds'])} seeds under the "
                       f"shipped function against {int(a[k]['seeds_outside'])} of "
                       f"{int(a[k]['seeds'])} under the transcription, on either side of the "
                       f"majority. Under the transcription the condition missed "
                       f"{len(misses_t)} slices; under the shipped function it misses "
                       f"{len(misses)}. That is one slice at the majority line, and it is "
                       f"printed as a difference and not reconciled."),
                      ("RevFarMissClause",
                       f", the remaining {'one' if len(misses) == 1 else str(len(misses))}, on "
                       f"{', '.join(_nm(q) for q in misses)}, sitting at the majority line under "
                       f"the shipped walk")]
            else:
                M += [("RevFarMissSentence", ""), ("RevFarMissClause", "")]
        # the comparison the code could actually make: the bound against the refined score it is
        # about to return, which is not the quantity Table I measures (third review round)
        wr = next((r for r in fp if r["predictor"] == "predicts_runaway_refined"), None)
        if wr:
            tp2, fp2 = int(wr["predicted_yes_observed_yes"]), int(wr["predicted_yes_observed_no"])
            fn2, tn2 = int(wr["predicted_no_observed_yes"]), int(wr["predicted_no_observed_no"])
            M += [("RevFarWarnPredictedYes", tp2 + fp2), ("RevFarWarnTruePos", tp2),
                  ("RevFarWarnFalsePos", fp2), ("RevFarWarnFalseNeg", fn2),
                  ("RevFarWarnTrueNeg", tn2), ("RevFarWarnRunaways", tp2 + fn2),
                  ("RevFarWarnSensitivity", f"{float(wr['sensitivity']):.2f}"),
                  ("RevFarWarnSpecificity", f"{float(wr['specificity']):.2f}"),
                  ("RevFarWarnSlices", int(wr["n"]))]

    # ---- 2026-09-18: the same condition with the scroll as the unit, and the permutation test
    ps = csv("far-field-per-scroll.csv")
    pm = csv("far-field-permutation.csv")
    if ps and pm:
        q = pm[0]
        M += [("RevFarScrollUnit", int(q["scrolls"])),
              ("RevFarScrollSlicesEach", int(ps[0]["slices"])),
              ("RevFarScrollsZeroMisses", int(q["scrolls_zero_misses"])),
              ("RevFarScrollsWithLeaving", int(q["scrolls_with_a_leaving_run"])),
              ("RevFarScrollsAllFlagged", int(q["scrolls_all_leaving_runs_flagged"])),
              ("RevFarPermRounds", int(q["sim_rounds"])), ("RevFarPermHits", int(q["sim_hits"])),
              ("RevFarPermP", q["sim_p_upper_bound"].replace("e-0", "e$-$").replace("e-", "e$-$")),
              ("RevFarPermExactP", q["exact_p"].replace("e-", "e$-$")),
              ("RevFarScrollMostLeaving", max(ps, key=lambda r: int(r["left_the_grid"]))["scroll"]),
              ("RevFarScrollNoLeaving", ", ".join(r["scroll"] for r in ps if not int(r["left_the_grid"])) or "none")]
        body("rev1-far-field-scrolls.tex",
             [f"{r['scroll']} & {r['flagged']} & {r['left_the_grid']} & {r['flagged_and_left']} & "
              f"{r['missed']} \\\\" for r in ps])

    # ---- 2026-09-18: the exponent of the weight, asked for by both model reviews
    # (declared in full before the run, in the rule of 2026-09-18 that governed it)
    ca = csv("exponent-ablation-cancellation-rate.csv")
    # The exponent table moved to compiled binaries on 2026-09-18: p = 0.5, 1.5 and 2 are the
    # weight raised to the exponent, p = 1 is the shipped expression and the control is the
    # shipped weighted mean, all from vc_gen_umbilicus. The density bias column is the one thing
    # left on the transcription here, because its sections are float polylines that the shipped
    # GridStore, which stores integer points, cannot hold; the caption says so.
    ek = csv("cpp-exponent-fifteen-k20.csv") or csv("exponent-ablation-fifteen-k20.csv")
    es = csv("cpp-exponent-seed-spread.csv") or csv("exponent-ablation-seed-spread.csv")
    ed = csv("exponent-ablation-synthetic-density.csv")
    if ca and ek and es and ed:
        import statistics
        # the cancellation, checked against the bar the addition of 03:52 fixed before looking
        secs = sorted({r["section"] for r in ca})
        ps_c = sorted({float(r["p"]) for r in ca})
        combos = ok = 0
        ratios = []
        for sec in secs:
            for pv in ps_c:
                rr = sorted([r for r in ca if r["section"] == sec and float(r["p"]) == pv],
                            key=lambda r: float(r["distance_units"]))
                combos += 1
                good = True
                for r in rr[1:]:
                    d = float(r["mean_gap_divided_by"]) if r["mean_gap_divided_by"] else None
                    if d is None:
                        continue
                    ratios.append(d)
                    if not (5.0 <= d <= 20.0 or float(r["mean_rel_gap"]) < 1e-6):
                        good = False
                    # not `sd`: that name holds the synthetic-density rows this function reads
                    # again further down, and shadowing it broke the regression test tolerances
                    sumdiv = float(r["sum_divided_by"]) if r["sum_divided_by"] else None
                    if sumdiv is not None and not (10 ** pv / 2 <= sumdiv <= 2 * 10 ** pv):
                        good = False
                ok += good
        M += [("RevExpCancelSections", len(secs)), ("RevExpCancelExponents", len(ps_c)),
              ("RevExpCancelMaxP", f"{max(ps_c):.0f}"), ("RevExpCancelCombos", combos),
              ("RevExpCancelPassed", ok),
              ("RevExpCancelRateLow", f"{min(ratios):.1f}"),
              ("RevExpCancelRateHigh", f"{max(ratios):.1f}"),
              ("RevExpCancelDecades", len({r["distance_units"] for r in ca})),
              ("RevExpCancelFarD", "10^9")]

        # p = 1 reproduces the paper's own estimates, to the digit. The compiled exponent run does
        # not recompute p = 1 (tools/cpp_exponent_score.py takes it from cpp-k20-estimates.csv), so
        # the comparison that means something is the transcription's, whose exponent run did compute
        # p = 1 (referee 2026-09-30, finding 2: the compiled check compared nothing and printed
        # "0 differences over 0"). A comparison over no rows stops the run.
        ee = csv("exponent-ablation-k20-estimates.csv")
        base = csv("k20-estimates.csv")
        if ee and base:
            b = {(r["scroll"], r["z"], r["k"]): (r["x"], r["y"])
                 for r in base if r["variant"] == "no-division"}
            n = diff = 0
            for r in ee:
                if abs(float(r["p"]) - 1.0) > 1e-12:
                    continue
                key = (r["scroll"], r["z"], r["k"])
                if key in b:
                    n += 1
                    diff += (r["x"] != b[key][0]) or (r["y"] != b[key][1])
            if n == 0:
                raise SystemExit("rev1_numbers.py: the p = 1 check compared no estimates")
            ce = csv("cpp-exponent-estimates.csv") or []
            if any(abs(float(r["p"]) - 1.0) <= 1e-12 for r in ce):
                raise SystemExit("rev1_numbers.py: cpp-exponent-estimates.csv now carries p = 1; "
                                 "compare it with cpp-k20-estimates.csv and say so in the text")
            M += [("RevExpReproEstimates", f"{n:,}"), ("RevExpReproDiffs", diff)]

        # the intervals and the paired counts of tools/exponent_intervals.py, written after a
        # referee asked on 2026-09-18 what supports p = 1 over its neighbours
        ag = csv("cpp-exponent-aggregate.csv") or csv("exponent-ablation-aggregate.csv")
        agg = {r["row"]: r for r in ag} if ag else {}

        # the table, one row per exponent, plus the published mean as the control
        ps = sorted({float(r["p"]) for r in ek})
        rows, key = [], {}
        for pv in ps:
            rr = [r for r in ek if float(r["p"]) == pv]
            med = statistics.median(float(r["median_mm"]) for r in rr)
            beats = sum(int(r["beats_threshold"]) for r in rr)
            outside = sum(int(r["outside"]) for r in rr)
            of = sum(int(r["inside_of"]) for r in rr)
            spread = statistics.median(float(r["spread_median_mm"]) for r in es
                                       if abs(float(r["p"]) - pv) < 1e-12)
            dens = [r for r in ed if abs(float(r["p"]) - pv) < 1e-12
                    and r["section"] == "density 1:10" and r["objective"] == "sum"]
            bias = float(dens[0]["fieldmax_err_median_mm"]) if dens else float("nan")
            key[pv] = dict(med=med, beats=beats, outside=outside, of=of, spread=spread, bias=bias,
                           n=len(rr))
            bold = (lambda t: f"\\textbf{{{t}}}") if abs(pv - 1.0) < 1e-12 else (lambda t: t)
            ci = agg.get(f"{pv:g}")
            cell = f"{med:.2f}" if not ci else f"{med:.2f} [{float(ci['ci_lo_mm']):.2f}, {float(ci['ci_hi_mm']):.2f}]"
            rows.append(" & ".join([bold(f"{pv:.1f}"), bold(f"{outside} of {of:,}".replace(",", "{,}")),
                                    bold(cell), bold(f"{beats} of {len(rr)}"),
                                    bold(f"{spread:.2f}"), bold(f"{bias:.2f}")]) + " \\\\")
            # a TeX control sequence takes letters only, so the exponent is spelled out
            tag = "P" + f"{pv:.1f}".replace(".", "").translate(
                str.maketrans({"0": "Zero", "1": "One", "2": "Two", "3": "Three", "4": "Four",
                               "5": "Five", "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine"}))
            M += [(f"RevExp{tag}Median", f"{med:.2f}"), (f"RevExp{tag}Beats", beats),
                  (f"RevExp{tag}Outside", outside), (f"RevExp{tag}Spread", f"{spread:.2f}"),
                  (f"RevExp{tag}Bias", f"{bias:.2f}")]
        # the control: the published weighted mean on the same slices and seeds
        k20 = csv("cpp-k20.csv") or csv("fifteen-k20.csv")
        ests = csv("cpp-k20-estimates.csv") or csv("k20-estimates.csv")
        if k20 and ests:
            asis = [r for r in k20 if r["variant"] == "as-is"]
            med_a = statistics.median(float(r["median_mm"]) for r in asis)
            out_a = sum(1 for r in ests if r["variant"] == "as-is" and int(r["inside"]) == 0)
            tot_a = sum(1 for r in ests if r["variant"] == "as-is")
            beats_a = sum(float(r["margin_vs_centroid_mm"]) >= L.THRESHOLD_MM for r in asis)
            M += [("RevExpMeanMedian", f"{med_a:.2f}"), ("RevExpMeanOutside", out_a),
                  ("RevExpMeanOutsideOf", tot_a), ("RevExpMeanBeats", beats_a)]
            # the same control read from the tables' own instrument, so the difference between
            # the two is a number in the paper and not something a reader has to notice
            # what the control read while this table was still the transcription's, kept so the
            # caption can say what moving the table to the compiled binaries repaired
            kt = csv("fifteen-k20.csv")
            if kt:
                import statistics as _st
                asis_t = [r for r in kt if r["variant"] == "as-is"]
                M += [("RevExpMeanMedianTranscription",
                       f"{_st.median(float(r['median_mm']) for r in asis_t):.2f}")]
            M += [("RevExpHalf", "0.5"), ("RevExpOneHalf", "1.5"), ("RevExpTwo", "2")]
            cim = agg.get("mean")
            cellm = f"{med_a:.2f}" if not cim else f"{med_a:.2f} [{float(cim['ci_lo_mm']):.2f}, {float(cim['ci_hi_mm']):.2f}]"
            rows.append(" & ".join(["mean", f"{out_a} of {tot_a:,}".replace(",", "{,}"),
                                    cellm, f"{beats_a} of {len(asis)}", "--", "0.00"])
                        + " \\\\")
        body("rev1-exponent.tex", rows)
        # the interior minimum, and what an argument for the smallest exponent would have to do.
        # The name says lowest and not best: the aggregate medians are not separated by their
        # intervals, so the only claim the evidence carries is which of them is the smallest.
        lowest = min(ps, key=lambda v: key[v]["med"])
        M += [("RevExpScrolls", key[ps[0]]["n"]), ("RevExpList", ", ".join(f"{v:g}" for v in ps)),
              ("RevExpLowest", f"{lowest:g}"),
              ("RevExpInterior", "interior" if ps[0] < lowest < ps[-1] else "at the edge"),
              ("RevExponentInteriorWord", "interior" if ps[0] < lowest < ps[-1] else "at the edge"),
              ("RevExpLow", f"{ps[0]:g}"), ("RevExpHigh", f"{ps[-1]:g}")]
        # p = 0.5 against p = 1, scroll by scroll, on the pre-registered threshold
        a = {r["scroll"]: float(r["median_mm"]) for r in ek if abs(float(r["p"]) - ps[0]) < 1e-12}
        one = {r["scroll"]: float(r["median_mm"]) for r in ek if abs(float(r["p"]) - 1.0) < 1e-12}
        worse = sum(a[s2] - one[s2] >= L.THRESHOLD_MM for s2 in a)
        better = sum(one[s2] - a[s2] >= L.THRESHOLD_MM for s2 in a)
        if agg:
            one_ci = agg["1"]
            lo1, hi1 = float(one_ci["ci_lo_mm"]), float(one_ci["ci_hi_mm"])
            others = [f"{v:g}" for v in ps if abs(v - 1.0) > 1e-12]
            clear = [t for t in others
                     if float(agg[t]["ci_hi_mm"]) < lo1 or float(agg[t]["ci_lo_mm"]) > hi1]
            overlap = [t for t in others if t not in clear]
            bet = {t: int(agg[t]["better_than_p1"]) for t in others}
            wor = {t: int(agg[t]["worse_than_p1"]) for t in others}
            M += [("RevExpCiLo", f"{lo1:.2f}"), ("RevExpCiHi", f"{hi1:.2f}"),
                  ("RevExpCiUnit", agg["1"]["bootstrap_unit"]),
                  ("RevExpCiClear", and_list(clear)), ("RevExpCiClearN", len(clear)),
                  ("RevExpCiOverlap", and_list(overlap)), ("RevExpCiOverlapN", len(overlap)),
                  ("RevExpBetterMax", max(bet.values())),
                  ("RevExpBetterMaxP", max(bet, key=lambda t: bet[t])),
                  ("RevExpWorseMin", min(wor.values())), ("RevExpWorseMax", max(wor.values()))]
        M += [("RevExpLowWorseOn", worse), ("RevExpLowBetterOn", better),
              ("RevExpLowBiasRatio", f"{key[1.0]['bias'] / key[ps[0]]['bias']:.1f}"),
              ("RevExpBarsAccuracyMin", 8)]

    # ---- reviewer's point 2: which scrolls had been measured before the criteria were written
    pt = csv("prereg-timeline.csv")
    if pt:
        q = {r["document"]: r for r in pt}
        f = q["preregistration-fifteen-references.md"]
        M += [("RevPreMeasuredPrimary", int(f["primary_measured_before"])),
              ("RevPreMeasuredPrimaryOf", int(f["primary_total"])),
              ("RevPreMeasuredPrimaryScrolls", ", ".join(f["primary_measured_before_scrolls"].split())),
              ("RevPreMeasuredConfirm", int(f["confirm_measured_before"])),
              ("RevPreUnmeasuredPrimary", int(f["primary_total"]) - int(f["primary_measured_before"])),
              ("RevPreFifteenWritten", f["stated_written"].replace("T", " ").replace("Z", "Z")),
              ("RevPreTwentyFourWritten", q["preregistration-twenty-four-scrolls.md"]["stated_written"]),
              ("RevPreTwentyFourSeeds", int(q["preregistration-twenty-four-scrolls.md"]["seeds_per_slice"])),
              ("RevPreTwentySeedsWritten", q["note-twenty-seeds.md"]["stated_written"].replace("T", " "))]

    # ---- reviewer's point 4: the asymmetry on all fifteen scrolls, and whether it orders them
    d15 = csv("density-asymmetry-fifteen.csv")
    ds = csv("density-asymmetry-fifteen-summary.csv")
    if d15 and ds:
        S = {(r["subset"], r["against"]): r for r in ds}
        def rho(subset, against, key):
            r = S[(subset, against)]
            M.extend([(f"RevAsym{key}Rho", f"{float(r['spearman_rho']):+.2f}"),
                      (f"RevAsym{key}P", f"{float(r['p_value']):.2f}"),
                      (f"RevAsym{key}N", int(r["n"]))])
        rho("fifteen", "estimator distance from reference", "FifteenErr")
        rho("fifteen", "margin over centroid", "FifteenMargin")
        rho("fifteen", "centroid distance from reference", "FifteenCentroid")
        rho("primary", "estimator distance from reference", "PrimaryErr")
        rho("confirmation", "estimator distance from reference", "ConfirmErr")
        ordered = sorted(d15, key=lambda r: float(r["sector_ratio_median"]))
        rank = {r["scroll"]: i + 1 for i, r in enumerate(ordered)}
        halves = sorted(d15, key=lambda r: float(r["dominant_half_fraction_median"]))
        for sc in ("PHerc0813", "PHerc1218", "PHerc0826"):
            r = next(q for q in d15 if q["scroll"] == sc)
            key = SCROLL_KEY[sc]
            M += [(f"RevAsym{key}Ratio", f"{float(r['sector_ratio_median']):.2f}"),
                  (f"RevAsym{key}Rank", rank[sc]),
                  (f"RevAsym{key}Half", f"{float(r['dominant_half_fraction_median']):.3f}"),
                  (f"RevAsym{key}SameHalf", f"{100 * float(r['same_half_plane_fraction']):.0f}"),
                  (f"RevAsym{key}Cos", f"{float(r['cosine_median']):.2f}")]
        M += [("RevAsymFifteenScrolls", len(d15)),
              ("RevAsymFifteenRatioLow", f"{float(ordered[0]['sector_ratio_median']):.2f}"),
              ("RevAsymFifteenRatioLowScroll", ordered[0]["scroll"]),
              ("RevAsymFifteenRatioHigh", f"{float(ordered[-1]['sector_ratio_median']):.2f}"),
              ("RevAsymFifteenRatioHighScroll", ordered[-1]["scroll"]),
              ("RevAsymFifteenRatioMedian", f"{float(ordered[len(ordered) // 2]['sector_ratio_median']):.2f}"),
              ("RevAsymHalfMaxScroll", halves[-1]["scroll"]),
              ("RevAsymHalfMax", f"{float(halves[-1]['dominant_half_fraction_median']):.3f}"),
              ("RevAsymHalfMin", f"{float(halves[0]['dominant_half_fraction_median']):.3f}"),
              ("RevAsymSameHalfMaxScroll", max(d15, key=lambda r: float(r["same_half_plane_fraction"]))["scroll"]),
              ("RevAsymSameHalfMax", f"{100 * max(float(r['same_half_plane_fraction']) for r in d15):.0f}"),
              ("RevAsymSameHalfMin", f"{100 * min(float(r['same_half_plane_fraction']) for r in d15):.0f}")]
        body("rev1-asymmetry-fifteen.tex",
             [f"{r['scroll']} & {float(r['sector_ratio_median']):.2f} & "
              f"{float(r['dominant_half_fraction_median']):.2f} & "
              f"{float(r['no_division_mm_table']):.2f} & {float(r['margin_vs_centroid_mm_table']):+.2f} & "
              f"{100 * float(r['same_half_plane_fraction']):.0f} \\\\" for r in d15])

    # ---- Meta C.1: the constant of the weight
    ss = csv("sensitivity-c-synthetic.csv")
    if ss:
        cs = sorted({float(r["c"]) for r in ss})
        M.append(("RevSensCs", ", ".join(f"{c:.0f}" for c in cs)))
        rows = []
        for sec in ("circle 1:1", "ellipse 1.4", "half circle", "density 1:10"):
            for obj in ("sum", "mean"):
                rr = sorted([r for r in ss if r["name"] == sec and r["objective"] == obj],
                            key=lambda r: float(r["c"]))
                if rr:
                    rows.append(f"{sec} & {obj} & " + " & ".join(
                        f"{float(r['err_median_units']):.0f}" for r in rr) + " \\\\")
                    for r in rr:
                        M.append((f"RevSensSyn{SEC[sec]}{obj.capitalize()}C{CNAME[int(float(r['c']))]}",
                                  f"{float(r['err_median_units']):.0f}"))
        body("rev1-sensitivity-synthetic.tex", rows)
    sc_ = csv("sensitivity-c-scrolls.csv")
    if sc_:
        import statistics
        cs = sorted({float(r["c"]) for r in sc_})
        n_scrolls = len({r["name"] for r in sc_})
        rows = []
        for c in cs:
            cells = []
            for obj in ("sum", "mean"):
                rr = [r for r in sc_ if float(r["c"]) == c and r["objective"] == obj]
                inside = sum(int(r["inside"]) for r in rr)
                allin = sum(int(r["inside"]) == int(r["n"]) for r in rr)
                jump = statistics.median(float(r["jump_med_pct"]) for r in rr)
                cen = statistics.median(float(r["centroid_med_pct"]) for r in rr)
                cells += [f"{inside}", f"{allin}", f"{jump:.2f}", f"{cen:.2f}"]
                tag = f"C{CNAME[int(c)]}{obj.capitalize()}"
                M += [(f"RevSensInside{tag}", inside), (f"RevSensAllInside{tag}", allin),
                      (f"RevSensJump{tag}", f"{jump:.2f}"), (f"RevSensCentroid{tag}", f"{cen:.2f}")]
            rows.append(f"{c:.0f} & " + " & ".join(cells) + " \\\\")
        body("rev1-sensitivity-scrolls.tex", rows)
        M += [("RevSensScrolls", n_scrolls),
              ("RevSensSlices", sum(int(r["n"]) for r in sc_ if float(r["c"]) == 100 and r["objective"] == "sum"))]

    # ---- Meta B: twenty seeds per slice
    # Two files, and which one a number comes from is the point. `k20t` is the transcription,
    # kept because the cap audit and the sampling audit are about the transcription and could not
    # be about anything else. `k20` is the shipped function, called through vc_gen_umbilicus over
    # the same slices and seeds with no cap at all: from 2026-09-18 the tables and the verdicts
    # are its numbers, and the ablations stay on the transcription.
    k20t = csv("fifteen-k20.csv")
    k20 = csv("cpp-k20.csv") or k20t
    if k20:
        vt = json.load(open(os.path.join(L.EV, "fifteen-k20-verdicts.json")))
        v = (json.load(open(os.path.join(L.EV, "cpp-k20-verdicts.json")))
             if os.path.exists(os.path.join(L.EV, "cpp-k20-verdicts.json")) else vt)
        ndt = [r for r in k20t if r["variant"] == "no-division"] if k20t else []
        old = json.load(open(os.path.join(L.EV, "frozen-verdicts.json")))
        for blk, key in (("primary", "Primary"), ("confirmation", "Confirm")):
            M += [(f"RevK{key}Scrolls", v[blk]["n"]), (f"RevK{key}Repaired", v[blk]["repaired"]),
                  (f"RevK{key}Beats", v[blk]["beats"]), (f"RevK{key}Loses", v[blk]["loses"]),
                  (f"RevK{key}RepairVerdict", v[blk]["repair"]),
                  (f"RevK{key}BeatVerdict", v[blk]["beat"]),
                  (f"RevK{key}ZeroMargins", len(v[blk]["margins_with_interval_including_zero"])),
                  (f"RevK{key}ZeroMarginScrolls",
                   ", ".join(v[blk]["margins_with_interval_including_zero"]) or "none")]
        changed = []
        for blk in ("primary", "confirmation"):
            if old[blk]["beat"] != v[blk]["beat"]:
                changed.append(f"{blk}: {old[blk]['beat']} to {v[blk]['beat']}")
            if ("won" if old[blk]["repair"] else "lost") != v[blk]["repair"]:
                changed.append(f"{blk} repair: changed")
        M += [("RevKVerdictsChanged", "; ".join(changed) if changed else "none"),
              ("RevKVerdictsChangedCount", len(changed)),
              ("RevKSeeds", int(k20[0]["seeds"])), ("RevKResamples", int(k20[0]["bootstrap_resamples"])),
              ("RevKBootSeed", str(k20[0]["bootstrap_seed"])),
              ("RevKInsideOf", int(k20[0]["inside_of"]))]
        nd = [r for r in k20 if r["variant"] == "no-division"]
        # The margins before rounding (tools/cpp_k20_margins.py, 2026-09-30, the referee's finding 3):
        # every count against the threshold or the spread is taken on them, since a margin printed
        # as 0.30 may not reach 0.30. A scroll missing from that file stops the run.
        _mg = {(q["scroll"], q["variant"]): float(q["margin_unrounded_mm"])
               for q in L.read_csv(os.path.join(L.EV, "cpp-k20-margins.csv"))}

        def mg(r):
            return _mg[(r["scroll"], r["variant"])]
        _r813 = next(r for r in nd if r["scroll"] == "PHerc0813")
        M += [("RevKZeroEightOneThreeMarginUnrounded", f"{mg(_r813):.4f}")]
        # the transcription's sample cap, found by the audit: what it changed, measured against the
        # frozen-sampling rerun kept beside it
        import csv as _csv
        mc = os.path.join(L.EV, "fifteen-k20-mincap.csv")
        if os.path.exists(mc):
            oldrows = {(q["scroll"], q["variant"]): q for q in L.read_csv(mc)}
            movedrows = [q for q in k20t if (q["scroll"], q["variant"]) in oldrows
                         and abs(float(oldrows[(q["scroll"], q["variant"])]["median_mm"]) - float(q["median_mm"])) > 0.005]
            me = os.path.join(L.EV, "k20-estimates-mincap.csv")
            movedest = totest = 0
            if os.path.exists(me):
                a = {(r["scroll"], r["z"], r["k"], r["variant"]): (float(r["x"]), float(r["y"])) for r in L.read_csv(me)}
                for r in L.read_csv(os.path.join(L.EV, "k20-estimates.csv")):
                    key = (r["scroll"], r["z"], r["k"], r["variant"])
                    if key in a:
                        totest += 1
                        movedest += abs(a[key][0] - float(r["x"])) > 1e-9 or abs(a[key][1] - float(r["y"])) > 1e-9
            M += [("RevKCapEstimatesMoved", movedest), ("RevKCapEstimatesTotal", totest),
                  ("RevKCapRowsMoved", len(movedrows)), ("RevKCapRowsTotal", len(k20t)),
                  ("RevKCapMovedScrolls", ", ".join(sorted({q["scroll"] for q in movedrows})) or "none")]
        # scrolls whose k = 0 row moved
        if ndt and "sparse_slices" in k20t[0]:
            moved = [r for r in ndt if int(r["sparse_slices"]) and abs(float(r["frozen_k0_mm"]) - float(r["median_k0_mm"])) > 0.011]
            M += [("RevKSparseScrolls", ", ".join(f"{r['scroll']} ({r['sparse_slices']} of {r['slices']} slices)" for r in ndt if int(r["sparse_slices"])) or "none"),
                  ("RevKSparseSliceTotal", sum(int(r["sparse_slices"]) for r in ndt)),
                  ("RevKMovedScrolls", "; ".join(f"{r['scroll']} from {float(r['frozen_k0_mm']):.2f} to {float(r['median_k0_mm']):.2f} mm" for r in moved) or "none")]
        M += [("RevKMaxIqr", max(float(r["iqr_mm"]) for r in nd)),
              ("RevKMaxIqrScroll", max(nd, key=lambda r: float(r["iqr_mm"]))["scroll"]),
              ("RevKZeroMarginsTotal", sum(int(r["margin_ci_includes_zero"]) for r in nd
                                          if mg(r) >= L.THRESHOLD_MM)),
              ("RevKWonTotal", sum(1 for r in nd if mg(r) >= L.THRESHOLD_MM))]
        # the predictions of inputs/note-twenty-seeds.md, checked rather than narrated
        byS = {r["scroll"]: r for r in nd}
        pred_zero = [s for s in ("PHerc0125", "PHerc0332") if int(byS[s]["margin_ci_includes_zero"])]
        M += [("RevKPredZeroHeld", len(pred_zero)),
              ("RevKZeroEightTwoSixZero", "includes" if int(byS["PHerc0826"]["margin_ci_includes_zero"]) else "excludes"),
              ("RevKTwoOneOneZero", "includes" if int(byS["PHerc0211"]["margin_ci_includes_zero"]) else "excludes")]
        asis_by = {r["scroll"]: r for r in k20 if r["variant"] == "as-is"}
        for r in nd:
            key = SCROLL_KEY[r["scroll"]]
            a = asis_by[r["scroll"]]
            M += [(f"RevK{key}AsIs", float(a["median_mm"])),
                  (f"RevK{key}OutsideAsIs", int(a["inside_of"]) - int(a["inside"])),
                  (f"RevK{key}OutsideFixed", int(r["inside_of"]) - int(r["inside"]))]
            M += [(f"RevK{key}Median", float(r["median_mm"])), (f"RevK{key}Lo", float(r["ci_lo_mm"])),
                  (f"RevK{key}Hi", float(r["ci_hi_mm"])), (f"RevK{key}Margin", float(r["margin_vs_centroid_mm"])),
                  (f"RevK{key}MarginLo", float(r["margin_ci_lo_mm"])),
                  (f"RevK{key}MarginHi", float(r["margin_ci_hi_mm"])),
                  (f"RevK{key}Centroid", float(r["centroid_mm"]))]
        # ---- the reference spread: rows whose margin falls under it are marked in the tables, as
        # preregistration-fifteen-references.md section 6 prescribes. The comparison value is the frozen
        # run's own macro; no verdict, threshold or count of wins moves with it.
        # What the value is, corrected on 2026-09-19: not the distance between two independent
        # annotations, which no scroll carries, but the distance on PHerc1218 between the hand
        # annotation and an umbilicus derived from sheet instance labels, which make_umbilicus.py
        # of vesuvius-sheet-tools builds as the papyrus centroid of each slice. It is a hand
        # against a mask centroid, and it sits within a fifth of a millimetre of the centroid
        # baseline these same tables carry: tools/second_reference.py measures that overlap, and
        # the article says so where it uses the number. The macro names are left as they were,
        # because umbilicus-numbers.tex is written by the frozen paper's own generator,
        # which is not in this folder and cannot be re-run from it.
        spread = umb("UmbReferenceSpread")
        M += [("RevSpreadOverThreshold", f"{spread / L.THRESHOLD_MM:.0f}"),
              ("RevSpreadRounded", f"{spread:.1f}")]
        frozen = {r["scroll"]: r for r in (csv("fifteen.csv") or [])}
        crossings = []
        for blk, key in (("primary", "Primary"), ("confirmation", "Confirm")):
            b = [r for r in nd if r["block"] == blk]
            won = [r for r in b if mg(r) >= L.THRESHOLD_MM]
            over = [r for r in won if mg(r) >= spread]
            under = [r for r in won if mg(r) < spread]
            M += [(f"RevK{key}MarginsWon", len(won)),
                  (f"RevK{key}UnderSpread", len(under)), (f"RevK{key}OverSpread", len(over)),
                  (f"RevK{key}BelowSpread",
                   sum(mg(r) < spread for r in b)),
                  (f"RevK{key}OverSpreadUm",
                   int(round(min((mg(r) - spread) * 1000 for r in over)))
                   if over else "none")]
            for r in b:
                f0 = frozen.get(r["scroll"])
                if not f0:
                    continue
                now, then = mg(r), float(f0["margin_vs_centroid_mm"])
                if (now >= spread) != (then >= spread):
                    crossings.append(f"{r['scroll']}, from {then:.2f} to {now:.2f} mm")
        # the same three counts over both blocks, for the abstract, which cannot carry a block
        won_all = [r for r in nd if mg(r) >= L.THRESHOLD_MM]
        M += [("RevKUnderSpreadTotal", sum(mg(r) < spread for r in won_all)),
              ("RevKOverSpreadTotal", sum(mg(r) >= spread for r in won_all)),
              ("RevKBelowSpreadTotal", sum(mg(r) < spread for r in nd)),
              ("RevKSpreadCrossings", "; ".join(crossings) if crossings else "none"),
              ("RevKSpreadCrossingCount", len(crossings))]

        # ---- how far the published estimator lands when it fails, the three worst rows
        asis = sorted((r for r in k20 if r["variant"] == "as-is"),
                      key=lambda r: float(r["median_mm"]), reverse=True)
        for tag, r in zip(("One", "Two", "Three"), asis[:3]):
            M += [(f"RevKAsIsWorst{tag}", float(r["median_mm"])),
                  (f"RevKAsIsWorst{tag}Scroll", r["scroll"])]
        M += [("RevTensMm", int(TENS_MM)),
              ("RevKAsIsTensOfMm", sum(float(r["median_mm"]) >= TENS_MM for r in asis)),
              ("RevKFixedTensOfMm", sum(float(r["median_mm"]) >= TENS_MM for r in nd)),
              ("RevKScrolls", len(nd))]

        for blk, name in (("primary", "rev1-k20-primary.tex"), ("confirmation", "rev1-k20-confirm.tex")):
            rows = []
            for s in [q["scroll"] for q in nd if q["block"] == blk]:
                a = next(q for q in k20 if q["scroll"] == s and q["variant"] == "as-is")
                b = next(q for q in k20 if q["scroll"] == s and q["variant"] == "no-division")
                marks = ("\\circ" if int(b["margin_ci_includes_zero"]) else "") \
                    + ("\\dagger" if mg(b) < spread else "")
                flag = f"$^{{{marks}}}$" if marks else ""
                rows.append(
                    f"{s} & {b['control_points']} & {float(a['median_mm']):.2f} & "
                    f"\\textbf{{{float(b['median_mm']):.2f}}} [{float(b['ci_lo_mm']):.2f}, {float(b['ci_hi_mm']):.2f}] & "
                    f"{float(b['centroid_mm']):.2f} & "
                    f"{float(b['fake_axis_mm']):.2f} & "
                    f"{float(b['margin_vs_centroid_mm']):+.2f} [{float(b['margin_ci_lo_mm']):+.2f}, {float(b['margin_ci_hi_mm']):+.2f}]{flag} & "
                    f"{int(a['inside_of']) - int(a['inside'])} to {int(b['inside_of']) - int(b['inside'])} \\\\")
            body(name, rows)

        # ---- the tables are the shipped function's, and this block says what that cost and what
        # it changed against the transcription that produced them before 2026-09-18
        cmp_rows = csv("cpp-vs-transcription.csv")
        # What the calls cost, counted from the per call seconds of cpp-k20-estimates.csv, which
        # cpp_k20.py wrote, and the guard from the constant that run used (the declaration's): the
        # hand written cpp-k20-cost.csv is no longer read, and the wall time and worker count it
        # carried from a log this folder does not ship are no longer printed (referee 2026-09-30,
        # finding 10).
        est_c = csv("cpp-k20-estimates.csv") or []
        if cmp_rows and est_c:
            import importlib.util as _iu
            _spec = _iu.spec_from_file_location("cpp_k20", os.path.join(os.path.dirname(REV1), "tools", "cpp_k20.py"))
            _ck = _iu.module_from_spec(_spec)
            _spec.loader.exec_module(_ck)
            _sec = [float(r["seconds"]) for r in est_c]
            sum_rows = [r for r in cmp_rows if r["variant"] == "no-division"]
            asis_rows = [r for r in cmp_rows if r["variant"] == "as-is"]
            worst_sum = max(sum_rows, key=lambda r: abs(float(r["delta_mm"])))
            worst_asis = max(asis_rows, key=lambda r: abs(float(r["delta_mm"])))
            deltas = sorted(abs(float(r["delta_mm"])) for r in sum_rows)
            flag_rows = [r for r in cmp_rows
                         if not int(r["agree"])]
            M += [("RevCppEstimates", f"{len(est_c):,}"),
                  ("RevCppCoreHours", f"{sum(_sec) / 3600:.2f}"),
                  ("RevCppMeanSeconds", f"{sum(_sec) / len(_sec):.2f}"),
                  ("RevCppWorstSeconds", f"{max(_sec):.2f}"),
                  ("RevCppGuardSeconds", int(_ck.GUARD_S)),
                  ("RevCppGuardHits", sum(int(r["guard"]) for r in est_c)),
                  ("RevCppRowsAgree", sum(int(r["agree"]) for r in cmp_rows)),
                  ("RevCppRowsTotal", len(cmp_rows)),
                  ("RevCppSumRowsAgree", sum(int(r["agree"]) for r in sum_rows)),
                  ("RevCppSumRowsTotal", len(sum_rows)),
                  ("RevCppSumWorstMove", f"{abs(float(worst_sum['delta_mm'])):.2f}"),
                  ("RevCppSumWorstScroll", worst_sum["scroll"]),
                  ("RevCppSumWorstFrom", f"{float(worst_sum['median_py_mm']):.2f}"),
                  ("RevCppSumWorstTo", f"{float(worst_sum['median_cpp_mm']):.2f}"),
                  ("RevCppSumMedianMove", f"{deltas[len(deltas) // 2]:.2f}"),
                  ("RevCppAsIsWorstMove", f"{abs(float(worst_asis['delta_mm'])):.2f}"),
                  ("RevCppAsIsWorstScroll", worst_asis["scroll"]),
                  ("RevCppFlagRows", len(flag_rows)),
                  ("RevCppFlagScrolls", ", ".join(r["scroll"] for r in flag_rows) or "none")]
            # ---- in bounds, counted over every single call of the recomputation, per OBJECTIVE.
            # This is the paper's central claim measured on the shipped function, and it is
            # counted here from the raw estimates rather than summed out of the row summaries,
            # so that no phrase can carry a count from one objective to the other.
            est = csv("cpp-k20-estimates.csv")
            if est:
                live = [r for r in est if not int(r["guard"])]
                per = {}
                for r in live:
                    key = (r["variant"], r["scroll"])
                    a, b = per.get(key, (0, 0))
                    per[key] = (a + int(r["inside"]), b + 1)
                for variant, tag in (("as-is", "AsIs"), ("no-division", "Sum")):
                    ins = sum(a for k, (a, b) in per.items() if k[0] == variant)
                    tot = sum(b for k, (a, b) in per.items() if k[0] == variant)
                    M += [(f"RevCppInside{tag}", f"{ins:,}"), (f"RevCppOutside{tag}", f"{tot - ins:,}"),
                          (f"RevCppInside{tag}Of", f"{tot:,}")]
                worst = sorted((k[1], a, b) for k, (a, b) in per.items() if k[0] == "as-is")
                worst.sort(key=lambda t: t[1])
                for tag, (name, a, b) in zip(("One", "Two"), worst[:2]):
                    M += [(f"RevCppInsideWorst{tag}", name),
                          (f"RevCppInsideWorst{tag}In", a), (f"RevCppInsideWorst{tag}Of", b)]
                M += [("RevCppScrollsMeasured", len({k[1] for k in per}))]
                # every call to the shipped function this paper rests on, across the three runs
                tot_all = len(live)
                # every role of the 24-scroll run, the spread seeds included (referee 2026-09-30,
                # finding 13: the position filter left 1,152 compiled calls out of the total)
                for extra, role in (("cpp-positions-24.csv", None),
                                    ("cpp-exponent-estimates.csv", None)):
                    rows_x = csv(extra) or []
                    tot_all += sum(1 for q in rows_x if not int(q["guard"])
                                   and (role is None or q.get("role") == role))
                # The worst row of the weighted sum IN THE COMPILED TABLES, for the two places
                # in the text that read it beside those tables. RevAblBWorst is the same quantity
                # in the search ablation, which is the transcription's, and stays there: one
                # macro was doing both jobs and the two tables disagree by design.
                sum_rows_k = [r for r in k20 if r["variant"] == "no-division"]
                wk = max(sum_rows_k, key=lambda r: float(r["median_mm"]))
                M += [("RevKSumWorst", f"{float(wk['median_mm']):.2f}"),
                      ("RevKSumWorstScroll", wk["scroll"])]
                M += [("RevCppAllEstimates", f"{tot_all:,}"),
                      ("RevCppAllGuardHits",
                       sum(int(q["guard"]) for name in ("cpp-k20-estimates.csv",
                                                        "cpp-positions-24.csv",
                                                        "cpp-exponent-estimates.csv")
                           for q in (csv(name) or [])))]
            # the one row that crosses a threshold, and it crosses in our favour, so it is named
            crossed = [r for r in sum_rows
                       if (float(r["margin_py_mm"]) <= -L.THRESHOLD_MM)
                       != (float(r["margin_cpp_mm"]) <= -L.THRESHOLD_MM)]
            M += [("RevCppLosesTranscription", vt["confirmation"]["loses"]),
                  ("RevCppLosesShipped", v["confirmation"]["loses"]),
                  ("RevCppLosesScroll", ", ".join(r["scroll"] for r in crossed) or "none"),
                  ("RevCppLosesFrom", f"{float(crossed[0]['margin_py_mm']):+.2f}" if crossed else "none"),
                  ("RevCppLosesTo", f"{float(crossed[0]['margin_cpp_mm']):+.2f}" if crossed else "none")]
    kn = csv("k20-search-noise.csv")
    if kn:
        r = next(q for q in kn if q["scroll"] == "PHerc0125" and int(q["slice_z"]) == 6891
                 and q["variant"] == "no-division")
        M += [("RevKNoiseTranscription", float(r["spread_median_mm"])),
              ("RevKNoiseCpp", float(r["cpp_spread_median_mm"]))]

    # ---- post hoc: two more rules of the bench on the same slices
    # The two blocks are written to two bodies and never pooled, as Tables II and III are. The
    # deciding rule is the pre-registered threshold applied to the best of the three simple rules
    # on each scroll, which is the strictest reading of the question and the only one that keeps a
    # margin of a hundredth of a millimetre out of the count of wins.
    bl = csv("baselines-k20.csv")
    if bl and k20:
        by = {}
        for r in bl:
            by.setdefault(r["scroll"], {})[r["rule"]] = r
        nd = {q["scroll"]: q for q in k20 if q["variant"] == "no-division"}
        pl_better = pl_better_untuned = ax_better = 0
        won, lost, neither, pooled = [], [], [], []
        bodies = {"primary": [], "confirmation": []}
        for s in L.CFG:
            if s not in by:
                continue
            q, v = by[s], nd[s]
            pl, ax = q["plateau_nearest_centroid"], q["argmax"]
            mark = "$^{t}$" if int(pl["tuned_on_this_scroll"]) else ""
            best = min((q[r] for r in ("centroid", "plateau_nearest_centroid", "argmax")),
                       key=lambda r: float(r["median_mm"]))
            gap = float(best["median_mm"]) - float(v["median_mm"])
            cells = (f"{s} & \\textbf{{{float(v['median_mm']):.2f}}} [{float(v['ci_lo_mm']):.2f}, {float(v['ci_hi_mm']):.2f}] & "
                     f"{float(v['centroid_mm']):.2f} & "
                     f"{float(pl['median_mm']):.2f} [{float(pl['ci_lo_mm']):.2f}, {float(pl['ci_hi_mm']):.2f}]{mark} & "
                     f"{float(ax['median_mm']):.2f} [{float(ax['ci_lo_mm']):.2f}, {float(ax['ci_hi_mm']):.2f}]")
            # the long paper of this tree keeps one pooled table of five columns; the short paper
            # keeps the two blocks apart and adds the margin, so both bodies are written
            pooled.append(cells + " \\\\")
            bodies[q["centroid"]["block"]].append(cells + f" & {gap:+.2f} \\\\")
            (won if gap >= L.THRESHOLD_MM else lost if gap < 0 else neither).append((s, q, v, best, gap))
            if float(pl["median_mm"]) < float(v["median_mm"]):
                pl_better += 1
                pl_better_untuned += not int(pl["tuned_on_this_scroll"])
            ax_better += float(ax["median_mm"]) < float(v["median_mm"])
        body("rev1-baselines.tex", pooled)
        body("rev1-baselines-primary.tex", bodies["primary"])
        body("rev1-baselines-confirm.tex", bodies["confirmation"])
        blocks = {"primary": "Primary", "confirmation": "Confirm"}
        M += [("RevBlDeclared", BASELINES_DECLARED),
              ("RevBlScrolls", len(by)), ("RevBlPlateauBetter", pl_better),
              ("RevBlPlateauBetterUntuned", pl_better_untuned),
              ("RevBlPlateauBetterScrolls", ", ".join(s for s in L.CFG if s in by and float(by[s]["plateau_nearest_centroid"]["median_mm"]) < float(nd[s]["median_mm"])) or "none"),
              ("RevBlArgmaxBetter", ax_better),
              ("RevBlTuned", sum(1 for s in by if int(by[s]["plateau_nearest_centroid"]["tuned_on_this_scroll"]))),
              ("RevBlTunedScrolls", and_list([s for s in L.CFG if s in by and int(by[s]["plateau_nearest_centroid"]["tuned_on_this_scroll"])])),
              ("RevBlUntuned", sum(1 for s in by if not int(by[s]["plateau_nearest_centroid"]["tuned_on_this_scroll"])))]
        for blk, key in blocks.items():
            M += [(f"RevBl{key}Won", sum(1 for w in won if w[1]["centroid"]["block"] == blk)),
                  (f"RevBl{key}Of", sum(1 for s in by if by[s]["centroid"]["block"] == blk)),
                  (f"RevBl{key}Lost", sum(1 for w in lost if w[1]["centroid"]["block"] == blk))]
        # every loss, in the order of the blocks, with the rule that takes it and the gap read
        # against the reference spread of PHerc1218, which is a hand against a mask centroid
        spread = umb("UmbReferenceSpread")
        M.append(("RevBlLosses", len(lost)))
        for tag, (s, q, v, best, gap) in zip(("One", "Two", "Three", "Four"), lost):
            M += [(f"RevBlLoss{tag}Scroll", s),
                  (f"RevBlLoss{tag}Fixed", float(v["median_mm"])),
                  (f"RevBlLoss{tag}Lo", float(v["ci_lo_mm"])),
                  (f"RevBlLoss{tag}Hi", float(v["ci_hi_mm"])),
                  (f"RevBlLoss{tag}Rule", RULE_NAME[best["rule"]]),
                  (f"RevBlLoss{tag}Best", float(best["median_mm"])),
                  (f"RevBlLoss{tag}BestLo", float(best["ci_lo_mm"])),
                  (f"RevBlLoss{tag}BestHi", float(best["ci_hi_mm"])),
                  (f"RevBlLoss{tag}Gap", abs(gap)),
                  (f"RevBlLoss{tag}Tuned", "tuned" if int(best["tuned_on_this_scroll"]) else "untuned"),
                  (f"RevBlLoss{tag}VsSpread", "smaller" if abs(gap) < spread else "larger")]
        M.append(("RevBlNeither", len(neither)))
        for tag, (s, q, v, best, gap) in zip(("One", "Two"), neither):
            M += [(f"RevBlNeither{tag}Scroll", s),
                  (f"RevBlNeither{tag}Fixed", float(v["median_mm"])),
                  (f"RevBlNeither{tag}Best", float(best["median_mm"])),
                  (f"RevBlNeither{tag}Rule", RULE_NAME[best["rule"]]),
                  (f"RevBlNeither{tag}Gap", abs(gap))]

    # ---- post hoc: the same question inside the umbilicus bench, on the bench's own sample
    bn = csv("bench-rules.csv")
    if bn and k20:
        bb = {}
        for r in bn:
            bb.setdefault(r["scroll"], {})[r["rule"]] = r
        masks = sorted({r["rule"] for r in bn if r["input"] == "mask"})
        away = [s for s in bb if int(bb[s]["villa as published"]["outside"])]
        fixed_out = sum(int(bb[s]["villa no division"]["outside"]) for s in bb)
        fixed_of = sum(int(bb[s]["villa no division"]["estimates"]) for s in bb)
        one = next(iter(bb.values()))["villa no division"]
        M += [("RevBenchScrolls", len(bb)), ("RevBenchHeights", int(one["heights"])),
              ("RevBenchLevel", int(one["level"])), ("RevBenchMaskRules", len(masks)),
              ("RevBenchOutsideOf", int(one["estimates"])),
              ("RevBenchAway", len(away)),
              ("RevBenchAwayScrolls", and_list(away)),
              ("RevBenchAwayCounts", and_list([bb[s]["villa as published"]["outside"] for s in away])),
              ("RevBenchStays", and_list([s for s in bb if s not in away])),
              ("RevBenchFixedOutside", fixed_out), ("RevBenchFixedOf", fixed_of)]
        # the scroll the repaired estimator loses on here, and by how many rules
        worst = max(bb, key=lambda s: sum(float(bb[s][m]["median_mm"]) < float(bb[s]["villa no division"]["median_mm"])
                                          for m in masks))
        w = bb[worst]
        beaten = [m for m in masks if float(w[m]["median_mm"]) < float(w["villa no division"]["median_mm"])]
        best_m = min(beaten, key=lambda m: float(w[m]["median_mm"]))
        M += [("RevBenchLossScroll", worst),
              ("RevBenchLossFixed", float(w["villa no division"]["median_mm"])),
              ("RevBenchLossBeaten", len(beaten)),
              ("RevBenchLossRule", RULE_NAME[best_m]),
              ("RevBenchLossBest", float(w[best_m]["median_mm"]))]
        # the two samples do not mix: the same centroid code on the same scroll, both samples
        c_here = {q["scroll"]: float(q["centroid_mm"]) for q in k20 if q["variant"] == "no-division"}
        gaps = {s: (float(bb[s]["centroid"]["median_mm"]), c_here[s]) for s in bb if s in c_here}
        s = max(gaps, key=lambda s: abs(gaps[s][0] - gaps[s][1]))
        M += [("RevBenchGapScroll", s), ("RevBenchGapThere", gaps[s][0]),
              ("RevBenchGapHere", gaps[s][1]), ("RevBenchGap", abs(gaps[s][0] - gaps[s][1])),
              ("RevBenchGapVsThreshold",
               "larger" if abs(gaps[s][0] - gaps[s][1]) > L.THRESHOLD_MM else "smaller")]

    # ---- Meta C.2: the ablation
    ab = csv("ablation-search.csv")
    if ab:
        by = {}
        for r in ab:
            by.setdefault(r["scroll"], {})[r["cell"]] = r
        rows = []
        for s in L.CFG:
            if s not in by:
                continue
            q = by[s]
            rows.append(f"{s} & " + " & ".join(
                f"{float(q[c]['median_mm']):.2f} [{float(q[c]['ci_lo_mm']):.2f}, {float(q[c]['ci_hi_mm']):.2f}]"
                for c in "abcd") + " \\\\")
        # An ablation is measured on the instrument that can ablate the thing: columns (c) and
        # (d) replace the search, which the shipped function does not let anyone replace, so this
        # table is the transcription's, controls included. That makes its columns (a) and (b) the
        # same quantity as Tables II and III by a different instrument, and the paper says by how
        # much rather than leaving a reader to find it.
        k20cmp = csv("cpp-k20.csv")
        if k20cmp:
            tab = {(r["scroll"], r["variant"]): r for r in k20cmp}
            moved, worst = 0, 0.0
            for s_ in by:
                for cell, variant in (("a", "as-is"), ("b", "no-division")):
                    t = tab.get((s_, variant))
                    if not t or cell not in by[s_]:
                        continue
                    d = abs(float(by[s_][cell]["median_mm"]) - float(t["median_mm"]))
                    moved += d > 0.005
                    worst = max(worst, d)
            M += [("RevAblControlRowsMoved", moved),
                  ("RevAblControlRowsOf", 2 * len(by)),
                  ("RevAblControlWorstMove", f"{worst:.2f}")]
        body("rev1-ablation.tex", rows)
        # column (d) against column (b), the comparison a referee asked for on 2026-09-18: the
        # sign on every scroll, the size of the difference, and how many reach the threshold the
        # rest of the paper decides on
        import statistics as _st
        db = [float(q["d"]["median_mm"]) - float(q["b"]["median_mm"]) for q in by.values()]
        d_over = [(s2, float(q["b"]["median_mm"]) - float(q["d"]["median_mm"]))
                  for s2, q in by.items()
                  if float(q["b"]["median_mm"]) - float(q["d"]["median_mm"]) >= L.THRESHOLD_MM]
        b_over = [(s2, float(q["d"]["median_mm"]) - float(q["b"]["median_mm"]))
                  for s2, q in by.items()
                  if float(q["d"]["median_mm"]) - float(q["b"]["median_mm"]) >= L.THRESHOLD_MM]
        M += [("RevAblDWorseThanB", sum(x > 0 for x in db)),
              ("RevAblDEqualB", sum(abs(x) < 5e-3 for x in db)),
              ("RevAblDMedianGain", f"{-_st.median(db):.2f}"),
              ("RevAblDBestGain", f"{-min(db):.2f}"),
              ("RevAblDWorstLoss", f"{max(db):.2f}"),
              ("RevAblDOverThreshold", len(d_over)),
              ("RevAblDOverThresholdScrolls", and_list([x[0] for x in d_over])),
              ("RevAblBOverThreshold", len(b_over)),
              ("RevAblBOverThresholdScrolls", and_list([x[0] for x in b_over])),
              ("RevAblBMedianOfScrolls", f"{_st.median(float(q['b']['median_mm']) for q in by.values()):.2f}"),
              ("RevAblDMedianOfScrolls", f"{_st.median(float(q['d']['median_mm']) for q in by.values()):.2f}"),
              ("RevAblScrolls", len(by)),
              ("RevAblCBetterThanB", sum(float(q["c"]["median_mm"]) < float(q["b"]["median_mm"]) for q in by.values())),
              ("RevAblDBetterThanB", sum(float(q["d"]["median_mm"]) < float(q["b"]["median_mm"]) for q in by.values())),
              ("RevAblABetterThanC", sum(float(q["a"]["median_mm"]) < float(q["c"]["median_mm"]) for q in by.values())),
              ("RevAblCInside", sum(int(q["c"]["inside"]) for q in by.values())),
              ("RevAblAInside", sum(int(q["a"]["inside"]) for q in by.values())),
              ("RevAblInsideOf", sum(int(q["a"]["inside_of"]) for q in by.values())),
              ("RevAblCBeatsCentroid", sum(float(q["c"]["margin_vs_centroid_mm"]) >= L.THRESHOLD_MM for q in by.values())),
              ("RevAblDBeatsCentroid", sum(float(q["d"]["margin_vs_centroid_mm"]) >= L.THRESHOLD_MM for q in by.values())),
              ("RevAblBBeatsCentroid", sum(float(q["b"]["margin_vs_centroid_mm"]) >= L.THRESHOLD_MM for q in by.values()))]
        # how many scrolls each cell still leaves tens of millimetres from the reference, counted
        # rather than described in words
        for c in "abcd":
            M += [(f"RevAbl{c.upper()}TensOfMm",
                   sum(float(q[c]["median_mm"]) >= TENS_MM for q in by.values())),
                  (f"RevAbl{c.upper()}Worst", round(max(float(q[c]["median_mm"]) for q in by.values()), 2))]

    # ---- Meta D: downstream spiral fitting
    sp = csv("spiral-downstream.csv")
    if sp:
        for r in sp:
            k = r["tag"]
            M += [(f"RevSpiral{k}Source", r["umbilicus"]),
                  (f"RevSpiral{k}Iterations", int(float(r["iterations"] or 0))),
                  (f"RevSpiral{k}Hours", f"{float(r['hours']):.1f}" if r["hours"] else "not run"),
                  (f"RevSpiral{k}Shift", r["median_shift_spacings"]),
                  (f"RevSpiral{k}ShiftAlt", r["median_shift_spacings_alt"]),
                  (f"RevSpiral{k}Relabel", r["relabel_k"]),
                  (f"RevSpiral{k}ShiftRelabeled", r["median_shift_relabeled_spacings"]),
                  (f"RevSpiral{k}Windings", r["windings_common"]),
                  (f"RevSpiral{k}Outcome", r["outcome"]),
                  (f"RevSpiral{k}AxisMm", r["axis_distance_from_reference_mm"])]
        with_ratio = [r for r in sp if r["shift_over_axis"] not in ("", None)]
        if with_ratio:
            rr = [float(r["shift_over_axis"]) for r in with_ratio]
            M += [("RevSpiralRatioLow", f"{min(rr):.2f}"), ("RevSpiralRatioHigh", f"{max(rr):.2f}"),
                  ("RevSpiralRatioRuns", len(rr)),
                  ("RevSpiralAxisRangeLow", f"{min(float(r['axis_distance_from_reference_mm']) for r in with_ratio):.2f}"),
                  ("RevSpiralAxisRangeHigh", f"{max(float(r['axis_distance_from_reference_mm']) for r in with_ratio):.1f}"),
                  ("RevSpiralOneSheetMm", f"{16.0 * 9.362 / 1000:.3f}")]
        body("rev1-spiral.tex", [f"{r['label']} & {r['axis_distance_from_reference_mm']} & "
                                f"{r['axis_distance_spacings']} & {r['windings_common']} & "
                                f"{r['median_shift_spacings']} & {r['median_shift_relabeled_spacings']} & "
                                f"{r['shift_over_axis'] or '--'} \\\\" for r in sp])

    ai = csv("axis-identifiability.csv")
    if ai:
        by = {r["run"]: r for r in ai}
        for k, r in by.items():
            M += [(f"RevIdent{k}Loss", f"{float(r['loss_median_last30']):.1f}"),
                  (f"RevIdent{k}LossEarly", f"{float(r['loss_median_before_dt']):.1f}"),
                  (f"RevIdent{k}Satisfied", int(r["satisfied_patches"])),
                  (f"RevIdent{k}Area", f"{float(r['satisfied_area_fraction']):.2f}")]
        best = min(ai, key=lambda r: float(r["loss_median_last30"]))
        M += [("RevIdentBestRun", best["run"]), ("RevIdentBestAxis", best["axis_distance_mm"]),
              ("RevIdentPatches", int(ai[0]["total_patches"])),
              ("RevIdentSatisfiedLow", min(int(r["satisfied_patches"]) for r in ai)),
              ("RevIdentSatisfiedHigh", max(int(r["satisfied_patches"]) for r in ai)),
              ("RevIdentAreaLow", f"{min(float(r['satisfied_area_fraction']) for r in ai):.2f}"),
              ("RevIdentAreaHigh", f"{max(float(r['satisfied_area_fraction']) for r in ai):.2f}")]

    # The spiral noise floor block of the working tree's generator is not here: its evidence
    # file is a study this folder does not carry, and no macro of this article expands from it.

    # ---- The patch itself (the short paper on the one line): the regression test's tolerances,
    # read from the villa clone that carries the commit, against the p90 over seeds of the density
    # table they were derived from, so that the paper states the tolerance the test holds and the
    # ratio it keeps to the measured spread instead of retyping either.
    VILLA_PATCH = (os.environ.get("VILLA_FORK") or os.environ.get("VILLA_UPSTREAM")
                   or "/data/repositories/villa")
    TEST = "volume-cartographer/core/test/test_normalgridtools.cpp"
    # The branch carries more than the patch now, so the commit is found by what it touches and
    # not by its position: only the patch commit changes core/src/normalgridtools.cpp. Reading
    # HEAD instead gave the driver commit on 2026-09-18, with two files and no test case, which
    # is a different commit entirely and would have been printed as the patch.
    SRC = "volume-cartographer/core/src/normalgridtools.cpp"
    try:
        # The commit is pinned; the clone is asked only whether it changes the source file,
        # which is what identified it when it was found by what it touches.
        ph = PATCH_COMMIT
        touched = subprocess.check_output(
            ["git", "-C", VILLA_PATCH, "show", "--name-only", "--format=", ph],
            text=True, stderr=subprocess.DEVNULL).split()
        if SRC not in touched:
            raise SystemExit(f"rev1_numbers: {ph[:9]} does not change {SRC} in {VILLA_PATCH}")
        # The tree, beside the commit. A commit hash changes whenever the message is reworded,
        # and this one has been amended twice already; the tree is what the measurements were
        # made on, so the paper names both and a rewording cannot make it false.
        tree = subprocess.check_output(["git", "-C", VILLA_PATCH, "rev-parse", ph + "^{tree}"],
                                       text=True, stderr=subprocess.DEVNULL).strip()
        test_src = subprocess.check_output(["git", "-C", VILLA_PATCH, "show", f"{ph}:{TEST}"],
                                           text=True, stderr=subprocess.DEVNULL)
        stat = subprocess.check_output(["git", "-C", VILLA_PATCH, "show", "--numstat",
                                        "--format=", ph], text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        ph, test_src, stat = "", "", ""
    if test_src and sd:
        M += [("RevPatchCommit", ph), ("RevPatchShort", ph[:9]),
              ("RevPatchTree", tree), ("RevPatchTreeShort", tree[:8]),
              ("RevPatchFiles", len([ln for ln in stat.splitlines() if ln.strip()]))]
        unit_mm = float(re.search(r"kUnitMm\s*=\s*([0-9.]+)", test_src).group(1))
        tols = [float(t) for t in re.findall(r"errorMm\(u\)\s*<\s*([0-9.]+)", test_src)]
        # the test cases the commit adds, counted on its own diff and not on the whole file, which
        # already held two cases on the empty grid
        try:
            diff = subprocess.check_output(["git", "-C", VILLA_PATCH, "show", "--format=", ph,
                                            "--", TEST], text=True, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            diff = ""
        M.append(("RevTestCasesAdded", len(re.findall(r"^\+TEST_CASE\(", diff, re.M))))
        # the three sections the test asserts on, in the order its cases are written
        order = [("circle 1:1", "CircleOne"), ("half circle", "Half"), ("density 1:10", "DensTen")]
        ratios = []
        for (sec, key), tol in zip(order, tols):
            r = [q for q in sd if q["section"] == sec and q["objective"] == "sum"][0]
            p90 = float(r["estimate_err_p90_units"]) * unit_mm
            ratios.append(tol / p90)
            M += [(f"RevTestTol{key}", f"{tol:.1f}"), (f"RevDens{key}SumEstPNinetyMm", f"{p90:.2f}")]
        M += [("RevTestTolMinRatio", f"{min(ratios):.2f}"), ("RevTestTolSections", len(tols))]

    # ---- the regression test as built and run here (audit of 2026-09-17, TEST-NORMALGRID.md)
    tr = csv("regression-test-run.csv")
    if tr:
        run = next(r for r in tr if r["row"] == "run")
        cases = {r["case"]: r for r in tr if r["row"] == "case"}
        M += [("RevTestCasesPassed", int(run["cases_passed"])), ("RevTestBuildSeconds", run["build_seconds"]),
              ("RevTestRunSeconds", run["run_seconds"]), ("RevTestCompiler", run["compiler"]),
              ("RevTestOpenCV", run["opencv"]), ("RevTestSourcesCommit", run["sources_commit"]),
              ("RevTestSameTree", run["same_tree"]),
              ("RevTestSecondRunIdentical", "identical" if run["second_run_identical"] == "yes" else "different"),
              ("RevTestEstimatesPrinted", int(run["estimates_printed"]))]
        for name, key in (("concentric-circles", "CircleOne"), ("half-circle", "Half"), ("thinned-1:10", "DensTen")):
            r = cases[name]
            M += [(f"RevTestRun{key}Mm", f"{float(r['distance_mm']):.2f}"),
                  (f"RevTestRun{key}Tol", f"{float(r['tolerance_mm']):.1f}"),
                  (f"RevTestRun{key}Inside", r["inside"])]
        M += [("RevTestRunDensTenX", f"{float(cases['thinned-1:10']['estimate_x']):.0f}"),
              ("RevTestRunDensTenLeansDense", "leans" if float(cases["thinned-1:10"]["estimate_x"]) > 4000 else "does not lean"),
              ("RevTestRunSeedIdentical", "identical" if cases["seed-repeatable"]["identical"] == "yes" else "different"),
              ("RevTestRunAllPass", "pass" if all(r["result"] == "PASS" for r in cases.values()) else "fail")]

    # ---- The cap on the hill climb, from tools/search_cap.py (maintainer review of PR 1823,
    # point 1). The cap is ours and not the C++'s, only the published objective ever met it, and
    # the rows below bound what it does to every number of Tables II and III.
    sc = csv("search-cap.csv")
    if sc:
        def pick(quantity, run=None, variant=None):
            for r in sc:
                if r["quantity"] == quantity and (run is None or r["run"] == run) \
                        and (variant is None or r["variant"] == variant):
                    return r
            return None

        def denom(r):
            m = re.match(r"of (\d+)", r["note"])
            return int(m.group(1)) if m else 0

        M.append(("RevCapSweeps", int(pick("cap")["value"])))
        for run, tag in (("k20-estimates", "Tables"), ("positions-24-refit", "Gen")):
            for variant, vtag in (("as-is", "AsIs"), ("no-division", "Fixed")):
                r = pick("capped_estimates", run, variant)
                M += [(f"RevCap{tag}{vtag}", int(r["value"])),
                      (f"RevCap{tag}{vtag}Of", denom(r))]
            s = pick("capped_scrolls", run, "as-is")
            M += [(f"RevCap{tag}AsIsScrolls", int(s["value"])),
                  (f"RevCap{tag}AsIsScrollList", s["note"])]
        g = pick("growth_ratio")
        M += [("RevCapGrowthSlice", g["scroll"].replace("PHerc", "PHerc.\\ ")),
              ("RevCapGrowthRatio", f"{float(g['value']):.2f}"),
              ("RevCapGrowthNote", g["note"])]
        for cap, tag in ((2000, "Capped"), (32000, "Big")):
            r = pick("walk_distance", f"cap {cap}", "as-is")
            if r:
                M.append((f"RevCapWalk{tag}", f"{float(r['value']):,.0f}".replace(",", "{,}")))
        b = pick("walk_distance", "compiled binary", "as-is")
        if b:
            M.append(("RevCapWalkCpp", f"{float(b['value']):,.0f}".replace(",", "{,}")))
        sh = pick("cap_shortfall")
        if sh:
            M.append(("RevCapShortfall", f"{float(sh['value']):.2f}"))
        rm, wm, vc = pick("rows_moved"), pick("worst_row_move"), pick("verdicts_changed")
        M += [("RevCapRowsMoved", int(rm["value"])), ("RevCapRowsTotal", denom(rm)),
              ("RevCapFactor", re.search(r"(\d+)x", rm["run"]).group(1)),
              ("RevCapWorstMove", f"{float(wm['value']):.2f}"),
              ("RevCapWorstMoveScroll", wm["scroll"].replace("PHerc", "PHerc.\\ ")),
              ("RevCapVerdictsChanged", vc["note"]),
              ("RevCapVerdictsChangedCount", int(vc["value"])),
              ("RevCapMovedVariants", ", ".join(sorted({r["variant"] for r in sc
                                                        if r["quantity"] == "row_moved"})) or "none")]

    # The caption of the gallery figure, as its tool wrote it, made safe for LaTeX: the tool's
    # text carries per cent signs, underscores in file names and the counts it checked against
    # the macros above.
    cap = os.path.join(REV1, "figures", "umbilicus-gallery-24.caption.txt")
    if os.path.exists(cap):
        text = open(cap).read().strip()
        for a, b in (("\\", "\\textbackslash "), ("%", "\\%"), ("_", "\\_"), ("&", "\\&"),
                     ("#", "\\#"), ("PHerc. ", "PHerc.\\ ")):
            text = text.replace(a, b)
        M.append(("RevGalleryCaption", text))

    p = os.path.join(PAPERS, "rev1-numbers.tex")
    with open(p, "w") as fh:
        fh.write("% Generated by tools/rev1_numbers.py from evidence/. Do not edit.\n")
        for name, value in M:
            fh.write(f"\\newcommand{{\\{name}}}{{{num(value)}\\xspace}}\n")
    print(f"written {p} ({len(M)} macros)")


if __name__ == "__main__":
    main()
