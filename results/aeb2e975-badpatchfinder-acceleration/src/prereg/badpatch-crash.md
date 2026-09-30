# badpatch-crash: which `.at` throws, on which key, and why that key is missing

Opened 2026-09-21 by the coordinator on the owner's instruction: «fai una ricostruzione con i
simboli e trova la problematica in badpatchfinder». Written before any number of this study exists.
**It diagnoses and changes nothing.**

## What is known without a debugger

`PHerc1447-seed34`, 28,054 patches, 505,213 relations, its `c` stage run with no cap:

    C40 stage 'c' rc=134 in 21 s, sheets 0
    terminate called after throwing an instance of 'std::out_of_range'
      what():  map::at

and the stage's log dies counting **35,206, 35,207, 35,208**. The `c` stage is
`badpatchfinder.cpp`, which has **one** line carrying `.at(`, line 428:

    for(int p : i)
        if (count==0)  PlacePatchInto(st, patches->at(p), p, aftx, true);
        else           for(const auto &al : am.at(p))

`AlignmentMap` is `std::map<int,std::vector<alignment> >` (`common_types.h:127`) and `patches` is a
`std::map<int,Patch>*`, so **both** throw exactly this message and the message cannot tell them
apart. Nine of the ten seeds of this search do **not** hit it: seeds 11, 35, 38, 40 and 48 write
eight to seventeen megabytes and are killed by their caps while still working, and seeds 01, 15 and
26 finish. This is one tree's fault, not the chain's general behaviour.

## What is measured

1. A build of the **same source by the same route** with debug symbols, differing from the binary
   that crashed in the symbols alone; its sha256 recorded, and the crash **reproduced** on the same
   tree before anything is read from it. A crash that does not reproduce is a different study.
2. The **stack at the throw**, from a core or from a debugger stop: which of the two `.at` calls,
   in which function, from which caller.
3. The **key**: the value of `p` that is missing, and which container is missing it.
4. Then the why: is that patch number present in the patches map, in the alignment map, in the
   growth's `rel.csv`, in the patch files on disk? One row per container, for that key.

## What this study may not do

It may not change a line of `scrollreading`. A fix changes what the chain produces and needs its own
declaration and its own bar; this one answers **where and why**, and stops.

It may also not conclude that the crash explains any other seed's failure. Five seeds are killed by
caps while working and that is a different question, which the uncapped runs are answering now.

## What would make it fail honestly

The crash not reproducing under the debug build, which would point at the optimiser or at
uninitialised memory and would be said plainly; or the missing key turning out to be present in
every container examined, which would mean the throw is somewhere the line reading did not find and
the study says so instead of forcing the hypothesis.
