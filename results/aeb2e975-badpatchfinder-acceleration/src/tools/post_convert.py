#!/usr/bin/env python3
"""The two changes body.tex needs after the house converter and before macroise.py.

WHY THIS IS A TOOL. body.tex is generated: md_to_tex.py (in the home's tools) converts the draft,
this runs, then macroise.py. Until 2026-09-23 both changes below were made by hand inside
body.tex, and a hand edit in a generated file is lost at the next conversion. That is how the
body fell a whole section behind the draft: nobody dared regenerate it.

1. A numbers.tex macro written in the draft, like \\CoverShareAllSeeds{}, is escaped by the
   converter into \\textbackslash{}CoverShareAllSeeds{} and would print as visible characters.
   It is put back ONLY when numbers.tex defines that name; any other escaped backslash is left
   alone, so gate 13 of build.sh still refuses it.
2. The provenance appendix has more rows than a page holds. As a table* float LaTeX reported
   «Float too large for page» at every build; a longtable can break across pages and cannot run
   in two columns, so the appendices switch to one column and the table becomes an xltabular.
3. A draft heading that carries no number («What this work is about, in plain words», «Figures»)
   becomes \\section* here. The converter strips the draft's numbers and lets LaTeX count, so an
   unnumbered heading took a number and pushed every later one up by one: the prose says
   «section 4» for «Two changes and their proof», which LaTeX had numbered V.

Usage: post_convert.py   (edits src/paper/body.tex in place and says what it did)
"""
import os, re, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BODY = os.path.join(S, "paper", "body.tex")
NUM = os.path.join(S, "paper", "numbers.tex")

APPENDIX = r"\section*{Appendix: where each number comes from}"
ONECOL = r"""%% The appendices run in ONE column from here. The provenance table below has more rows
%% than a page holds: as a table* float LaTeX said "Float too large for page" at every build,
%% which the build gate counts as a failure. A float cannot break across pages; a longtable can,
%% and longtable cannot run in two column mode. Both appendices are the last thing in the
%% article, so switching here costs nothing and no text after it is reflowed.
\clearpage
\onecolumn
"""
OLD_HEAD = "\\begin{table*}[t]\n\\centering\n\\small\n\\begin{tabularx}{\\textwidth}{rX}\n" \
           "\\toprule\nmarker & file and column \\\\\n\\midrule\n"
NEW_HEAD = ("%% xltabular is longtable plus the X column this table already used.\n"
            "\\begin{xltabular}{\\textwidth}{rX}\n\\toprule\nmarker & file and column \\\\\n"
            "\\midrule\n\\endfirsthead\n\\toprule\nmarker & file and column \\\\\n\\midrule\n"
            "\\endhead\n\\midrule\n"
            "\\multicolumn{2}{r}{\\footnotesize\\itshape continued on the next page}\\\\\n"
            "\\endfoot\n\\bottomrule\n\\endlastfoot\n")
OLD_TAIL = "\\bottomrule\n\\end{tabularx}\n\\end{table*}"


def main():
    names = set(re.findall(r"\\newcommand\{\\(\w+)\}", open(NUM).read()))
    b = open(BODY).read()

    restored = []

    def back(m):
        if m.group(1) in names:
            restored.append(m.group(1))
            return "\\" + m.group(1) + "{}"
        return m.group(0)
    b = re.sub(r"\\textbackslash\{\}(\w+)\{\}", back, b)
    print("  macros put back from their escaped form: %d %s" % (len(restored), sorted(set(restored))))

    if "\\onecolumn" in b:
        sys.exit("post_convert: body.tex already has \\onecolumn, run it on a fresh conversion")
    a = b.find(APPENDIX)
    if a < 0:
        sys.exit("post_convert: no provenance appendix in body.tex")
    h = b.find(OLD_HEAD, a)
    t = b.find(OLD_TAIL, h)
    if h < 0 or t < 0:
        sys.exit("post_convert: the provenance table is not in the shape the converter writes")
    b = (b[:a] + ONECOL + b[a:h] + NEW_HEAD + b[h + len(OLD_HEAD):t] + "\\end{xltabular}"
         + b[t + len(OLD_TAIL):])
    print("  provenance appendix: one column, xltabular")

    draft = open(os.path.join(S, "paper", "draft.md")).read()
    unnumbered = [h.strip() for h in re.findall(r"^## (?!\d)(.+)$", draft, re.M)]
    starred = []
    for h in unnumbered:
        old = "\\section{%s}\n" % h
        if b.count(old) == 1:
            b = b.replace(old, "\\section*{%s}\n" % h)
            starred.append(h)
    print("  unnumbered draft headings set as \\section*: %s" % starred)
    open(BODY, "w").write(b)


if __name__ == "__main__":
    main()
