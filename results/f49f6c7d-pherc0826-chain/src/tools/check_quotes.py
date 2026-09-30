#!/usr/bin/env python3
"""Every quotation in body.tex must be found, character for character, in the raw page it quotes.

The article quotes the organisers' open problems page and Stevens' usage text. A quote typed from
memory, or from a summary of the page, is the failure this refuses. It takes every ``...'' span of
body.tex (TeX quotes), undoes the TeX spacing of the span (~ and line breaks), and looks for it in
the sources below; a quote found in none of them stops the build. A span that is a term being defined
rather than a quotation (``the same place'') is listed in NOT_QUOTES with the reason.

Usage: check_quotes.py
"""
import glob, html, os, re, subprocess, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOT_QUOTES = {"the same place": "a term the text defines, not a quotation",
              "seeds": "the name of a table column", "Not measurable": "the words a table cell prints",
              "ladder unfinished": "the words a table cell prints"}


def sources():
    out = []
    # Only the newest copy of the organisers' open problems page is a source (2026-09-30: villa pull request 1937
    # changed the page; the text quotes the page as it reads now, and a quote found only in the older copy stops the build).
    pages = glob.glob(os.path.join(S, "inputs", "open-problems", "open-problems-*.html")) + \
        glob.glob(os.path.join(S, "inputs", "open-problems", "open-problems-*.md"))
    newest = max(pages, key=lambda p: re.search(r"(\d{8}T\d{6}Z)", os.path.basename(p)).group(1))   # the name, not the path
    out.append(("open problems page, %s" % os.path.basename(newest), html.unescape(re.sub(r"<[^>]+>", "", open(newest).read()))))
    out.append(("simpaper10 at 62cbc21", subprocess.check_output(
        ["git", "-C", "/data/repositories/scrollreading", "show", "62cbc21:pipeline9/simpaper10.cpp"]).decode()))
    for p in glob.glob(os.path.join(S, "evidence", "studies", "area-0826-90", "stevens-method.csv")):
        out.append(("stevens-method.csv", open(p).read()))
    return out


def main():
    body = "\n".join(l for l in open(os.path.join(S, "paper", "body.tex")).read().splitlines()
                     if not l.lstrip().startswith("%"))
    src = [(n, re.sub(r"\s+", " ", t)) for n, t in sources()]
    bad, n = [], 0
    for m in re.finditer(r"``(.+?)''", body, re.S):
        q = re.sub(r"\s+", " ", m.group(1).replace("~", " ")).strip()
        if q in NOT_QUOTES:
            continue
        q = re.sub(r"\\[A-Za-z]+\{\}", "  ", q).replace("cm$^2$", "cm²")   # a macro inside a quote is checked by its own CSV
        parts = [x.strip() for x in re.split(r"\s{2,}", q) if x.strip()]
        n += 1
        where = [name for name, t in src if all(p in t for p in parts)]
        if not where:
            bad.append(q)
        else:
            print("  quote found in %s: %s" % (where[0], q[:70]))
    for q in bad:
        print("  !! quote not found in any source: %s" % q)
    print("check_quotes.py: %d quotation(s), %d not found" % (n, len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
