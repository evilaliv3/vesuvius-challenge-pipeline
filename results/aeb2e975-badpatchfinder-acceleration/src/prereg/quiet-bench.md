# quiet-bench: the headline numbers of the `c` stage and of the grid cube, re measured on a quiet machine

Opened 2026-09-21T23:25:22Z (`date -u`), PLAN 58, on the director's direction of
2026-09-21T21:42:53Z, point 2:

> Then the quiet bench (PLAN 58), about six hours, nothing else running: the c stage pairs on
> seeds 26, 40 and 38 (slow once, fast three times, four threads, fresh copies), the stage table
> of the three grid cubes gate on and gate off; each run with cores busy before it in the CSV.

and PLAN 58's own row, «three arms, the third without `performance/00002`, on the owner's word»,
whose reason is `context/coordinator/reviewed/2026-09-21-a8s-numbers-cannot-be-read-back.md` and
the director's verdict of 2026-09-21T22:18:55Z in that same file.

Written before any number of this study exists, builds included. Machine at the moment of writing,
first line of `/data/scrollagent/tools/machine.sh`:
`load 4.36 / 18   cores busy 3.2 / 24   MemAvailable 104.0 GB / floor 20   our disk 415 GB / 492   root free 6 GB`.
The machine is **not yet quiet**: `runs/rev1/c-stage-on-0139` is running its timing rounds under
PGID 3103896 and `runs/rev1/unroll-two-arms` is running `tools/measure_arms.py` under PGID 3127560.
Neither is touched. No run of this study starts until both process groups have ended, waited on by
PID with `kill -0 -- -PGID`, never by a name pattern.

## 1. The question

Two headline figures of this home were measured on a machine carrying other work, and a third has
no evidence on this disk at all. This study measures all three with nothing else running:

1. What the `c` stage costs on seeds 26, 40 and 38 of `runs/rev1/seed-search-1447`, in the arm
   that ships today (`plain`) and in the arm the pull request proposes (`c2`).
2. What `patches/performance/00002-selection-render-state-and-precomputed-normals.patch`, the
   patch the prepared text A8 claims seventeen times for, is worth **on this disk tonight**.
3. What one grid cube of `out/grid-0139-12x12x12` costs stage by stage, gate on and gate off, in
   seconds that can be read as seconds and not only as proportions.

## 2. What is not in this study

**Identity is not re measured.** It does not depend on load. What stands as it is:
`c-stage-cost/evidence/identity.csv` (585 rows), `c-stage-cost/evidence/identity-seed11-untouched.csv`
(40 rows) and `c-stage-on-0139/evidence/identity-by-tree.csv` (936 files written by the downstream).
No claim about bytes is made here, for any arm, and in particular none for the `noA8` arm.

No change is proposed and no patch is written. Nothing is published from here.

## 3. Part 1, the `c` stage, three arms on three seeds

Seeds 26, 40 and 38 of `runs/rev1/seed-search-1447/out`, whose growth trees hold 9,512, 14,959 and
22,205 patch files. Every run is on a **fresh copy** of the growth tree, made with `cp -a` into this
study's own `scratch/`; nothing under `seed-search-1447` is ever written, and no run happens in
place. Four OpenMP threads for every run of every arm. **One run at a time and nothing else of ours
on the machine.**

| arm | series | repeats per seed |
|---|---|---|
| `plain` | `build` + `performance` + `corrections-inert` + `corrections/00001..00006` | once |
| `c2` | `plain` plus `corrections/00007`, `00008`, `00009` | three times |
| `noA8` | `plain` with `performance/00002` removed | three times on seed26, once each on seed40 and seed38 |

`plain` and `c2` are the binaries `c-stage-cost/scratch/bin/plain/simpaper10` and
`.../bin/c2/simpaper10`, the ones whose sha256 are in `c-stage-cost/evidence/binaries.csv`. They
are read, never written. `noA8` is a new build, laid down and compiled by the route of
`c-stage-cost/tools/lay_source.sh` and `c-stage-cost/tools/build_one.py`, in this study's own copy
of the source tree.

**Known reference, checked before any arm runs.** A fourth build, `plain-repro`, is laid down from
the same patch files as `plain` and compiled by the same route. Its `sha256_stripped` must equal
that of `c-stage-cost/scratch/bin/plain/simpaper10`. If it does not, the `noA8` arm is not a
controlled difference, the row says so and the arm's numbers are withdrawn. This is the outside
reference of the addition of 2026-09-20T13:56:32Z, taken against a binary built before this study
existed.

## 4. Part 2, the stage table of three grid cubes, gate on and gate off

The three cubes NOTE 1 of `runs/rev1/cube-time-map` fixed before any of them had been meshed:
`z09216_y03840_x03840`, `z09472_y02560_x02560`, `z09728_y03712_x02560`, of
`runs/rev1/scrollfiesta-grid-0139/out/grid-0139-12x12x12/cubes_PRED`. The binary is
`runs/rev1/cvt-parallel/scratch/bin/cube_mesh-MBF`, the same one, its sha256 written in every row.
The environment is `cube-time-map/tools/run_cube.sh` unchanged but for the one variable that is the
arm: `BPA_GROW_WIND_TOL=0.45` is the gate on and `BPA_GROW_WIND_TOL=0` is the gate off, which is
how `cvt-parallel/tools/run_cube.sh` writes it. Four OpenMP threads, halo 13, no timeout, final
dump only, trim inset 0, umbilicus 3163/3276 of that grid's own manifest, wrap pitch 13.25.

Every cube is meshed into **this study's own `out/`**. Nothing under `cube-time-map/out/` or
`cube-time-map/evidence/` is written.

Six runs, one at a time, gate on first so that the arm that ships is the one measured earliest in
the quiet window. Every stage of a cube comes from the same run, as `cube-time-map` required, and
the stage lines are read from `cube_mesh`'s own output by `cube-time-map/tools/stage_map.py`
re pointed at this study's CSV, never from the `Timings:` summary.

## 5. The order, and why

The two `plain` runs on seeds 40 and 38 are about two hours each and the two `noA8` runs on the same
seeds are longer still, so the order is fixed now, before any number, cheapest and most informative
first, and it is not changed afterwards:

1. seed26, all three arms (`plain` once, `c2` three times, `noA8` three times).
2. Part 2, six cube runs, gate on then gate off.
3. seed40: `plain` once, `c2` three times.
4. seed38: `plain` once, `c2` three times.
5. `noA8` on seed40, once.
6. `noA8` on seed38, once.

seed26 is where A8's contribution is visible in minutes rather than hours: on that tree the
enumeration this study's other patches attack is cheap (`c-stage-cost/evidence/runs.csv`: `plain`
39.0 to 39.8 s over four runs, `c1` 47.6 to 50.2), so what is left is the placement A8 changed.

## 6. Caps, declared before the fact

- **Time caps on the `noA8` arm only**: 3,600 s a run on seed26, 14,400 s a run on seed40 and on
  seed38, applied with `timeout -s TERM`. `performance/00002` carries the parallelisation of the
  placement loop, so the arm without it is slower than `plain` by an unknown factor and a run that
  never ends is not a result. **A cap that bites is written as a bound**, «greater than N seconds,
  stopped by the cap at HH:MMZ», never as a time. The director's note of 22:18:55Z asks for no cap;
  the coordinator's instruction of 23:2xZ sets these two, and the disagreement is recorded here
  rather than resolved by this study. No cap of any kind on `plain` or on `c2` or on any cube.
- **The bench is longer than six hours in the worst case**, about thirteen if both `noA8` caps bite,
  and the order of section 5 is what makes that acceptable: every number but the last two lands
  inside about five and a half hours.
- Nothing starts while cores busy is above **1.0 of 24** read from `/proc/stat` ticks, which is this
  study's quiet bar and is stricter than the hard cap of 22 because a bench measured beside other
  work is worth nothing. A run refused by the bar is written down as refused, with the reading.
- Disk: the copies are 1.1, 2.1 and 2.8 GB and each is removed as soon as its row is written, so
  this study holds under 10 GB of trees at any moment. `/data` carries 415 GB of our 492 GB budget
  at the moment of writing. **If a copy would take the total past 470 GB the bench stops and says
  so.** `df -B1G /data` is read before each part and the reading written into `evidence/disk.csv`.
- `TMPDIR=/data/tmp`. Nothing here needs the network and nothing costs money.
- No process group this study did not create is signalled, ever. No `pkill -f`, no `pgrep -f`.
- Nothing is written outside `runs/rev1/quiet-bench/` and `ledger/ledger.csv`.

## 7. What would make this fail honestly

- `plain-repro` not reproducing `plain`'s stripped sha256: the `noA8` arm is withdrawn and the
  outcome says the patch series could not be laid down twice to the same binary.
- The machine not becoming quiet: the bench does not start, and the outcome says so with the
  process groups that were still running and the time it waited.
- A `c` stage returning non zero: the row is written with its return code and the seconds are not
  quoted as a time for that arm.
- A cube whose stage lines do not sum to near its wall clock: written as it comes out, not smoothed.
- The `noA8` arm hitting its cap on seed40 and on seed38 and finishing on seed26: then A8's factor
  is stated on seed26 only, with the two bounds beside it, and the text that needs it says
  «measured on seed26 tonight» and nothing else.
- A spread over the three repeats of `c2` wider than the difference it is used to argue: then the
  difference is reported as within the spread and no factor is claimed.
