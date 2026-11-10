# src/render/m3m4: how the stacks of the Rectina m3 and m4 reads were rendered

The October pieces of `src/render` (the patch `pas-p1bcpp.patch`, `build-recipe.sh`, `PINS.csv`) describe the renders that Reader v2, Reader v3, Rectina m1 and Rectina m2 were read on. They are unchanged and are not what m3 and m4 were trained or scored on.

Rectina m3 and m4 were trained on, and scored on, bicubic renders made with the renderer `vc_render_tifxyz` of villa main at commit 7e6b82164 plus three corrections (the derivatives at the border of a tile, the fast conversion to 8 bit, and the vertex normals of villa pull request 2449). The binary of that build has sha256 3bed5ae8f1f887130f07ad0df195c8ecc62b2c843f087c9f46f2625ddd6c26d3 (line `C2` of `binary-hashes.txt`). The three corrections are not copied into this folder as patch files: that is a gap of this release, and the build is named here by its commit and binary hash only.

Settings of the stacks as the tools call the binary: scale 1, group 0 (or the group of the volume), 23 planes at step 1 with the surface at plane 11, flipped normals, pyramid 0, bicubic surface interpolation, voxel size from the volume in micrometers; `render_set_c2_one.py` stores uint16 = v x 256 for the set; the divisor used to read each unit (255 or 65280) is the one `reads.json` gives for that unit.

- `render_set_c2_one.py SEGMENT`: tiled bicubic render of one segment of the set (the 87 training segments and the held-out windows), with a shift probe against the earlier render. `--check-all` is a read only preflight.
- `control_render.py UNIT`: renders again one of the six control units on its old box and compares it with the earlier stored stack under declared gates (`control_render_lib.py` holds the unit tables).
- `binary-hashes.txt`: the sha256 of the binaries of the study, of which `C2` is the one used.

`src/evidence/render/render-manifest.sha256` is the digest of every rendered segment of the training set.

These scripts are the study files, byte for byte, with the paths of the machine of the study and a log line appended to a study ledger that does not exist outside it. They were not run again for this folder and need the volumes, the meshes and the binary named above.
