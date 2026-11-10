# src/read/m3m4: how the Rectina m3 and m4 maps were read

The maps of Rectina m3 and m4 in the article were read on graphics processors with the read job of the study, not with the public `rectina_read.py` of this folder (that one is the same as in the October version and was not run for these two checkpoints). The three files here are the read path as it was used, copied byte for byte from the study:

- `m5m6_read.py CHECKPOINT READS_JSON OUTDIR`: builds a job file and starts `gpr_podread.py` on it. In the study the checkpoint of Rectina m3 was called M5 and that of Rectina m4 M6, which is why the names `m5m6` appear in file names. Environment: `M5M6_READ_DEVICE` (cuda by default), `M5M6_VSRC` (the `vesuvius` source tree of villa main at 7e6b82164 with the training patch of `src/evidence/training`), `M5M6_STACKROOT` (the folder of the stacks named in `reads.json`), `M5M6_THREADS`.
- `gpr_podread.py`: the job runner. It refuses an environment that holds access tokens.
- `gpr_rv2gpu.py`: the reader module, a copy of the read loop of the earlier reader with its credit in the first line: the lattice follows the crop of the checkpoint, four lattice origins, two views, starts as listed in `reads.json`.

`src/evidence/reads/reads.json` lists the fourteen units read (eight held-out windows rendered from the training volumes, six controls), the seven starts, the 17 plane depth, and the sha256 of each stack. `reads-m3-ag1.csv` and `reads-m4-ag1.csv` are the per start records of unit ag1.

Same as October: the map is a ranking score, not calibrated. Not the same: the patch is 128 pixels for m3 and 384 for m4, the renders are the bicubic renders of `src/render/m3m4`.

Not tested here: these files were not run again for this folder; the maps they wrote are the ones scored in the article. The file paths inside the scripts are the paths of the machine of the study, kept as they were.
