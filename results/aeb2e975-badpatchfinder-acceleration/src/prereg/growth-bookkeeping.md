# DECLARATION: growth-bookkeeping (PLAN 48)

Written 2026-09-21T15:18:27Z (`date -u`), before any finding of this study exists. Not retouched:
additions are dated and marked as additions.

## What this study is

A read of the source of the growth stage (`simpaper10.cpp` and what it calls) and of the growth
logs already on disk. **No growth, no stage, no pipeline run.** Compilation is allowed only if a
question cannot be answered by reading, and the outcome must say why it was needed.

The fact to be explained, taken from the director's direction of 2026-09-21T14:30:36Z and to be
read back from its CSV before anything else: on `PHerc1447-seed34` the growth wrote a `rel.csv`
naming 104 patch ids with no `patch_<n>.bin` on disk, while the other eight seeds of the same
search that wrote a `rel.csv` name zero such ids
(`/data/scrollagent/runs/rev1/seed-search-1447/evidence/alignment-fanout.csv`, column
`keys_without_a_patch_file`). Those orphan ids aborted the `c` stage at `badpatchfinder.cpp`
line 436.

## The four questions, in the order the outcome answers them

### Q1. Who writes `rel.csv`, and from what

What would answer it: the two write sites in `simpaper10.cpp` (around lines 451 and 739) read in
the source, naming the container iterated, where its keys are created and where its values are
created, each with file and line. Evidence: `evidence/relcsv-writers.csv`, one row per write site
and per container, with file, line and the exact statement.

How it fails honestly: if the write is behind a macro, a template or a helper in another
translation unit that this disk does not hold, the outcome says which symbol could not be
resolved and stops there.

### Q2. Where a patch id is allocated, and whether id and geometry can come apart

What would answer it: the allocation site of a patch id and every site that writes
`patch_<n>.bin`, compared. The question is whether the source admits a path where an id enters
the container that feeds `rel.csv` while its `patch_<n>.bin` is never written, or is written and
then removed. Evidence: `evidence/id-allocation.csv`, one row per site (allocation, insertion into
the rel container, geometry write, geometry delete or skip), file, line, condition under which it
runs.

How it fails honestly: «no such path exists in the source» is a valid answer and is written as
such, with the lines that make the two operations inseparable. If the paths cannot be ordered
without running the code, the outcome says the static read is not conclusive.

### Q3. What is different about seed34's growth

What would answer it: a comparison of the ten growth logs of
`/data/scrollagent/runs/rev1/seed-search-1447/log/` on counts of the lines that the source shows
to be emitted at the sites found in Q1 and Q2 (patch written, patch dropped, error, retry,
threading or memory messages), plus the tail of each log. Evidence: `evidence/log-compare.csv`,
one row per seed, one column per counted pattern, with the command that produced each count
written in the file's comment header.

Cost rule: the logs are large (seed34 is about 4.3 million lines). Counting is sequential, one
log at a time, no parallel sweep, and the machine is read with `tools/machine.sh` before and
after.

How it fails honestly: «the logs do not distinguish it» is a real answer and will be written if
the counted patterns separate no seed. A mechanism will not be asserted from a correlation on
one seed.

### Q4. Ours or Stevens'

What would answer it: the code path identified in Q2 located in the upstream source
(`/data/repositories/scrollreading`, at the commit the binaries were built from) and then in the
patched source used here (`scratch/src-*/patches/` of `badpatch-crash` and `orphan-guard` and of
`seed-search-1447`, with `SERIES.md`), to determine whether the path exists upstream unpatched or
is introduced or enabled by a patch of this home. Evidence: `evidence/upstream-vs-ours.csv`, with
the upstream file and line, the patch file that touches those lines if any, and the verdict per
site. The build route of the binaries actually used is read from
`seed-search-1447/tools/build_binaries.py`.

Verdict values allowed: `upstream`, `ours`, `cannot tell from this disk`. A guess is not allowed.
If the upstream clone is not at the commit the binaries were built from, or if the patch series
cannot be mapped onto the built tree, the verdict is `cannot tell from this disk` and the outcome
says which artefact is missing.

## Rules this study runs under

- Writes only inside `/data/scrollagent/runs/rev1/growth-bookkeeping/`. Nothing is written in
  another study's directory, and no running script is touched.
- Never `pkill -f` nor `pgrep -f`; no process this study did not start is signalled. The machine
  is shared: four growths and other stages run under other process groups.
- Every number reported is read back from the CSV or the file it came from. A number quoted from
  another study's prose is not evidence; its CSV is found first.
- Every CSV is written with `csv.writer` and carries a comment line saying what each column is.
- A claim about the source carries file and line. A count over the logs carries its command.
- Every non trivial action gets a row through `/data/scrollagent/tools/ledger.py`, append only.
- `TMPDIR=/data/tmp`. No network, no spending.
- No dash as punctuation, no AI signature.

## What would make the whole study fail honestly

If the source that the binaries were built from is not on this disk (built tree removed, patches
applied to a copy since deleted), then Q1, Q2 and Q4 rest on a source that may not be the one that
ran, and the outcome says so at the top instead of reporting line numbers as if they were the
binary's. The first action after this declaration is therefore to establish which source tree the
`simpaper10` binary of the seed search was built from.
