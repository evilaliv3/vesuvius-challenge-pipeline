#!/usr/bin/env bash
# finalize.sh: the final build of the 0826 article at the declared cut off (director 2026-09-28T12:21:38Z).
#
# Run by hand, by a round, at or after 2026-09-29T03:31:00Z (one minute after the cut off of tools/cutoff.py);
# it refuses to run earlier. At nice 10:
#   1. copy_evidence.py      the last snapshot of every study the article cites;
#   2. cutoff.py             the decisions of the cut off, taken once and kept (road 1b, item 91 arms);
#   3. render.sh             the three plotted figures from the snapshot;
#   4. render_rasters.sh     the raster figures (the load guard lifted: they compare rows, not times);
#   5. paper/build.sh        the ARTICLE, every gate; article.pdf only if all pass;
#   6. page PNGs of the article (or of a preview, if the article refused) under
#      /data/scrollagent/outputs/artifacts/fifth-work/final/, and one ledger row with the outcome.
# It never kills anything, never commits and never edits the owner's commit script: the two shas that
# script needs are left for the round that reads this log.
set -u -o pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC=$(dirname "$HERE")
OUTD=/data/scrollagent/outputs/artifacts/fifth-work/final
LOG=$OUTD/finalize.log
export TMPDIR=/data/tmp
mkdir -p "$OUTD"
exec >> "$LOG" 2>&1
AT=${FINALIZE_AT:-2026-09-29T03:31:00Z}
if [ "$(date -u +%FT%TZ)" \< "$AT" ]; then echo "$(date -u +%FT%TZ) refused: before $AT"; exit 1; fi
echo "$(date -u +%FT%TZ) running"
cd "$SRC" || exit 1
rc=0
nice -n 10 python3 tools/copy_evidence.py || rc=1
nice -n 10 python3 tools/cutoff.py || rc=1
nice -n 10 bash tools/render.sh || rc=1
SA_FIGURES_IGNORE_LOAD=1 nice -n 10 bash tools/render_rasters.sh || rc=1
nice -n 10 bash paper/build.sh; brc=$?
PDF=$SRC/../article.pdf; what=article
if [ "$brc" != "0" ]; then
  PREVIEW=1 PREVIEW_DIR=$OUTD nice -n 10 bash paper/build.sh; PDF=$OUTD/pherc0826-chain-preview.pdf; what="preview (the article refused)"
fi
S=$(mktemp -d /tmp/sa-final-XXXX) && cp "$PDF" "$S/p.pdf" && (cd "$S" && TMPDIR=$S gs -dQUIET -dBATCH -dNOPAUSE -sDEVICE=png16m -r110 \
  -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -o p-%d.png p.pdf) && cp "$S"/p-*.png "$OUTD"/; rm -rf "$S"
echo "$(date -u +%FT%TZ) done: build rc=$brc, steps rc=$rc, pages of the $what in $OUTD"
python3 -c "
import sys; sys.path.insert(0, '/data/scrollagent/tools'); from ledger import row
row('fifth-work-0826-finalize', 'finalize.sh at the cut off: build rc $brc (0 means article.pdf written), steps rc $rc; pages of the $what in outputs/artifacts/fifth-work/final; decisions in src/evidence/derived/cutoff.csv',
    command='src/tools/finalize.sh', artifact='$OUTD/finalize.log', actor='coordinator-agent')"
