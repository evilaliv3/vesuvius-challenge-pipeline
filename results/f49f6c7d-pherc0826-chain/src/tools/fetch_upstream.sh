#!/usr/bin/env bash
# fetch_upstream.sh: read the upstream items this article names that results/facts does not carry, from
# the GitHub API, anonymously, one file per item with its response headers (the Date header is the time
# of the reading). The items results/facts carries (scrollreading 2, 3, 4; villa 1885, 1914, 1915) are
# copied from its newest saved stamp instead, so both documents state the same reading.
# It refuses to overwrite a good answer with an error answer (a rate limit, a 404): the old file stays.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT=$HERE/../inputs/github-api
FACTS=$(ls -d "$HERE"/../../../facts/inputs/github-api/*/ 2>/dev/null | sort | tail -1)
for n in ScrollPrize_villa-1885 ScrollPrize_villa-1914 ScrollPrize_villa-1915 WillStevens_scrollreading-2 WillStevens_scrollreading-3 WillStevens_scrollreading-4; do
  [ -n "$FACTS" ] && cp "$FACTS/$n.json" "$FACTS/$n.headers.txt" "$OUT/" && echo "copied from results/facts: $n"
done
for spec in ScrollPrize/villa:1875 ScrollPrize/villa:1877 Hob3rMallow/scrollfiesta_public:17 Hob3rMallow/scrollfiesta_public:18 \
            Hob3rMallow/scrollfiesta_public:19 Hob3rMallow/scrollfiesta_public:20 Hob3rMallow/scrollfiesta_public:21; do
  r=${spec%%:*}; n=${spec##*:}; f=$OUT/$(echo "$r" | tr '/' '_')-$n
  curl -s -m 20 -D "$f.headers.tmp" "https://api.github.com/repos/$r/issues/$n" -o "$f.json.tmp"
  if python3 -c "import json,sys; d=json.load(open('$f.json.tmp')); sys.exit(0 if 'number' in d else 1)" 2>/dev/null; then
    mv "$f.json.tmp" "$f.json"; mv "$f.headers.tmp" "$f.headers.txt"; echo "fetched: $r#$n"
  else
    rm -f "$f.json.tmp" "$f.headers.tmp"; echo "NOT fetched (kept the previous file if any): $r#$n"
  fi
done
