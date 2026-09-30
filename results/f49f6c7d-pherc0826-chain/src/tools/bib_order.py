#!/usr/bin/env python3
"""Check that the references are numbered in the order a reader first meets them.

In the IEEE style a reference's number is the order of its first citation in the text. The
bibliography here is a hand written `thebibliography`, so the numbers are simply the order of the
`\\bibitem` lines, and nothing in the build notices when that order and the order of first citation
have drifted apart. This is what notices.

Reading the source is not enough to answer the question. A `\\cite` inside a caption, inside a
table or inside a footnote reaches the page somewhere other than where its line sits in the file,
a float moves to the top of a page or to the next one, and one `\\cite` can carry several keys. The
order that matters is the order the numbers are printed in, so that is what is read: the paper is
composed once more with `\\cite` taught to log its keys at shipout, which is the moment a page is
written out, in the order the marks sit on the page. The log is therefore the reader's order and
not the file's.

Three checks, and all three have to pass:

  every reference is cited      a bibitem nothing cites is a number the reader can never meet
  every citation has an entry   a cite with no bibitem is an undefined reference
  the numbers rise              scanning the composed document, the first appearance of [2] comes
                                after the first appearance of [1], and so on to the end. If the
                                first appearance of [5] comes before that of [4], the order is
                                still wrong, and the tool says which pair is out of order.

    bib_order.py [TEX]        default: paper/papers/umbilicus-score-patch.tex
    bib_order.py --fix        rewrite the bibitem block in the order of first citation

`--fix` moves whole `\\bibitem` entries and nothing else. The keys do not change, so no `\\cite`
is touched and the numbers follow by themselves.

Exit status: 0 in order, 1 out of order or a citation problem, 2 the tool could not run.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)

INSTRUMENT = r"""
\makeatletter
\newwrite\bibord@out
\immediate\openout\bibord@out=\jobname.bibord
\let\bibord@cite\cite
\renewcommand\cite[1]{\write\bibord@out{#1}\bibord@cite{#1}}
\makeatother
"""


def expand(path, depth=0):
    """The source with every \\input pulled in, the way the build's own gate reads it."""
    text = open(path, encoding="utf-8").read()
    base = os.path.dirname(path)

    def sub(m):
        name = m.group(1)
        p = os.path.join(base, name if name.endswith(".tex") else name + ".tex")
        return expand(p, depth + 1) if os.path.exists(p) and depth < 3 else ""
    return re.sub(r"\\(?:input|inputrows)\{([^}]+)\}", sub, text)


def strip_comments(text):
    return re.sub(r"(?<!\\)%.*", "", text)


def bibitems(text):
    return re.findall(r"\\bibitem\{([^}]+)\}", text)


def cited_keys(text):
    return [k.strip() for m in re.finditer(r"\\cite\{([^}]+)\}", text)
            for k in m.group(1).split(",")]


def shipout_order(tex):
    """The keys in the order their marks are printed, read from a composed run of the paper."""
    papers = os.path.dirname(tex)
    paper_dir = os.path.dirname(papers)
    name = os.path.splitext(os.path.basename(tex))[0]
    source = open(tex, encoding="utf-8").read()
    if re.search(r"\\cite\s*\[", source):
        raise SystemExit("bib_order: this paper uses \\cite with an optional argument; the "
                         "instrumented \\cite here takes one argument only")
    marker = r"\begin{document}"
    if marker not in source:
        raise SystemExit("bib_order: no \\begin{document} in " + tex)
    patched = source.replace(marker, marker + "\n" + INSTRUMENT, 1)

    with tempfile.TemporaryDirectory(prefix="bib_order-", dir=os.environ.get("TMPDIR")) as d:
        # the whole of paper/ is copied, not just papers/, because the figures are included by a
        # path relative to it and a run without them is not the composed paper
        root = os.path.join(d, "paper")
        shutil.copytree(paper_dir, root, ignore=shutil.ignore_patterns("build"))
        work = os.path.join(root, os.path.basename(papers))
        with open(os.path.join(work, os.path.basename(tex)), "w", encoding="utf-8") as fh:
            fh.write(patched)
        env = dict(os.environ)
        env["TEXINPUTS"] = f".:{work}//:{os.path.join(root, 'cls')}:"
        env["SOURCE_DATE_EPOCH"] = env.get("SOURCE_DATE_EPOCH", "1789776000")
        env["FORCE_SOURCE_DATE"] = "1"
        for _ in range(2):          # twice, so that the page numbers and the marks have settled
            p = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                                os.path.basename(tex)], cwd=work, env=env,
                               capture_output=True, text=True)
        if p.returncode != 0:
            sys.stderr.write(p.stdout[-3000:])
            raise SystemExit("bib_order: the instrumented build failed")
        log = os.path.join(work, name + ".bibord")
        if not os.path.exists(log):
            raise SystemExit("bib_order: the instrumented build wrote no citation log")
        keys = []
        for line in open(log, encoding="utf-8"):
            for k in line.strip().split(","):
                if k.strip():
                    keys.append(k.strip())
        aux = os.path.join(work, name + ".aux")
        numbers = dict(re.findall(r"\\bibcite\{([^}]+)\}\{(\d+)\}", open(aux, encoding="utf-8").read()))
    return keys, {k: int(v) for k, v in numbers.items()}


def first_appearance(keys):
    """The keys in the order each is first printed, with repeats dropped."""
    out = []
    for k in keys:
        if k not in out:
            out.append(k)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="check the reference numbering against the composed paper")
    ap.add_argument("tex", nargs="?",
                    default=os.path.join(SRC, "paper", "papers", "umbilicus-score-patch.tex"))
    ap.add_argument("--fix", action="store_true",
                    help="rewrite the bibitem block in the order of first citation")
    args = ap.parse_args(argv)
    tex = os.path.abspath(args.tex)
    if not os.path.exists(tex):
        print(f"not a file: {tex}", file=sys.stderr)
        return 2

    full = strip_comments(expand(tex))
    entries = bibitems(full)
    cited = cited_keys(full)
    print(f"bib_order: {os.path.relpath(tex, SRC)}")
    print(f"  {len(entries)} reference(s), {len(cited)} citation(s) in the source")

    bad = sorted(set(cited) - set(entries))
    unused = sorted(set(entries) - set(cited))
    problems = []
    if bad:
        problems.append(f"cited with no entry: {', '.join(bad)}")
    if unused:
        problems.append(f"entries never cited: {', '.join(unused)}")

    keys, numbers = shipout_order(tex)
    order = first_appearance(keys)
    print(f"  {len(keys)} citation mark(s) printed, {len(order)} reference(s) reached the page")

    never = [k for k in entries if k not in order]
    if never:
        problems.append(f"entries whose number never appears in the composed paper: {', '.join(never)}")

    printed = [numbers.get(k, 0) for k in order]
    print("  order of first appearance: " + ", ".join(f"[{numbers.get(k, 0)}] {k}" for k in order))
    out_of_order = [(order[i], printed[i], order[i + 1], printed[i + 1])
                    for i in range(len(printed) - 1) if printed[i + 1] < printed[i]]
    for a, na, b, nb in out_of_order:
        problems.append(f"[{nb}] {b} is first cited after [{na}] {a}, so the numbers do not rise")

    if args.fix:
        text = open(tex, encoding="utf-8").read()
        block = re.search(r"(\\bibitem\{.*?)(?=\n\\end\{thebibliography\})", text, re.S)
        if not block:
            print("  could not find the bibitem block", file=sys.stderr)
            return 2
        raw = block.group(1)
        pieces = re.split(r"(?=\\bibitem\{)", raw)
        pieces = [p for p in pieces if p.strip()]
        by_key = {}
        for p in pieces:
            by_key[re.match(r"\\bibitem\{([^}]+)\}", p).group(1)] = p.rstrip("\n")
        want = order + [k for k in entries if k not in order]
        if sorted(want) != sorted(by_key):
            print("  refusing to rewrite: the entries and the printed order do not agree",
                  file=sys.stderr)
            return 2
        new = "\n\n".join(by_key[k] for k in want) + "\n"
        open(tex, "w", encoding="utf-8").write(text.replace(raw, new, 1))
        print("  rewrote the bibitem block in the order of first citation: " + ", ".join(want))
        print("  rebuild, then run this tool again with no --fix")
        return 0

    if problems:
        print("\nFAIL:")
        for p in problems:
            print("  " + p)
        return 1
    print("\nOK: every reference is cited, every citation has an entry, and the numbers rise "
          "in the order the reader meets them")
    return 0


if __name__ == "__main__":
    sys.exit(main())
