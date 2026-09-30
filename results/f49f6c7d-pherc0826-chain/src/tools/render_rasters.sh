#!/usr/bin/env bash
# render_rasters.sh: draw the raster figures C10 to C15 of results/f49f6c7d-pherc0826-chain.
#
# Each tool writes its PNG under ../paper/figures and its plotted table under ../evidence/figures. C11 reads C10's
# table (the height and the crop), so C10 runs first. C10, C11 and C13 read raw scan chunks of PHerc0826 through the
# shared cache /data/scrollagent/data/cache/raw-chunks (fetched from the open data bucket only when absent); C10 and C13
# read the local m7 prediction and the delivered sheets under /data/scrollagent/runs/rev1; C12 recomputes arm a2 on one
# sheet with the chain's own imported code (about a minute and a half of one core).
#
# With --check, every tool is rerun with --out into a temporary folder and its rows after line 1 are compared with the
# table on disk; the PNGs are not touched. Runs at nice 10. figlib.require_free_machine is left as it is: set
# SA_FIGURES_IGNORE_LOAD=1 in the environment to draw beside other work.
set -u -o pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${SA_PY:-/data/scrollagent/.venv/bin/python}"
export TMPDIR="${TMPDIR:-/data/tmp}"
EV="$HERE/../evidence/figures"
FAILED=0
CHECK=0
[ "${1:-}" = "--check" ] && CHECK=1
say() { printf '%s  %s\n' "$(date -u +%FT%TZ)" "$*"; }
# c-f15-setseed-91 is held out (2026-09-28T08:5xZ): it reads the live item 91 study, which is still running;
# it returns when item 91's squares are frozen into the snapshot.
# c-f16-certified-square and c-f17-where-squares (2026-09-28, the figure order of the director's note of
# 18:29:38Z) write raster assets under ../paper/figures/assets and a TikZ body; their .tex is then set with
# pdflatex into ../paper/figures and a PNG is made beside it, as render.sh does for the vector figures.
# c-f20-best-windows (2026-09-29, the reframe around the checks, director 06:54:31Z) is drawn the same way from
# best-windows-0826's panel data, pinned by sha256 in c-f20-best-windows-pins.csv.
for name in c-f10-papyrus c-f12-a2-flags c-f13-setseed c-f16-certified-square c-f17-where-squares c-f20-best-windows c-f21-r2c c-f22-v8in-w016 c-f23-v8in-0826 c-f24-v8in-more; do
  if [ "$CHECK" -eq 1 ]; then
    tmp=$(mktemp -d "$TMPDIR/sa-raster-check-XXXXXX") || { FAILED=$((FAILED+1)); continue; }
    say "check   $name"
    if ( cd "$HERE" && nice -n 10 "$PY" "./$name.py" --out "$tmp/$name.csv" --png "$tmp/$name.png" ) >"$tmp/log" 2>&1 \
       && cmp -s <(tail -n +2 "$EV/$name.csv") <(tail -n +2 "$tmp/$name.csv"); then
      say "same    $name"
    else
      FAILED=$((FAILED+1)); say "DIFFERS $name (see $tmp)"; continue
    fi
    rm -rf "$tmp"
  else
    say "raster  $name"
    ( cd "$HERE" && nice -n 10 "$PY" "./$name.py" ) || { FAILED=$((FAILED+1)); say "FAILED  $name.py"; continue; }
    if [ -f "$HERE/$name.tex" ]; then
      OUT="$HERE/../paper/figures"
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
    fi
  fi
done
[ "$FAILED" -eq 0 ] && say "every raster done" || { say "$FAILED step(s) failed"; exit 1; }
