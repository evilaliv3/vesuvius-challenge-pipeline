#!/bin/bash
# The patch files are the change, and this is the check that says so.
#
# Two working copies are laid down from nothing by build.sh, which removes its output folder and
# copies the pinned upstream into it before applying the patch groups:
#   A  the series with 00007 alone
#   B  the series with 00007, 00008 and 00009
# Then the edit scripts that wrote the changes are run on a copy of A, and the result is compared
# with B byte for byte. If they agree, the patch files and the edit scripts say the same thing and
# the source that was built is the source the patches lay down.
#
# Writes evidence/patch-verification.csv.
set -eu
S=/data/scrollagent/runs/rev1/c-stage-cost
SRC=$S/scratch/src
HOLD=$S/scratch/held-patches
W=$S/scratch/verify
C1=00008-a-dead-prefix-is-not-extended.patch
C2=00009-frequency-table-of-the-cover-is-a-vector.patch
mkdir -p "$HOLD" "$W"

restore() { for f in $C1 $C2; do [ -f "$HOLD/$f" ] && mv "$HOLD/$f" "$SRC/patches/corrections/"; done; true; }
trap restore EXIT

for f in $C1 $C2; do mv "$SRC/patches/corrections/$f" "$HOLD/"; done
TMPDIR=/data/tmp JOBS=1 "$SRC/build.sh" pure > /dev/null 2>&1 || true
TMPDIR=/data/tmp JOBS=6 "$SRC/build.sh" corrected > "$S/log/verify-lay-A.txt" 2>&1
cp "$SRC/build/corrected/badpatchfinder.cpp" "$W/A-guard-only.cpp"
restore
TMPDIR=/data/tmp JOBS=6 "$SRC/build.sh" corrected > "$S/log/verify-lay-B.txt" 2>&1
cp "$SRC/build/corrected/badpatchfinder.cpp" "$W/B-from-the-patches.cpp"

cp "$W/A-guard-only.cpp" "$W/C-from-the-edits.cpp"
/data/scrollagent/.venv/bin/python "$S/tools/apply_c1.py" "$W/C-from-the-edits.cpp" > /dev/null
/data/scrollagent/.venv/bin/python "$S/tools/apply_c2.py" "$W/C-from-the-edits.cpp" > /dev/null

same=no
cmp -s "$W/B-from-the-patches.cpp" "$W/C-from-the-edits.cpp" && same=yes
{
  echo "# the patch files against the edit scripts that wrote them. A is a working copy laid by"
  echo "# build.sh from the pinned upstream plus the series up to 00007; B is the same laid with"
  echo "# 00008 and 00009 in the series as well; C is A with the two edit scripts run on it."
  echo "# identical says whether B and C are byte for byte the same file, which is what makes the"
  echo "# patch files, and not a hand edited working copy, the thing that was built and measured."
  echo "file,sha256,bytes,what_it_is"
  for n in A-guard-only B-from-the-patches C-from-the-edits; do
    printf '%s,%s,%s,%s\n' "$n" "$(sha256sum "$W/$n.cpp" | cut -d' ' -f1)" "$(stat -c%s "$W/$n.cpp")" \
      "$n"
  done
  printf 'B_equals_C,%s,,the patch files lay down exactly the source the edit scripts produce\n' "$same"
} > "$S/evidence/patch-verification.csv"
cat "$S/evidence/patch-verification.csv"
