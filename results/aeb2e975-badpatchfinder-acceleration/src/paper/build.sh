#!/usr/bin/env bash
# Build the article of research/00001 and put it where it is delivered, at
# <public folder>/article.pdf. This is the only build of that article: the public folder holds the
# PDF and the science, and every source that typesets it lives here.
#
# Gates, all of them checked before and after latexmk:
#
#   1. no long dash anywhere in the source;
#   2. every \cite has a \bibitem;
#   3. every \includegraphics exists and its stem is named by a script that draws it, which is a
#      script of the public folder's src/tools or inputs, because the figures are drawn from the
#      evidence and the drawing is science;
#   4. the paper carries the side stripe of the series, which is papers/sidestripe.tex in the
#      preamble and \sidestripe{<folder number>} after \begin{document};
#   5. latexmk with -halt-on-error;
#   6. zero "LaTeX Warning" lines in the log (undefined reference, undefined citation, label
#      multiply defined);
#   7. no overfull box wider than 2 pt;
#   8. /CreationDate and /ModDate in the PDF are the declared SOURCE_DATE_EPOCH, checked by
#      tools/check_build_date.py, so that a date taken from the clock cannot pass for one that
#      was chosen;
#   9. tools/pdf_pages.py counts the pages of the delivered file three ways and refuses when the
#      three disagree.
#
# Usage: ./build.sh [name]        default name: umbilicus-score-patch
#
# A fixed date makes the build byte reproducible: pdfTeX stamps /CreationDate, /ModDate and the
# trailer /ID from the clock, so two builds of the same source differ without it. The value is
# 2026-09-26T00:00:00Z, the date of this revision, in seconds; it is the date the article carries
# in the stripe down the margin of its first page, and it is bumped when the paper is revised, so
# that the front page never claims a day older than the text on it. FORCE_SOURCE_DATE makes
# pdfTeX use it for the dates it writes into the file as well as for \today. The preamble also
# sets \pdfsuppressptexinfo=-1, without which pdfTeX writes the absolute path of every included
# figure into the file.
export SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH:-1790726400}   # 2026-09-30T00:00:00Z, the build day of v5
export FORCE_SOURCE_DATE=1

# GATE 0, added 2026-09-22 on the owner's word: the publication date in the side stripe is the
# day this folder entered the PUBLIC repository, and it is written by hand in
# papers/published-date.tex, never taken from the clock. A date in the future is refused here,
# because a front page that claims a publication day that has not happened is worse than one
# that says nothing. An empty date is not an error: it means the folder is not published yet and
# the stripe carries «not yet published».
python3 - "$(dirname "$0")/published-date.tex" "$SOURCE_DATE_EPOCH" <<'PYGATE' || exit 1
import datetime, re, sys
p, epoch = sys.argv[1], int(sys.argv[2])
# The COMMENTED example in the header of published-date.tex is a \\newcommand too, and
# re.search took it: on 2026-09-22T16:59Z this gate read the example date 2026-09-22 out of a
# comment and refused a build whose real \\PublishedDateIso is empty. A gate that reads a
# comment is not reading the document. TeX comments are stripped first, and of the definitions
# that remain the LAST is taken, because that is the one TeX itself would end up with.
src = "\n".join(re.sub(r"(?<!\\)%.*$", "", ln) for ln in open(p).read().splitlines())
found = re.findall(r"\\newcommand\{\\PublishedDateIso\}\{([^}]*)\}", src)
if not found:
    sys.exit("build: %s defines no \\PublishedDateIso outside its comments" % p)
iso = found[-1].strip()
if not iso:
    print("  published date: none, the stripe says not yet published")
    raise SystemExit(0)
try:
    d = datetime.date.fromisoformat(iso)
except ValueError:
    sys.exit("build: \\PublishedDateIso is %r, which is not a date" % iso)
built = datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc).date()
if d > built:
    sys.exit("build: the publication date %s is after the build date %s, refused" % (d, built))
print("  published date: %s, on or before the build date %s" % (d, built))
PYGATE

# THE SECOND PINNED CONSTANT, and the reason it is pinned.
#
# pdfTeX derives the trailer /ID from the ABSOLUTE PATH of the file it writes, so the same source
# built into two directories gives two files that differ in those bytes and in nothing else. The
# path is therefore declared here, exactly like the date, and it is the path the article has
# always been built at: <public folder>/src/paper/build. The directory holds nothing but the run
# and is removed at the end, and the public folder's .gitignore keeps it out of the repository
# while it is there.
#
# Set PAPER_BUILD_DIR to build somewhere else. The PDF is then the same article in every byte but
# the trailer /ID, which will no longer match the sha256 the delivered file carries.
PUBLIC=${PAPER_PUBLIC:-/data/repositories/vesuvius-challenge-pipeline-private/results/aeb2e975-badpatchfinder-acceleration}
BUILD=${PAPER_BUILD_DIR:-$PUBLIC/src/paper/build}

set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
PRIV=$(dirname "$HERE")
NAME=${1:-badpatchfinder-acceleration}
TEX=$HERE/$NAME.tex
rc=0
created=""
[ -d "$BUILD" ] || created=$BUILD
mkdir -p "$BUILD" || exit 1

# The date on the front page comes from the same epoch as the metadata and is never typed: the
# stripe reads \BuildDateLong out of papers/build-date.tex, which is written here on every build.
# Change SOURCE_DATE_EPOCH above and the stripe follows it, as does /CreationDate.
{ printf '%% Generated by paper/build.sh from SOURCE_DATE_EPOCH. Do not edit by hand.\n'
  printf '\\newcommand{\\BuildDate}{%s\\xspace}\n' "$(date -u -d "@$SOURCE_DATE_EPOCH" +%Y-%m-%d)"
  printf '\\newcommand{\\BuildDateLong}{%s}\n' "$(date -u -d "@$SOURCE_DATE_EPOCH" "+%-d %B %Y")"
} > "$HERE/build-date.tex"
echo "  build date $(date -u -d "@$SOURCE_DATE_EPOCH" +%Y-%m-%d) (SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH)"
echo "  build dir  $BUILD"

if grep -qE -- '---|\xe2\x80\x94|\xe2\x80\x93' "$TEX"; then echo "  !! long dash in the source"; rc=1; fi

# GATE 14, a stop: on 2026-09-23 the headings of sections 4 and 7 were glued to the end of a
# paragraph in draft.md, so body.tex printed «\#\# 4.» as text and the article had no section 4.
python3 - "$HERE/draft.md" "$HERE/body.tex" <<'PYHEAD' || { echo "build: refused by gate 14"; exit 1; }
import re, sys
bad = [(i, l.strip()[:90]) for i, l in enumerate(open(sys.argv[1]), 1)
       if any(m.start() != 0 for m in re.finditer(r"(?<!#)#{2,} ", l))]
lit = [(i, l.strip()[:90]) for i, l in enumerate(open(sys.argv[2]), 1) if "\\#\\#" in l]
for i, l in bad: print("   draft.md line %d: a heading marker not at line start: %s" % (i, l))
for i, l in lit: print("   body.tex line %d: a literal \\#\\#: %s" % (i, l))
if bad or lit: sys.exit(1)
print("  headings: every marker in draft.md at line start, no literal \\#\\# in body.tex")
PYHEAD

# GATE 15, a stop: until 2026-09-23 a src/tools/numbers.py hid Python's own numbers module, so every tool
# there that imports numpy died when a reader ran it; one such tool is started here as a reader starts it.
FIGPY=${SA_PY:-/data/scrollagent/.venv/bin/python}; [ -x "$FIGPY" ] || FIGPY=python3
( cd "$PRIV/.." && "$FIGPY" src/tools/s-f6-coverage-beside-a-published-segment.py --help > /dev/null ) \
  || { echo "build: refused by gate 15, src/tools/s-f6-coverage-beside-a-published-segment.py does not start from src/tools"; exit 1; }
echo "  gate 15: src/tools/s-f6-coverage-beside-a-published-segment.py starts from src/tools ($FIGPY)"

# Every paper of the series carries the side stripe, which says in the margin of the first page
# what the paper is and when it was built. One without it is a bug, not a choice.
# The argument is the FOLDER, which is a name like aeb2e975-badpatchfinder-acceleration and
# not a number. This test asked for \sidestripe{<digits>} until 2026-09-22T17:26Z and so failed
# every paper of the series that actually carries the stripe, including this one.
if ! grep -q '\\input{sidestripe}' "$TEX" || ! grep -qE '\\sidestripe\{[A-Za-z0-9][A-Za-z0-9-]*\}' "$TEX"; then
  echo "  !! no side stripe: the paper must \input{sidestripe} in the preamble and call"
  echo "     \sidestripe{<its folder number>} after \begin{document} (papers/sidestripe.tex)"
  rc=1
fi

python3 - "$TEX" "$PUBLIC/src/tools" "$PUBLIC/src/inputs" <<'PY' || rc=1
import re, sys, pathlib
tex = pathlib.Path(sys.argv[1])
dirs = [pathlib.Path(p) for p in sys.argv[2:]]
def expand(s, depth=0):
    def sub(m):
        p = tex.parent / (m.group(1) + ("" if m.group(1).endswith(".tex") else ".tex"))
        return expand(p.read_text(), depth + 1) if p.exists() and depth < 3 else ""
    return re.sub(r"\\(?:input|inputrows)\{([^}]+)\}", sub, s)
full = expand(tex.read_text())
cited = {k.strip() for m in re.finditer(r"\\cite\{([^}]+)\}", full) for k in m.group(1).split(",")}
have = set(re.findall(r"\\bibitem\{([^}]+)\}", full))
bad, unused = sorted(cited - have), sorted(have - cited)
scripts = "\n".join(p.read_text(errors="ignore") for d in dirs if d.is_dir()
                    for p in sorted(list(d.glob("*.py")) + list(d.glob("*.sh"))))
figs = [m.group(1) for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", full)]
nofig = [f for f in figs if pathlib.Path(f).stem not in scripts]
# \includegraphics is written WITHOUT an extension, because LaTeX picks one from
# \DeclareGraphicsExtensions. Testing (tex.parent / f).exists() on an extensionless path is
# therefore always False, and on 2026-09-22T17:26Z this line reported all six figures missing
# while the gate after it found all six on disk and said so. Two gates disagreeing about the
# same six files is worse than neither: here the extensions LaTeX would try are tried.
EXTS = ["", ".pdf", ".png", ".jpg", ".jpeg", ".eps"]
def on_disk(f):
    p = tex.parent / f
    return any((p.with_suffix(e) if e else p).exists() for e in EXTS) or p.exists()
missing = [f for f in figs if not on_disk(f)]
if bad: print("  !! cited without a bibitem:", bad)
if unused: print("  ?  bibitems never cited:", unused)
if nofig: print("  !! figures with no producing script in the public folder:", nofig)
if missing: print("  !! figure files missing:", missing)
ok = not (bad or nofig or missing)
print("  citations and figures:", "ok" if ok else "PROBLEMS")
sys.exit(0 if ok else 1)
PY

cd "$HERE" || exit 1
if TEXINPUTS=".:$HERE//:$HERE/cls:" latexmk -pdf -interaction=nonstopmode -halt-on-error \
     -outdir="$BUILD" "$NAME.tex" > "$BUILD/build.log" 2>&1; then
  warns=$(grep -c "LaTeX Warning" "$BUILD/$NAME.log" || true)
  over=$(awk 'match($0,/^Overfull \\hbox \(([0-9.]+)pt too wide\)/,m) && m[1]+0 > 2 {print "    " $0}' "$BUILD/$NAME.log")
  # the log wraps at 79 columns, so the page count is read from the log with the newlines
  # taken out
  pages=$(tr -d '\n' < "$BUILD/$NAME.log" | grep -o "Output written on[^(]*([0-9]* pages" \
          | grep -o "[0-9]* pages" | head -1)
  echo "  -> $pages, LaTeX warnings: $warns"
  if [ "$warns" != "0" ]; then grep "LaTeX Warning" "$BUILD/$NAME.log" | head -20; rc=1; fi
  if [ -n "$over" ]; then echo "  !! overfull boxes wider than 2 pt:"; echo "$over"; rc=1; fi
  # The last gates: the dates inside the file must be the declared epoch and not the clock. If
  # SOURCE_DATE_EPOCH had not reached pdfTeX nothing above would have noticed, and the paper would
  # carry a date nobody chose that looks exactly like one somebody did.
# GATES 10 and 11, wired in 2026-09-22: the owner names four gates for this build, the build
# date, the pages, English only and the order of the bibliography. The script as copied ran only
# the first two; the other two exist as tools in src/tools and were simply never called from
# here. They are called now, before latexmk, so a paper with an Italian sentence in it or a
# bibliography numbered out of the order it is cited in does not reach a PDF.
# GATE 12, added 2026-09-22 on the owner's word: the figures the article includes must be the
# figures on disk, by count and by name. The converter that makes the body had no branch for a
# caption block at all, so both articles were built, measured and reported with ZERO
# \includegraphics in them and nobody saw it until a preview was looked at. A count is the
# cheapest thing that would have caught it.
python3 - "$HERE/body.tex" "$HERE/figures" <<'PYFIG' || rc=1
import os, re, sys
body, figdir = sys.argv[1], sys.argv[2]
used = set(re.findall(r"\\includegraphics\[[^]]*\]\{figures/([^}]+)\}", open(body).read()))
have = {f.rsplit(".", 1)[0] for f in os.listdir(figdir)
        if f.endswith((".pdf", ".png")) and re.match(r"^[as]-f\d+-", f)}
if used != have:
    print("build: the figures included and the figures on disk differ")
    for f in sorted(have - used):
        print("   on disk, never included: %s" % f)
    for f in sorted(used - have):
        print("   included, not on disk:   %s" % f)
    sys.exit(1)
print("  figures: %d included, %d on disk, the same names" % (len(used), len(have)))
PYFIG
# GATE 13, added 2026-09-22 on the owner's word: no backslash reaches the typeset text. A macro
# written into the markdown before conversion gets its backslash escaped by the converter and
# prints as visible characters: «\prov1» appeared in the middle of a sentence on page 1 of the
# draft the owner read, and nothing in the build noticed. \textbackslash in the body is that
# mistake and this refuses it; if a paper ever needs a real backslash in its prose, this gate is
# the place to say so deliberately.
python3 - "$HERE/body.tex" <<'PYBS' || rc=1
import re, sys
b = open(sys.argv[1]).read()
# Two shapes, not one. \textbackslash{} is a backslash the converter escaped by mistake. A bare
# \\ in running prose is a backslash it DOUBLED by mistake: LaTeX reads it as a line break and
# prints what follows as literal text, which is how «Fig. reffig:s3» reached page 3. Inside a
# table row \\ is correct and is not counted.
rows = [i for i, l in enumerate(b.split("\n")) if l.rstrip().endswith("\\\\")]
hits = [(b[:m.start()].count("\n") + 1, b[max(0, m.start()-45):m.start()+30].replace("\n", " "))
        for m in re.finditer(r"\\textbackslash\{\}", b)]
hits += [(b[:m.start()].count("\n") + 1, b[max(0, m.start()-45):m.start()+30].replace("\n", " "))
         for m in re.finditer(r"\\\\(?=[A-Za-z])", b)]
if hits:
    print("build: %d escaped backslash(es) in the typeset text" % len(hits))
    for line, ctx in hits[:5]:
        print("   body.tex line %d: ...%s..." % (line, ctx))
    sys.exit(1)
print("  no escaped backslash in the typeset text")
PYBS
python3 "$PRIV/tools/english_only.py" "$PUBLIC" --quiet || rc=1
python3 "$PRIV/tools/bib_order.py" "$TEX" || rc=1
# GATE 16, added 2026-09-28 on the director's note of 12:12:31Z (the owner's word): the facts the
# September works share (the c stage factor, the growth factors on PHerc. 0826, the upstream states,
# the eligibility of the scrolls, Stevens' 365 cm2 and our 363.8629, the bio) are one table,
# results/facts/facts.csv, written by results/facts/facts.py from its sources. A value this article
# states that differs from the table refuses the build. A copy of this folder published on its own
# has no results/facts beside it, and there the gate says so and is not run.
FACTS=$PUBLIC/../facts/check_facts.py
if [ -f "$FACTS" ]; then python3 "$FACTS" "$PUBLIC" --tex "$TEX" || rc=1
else echo "  facts gate: no results/facts beside this folder, not run"; fi
  python3 "$PRIV/tools/check_build_date.py" "$BUILD/$NAME.pdf" "$SOURCE_DATE_EPOCH" || rc=1
  if [ "$rc" = "0" ]; then
    cp "$BUILD/$NAME.pdf" "$PUBLIC/article.pdf"
    echo "  -> $PUBLIC/article.pdf"
    python3 "$PRIV/tools/pdf_pages.py" "$PUBLIC/article.pdf" || rc=1
  else
    echo "  !! a gate failed, $PUBLIC/article.pdf left as it was"
  fi
else
  echo "  !! latexmk failed, see $BUILD/build.log"; grep -A3 "^!" "$BUILD/$NAME.log" | head -20; rc=1
fi
# The run leaves nothing in the public folder: the build directory is scratch and is removed, and
# its parent with it when this run is what made it.
if [ -n "$created" ]; then rm -rf "$created"; rmdir "$(dirname "$created")" 2>/dev/null; fi
echo "build done (rc=$rc)"
exit $rc
