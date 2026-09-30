#!/bin/bash
# The check that -g changed no instruction: the .text section of the binary built with -g against
# the .text section of the binary built without it. strip alone does not answer this, because the
# GNU build id is a hash of the whole file and differs whenever the debug sections do; the
# executable section is what runs.
#
# Writes evidence/text-section-identity.csv.
set -eu
S=/data/scrollagent/runs/rev1/c-stage-cost
OUT=$S/evidence/text-section-identity.csv
{
  echo "# the .text section of each binary built with -g beside the same build without it."
  echo "# text_sha256 is sha256 of the bytes objcopy --only-section=.text extracts. Two rows of"
  echo "# a pair with the same text_sha256 mean -g added debug sections and changed no"
  echo "# instruction, so a time measured on the -g build is a time of the code that ships."
  echo "label,debug_flag,text_bytes,text_sha256,binary"
} > "$OUT"
for L in guarded guarded-g c1 c1-g c2 c2-g; do
  B=$S/scratch/bin/$L/simpaper10
  [ -f "$B" ] || continue
  T=/data/tmp/text-$L.bin
  objcopy --only-section=.text -O binary "$B" "$T"
  case "$L" in *-g) D=yes;; *) D=no;; esac
  printf '%s,%s,%s,%s,%s\n' "$L" "$D" "$(stat -c%s "$T")" "$(sha256sum "$T" | cut -d' ' -f1)" "$B" >> "$OUT"
  rm -f "$T"
done
cat "$OUT"
