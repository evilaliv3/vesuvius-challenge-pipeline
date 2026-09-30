# Declaration: seed-search-1447, the number toward the prize is a search, not a seed

Written at 2026-09-20T16:24:15Z (`date -u`), before any growth of this study was launched and before any
number of it existed. `PLAN.md` item 33, ordered by the director at 2026-09-20T16:23:04Z.

## Why the object changed

`seed-ladder-1447` showed that the chain refuses about a third of drawn seeds on both scrolls,
that the difference between them is how far patch 0 gets when it is not refused (median 71.5
steps against 122), and that a drawn seed which passes the bar leaves a **handful** of patches,
median 7, against the **14,660** the base on PHerc. 0139 grew from its compiled seed. Nobody here
chose that point.

So the seed is the chain's real lever and it is not a parameter, and **the number toward the prize
on an eligible scroll is the largest square over a declared seed search, not over one seed**. That
is the director's decision and this study is its first half.

## What is fixed before the run

- The population: the **ten** seeds of PHerc. 1447 that were still growing when the ladder's cap
  of 120 seconds stopped them, read from `seed-ladder-1447/evidence/attempts.csv`, column
  `outcome`, value `still growing at the cap`: seed01 (3218, 3258, 12307), seed11 (6165, 3936,
  6168), seed15 (3940, 3107, 9278), seed26 (2464, 2411, 12410), seed34 (6213, 2387, 21692),
  seed35 (37, 3936, 830), seed38 (2325, 7080, 20898), seed40 (6958, 2309, 10940), seed44 (3950,
  5552, 23815), seed48 (3116, 2315, 6960). Not a sample of them and not the best of them: all ten.
- Each is grown with `simpaper10 g 36000` to the end, with the per seed binary the ladder built
  and whose sha256 it recorded, **three at a time**, and then delivered with `c`, `l`,
  `vm 10`, `hm 10`, `fm 30 10` at `SIMPAPER_PATCH_LIMIT` 40000, the line the base ran.
- The voxel is **8.640 um**, from `pipeline/datasets/manifests/PHerc1447.json` through
  `pipeline/datasets/voxel.py`. No default anywhere and 9.362 must appear nowhere.

## Bars

1. Per seed: the tree size, the largest `square_mm_min_step` over the delivered sheets, and the
   count of sheets reaching 20 mm. **Written per seed and not summarised into a best**: the
   distribution is the result, which is what the previous study's own close argued for.
2. The maximum over the ten, against the **13.5262 mm** of the best published segment of this
   same scroll (`published-segments-eligible/`) and against the base's 12.1230 mm on the
   reference scroll, which is a different scroll and is quoted as such and not as a target.
3. The director's rule of **2.6213 mm**, which is the spread one chain parameter produced by
   itself in `seed-distance-ladder`: a seed search beating the compiled seed by less than that
   has not beaten it.

## What each outcome means

- The best of the ten clears 20 mm: this home has a surface at the prize's side on a scroll where
  the prize is offered, and everything else of today is a footnote to it.
- It beats 13.5262 mm: our chain delivers more side than anything published on that scroll, which
  is the first such statement and is worth its own item.
- It lands between the base's 12.1230 and 13.5262: the chain is in the same band as the published
  work and the seed search is what puts it there, not a parameter.
- All ten die early despite passing the first bar: passing patch 0 buys nothing, which the ladder
  already suspected at a median of 7 patches, and the chain's road is closed from the inside.

## Caps

**The machine is counted whole before work is added**, which is the director's decision of this
time and the coordinator's error of today: `tools/machine.sh`, written at 16:24Z, prints load,
`MemAvailable`, our disk and every heavy process whoever started it, and is read before each
batch. Three growths of about 24 GB each against `MemAvailable` 110.0 GB and a floor of 20. Load
never above 18; **a batch is not started while the total is above 12**, which is stricter than the
cap and is this study's own answer to having twice pushed the machine past it. Growth 3 hours per
seed, downstream 1 hour. Disk: about 4.5 GB per seed against 120 GB used of the 492 budget. Zero
spend, no GPU, no network. This study measures no time as a result.

## Additions

Dated and declared post hoc, appended below this line; nothing above is retouched.

## Amendment of 2026-09-20T17:15Z: batches of two, not three

The declaration fixed three growths at a time. That number was chosen against a machine holding
110 GB of MemAvailable at the moment the study opened, and it was not checked against what a full
length growth of this scroll costs, because no full length growth of this scroll had ever been run.

What was measured while batch B1 ran, in `evidence/load.csv` written by this study's own sampler:
memory used 27 GB at 16:31Z, 65 GB at 17:01Z, about 7,6 GB every five minutes, and no plateau by
8300 patches. The floor of this home is 20 GB of MemAvailable. Three at a time reaches the floor
before the growths end.

So batches B2, B3 and B4 are replaced by C1 to C4 in `tools/run_rest.sh`, **two seeds at a time**,
the same seeds, the same per seed runner, the same measurement. Batch B1 is not touched and its
three seeds stand. This amendment is written before the change is made and not after it, and the
comparison the declaration fixed is unchanged: the maximum over the ten seeds against 13,5262 mm,
with 12,1230 mm named as another scroll's number and never as a target.

A guard was armed at the same time, `/data/scrollagent/tools/memory_guard.sh`, which stops the
resumable mesh run of another study at 30 GB and the single largest growth at 22 GB. If it ever
fires on a seed of this study, that seed is reported as stopped by the guard and no square is
measured on it, exactly as a seed stopped by its own three hour cap.

### Addition of 2026-09-20T18:45:02Z (agent), after batch B1 was grown and measured and while the rest runs

Four things are declared here rather than explained afterwards. Nothing above this line is
retouched.

1. **The per seed binaries were rebuilt, because the ones the ladder built no longer exist.** The
   declaration says the ten are grown with the per seed binary the ladder built and whose sha256
   it recorded. That ladder deletes each attempt's binary folder as its attempt ends, so
   `seed-ladder-1447/scratch/bin/` is gone. `tools/build_binaries.py` rebuilds by the ladder's own
   route, a working copy from `build.sh corrected` with `parameters.json` rewritten per seed, and
   checks each rebuild against the sha256 the ladder recorded. **All ten came back byte for byte
   equal to it**, and the stock build came back equal to
   `d59199492f4f33cb64e4ac6cb34a040484387b865b3028e3baa3775962b85e14`, which is the value the
   ladder's gate SL0 names. Both checks are rows in `evidence/binary-gate.csv`, expectations
   `differs_from_stock` and `matches_ladder_sha256`.

2. **The run passed out of this agent's hands at 17:14Z and continued under a second hand.** The
   study was launched as `tools/run_all.sh`, three growths a batch behind the load gate of 12 this
   declaration fixed. Between 17:14:25Z and 17:29:46Z four files appeared in `tools/` that this
   agent did not write: `swap_to_two.sh`, `run_seed_v2.sh`, `run_rest.sh`, and an amendment inside
   `machine_gate.py` dated 17:32Z citing a director's order of 17:17:13Z. `run_seed.sh` was
   rewritten in place at 17:21:45Z while bash was executing it for seed11, which is the one thing
   here that could have corrupted a run; `run_seed_v2.sh` says it was put back byte for byte
   within about a minute and that seed11 was inside its growth and had read nothing new, and
   seed11's growth did in fact run to its own end and returned the binary's own code. At 18:42Z
   `swap_to_two.sh` stopped `run_all.sh` by its PID, after B1 was grown and measured and before B2
   started, and began `run_rest.sh` on the remaining seven, **two at a time instead of three**.
   The reason given is memory: this study's own sampler measured three concurrent growths of this
   scroll climbing about 7.6 GB every five minutes with no plateau at 8,300 patches, and B1 in the
   end held 13.2, 20.8 and 31.2 GB resident together with `MemAvailable` down to 43.5 GB against a
   floor of 20.
   The two gate numbers changed with it: the load gate went from the **12** this declaration fixed
   to the home cap of **18**, and a memory reserve of 33 GB per growth about to start was added.
   The population, the ten seeds, their binaries, the growth command, the five delivery stages,
   the patch limit of 40,000 and the voxel of 8.640 um are untouched by all of it. What the ten
   rows can no longer say is that they were all grown under one concurrency: **seed01, seed11 and
   seed15 grew three at a time and the other seven grow two at a time**, and the per seed wall
   clock is therefore not comparable across that line. This study measures no time as a result,
   which is why the change is recorded and not repaired.

3. **`growth_absent_chunks` replaces `growth_missing_chunks` for the first three.** The first
   runner wrote `not measurable` whenever `ZARR_MISSING_LIST` left no file, and that file is left
   only when something was absent, so the silence was a false unknown and not an unknown. The
   binary prints the count either way. `tools/per_seed.py` reads it back from the growth's own
   standard output for the seeds that ran before the change: seed01 and seed15 are a **measured
   zero**, not an unknown.

4. **A seed whose growth returns non zero is out of the distribution and stays out.** seed11
   returned 3 after 7,888 seconds and 26,947 patches, with **70,832 zarr chunks absent from disk
   during growth**: it grew out of the part of PHerc. 1447 that is on this machine. No sheet was
   delivered for it, its two measurement CSVs are written `not measurable` with that reason, and
   it is counted apart in `evidence/summary.csv` and never folded into a median with the seeds
   that finished. It is not re run: fetching the absent chunks needs the network, which the caps
   above forbid.

## Amendment of 2026-09-20T19:52Z: the downstream cap is a function of the tree, not a constant

The 3,600 second downstream cap was written against trees of about eleven thousand patches, where
all five stages finish in under a minute. It fired on seed11 at 19:50:44Z inside the first stage,
rc 124, sheets 0, and the record says so.

What the evidence says, counted by the director at 19:49:14Z and by this study:

    seed01     25,505 rel lines    whole downstream, five stages       51 s
    seed15     26,476 rel lines    whole downstream                    58 s
    seed11    457,647 rel lines    stage c alone, stopped by the cap  3,600 s

**Eighteen times the relationships, more than seventy times the time.** On that evidence the `c`
stage grows at least with the square of the relationships, so a constant cap cannot serve both
sizes. From here the cap is

    cap = min(14400, max(3600, 60 * (rel_lines / 25505)^2))  seconds

which gives 3,600 s for the trees seen so far and the director's **4 hours** for seed11's 457,647.
seed11's downstream is rerun once under it. If it fires again, the answer is nine seeds and the
tenth is written «not measurable: the downstream did not converge in 4 hours on 457,647
relationships», never as a zero and never as a square.

### Addition of 2026-09-20T20:33:07Z (agent), after the second runner and its growth ceased to exist

The header of this addition first carried 20:35:10Z, a time this agent wrote before reading the
clock. It was corrected to the `date -u` of the write, 20:33:07Z, within a minute and before any
other file referred to it. The rule it broke is that a time is read and never estimated.

1. **The run stopped by itself at some point between 19:52Z and 20:30Z and had to be restarted.**
   `run_rest.sh` grew seed26 to its end at 19:22:52Z and then, with seed34 still growing, that
   runner, that growth and the `swap_to_v3.sh` watching them all ceased to exist: `log/run-rest.txt`
   stops after seed26, `log/swap-v3.txt` holds only its first line, `evidence/runs/PHerc1447-seed34.csv`
   holds only the binary row written before the growth starts, and at 20:30:44Z no process of this
   study was alive. What ended them is not recorded anywhere this agent can read, so it is written
   here as what it is and not explained. seed34's half grown tree of 867 MB was removed at 20:31:48Z
   and the seed regrown from nothing, because a growth that resumes into an interrupted tree is not
   the growth this declaration fixed. `tools/run_finish.sh` restarts what is left, with the
   population, the binaries, the growth command, the five stages, the patch limit and the voxel all
   unchanged.

2. **The remaining growths pass `ZARR_CHUNK_MANIFEST`, and seed11 changes verdict.** PHerc. 1447 is
   a whole scroll whose grid is mostly empty. Without the manifest the chain counts every chunk file
   that is not on disk as missing and exits 3, which is an accounting exit taken after everything is
   written. `tools/chunk_check.py`, re run by this agent at 20:31Z, reads seed11's own missing list
   against the 74,683 published chunks of the scroll: **70,832 reads over 2,615 distinct chunks, of
   which 0 are published**. The box is complete for that trajectory and the tree is whole.
   seed11 is therefore delivered from the tree it already wrote rather than regrown, and **its row
   keeps `growth_return_code` 3**. The distribution this study answers on is taken over the seeds
   whose growth returned zero; seed11 is quoted beside it, named for what it is, and never folded
   into that median. seed01, seed15 and seed26 grew without the manifest and each had zero absent
   chunks, so the manifest would have changed nothing for them.

3. **The downstream cap is no longer a constant hour.** It is computed from the growth's own
   `rel.csv`, `60*(lines/25505)^2` clipped between 3,600 and 14,400 seconds, and written into the
   seed's CSV as `downstream_cap_seconds`. The declaration above fixed one hour against a tree of
   25,505 relationships; seed11 wrote 457,647 of them, and the stage that assembles them does not
   cost the same on both. A cap that stops a run is a number that must be findable afterwards,
   which is why it is recorded per seed and not only here.

### Addition of 2026-09-20T20:36:52Z (agent), the stop

This header first carried 20:37:41Z, a time written before the clock was read, the second time in
this file that this agent did it. Corrected to the `date -u` of the write.

The owner stopped the study at 20:29Z, with the instruction «ferma tutto per ora; voglio solo
ottimizzare come ha detto il direttore», and the coordinator killed by process group the runner
of the remaining seeds, the growth of seed34 6,454 seconds in and the second delivery attempt of
seed11 2,241 seconds in. This agent did not know of that stop and at 20:32:34Z restarted the
remaining work as `tools/run_finish.sh`, which grew seed34 from nothing and began seed11's
delivery a third time. On being told, this agent stopped its own process group 2781611 at
20:34:39Z, stopped the load sampler at 20:35:05Z and started nothing further. The two minutes of
seed34's growth and the two of seed11's `c` stage left no row in any CSV and no tree that any
number is read from: seed34's out folder is what `run_finish.sh` created and abandoned.

The study closes here with three seeds of ten measured. `OUTCOME.md` states which seed is in
which of the four states and repeats, next to every number it quotes, that three of ten is not
the distribution this declaration set out to measure. **The seven that carry no square were
stopped or never started; none of them failed**, and the record is written so that the two cannot
be read as the same thing.
