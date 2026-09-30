#!/usr/bin/env python3
"""The three source CSVs of growth-bookkeeping, written with csv.writer.

Two trees are named in every row and nothing is inferred from one alone:
  built      /data/scrollagent/runs/rev1/seed-search-1447/scratch/src/build/corrected/<file>
             the working copy build.sh corrected lays down and make compiles, which is the source
             of the binary that grew every one of the ten seeds.
  upstream   /data/scrollagent/runs/rev1/seed-search-1447/scratch/src/upstream/scrollreading/
             pipeline9/<file>, byte identical to WillStevens' commit 62cbc21 (git hash-object of
             the copy is 92fe15b, which is 62cbc21:pipeline9/simpaper10.cpp).
Line numbers were read with grep -n on those files on 2026-09-21.
"""
import csv

B = "runs/rev1/seed-search-1447/scratch/src/build/corrected/"
U = "runs/rev1/seed-search-1447/scratch/src/upstream/scrollreading/pipeline9/"
E = "/data/scrollagent/runs/rev1/growth-bookkeeping/evidence/"

writers = [
    ["growth, the g mode", B + "simpaper10.cpp", 557, U + "simpaper10.cpp", 450,
     "std::ofstream os(outPath(\"/rel.csv\"))",
     "*am, the AlignmentMap, std::map<int,std::vector<alignment>> (common_types.h:158)",
     "a.first, the key: the id of the patch the round had just grown, put there at "
     + B + "simpaper10.cpp:496 and 497 as (*am)[i+patchGenNum]",
     "std::get<0>(al), field zero of the alignment tuple: the id Aligner::AlignPatches carries "
     "out of the big patch (align_patches.cpp:431 of the built copy, 424 upstream)",
     "yes, this wrote seed34's rel.csv: the runner calls only g and then c l vm hm fm "
     "(seed-search-1447/tools/run_seed_v3.sh lines 57 to 60 and 99 to 106)"],
    ["u, a mode added here", B + "simpaper10.cpp", 896, "not in upstream", "",
     "std::ofstream os(outPath(\"/rel.csv\"))",
     "candidate, a vector of pairs of ids of patches read from folders given on the command line "
     "(" + B + "simpaper10.cpp:863 to 875)",
     "candidate[k].second, the second patch of the pair",
     "std::get<0>(a) of the alignment the aligner returned for that pair",
     "no: u is never called by the runner, and it is our own code, added by "
     "patches/performance/00001-output-folder-and-limits-chosen-at-run-time.patch"],
]

sites = [
    ["an id is allocated", B + "simpaper10.cpp", 405, U + "simpaper10.cpp", 298,
     "(*patches)[i+patchGenNum] = Patch();",
     "once per seed of the round, before the patch is grown; i runs from startingPatch and "
     "advances by the number of seeds of the round",
     "the id exists in the in memory map only"],
    ["the id is given to the grower", B + "simpaper10.cpp", 412, U + "simpaper10.cpp", 305,
     "steps[patchGenNum] = pg[patchGenNum]->GeneratePatch(...,i+patchGenNum,false);", "always",
     "nothing on disk yet"],
    ["the id becomes a key of the alignment map", B + "simpaper10.cpp", 496, U + "simpaper10.cpp",
     389, "(*am)[i+patchGenNum] = std::vector<alignment>(); then push_back(a)",
     "only for an alignment that passes VarianceTest", "first column of rel.csv"],
    ["the id is written into the big patch", B + "simpaper10.cpp", 516, U + "simpaper10.cpp", 409,
     "AddToBigPatch(bp,(*patches)[i+patchGenNum],i+patchGenNum);",
     "only when the patch was accepted, and at " + B + "simpaper10.cpp:428 for the first patch of "
     "the growth, which is accepted without being aligned",
     "the id is stamped on every point of the patch in surface.bp (bigpatch.cpp:296 of the built "
     "copy) and stays there until those points are erased"],
    ["the id is dropped, no geometry", B + "simpaper10.cpp", 528, U + "simpaper10.cpp", 421,
     "unalignedCount++; patches->erase(i+patchGenNum);",
     "two alignment attempts, flipped for the second, and no alignment passed",
     "no patch file is ever written for it; it is not in the big patch either, so on its own it "
     "produces no rel.csv row"],
    ["the id is dropped, no geometry", B + "simpaper10.cpp", 535, U + "simpaper10.cpp", 428,
     "printf(\"Not enough growth steps\"); patches->erase(i+patchGenNum);",
     "steps < MIN_PATCH_ITERS", "as the row above: 7,947 of seed34's 36,001 ids end here or above"],
    ["geometry is written", B + "simpaper10.cpp", 551, U + "simpaper10.cpp", 445,
     "for(auto &p : *patches) p.second.Write(outPath(\"/patches\"),p.first);",
     "once, after the whole growth: one patch_<id>.bin per surviving entry of the map",
     "this is the only place the growth writes geometry, and a growth stopped before it leaves "
     "the patches folder empty and the big patch full"],
    ["geometry can fail to be written and nobody is told", B + "common_types.cpp", 227,
     U + "common_types.cpp", 207,
     "Patch::Write returns false when fopen of patch_<i>.bin fails; the caller at "
     + B + "simpaper10.cpp:553 ignores the return value",
     "whenever fopen fails", "an id with an alignment and no file, inside a single run; no "
     "evidence that this is what happened on seed34"],
    ["the big patch is opened where it is found, not created empty", B + "simpaper10.cpp", 326,
     U + "simpaper10.cpp", 219, "BigPatch *bp = OpenBigPatch(outPath(\"/surface.bp\").c_str());",
     "every growth", "points of an earlier run into the same folder are still there, with that "
     "run's ids on them"],
    ["the numbering restarts from the in memory map alone", B + "simpaper10.cpp", 329,
     U + "simpaper10.cpp", 222,
     "startingPatch is the largest key of *patches plus one; g mode passes a map that was just "
     "allocated empty (" + B + "simpaper10.cpp:1005 and 1007; upstream mode g is at 704, its empty map at 711 and its "
     "call at 713)",
     "every g run", "after an interrupted growth the new run numbers from 0 again while the big "
     "patch still carries the old ids: the two numberings overlap"],
    ["the alignment target is read out of the big patch", B + "bigpatch.cpp", 219,
     U + "bigpatch.cpp", 204, "patch = bGridPoints[i].patch; ... gridPoint(qx,qy,vx,vy,vz,patch)",
     "every alignment of the growth, through ReadPatchPoints at align_patches.cpp:43",
     "that id becomes the key of matchList (align_patches.cpp:255 built, 251 upstream), then "
     "currentPatch (296 built, 292 upstream), then field zero of the alignment (431 built, 424 "
     "upstream), then the second column of rel.csv"],
]

ours = [
    ["the rel.csv writer of the growth", U + "simpaper10.cpp:450", B + "simpaper10.cpp:557",
     "performance/00001 only, and only to turn OUTPUT_DIR into outPath(); corrections/00004 adds "
     "the one line os << std::setprecision(9). Upstream already writes all thirteen fields",
     "upstream", "the container, its keys and its values are upstream's"],
    ["OpenBigPatch on an existing folder", U + "simpaper10.cpp:219", B + "simpaper10.cpp:326",
     "performance/00001, the path expression only", "upstream", ""],
    ["startingPatch from the in memory map", U + "simpaper10.cpp:222", B + "simpaper10.cpp:329",
     "none: the lines appear in performance/00001 as context and are unchanged", "upstream", ""],
    ["the two erases", U + "simpaper10.cpp:421 and 428", B + "simpaper10.cpp:528 and 535",
     "none: context of performance/00001", "upstream", ""],
    ["the geometry write loop and its ignored return", U + "simpaper10.cpp:445 and 446",
     B + "simpaper10.cpp:551 and 553", "performance/00001, the path expression only",
     "upstream", "Patch::Write itself is byte identical in the two trees (upstream 175 to 215, "
     "built 195 to 235)"],
    ["the id carried from the big patch into the alignment", U + "bigpatch.cpp:204 and "
     "align_patches.cpp:251, 292, 424", B + "bigpatch.cpp:219 and align_patches.cpp:255, 296, 431",
     "none: bigpatch.cpp is changed only by the std::sort of the chunk listing added at built "
     "line 115, align_patches.cpp only at upstream 211 (built 215, the right angle test) and "
     "upstream 397 (built 404, the representative transform)", "upstream", "the two corrections in align_patches "
     "change which alignments are found, not which id is written on one"],
    ["the u mode and its own rel.csv writer", "not in upstream", B + "simpaper10.cpp:828 to 934",
     "performance/00001 adds the whole mode", "ours",
     "never called by the runner of seed-search-1447, so it wrote nothing on seed34"],
    ["one output folder per run", "upstream compiles OUTPUT_DIR in (parameters.h:2, "
     "\"d:/pipelineOutput\")", B + "common_types.cpp:11 to 27, SIMPAPER_OUTPUT_DIR",
     "performance/00001", "ours",
     "it changes which folder is reused, not whether a folder is reused: with upstream's compiled "
     "constant every run of g writes into the same folder, so an interrupted growth followed by "
     "another is upstream's default case, not an arrangement of ours"],
]

with open(E + "relcsv-writers.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# the places that write a rel.csv, read in the source that built the binary the "
                "ten seeds ran. built_line and upstream_line are grep -n line numbers in the two "
                "trees named in the header of tools/source_sites.py. container_iterated: what the "
                "loop walks. keys_come_from and values_come_from: where the two columns are "
                "created. wrote_seed34: whether this writer produced the file the crash was found "
                "in."])
    w.writerow(["writer", "built_file", "built_line", "upstream_file", "upstream_line",
                "statement", "container_iterated", "keys_come_from", "values_come_from",
                "wrote_seed34s_rel_csv"])
    for r in writers:
        w.writerow(r)

with open(E + "id-allocation.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# every site where a patch id is created, recorded, written or dropped, in the "
                "growth. condition: when the line runs. consequence: what is left behind. The "
                "rows are in the order the growth reaches them."])
    w.writerow(["site", "built_file", "built_line", "upstream_file", "upstream_line", "statement",
                "condition", "consequence"])
    for r in sites:
        w.writerow(r)

with open(E + "upstream-vs-ours.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# for each site of the orphan path: where it is upstream, where it is in the "
                "built copy, which patch of the laboratory's series touches it, and whose code "
                "the site is. verdict is upstream when the site exists and behaves the same in "
                "WillStevens' 62cbc21, ours when it exists only under a patch of this home."])
    w.writerow(["site", "upstream", "built", "patches_of_the_series_that_touch_it", "verdict",
                "note"])
    for r in ours:
        w.writerow(r)

print("written")
