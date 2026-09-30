# orphan-guard: a chain through a patch with no geometry is never built

Opened 2026-09-21 by the coordinator on the owner's instruction «si certo ricostruisci ora» and the
director's decision of 13:18:10Z. PLAN 47's first change. Written before a line is changed.

## What is being fixed, and it is not the line that throws

`badpatch-crash` established it, and the numbers are its:

- `patches` is keyed by the `patch_<n>.bin` files on disk; `am`, the `AlignmentMap`, is keyed by
  `rel.csv` **plus the reverse edges**, and `AugmentAlignmentMap` inserts every alignment target as a
  key **without checking that the target was loaded**.
- So a chain can be assembled through a patch that has alignments and no geometry, and the first
  call that asks for its geometry throws: `patches->at(p)`, `badpatchfinder.cpp` line 436, in the
  branch that places the **last** element of the chain.
- On `PHerc1447-seed34`: `rel.csv` names **104** ids with no file, exactly **73** can be the second
  element of a kept length two chain, and those 73 are **exactly** the 73 the crash reported. The
  counts close with no residue.
- **Seeds 01, 15, 26, 11, 35, 38, 40 and 48 have zero such ids**, counted over 457,647, 384,333,
  304,256, 230,513 and 284,922 relation rows. This is one tree, not the chain's normal state.

**The guard goes where the chain is assembled, not at line 436**, which is one of three places that
would throw. A chain through a patch with no geometry is never built.

## What the change must do

1. Refuse to build a chain containing an id that is not a key of `patches`.
2. **Count** what it refused: the number of chains skipped and the number of distinct ids involved,
   written to the stage's own log and to a row beside that tree's orphan count. A run that silently
   drops 73 chains must say so as loudly as one that dies.
3. Nothing else. No other behaviour of the stage moves.

## The bar, from the director, and it is not negotiable

- The delivered sheets of **seeds 01, 15 and 26 byte identical** to today's. Those trees have zero
  orphans, so identity is expected by construction; the runs happen anyway, because «expected by
  construction» is the kind of sentence this home has been wrong about four times in two days.
- **seed34's `c` stage runs past the point of the crash**, that is past 21 s, and reports its skipped
  chains.
- The binary is built by the same route as the one that crashed, whose plain rebuild came out **byte
  for byte equal** (sha `340d157c...`), so a difference in output is a difference the change made.

## Where the change is made

On the **laboratory's copy**, never in `/data/repositories/scrollreading` directly. The patch is
prepared as a diff with its own file, the way every upstream contribution of this home is.

## What would make it fail honestly

A delivered sheet of seeds 01, 15 or 26 differing by one byte, which would mean the guard fires
where it was not supposed to; seed34's stage dying at the same 21 s, which would mean the assembly
is not where the chain is built; or the skipped count coming out zero on seed34, which would mean
the guard is not reached at all and the diagnosis pointed at the wrong place.
