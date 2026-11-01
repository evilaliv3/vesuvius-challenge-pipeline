# src/render: how the Rectina stacks were rendered

This folder documents the renderer that produced the surface volume stacks the Rectina ink reader was trained and read on. It is a record of a
recipe, not a new component. It does not replace the render component of the public chain.

## Which renderer this is, and which it is not

The Rectina stacks were rendered by the villa tool vc_render_tifxyz built from the upstream villa commit a4979b99004934955784ea19b30da66cfe5f9ead plus one patch,
pas-p1bcpp.patch (sha256 6138aebd6b794a6f40710a562d10b148dd6c52cc20c23316300abd1db615c9db, seven files, in this folder). The binary built from it had sha256 15252e5b61e64938e2ee4b51a3742883e27fe18f4421bfd8343872ebdb796920.

That is not the binary of the public render component (src/components/render, binary sha256 8401cea2..., 28 slices by default,
config/default.json). A stack rendered by that component is a different stack: different upstream commit, different interpolation
and normals code, uint8 style output, 28 planes. The two were not compared for equality of the maps they lead to. Anyone who wants the stacks the
Rectina maps were read from must use this recipe, not the component's default.

One control unit is the declared exception: its stack was rendered by another build (villa a4979b99 with the merged bicubic change, no patch)
as uint8 and read as stored. The stacks file records it as the only stack without a divisor.

## What the patch adds

The patch is a delta of 7 files over upstream a4979b99. It adds to vc_render_tifxyz four options, with the help text of the patch: --p1bf-float32 (float32 zarr
output, no cast to uint8; for a uint8 source volume, zarr output only), --p1bf-global-origin (surface coordinates taken from the global canvas pixel index, so a tile
does not depend on its crop), --p1bcpp-bilinear-normals (the surface normal blended bilinearly between the 4 node normals; needs linear surface interpolation)
and --interp (volume sampling, trilinear or tricubic Catmull-Rom; tricubic needs --p1bf-float32). The stacks used --interp trilinear.

## Render settings of the Rectina stacks

Command line flags, as recorded in the render records of the control units: --scale 1 --group-idx 0 --num-slices 23 --slice-step 1 --flip-normals
--pyramid 0 --surface-interpolation linear --p1bf-float32 --p1bf-global-origin --p1bcpp-bilinear-normals --interp trilinear, with --crop-x, --crop-y,
--crop-width, --crop-height giving the tile and --voxel-size / --voxel-unit micrometer from the volume. Planes: 23 at step 1, plane 11 on the surface.
(The five-model bench rendered 35 planes and cut the central 23 from them; the stacks handed to the reader hold 23 planes either way.)

Storage: the renderer samples in float32 on the 0 to 255 grey scale. The stacks hold uint16 = rint(clip(v, 0, 255) * 256). The reader divides by
65280 (= 255 * 256) to get values between 0 and 1. The stacks CSV of the read run lists 13 uint16 stacks, all with 23 planes and divisor 65280.0.

## What is in this folder

README.md, pas-p1bcpp.patch, build-recipe.sh (the cmake configure line and the dependency commits), PINS.csv (every hash and commit),
test-result.csv (the checks, one row each, with what was expected), SHA256SUMS.

## What was and was not tested

Tested by a registered tool on the real inputs (test-result.csv): the patch file hash equals the pin and the hash in the first build record;
the patch touches the declared 7 files; the villa clone holds the pinned commit; git apply --check of the patch against that commit succeeds in a
throwaway index (the clone is untouched), and the same patch with one flipped byte is refused; the cmake line and dependency commits of
build-recipe.sh equal those of the registered build script; the stacks CSV and a render record carry the documented settings; the encoder line is the documented one;
the rebuilt binary on disk has the pinned hash.

Not tested, and said so: (1) The original binary 15252e5b61e6 is not on disk any more (a cleanup on 2026-10-27 removed it), so its hash is
taken from two records that agree and could not be re-measured. (2) The binary was not rebuilt in this release. A rebuild of 2026-10-28 from the same commit,
patch and recipe gave a different file hash, 8a4ca38c1c16, as compilers do not promise identical bytes; the rebuilt binary reproduced a stored render shard
bit for bit in a reference run (row R1b of the rebuild's reference file, quoted in test-result.csv as R4g). (3) That PR 1818 is an ancestor of the
pinned commit could not be proved in the shallow local clone; the build script checked it when it first built. (4) The equality of the stacks of this recipe
and of the public component was not measured.

## Rebuild

WORK=/some/empty/folder bash build-recipe.sh. It needs network access to clone villa and two dependencies, cmake and a C++ toolchain.
