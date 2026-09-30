#!/usr/bin/env python3
"""Copy the evidence this work cites, and the tools that wrote it, from the laboratory's studies.

WHY THIS IS A TOOL. The chain on PHerc. 0826 was still delivering seeds while this work was written,
so every file under src/evidence/studies/ is a SNAPSHOT taken at one moment, and a number in the
article is true of that moment. A copy made by hand has no moment and no source. This one writes
src/evidence/MANIFEST.csv: one row per copied file with its source path, its sha256, the time of
the copy, the tool the file names as its writer, and whether that tool is shipped beside it.

THE CHECKS ARE COLUMNS. `names_tool` says what the file's header (its comment line, or its `tool`
column) names as the writer; `tool_shipped` says whether that tool is in src/tools/studies/. The copy
refuses when any cited file names no tool or names one that is not shipped, because a work ships,
beside each evidence file it cites, the tool that wrote it (rule of 2026-09-22T13:17:39Z).

A file listed here that does not exist at its source is NOT an error: it is a PENDING file, the
measurement has not written it yet, and its MANIFEST row says «pending» in column `status`.
paper_numbers.py then refuses to fill any macro that reads it, and the build refuses the article.

LOCATIONS WITHHELD (director 2026-09-30, the owner's decision: the article goes out without locations on the scroll).
DROP names, per (study, file), the columns that give a scan position (a seed point, a start point, a radius or angle
about the umbilicus, a height); they are removed from the shipped copy when it is made, and REDACT replaces a position
written inside a text cell. MANIFEST.csv says which in its column `columns_dropped`, and its sha256 is the sha256 of
the shipped, filtered copy. `--drop-shipped` applies the same filter to the copies already shipped, without reading
the studies again, so that the numbers keep resting on the snapshot they were taken from.

Usage: copy_evidence.py [--dry-run] [--only STUDY ...] [--drop-shipped]
"""
import argparse, csv, glob, hashlib, os, re, shutil, subprocess, sys

RUNS = "/data/scrollagent/runs/rev1"
SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(SRC, "evidence", "studies")
TO = os.path.join(SRC, "tools", "studies")

# study -> (evidence patterns relative to RUNS/<study>/evidence, tools relative to RUNS)
# A tool path here is the path the evidence names; it is shipped under tools/studies/<its study>/.
PLAN = {
    "chain-0826": (
        ["per-seed-queue.csv", "seed-rule.csv", "ladder.csv", "wave-sizing.csv",
         "wave4-sources.csv", "wave4-near-draw.csv", "wave5-sources.csv", "wave5-near-draw.csv", "identity-0826-all.csv",
         "identity-0826-summary.csv", "a2-cluster/PHerc0826-seed*.csv",
         "squares-PHerc0826-seed*.csv", "a2-cluster-reference.csv", "inputs/i5-coverage.csv", "build-objects-check.csv"],
        ["chain-0826/tools/per_seed.py", "chain-0826/tools/seed_rule_check.py",
         "chain-0826/tools/seed_rule_check_v2.py", "chain-0826/tools/ladder.sh",
         "chain-0826/tools/ladder_par.sh", "chain-0826/tools/wave_sizing.py",
         "chain-0826/tools/wave4_sources.py", "chain-0826/tools/draw_near.py",
         "chain-0826/tools/draw_seeds.py", "chain-0826/tools/draw_near_wave5.py", "chain-0826/tools/wave5_sources.py", "chain-0826/tools/identity_summary.py",
         "chain-0826/tools/identity_0826.sh", "chain-0826/tools/a2_cluster_seed.py",
         "chain-0826/tools/measure_seed.sh", "seed-search-1447/tools/square.py",
         "chain-0826/tools/check_inputs_0826.py", "chain-0826/tools/run_seed.sh", "chain-0826/tools/build_objects_check.py"]),
    "growth-lto-pgo-1447": (
        ["identity-0826-summary.csv", "identity-0826-mlp.csv"],
        ["growth-lto-pgo-1447/tools/identity_compare_arms.py"]),
    "growth-exact-fixes-88": (
        ["clock-summary-PHerc0826-seed237.csv", "clock-runs-PHerc0826-seed237.csv"],
        ["growth-exact-fixes-88/tools/clock_summary_fixes.py",
         "growth-exact-fixes-88/tools/clock_fixes.sh"]),
    "hot-lines-88": (
        ["clock-summary.csv", "clock-runs.csv", "identity-l-summary.csv"],
        ["hot-lines-88/tools/clock_summary_zl.py", "hot-lines-88/tools/clock_zl2.sh",
         "hot-lines-88/tools/identity_l.py"]),
    "area-0826-90": (
        ["union.csv", "one-lamina.csv", "stevens-method.csv", "stevens-method-0826.csv",
         "collection-four-6365.csv", "collection-control-6365.csv",
         "collection-setseed-seed6365.csv", "collection-setseed-seed2019.csv",
         "collection-setseed-seed5630.csv", "squares-coll-setseed-seed6365.csv", "traced-reference.csv", "road1b-seeds.csv",
         # PENDING until road 1b ends: the collection of the eight nearest seeds of
         # road1b-seeds.csv (ranks 1 to 8; the director cut the list from 12 to 8 before launch,
         # 2026-09-28T06:01:51Z, for time and memory), measured by the same tool into
         # collection-eight-6365.csv, the columns of collection-four-6365.csv. Name confirmed by
         # the coordinator 2026-09-28T06:0xZ; it replaced collection-road1b-6365.csv, a guess.
         "collection-eight-6365.csv",
         # road 1b closed 2026-09-28T15:50:25Z (director): its two stage c runs and their RSS stops
         "road1b-memory.csv"],
        ["area-0826-90/tools/area90.py", "area-0826-90/tools/lamina.py",
         "area-0826-90/tools/stevens_method.py", "area-0826-90/tools/traced_sum.py",
         "area-0826-90/tools/road1b_seeds.py", "area-0826-90/tools/road1b_memory.py"]),
    # 2026-09-28T08:1xZ: quiet-window-2026-09-27, quiet-bench and four-corrections-0826-93 were added
    # for the module sections and removed the same hour on the director's note of 08:03:17Z (owner's
    # rule): the article measures only the assembly on PHerc0826; the component works are cited for
    # their own measurements on their authors' data, and item 93's section is dropped.
    "nongrowth-profile-1447": (
        ["build-objects-only.csv"],
        ["nongrowth-profile-1447/tools/objects_only.py"]),
    # item 95 (c) (coordinator 2026-09-28T14:2xZ): the five capped seeds regrown at g 72000. summary.csv is
    # NOT copied: its tool crashed and wrote «not measurable» everywhere; the per seed files are read.
    # checks-PHerc0826-seed2604.csv is this work's request (v2 crossing map and one lamina test on the
    # 21.7474 mm sheet, columns check, verdict in {clean, crossing found, not measurable}); not pending:
    # tools/cutoff.py decides at the cut off what the text says of those checks.
    "square20-0826-95": (
        ["cap-check.csv", "runs-PHerc0826-seed*.csv", "identity-36000-PHerc0826-seed*.csv",
         "squares-PHerc0826-seed*.csv", "a2-cluster/PHerc0826-seed*.csv", "checks-PHerc0826-seed2604.csv",
         # item 95 (f) (director 2026-09-28T21:22:13Z): the ten next capped seeds regrown at g 72000
         "cap-check-next10.csv"],
        ["square20-0826-95/tools/cap_and_size.py", "square20-0826-95/tools/cap_and_size_v2.py", "square20-0826-95/tools/regrow72.sh",
         "square20-0826-95/tools/measure72.sh", "square20-0826-95/tools/a2_72.py",
         "square20-0826-95/tools/checks_file.py"]),
    # item 96 (director 2026-09-28T12:30:13Z): simpaper10 reading the seed and volume at run time, one
    # binary for all seeds, bar G6 identity. Its summary is NOT pending: the text switches on whether it
    # exists and holds (declared rule, the build refuses nothing either way). The name is this work's
    # request, in chain-0826/evidence/identity-0826-summary.csv's form (last column identity_holds).
    "runtime-params-96": (
        ["identity-summary.csv", "identity-0826-runtime.csv"],
        ["runtime-params-96/tools/identity_compare_runtime.py", "runtime-params-96/tools/identity_runtime.sh"]),
    # PENDING until item 91 writes it: one row per arm. The study did not exist when this work
    # was opened (2026-09-28T05:50Z); the file name and columns are this work's request and are
    # reconciled with the study's own when it lands, with a dated line in PLACEHOLDERS.md.
    "stevens-changes-0826-91": (
        ["arms.csv", "per-run.csv", "seeds.csv"],
        ["stevens-changes-0826-91/tools/aggregate91.py", "stevens-changes-0826-91/tools/select_seeds.py"]),
    # director 2026-09-28T18:20:15Z: squares of 10 mm or more found per machine hour, Stevens' pipeline
    # (item 91 arm A, the random waves, 3 at once) against ours (arm C, every wave as run, 7 at once),
    # whole search cost; formula declared in search-yield-0826/DECLARATION.md before it was computed.
    # yield.py reads this work's own frozen chain-0826 snapshot and C40 rows of certified-squares.csv.
    "search-yield-0826": (
        ["yield.csv", "yield-seeds.csv"],
        ["search-yield-0826/tools/yield.py"]),
    # director 2026-09-29T02:21:36Z: the fibre score of every certified piece of 10 cm2 or more and the bar 0.75 x the
    # reference seed3648 C40 S0, declared in certified-piece-0826/DECLARATION.md (additions 01:24:25Z and 02:22:50Z)
    # before any score existed. fibre2.py imports fibre.py, which imports dark.py and piece_texture.py.
    "certified-piece-0826": (
        ["fibre-score.csv", "fibre-ranking.csv"],
        ["certified-piece-0826/tools/fibre.py", "certified-piece-0826/tools/fibre2.py",
         "certified-piece-0826/tools/dark.py", "certified-piece-0826/tools/piece_texture.py"]),
    # director 2026-09-29T06:54:31Z (owner's word), the reframe around the checks: the clean 20 x 20 mm windows of
    # best-windows-0826 (DECLARATION.md 06:14:07Z and its dated additions), their axis aligned renders by that study's
    # own tools/align.py (not render-routes-0826's regrid_z.py, which is under the director's review) and the
    # straightened sections of the best three. No ink file of that study is copied: PHerc0826 ink never enters
    # this article.
    "best-windows-0826": (
        ["windows.csv", "attempts.csv", "selftest.csv", "angles.csv", "aligned.csv", "renders.csv", "straight.csv"],
        ["best-windows-0826/tools/bw.py", "best-windows-0826/tools/align.py", "best-windows-0826/tools/panels.py",
         "best-windows-0826/tools/straight.py"]),
    # The end to end positive control on the labelled w016 region of PHerc. 0139 (director 2026-09-29T06:22:17Z;
    # DECLARATION.md of that study): the verdict rows (appended, never rewritten) and the scored reads behind them.
    # PHerc. 0139 is not a prize restricted scroll; no ink output of PHerc. 0826 is read here.
    "positive-control-0139": (
        ["verdict.csv", "control.csv",
         # director 2026-09-29T12:52:52Z: the nulls of our sheets and run_one_v2's label free statistic on known ink
         "null-best.csv", "labelfree-w016.csv"],
        ["positive-control-0139/tools/verdict.py", "positive-control-0139/tools/score.py",
         "positive-control-0139/tools/null_best.py", "positive-control-0139/tools/labelfree_table.py"]),
    # The headline of the reframe (director 12:52:52Z and 15:38:23Z, owner's word): our start, the organisers' tracer
    # (villa vc_grow_seg_from_seed with vc_gen_normalgrids) on a 60 mm crop, our checks. Only the R2c rows are cited; the
    # regrid self test is copied for the one sentence that says why no regridding is used. Its ink files are not copied.
    "render-routes-0826": (
        ["square-checks.csv", "routes.csv", "old-square-on-r2c.csv", "r2c-runs.csv", "regrid-selftest.csv", "aligned-square.csv"],
        ["render-routes-0826/tools/sq_checks.py", "render-routes-0826/tools/routes.py",
         "render-routes-0826/tools/old_square.py", "render-routes-0826/tools/r2c_grow.sh",
         "render-routes-0826/tools/regrid_z.py", "render-routes-0826/article-figure/fig_r2c.py",
         "render-routes-0826/tools/align_square.py"]),
    # Youssef Nader's v8-in ink model (owner's order of 2026-09-30): the release read at its pinned revision, the maps of the
    # two R2c squares described, the sheet over null ratio on known ink and on PHerc0826 (ink-v8in-0826), and the depth
    # order measured on PHerc0139 w016 (selftrain-v8in-0826).
    "ink-v8in-0826": (
        ["hf-files.csv", "describe-v2.csv", "ratio-calibration.csv"],
        ["ink-v8in-0826/tools/hf_files.py", "ink-v8in-0826/tools/upright_full.py", "ink-v8in-0826/tools/ratio_cal.py"]),
    # v8-in on the whole R2d surface of seed 2715, and the reads that follow it (owner's order of 2026-09-30): one
    # describe.csv per study, read by src/tools/v8in_reads.py; a study added later is one more entry here.
    "ink-v8in-0826-r2d": (
        ["describe.csv"],
        ["ink-v8in-0826-r2d/tools/stitch_r2d.py"]),
    "selftrain-v8in-0826": (
        ["order-0139.csv"],
        ["selftrain-v8in-0826/tools/w016.py"]),
    # Axial cuts through the R2d square of seed 2715 and through the headline square (director 2026-09-30, study cuts-2715):
    # the verdict per cut, the void test on the headline square and the air proxy with its reference. cuts.py and drift.py,
    # which fix the heights of the cuts and the crack's position, are not shipped (no position on the scroll).
    "cuts-2715": (
        ["verdict.csv", "headline-cuts.csv", "headline-air.csv", "air-reference.csv", "headline-eye.csv"],
        ["cuts-2715/tools/sheetrun.py", "cuts-2715/tools/headline.py", "cuts-2715/tools/air_ref.py",
         "cuts-2715/tools/headline_eye.py"]),
    # The renderer check (ink-finetune-k2): our base render against the organisers' surface volume, NCC.
    "ink-finetune-k2": (
        ["refcheck.csv"],
        ["ink-finetune-k2/tools/refcheck.py"]),
}


# THE CHAIN AS RUN (director 2026-09-28T16:50:23Z, point 2 of that note). chain-0826 is FROZEN at its
# relaunch: the director relaunched it at 2026-09-28T16:15:12Z (chain-0826/log/launch-chain.txt, line
# «2026-09-28T16:15:12Z [launch-chain] started»; DECLARATION.md, the dated g 72000 addition) after item 96
# installed, at 2026-09-28T15:27:32Z, a run_seed.sh that grows «$BIN g $GEN» with GEN=72000 and runs the
# downstream with SIMPAPER_PATCH_LIMIT 80000. The article's chain is the chain before that relaunch, grown
# at g 36000 with 40000; the g 72000 growths are reported apart and never pooled with it.
# The rule, per chain-0826 evidence file, in this order (column chain_as_run of MANIFEST.csv, and one row
# per chain seed in evidence/derived/chain-as-run.csv):
#   1. a file of a seed (PHerc0826-seed<n> in its name) whose live evidence/runs/<seed>.csv carries any
#      of new_file_rows is out: those rows are written only by a run_seed.sh installed on 2026-09-28
#      (growth_generation_cap and downstream_patch_limit by the g 72000 file, seed_at_run_time by the
#      runtime-seed file of 15:17:19Z), and a seed without them was grown at g 36000 with 40000
#      (DECLARATION.md: «a seed without those rows was grown at g 36000 with 40000»);
#   2. a file last written before the freeze is copied as it is now;
#   3. a file written at or after the freeze is not copied: the copy already shipped stands if the
#      previous MANIFEST.csv row says its source was written before the freeze (column
#      source_written_utc, else copied_utc) and the shipped copy's sha256 still matches that row;
#   4. otherwise (a file first written after the freeze) it is out, «written after the freeze».
# Rule 1 already implies «growth ended before the relaunch»: no seed without those rows can start
# after it, since every start after 16:15:12Z runs the new file, which writes downstream_patch_limit.
FREEZE = {
    "chain-0826": {
        "at": "2026-09-28T16:15:12Z",
        "source": "chain-0826/log/launch-chain.txt «2026-09-28T16:15:12Z [launch-chain] started»; DECLARATION.md g 72000 addition",
        "new_file_rows": ("growth_generation_cap", "downstream_patch_limit", "seed_at_run_time"),
        # A tool changed at or after the first install of that day (15:17:19Z, next-runtime) drifted from the
        # chain as run: it must be shipped from its pre-install backup (TOOL_FROM), or the copy refuses.
        "tools_changed_from": "2026-09-28T15:17:19Z",
    },
}
# The tools of the chain as run, shipped from the backup of item 96's first install of that day
# (next-runtime, 15:17:19Z), with the sha256 the backup must have: the file installed from
# 2026-09-27T14:14:20Z until 15:17:19Z, the one every seed of the chain as run ran. It grows
# «$BIN g 36000» and runs SIMPAPER_PATCH_LIMIT 40000 (the director's «pre-install run_seed.sh»). The file
# between the two installs (next-g72000 backup, ebc223c3...) adds only the runtime-seed branch and ran no
# seed: the chain runner was stopped from 06:07:39Z to the relaunch (coordinator, 2026-09-28T17:07Z).
TOOL_FROM = {
    "chain-0826/tools/run_seed.sh": (
        "chain-0826/scratch/next-runtime/backup-20260928T151719Z/tools/run_seed.sh",
        "dcf736c10d8fe3dff1699b1a4ffe32d872c04b86da42463e71e23cd5eff6e80f"),
}
SEED_RE = re.compile(r"(PHerc0826-seed\d+)")

# Locations withheld (see the docstring): (study, file) -> columns removed from the shipped copy.
DROP = {
    ("chain-0826", "seed-rule.csv"): ["seed_x", "seed_y", "seed_z", "pred_chunk_zyx", "raw_chunk_zyx"],   # chunk indices place a seed too
    ("chain-0826", "per-seed-queue.csv"): ["seed_x", "seed_y", "seed_z"],
    ("chain-0826", "wave4-sources.csv"): ["seed_x", "seed_y", "seed_z"],
    ("chain-0826", "wave5-sources.csv"): ["seed_x", "seed_y", "seed_z"],
    ("chain-0826", "wave4-near-draw.csv"): ["seed_x", "seed_y", "seed_z"],
    ("chain-0826", "wave5-near-draw.csv"): ["seed_x", "seed_y", "seed_z"],
    ("render-routes-0826", "r2c-runs.csv"): ["x", "y", "z"],
    ("render-routes-0826", "square-checks.csv"): ["radius_median_vox", "radius_p5_p95_vox"],
    ("render-routes-0826", "routes.csv"): ["regrid_r_med_vox", "regrid_theta_span_deg", "grid"],
    ("best-windows-0826", "aligned.csv"): ["centre_z"],
    ("cuts-2715", "verdict.csv"): ["zc", "eye"],
    ("cuts-2715", "headline-cuts.csv"): ["zc", "strip_png", "box_png", "zoom_png"],
    ("cuts-2715", "headline-air.csv"): ["zmin", "zmax"],
}
# (study, file) -> column whose cells name a cut by its height («crack-10569»): the height is cut from the name.
HEIGHT_NAMES = {("cuts-2715", f): "cut" for f in ("verdict.csv", "headline-cuts.csv", "headline-eye.csv")}
HEIGHT_IN_NAME = re.compile(r"-\d{4,5}$")
HEIGHT_NOTE = ": the height in the cut's name withheld"
# (study, file) -> (column, pattern, replacement): a position written inside a text cell.
REDACT = {
    ("runtime-params-96", "identity-0826-runtime.csv"):
        ("seed_from_environment", re.compile(r"Seed at run time: -?\d+ -?\d+ -?\d+"), "Seed at run time: x y z withheld"),
}


# The seed point a runs file records at run time (row seed_at_run_time) is a scan position too: chain_as_run() writes
# it as «withheld», in its column and inside its why text, and so into MANIFEST.csv's chain_as_run column.
RUNTIME_SEED = re.compile(r"seed_at_run_time=-?\d+ -?\d+ -?\d+")


def hide_runtime_seed(text):
    return RUNTIME_SEED.sub("seed_at_run_time=withheld", text)


# The shipped copies carry no internal marking and no absolute path of this machine (the referee, 2026-09-30): the word
# PRIVATE the studies write in their header lines is removed, and the paths are cut to where they are relative.
CLEAN_SUBS = ((re.compile(r";\s*PRIVATE(, no text uses it)?"), ""),
              (re.compile(r"/data/scrollagent/runs/rev1/"), ""),
              (re.compile(r"/data/scrollagent/data/datasets/"), "datasets/"),
              (re.compile(r"/data/scrollagent/outputs/artifacts/"), "outputs/artifacts/"),
              (re.compile(r"/data/scrollagent/"), ""),
              (re.compile(r"/data/repositories/vesuvius-challenge-pipeline-private/"), ""),
              (re.compile(r"/data/repositories/"), ""),
              (re.compile(r"/data/opt/"), ""),
              (re.compile(r"/data/tmp/"), "scratch/"))
CLEAN_NOTE = "internal marking removed and absolute paths cut"


def clean_text(t):
    for rx, rep in CLEAN_SUBS:
        t = rx.sub(rep, t)
    return t


def clean_copy(path):
    """Apply CLEAN_SUBS to a shipped copy in place; returns True when it changed."""
    raw = open(path, newline="").read()
    new = clean_text(raw)
    if new == raw:
        return False
    with open(path, "w", newline="") as fh:
        fh.write(new)
    return True


def withheld(study, rel):
    """What the shipped copy of (study, rel) withholds, as MANIFEST.csv's column columns_dropped says it."""
    parts = list(DROP.get((study, rel), []))
    if (study, rel) in REDACT:
        parts.append("%s: the seed point replaced by «x y z withheld»" % REDACT[(study, rel)][0])
    if (study, rel) in HEIGHT_NAMES:
        parts.append(HEIGHT_NAMES[(study, rel)] + HEIGHT_NOTE)
    return "; ".join(parts)


def filter_copy(study, rel, path, already=""):
    """Remove DROP's columns and apply REDACT to the shipped copy at path, in place. The comment lines above the header
    are kept as they are; a column DROP names that the header does not have stops the copy (a renamed column would
    otherwise ship the position under its new name), unless `already` (the copy's MANIFEST columns_dropped) says an earlier
    run of this filter withheld it. Returns the number of cells changed or removed."""
    done_before = {c.strip() for c in already.split(";")}
    cols, red = DROP.get((study, rel), []), REDACT.get((study, rel))
    if red and red[0] + ": the seed point replaced by «x y z withheld»" in done_before:
        red = None
    hn = HEIGHT_NAMES.get((study, rel))
    if hn and hn + HEIGHT_NOTE in done_before:
        hn = None
    cols = [c for c in cols if c not in done_before]
    if not cols and not red and not hn:
        return 0
    raw = open(path, newline="").read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.splitlines(keepends=True)
    k = 0
    while k < len(lines) and lines[k].lstrip().startswith(("#", '"#')):
        k += 1
    table = list(csv.reader(lines[k:]))
    head = table[0]
    missing = [c for c in cols if c not in head and c not in done_before] + ([red[0]] if red and red[0] not in head else [])
    if missing:
        sys.exit("copy_evidence.py: %s/%s has no column %s to withhold" % (study, rel, ", ".join(missing)))
    keep = [i for i, c in enumerate(head) if c not in cols]
    n, nred, out = 0, 0, []
    for j, r in enumerate(table):
        if not r:
            continue
        if j and red:
            ci = head.index(red[0])
            new = red[1].sub(red[2], r[ci])
            nred += new != r[ci]
            r[ci] = new
        if j and hn:
            ci = head.index(hn)
            new = HEIGHT_IN_NAME.sub("", r[ci])
            nred += new != r[ci]
            r[ci] = new
        n += (len(r) - len(keep)) if j else 0
        out.append([r[i] for i in keep])
    if red and nred == 0:
        sys.exit("copy_evidence.py: %s/%s: REDACT found no position in column %s" % (study, rel, red[0]))
    with open(path, "w", newline="") as fh:
        fh.write("".join(lines[:k]))
        csv.writer(fh, lineterminator=nl).writerows(out)
    return n + nred


def drop_shipped(dry):
    """Apply DROP and REDACT to the copies already shipped and rewrite their MANIFEST.csv rows (sha256, columns_dropped).
    Nothing is read from the studies. A copy whose header no longer has the columns is not filtered twice."""
    p = os.path.join(SRC, "evidence", "MANIFEST.csv")
    raw = open(p, newline="").read().splitlines(keepends=True)
    head_line = raw[0]
    rows = list(csv.DictReader(raw[1:]))
    fields = list(rows[0]) + ([] if "columns_dropped" in rows[0] else ["columns_dropped"])
    done = []
    for r in rows:
        key = (r["study"], r["file"])
        r.setdefault("columns_dropped", "")
        if key not in DROP and key not in REDACT and key not in HEIGHT_NAMES:
            continue
        d = os.path.join(EV, *key)
        if r["status"] not in ("copied", "frozen") or not os.path.exists(d):
            sys.exit("copy_evidence.py: %s/%s is not shipped (%s)" % (key[0], key[1], r["status"]))
        if sha(d) != r["sha256"] and r["columns_dropped"] != withheld(*key):
            sys.exit("copy_evidence.py: %s/%s is not the copy its MANIFEST row names" % key)
        if r["columns_dropped"] == withheld(*key):
            continue
        n = 0 if dry else filter_copy(key[0], key[1], d, r["columns_dropped"])
        r["sha256"], r["columns_dropped"] = (sha(d) if not dry else r["sha256"]), withheld(*key)
        done.append("%s/%s (%d cells)" % (key[0], key[1], n))
    nman = 0
    for r in rows:                         # the runtime seed point inside the chain_as_run text of excluded files
        new = hide_runtime_seed(r.get("chain_as_run", ""))
        nman += new != r.get("chain_as_run", "")
        r["chain_as_run"] = new
    ca = os.path.join(SRC, "evidence", "derived", "chain-as-run.csv")
    ncas = 0
    if os.path.exists(ca):
        craw = open(ca, newline="").read().splitlines(keepends=True)
        k = 0
        while k < len(craw) and craw[k].lstrip().startswith(("#", '"#')):
            k += 1
        crows = list(csv.DictReader(craw[k:]))
        for cr in crows:
            v = cr["seed_at_run_time"]
            if v not in ("no row", "withheld"):
                if not re.fullmatch(r"-?\d+ -?\d+ -?\d+", v.strip()):
                    sys.exit("copy_evidence.py: chain-as-run.csv seed_at_run_time %r is not a point" % v)
                cr["seed_at_run_time"] = "withheld"
                ncas += 1
            cr["why"] = hide_runtime_seed(cr["why"])
            if RUNTIME_SEED.search(cr["why"]):
                sys.exit("copy_evidence.py: a runtime seed point is left in chain-as-run.csv")
        if not dry:
            with open(ca, "w", newline="") as fh:
                fh.write("".join(craw[:k]))
                w = csv.DictWriter(fh, fieldnames=list(crows[0]))
                w.writeheader()
                w.writerows(crows)
    done.append("derived/chain-as-run.csv (%d runtime seed points)" % ncas)
    done.append("MANIFEST.csv chain_as_run (%d rows)" % nman)
    ncl = 0
    for r in rows:                         # every shipped copy: no PRIVATE word, no absolute path
        r["source"] = clean_text(r.get("source", ""))
        if r["status"] not in ("copied", "frozen"):
            continue
        d = os.path.join(EV, r["study"], r["file"])
        if os.path.exists(d) and d.endswith((".csv", ".txt")) and (dry or clean_copy(d)) and not dry:
            r["sha256"] = sha(d)
            if CLEAN_NOTE not in r["columns_dropped"]:
                r["columns_dropped"] = (r["columns_dropped"] + "; " if r["columns_dropped"] else "") + CLEAN_NOTE
            ncl += 1
    done.append("%d shipped copies cleaned (%s)" % (ncl, CLEAN_NOTE))
    missing = [k for k in list(DROP) + list(REDACT) if not any((r["study"], r["file"]) == k for r in rows)]
    if missing:
        sys.exit("copy_evidence.py: DROP or REDACT names a file MANIFEST.csv does not: %s" % missing)
    if not dry:
        now = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
        with open(p, "w", newline="") as fh:
            base = re.sub(r"; columns_dropped \(added .*$", "", head_line.rstrip("\r\n").rstrip('"'))
            base = base.replace("copied from /data/scrollagent/runs/rev1/<study>/evidence",
                                "copied from the study folder <study>/evidence of the laboratory")
            fh.write(base + "; columns_dropped (added %s by --drop-shipped): the columns withheld "
                     "from the shipped copy, whose sha256 is then the sha256 of that filtered copy\"\n" % now)
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    print("copy_evidence.py --drop-shipped: %d file(s) filtered: %s" % (len(done), ", ".join(done) or "none"))
    return 0


def utc(ts):
    return subprocess.check_output(["date", "-u", "-d", "@%d" % int(ts), "+%FT%TZ"]).decode().strip()


def runs_rows(study, seed):
    """{quantity: value} of the live evidence/runs/<seed>.csv, or None when there is none."""
    p = os.path.join(RUNS, study, "evidence", "runs", seed + ".csv")
    if not os.path.exists(p):
        return None
    with open(p, newline="") as fh:
        return {r["quantity"]: r["value"] for r in csv.DictReader(l for l in fh if not l.startswith(('"#', "#")))}


def chain_as_run(study, fz, now, dry):
    """One row per live runs/<seed>.csv of a frozen study: its cap rows and whether it is in the chain as run."""
    out, excluded = [], {}
    for p in sorted(glob.glob(os.path.join(RUNS, study, "evidence", "runs", "PHerc0826-seed*.csv"))):
        seed = os.path.basename(p)[:-4]
        q = runs_rows(study, seed)
        hit = [k for k in fz["new_file_rows"] if k in q]
        why = hide_runtime_seed("no: %s in runs/%s.csv" % ("; ".join("%s=%s" % (k, q[k]) for k in hit), seed)) if hit else \
              "yes: no row of %s in runs/%s.csv" % (", ".join(fz["new_file_rows"]), seed)
        if hit:
            excluded[seed] = why
        out.append({"attempt": seed, "runs_csv_sha256": sha(p), "runs_csv_written_utc": utc(os.path.getmtime(p)),
                    "freeze_utc": fz["at"], "binary_series": q.get("binary_series", "none"),
                    "growth_generation_cap": q.get("growth_generation_cap", "no row"),
                    "downstream_patch_limit": q.get("downstream_patch_limit", "no row"),
                    "seed_at_run_time": "withheld" if "seed_at_run_time" in q else "no row",
                    "in_chain_as_run": "no" if hit else "yes", "why": why})
    if not dry:
        d = os.path.join(SRC, "evidence", "derived", "chain-as-run.csv")
        with open(d, "w", newline="") as fh:
            fh.write('"# written by src/tools/copy_evidence.py at %s: one row per %s/evidence/runs/<seed>.csv; '
                     'the chain as run is frozen at %s (%s); a seed is out when its runs file carries a row of %s"\n'
                     % (now, study, fz["at"], fz["source"], ", ".join(fz["new_file_rows"])))
            w = csv.DictWriter(fh, fieldnames=list(out[0]))
            w.writeheader()
            w.writerows(out)
    return excluded


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# Files whose header names no writer, with the tool that writes them (none at present).
TOOL_OF = {}


def named_tool(p):
    """What the file names as its writer: «written by X» in a comment line, else a `tool` column."""
    for k, v in TOOL_OF.items():
        if p.endswith(k):
            return v
    with open(p, newline="") as fh:
        head = fh.read(4096)
    m = re.search(r"written by ([A-Za-z0-9_./+-]+\.(?:py|sh))", head)
    if m:
        return m.group(1)
    rows = list(csv.reader(head.splitlines()))
    for i, r in enumerate(rows):
        if r and not r[0].lstrip().startswith("#"):
            if "tool" in r and i + 1 < len(rows) and len(rows[i + 1]) > r.index("tool"):
                return rows[i + 1][r.index("tool")]
            break
    m = re.search(r"from (tools/[A-Za-z0-9_]+\.py)", head)
    return m.group(1) if m else ""


def shipped(study, tool):
    """The shipped copy of a named tool, or '' when it is not shipped."""
    if not tool:
        return ""
    base = os.path.basename(tool)
    for cand in glob.glob(os.path.join(TO, "*", base)):
        return os.path.relpath(cand, SRC)
    return ""


def previous_manifest():
    """{(study, file): row} of the MANIFEST.csv this run replaces, or {} when there is none."""
    p = os.path.join(SRC, "evidence", "MANIFEST.csv")
    if not os.path.exists(p):
        return {}
    with open(p, newline="") as fh:
        return {(r["study"], r["file"]): r for r in csv.DictReader(l for l in fh if not l.startswith('"#'))}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--drop-shipped", action="store_true",
                    help="withhold DROP's columns and REDACT's cells in the copies already shipped; read no study")
    ap.add_argument("--only", action="append", default=[],
                    help="copy only this study (repeatable); every other study keeps its MANIFEST rows and its copies "
                         "as they are, so a study added late does not re snapshot the ones the numbers already rest on")
    a = ap.parse_args()
    if a.drop_shipped:
        return drop_shipped(a.dry_run)
    unknown = [x for x in a.only if x not in PLAN]
    if unknown:
        sys.exit("copy_evidence.py: --only names no study of PLAN: %s" % ", ".join(unknown))
    now = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    prev = previous_manifest()
    rows, bad, trows = [], [], []
    for study, (pats, tools) in PLAN.items():
        if a.only and study not in a.only:
            kept = [dict(r, columns_dropped=r.get("columns_dropped", "")) for (st, _), r in prev.items() if st == study]
            if not kept:
                bad.append("--only: %s has no row in the previous MANIFEST.csv to keep" % study)
            rows.extend(kept)
            continue
        fz = FREEZE.get(study)
        for t in tools:
            s = os.path.join(RUNS, t)
            d = os.path.join(TO, t.split("/", 1)[0], os.path.basename(t))
            if not os.path.exists(s):
                bad.append("tool %s not at its source" % t)
                continue
            src = s
            if fz and t in TOOL_FROM:
                src = os.path.join(RUNS, TOOL_FROM[t][0])
                if not os.path.exists(src) or sha(src) != TOOL_FROM[t][1]:
                    bad.append("tool %s: its pre-install backup %s is missing or not sha256 %s" % (t, TOOL_FROM[t][0], TOOL_FROM[t][1]))
                    continue
            elif fz and utc(os.path.getmtime(s)) >= fz["tools_changed_from"]:
                bad.append("tool %s changed at %s, after %s: ship its pre-install version (TOOL_FROM)"
                           % (t, utc(os.path.getmtime(s)), fz["tools_changed_from"]))
                continue
            if fz:
                trows.append({"tool": t, "shipped_as": os.path.relpath(d, SRC), "shipped_from": os.path.relpath(src, RUNS),
                              "sha256": sha(src), "live_sha256": sha(s), "same_as_live": "yes" if sha(src) == sha(s) else "no",
                              "live_written_utc": utc(os.path.getmtime(s))})
            if not a.dry_run:
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copy2(src, d)
        excluded = chain_as_run(study, fz, now, a.dry_run) if fz else {}
        for pat in pats:
            hits = sorted(glob.glob(os.path.join(RUNS, study, "evidence", pat)))
            if not hits:
                rows.append({"study": study, "file": pat, "source": os.path.join(RUNS, study, "evidence", pat),
                             "status": "pending", "sha256": "", "copied_utc": now,
                             "names_tool": "", "tool_shipped": "", "source_written_utc": "",
                             "chain_as_run": "yes" if fz else "not frozen", "columns_dropped": ""})
                continue
            for s in hits:
                rel = os.path.relpath(s, os.path.join(RUNS, study, "evidence"))
                d = os.path.join(EV, study, rel)
                tool = named_tool(s)
                ship = shipped(study, tool)
                row = {"study": study, "file": rel, "source": s, "status": "copied",
                       "sha256": sha(s), "copied_utc": now, "names_tool": tool or "none",
                       "tool_shipped": ship or "no", "source_written_utc": utc(os.path.getmtime(s)),
                       "chain_as_run": "not frozen", "columns_dropped": withheld(study, rel)}
                copy = True
                if fz:
                    m = SEED_RE.search(rel)
                    written = utc(os.path.getmtime(s))
                    old = prev.get((study, rel))
                    if m and m.group(1) in excluded:                                    # rule 1
                        row.update(status="excluded", sha256="", copied_utc="", chain_as_run=excluded[m.group(1)])
                        copy = False
                    elif written < fz["at"]:                                            # rule 2
                        row["chain_as_run"] = "yes: written %s, before the freeze %s" % (written, fz["at"])
                    elif old and (old.get("source_written_utc") or old["copied_utc"]) and \
                            (old.get("source_written_utc") or old["copied_utc"]) < fz["at"] and os.path.exists(d) \
                            and sha(d) == old["sha256"]:                               # rule 3
                        was = old.get("source_written_utc") or old["copied_utc"]
                        row.update(status="frozen", sha256=old["sha256"], copied_utc=old["copied_utc"],
                                   source_written_utc=was,
                                   chain_as_run="yes: the copy of %s (source written by %s) stands; the source changed at %s, after the freeze %s"
                                   % (old["copied_utc"], was, written, fz["at"]))
                        copy = False
                    else:                                                               # rule 4
                        row.update(status="excluded", sha256="", copied_utc="",
                                   chain_as_run="no: written %s, after the freeze %s, no copy from before it" % (written, fz["at"]))
                        copy = False
                    if row["status"] == "excluded" and os.path.exists(d) and not a.dry_run:
                        os.remove(d)
                if copy and not a.dry_run:
                    os.makedirs(os.path.dirname(d), exist_ok=True)
                    shutil.copy2(s, d)
                    if row["columns_dropped"]:
                        filter_copy(study, rel, d)
                        row["sha256"] = sha(d)
                rows.append(row)
                if row["status"] != "excluded" and (not tool or not ship):
                    bad.append("%s/%s names %r, shipped %r" % (study, rel, tool, ship))
    out = os.path.join(SRC, "evidence", "MANIFEST.csv")
    if not a.dry_run:
        with open(out, "w", newline="") as fh:
            fh.write('"# written by src/tools/copy_evidence.py at %s: one row per file this work '
                     'cites, copied from the study folder <study>/evidence of the laboratory; status pending '
                     'means the measurement has not written the file yet; chain_as_run applies the freeze '
                     'of chain-0826 at %s (copy_evidence.py FREEZE): excluded files are not shipped, frozen '
                     'files keep the copy made before the freeze; columns_dropped: the columns withheld from the shipped copy '
                     '(DROP, REDACT), whose sha256 is then the sha256 of that filtered copy"\n' % (now, FREEZE["chain-0826"]["at"]))
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        if trows:
            with open(os.path.join(SRC, "evidence", "derived", "chain-tools.csv"), "w", newline="") as fh:
                fh.write('"# written by src/tools/copy_evidence.py at %s: every tool of the frozen chain-0826 as shipped '
                         'under src/tools/studies, with the file it was copied from and its sha256; a tool changed '
                         'at or after %s is shipped from its pre-install backup (TOOL_FROM)"\n'
                         % (now, FREEZE["chain-0826"]["tools_changed_from"]))
                w = csv.DictWriter(fh, fieldnames=list(trows[0]))
                w.writeheader()
                w.writerows(trows)
    n = {k: sum(r["status"] == k for r in rows) for k in ("copied", "frozen", "excluded", "pending")}
    print("copy_evidence.py: %d file(s) copied, %d frozen, %d excluded from the chain as run, %d pending: %s" % (
        n["copied"], n["frozen"], n["excluded"], n["pending"],
        ", ".join("%s/%s" % (r["study"], r["file"]) for r in rows if r["status"] == "pending") or "none"))
    for b in bad:
        print("  !! " + b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
