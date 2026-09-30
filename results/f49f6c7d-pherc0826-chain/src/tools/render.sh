#!/usr/bin/env bash
# render.sh: draw the figures of results/f49f6c7d-pherc0826-chain, tables first, then the plots.
#
# The plot step is results/render_all.sh's plot(), copied: pdflatex into ../paper/figures, then
# ghostscript to a PNG beside it. Ghostscript on this machine cannot read or write under /data, so
# the PDF is staged in /tmp (tens of kilobytes, removed after each figure). Both figures read a
# few hundred CSV rows; nothing here reads a volume. Runs at nice 10.
set -u -o pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${SA_PY:-/data/scrollagent/.venv/bin/python}"
export TMPDIR="${TMPDIR:-/data/tmp}"
OUT="$HERE/../paper/figures"
FAILED=0
say() { printf '%s  %s\n' "$(date -u +%FT%TZ)" "$*"; }
mkdir -p "$OUT"
for name in c-f1-pipeline c-f2-best-square c-f3-stevens-formula c-f18-arms-steps c-f19-yield-waves; do
  say "table   $name"
  ( cd "$HERE" && nice -n 10 "$PY" "./$name.py" ) || { FAILED=$((FAILED+1)); say "FAILED  $name.py"; continue; }
  say "plot    $name"
  ( cd "$HERE" && nice -n 10 pdflatex -interaction=nonstopmode -halt-on-error \
      -output-directory="$OUT" "$name.tex" > "$OUT/$name.pdflatex.log" 2>&1 ) \
    || { FAILED=$((FAILED+1)); say "FAILED  $name: see $OUT/$name.pdflatex.log"; continue; }
  stage=$(mktemp -d /tmp/sa-figure-XXXXXX) || { FAILED=$((FAILED+1)); continue; }
  cp -f "$OUT/$name.pdf" "$stage/f.pdf"
  if TMPDIR="$stage" gs -dQUIET -dBATCH -dNOPAUSE -sDEVICE=png16m -r300 -dTextAlphaBits=4 \
       -dGraphicsAlphaBits=4 -o "$stage/f.png" "$stage/f.pdf" >/dev/null 2>&1 && [ -s "$stage/f.png" ]; then
    cp -f "$stage/f.png" "$OUT/$name.png"
  else
    FAILED=$((FAILED+1)); say "FAILED  $name: ghostscript"
  fi
  rm -rf "$stage"
done
[ "$FAILED" -eq 0 ] && say "every figure drawn" || { say "$FAILED step(s) failed"; exit 1; }
