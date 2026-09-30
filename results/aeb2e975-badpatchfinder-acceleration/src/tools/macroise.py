#!/usr/bin/env python3
"""Replace the literal numbers of body.tex with the macros paper_numbers.py generated.

WHY THIS IS A TOOL AND NOT AN EDIT. body.tex is generated from the draft; an edit made by hand
inside it is lost the next time it is generated. This runs after the conversion, reads the macros
out of numbers.tex, and substitutes. Regenerating the body and running this again gives the same
file, which is the only way the article stays reproducible.

WHAT IT REFUSES TO DO. A number like 3 or 0 is not substituted: it appears in a hundred places
that have nothing to do with the macro, and a wrong substitution is worse than a literal because
it reads as verified. Only a value of at least four characters is considered, which is what makes
`31.11` and `94,962` safe and `3` untouchable. Everything it does and everything it leaves is
printed, and a macro whose value it could not find anywhere is named: that is usually a number
the prose rounds differently from the CSV, which is a thing to look at and not to hide.
"""
import os, re, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUM = os.path.join(S, "paper", "numbers.tex")
BODY = os.path.join(S, "paper", "body.tex")
MIN_LEN = 4

# Short values that ARE placed, each because every occurrence in the body was read and found to
# be the same quantity. This list is the exception to MIN_LEN and it is deliberately an opt in:
# the default stays safe, and letting a three digit number through is a decision somebody made
# and wrote down, not a threshold somebody lowered.
#
# Checked 2026-09-22T17:47Z, every occurrence, not a sample: the counts below are what the body
# held at that moment and the tool prints what it finds, so a disagreement is visible.
#
# The boundary guard still applies and is what makes these safe from the obvious collisions: it
# refuses a match touching a digit, a dot or a comma, so 327 is not taken out of 946,327 and 86
# is not taken out of 4.86.
SHORT_ALLOWED = {
    "MixedOrphanIds":         "104, 9 occurrences, every one the orphan ids of that one tree",
    "MixedImpossibleIds":     "413, 7 occurrences, every one the ids the log says are not the run's",
    "MixedImpossibleNoFile":  "86, 3 occurrences, every one the impossible ids with no patch file",
    "MixedImpossibleWithFile": "327, 5 occurrences, every one the impossible ids re created",
    "RefusedChainsTwo":       "202, 7 occurrences, every one the chains refused at length 2",
    "RefusedPatchesTwo":      "73, 5 occurrences, every one the patches involved at length 2",
}


def macros():
    out = {}
    for ln in open(NUM):
        m = re.match(r"\\newcommand\{\\(\w+)\}\{(.*?)\\xspace\}", ln.strip())
        if m:
            out[m.group(1)] = m.group(2)
    return out


def ambiguous(macs):
    """Macros that share a value, which this tool must never place by itself.

    Carried over on 2026-09-23 from the sister tool of work A, where it was MEASURED at 12:1xZ:
    two macros of that work held 1.1891, and substituting by value put the one naming the wrong
    quantity into a row. A value shared by two macros is not a thing a substitution can decide,
    so it is refused and both names are printed for a person to place by hand in the draft."""
    from collections import defaultdict
    by = defaultdict(list)
    for k, v in macs.items():
        by[v].append(k)
    return {v: sorted(ks) for v, ks in by.items() if len(ks) > 1}


def main():
    ms = macros()
    if not ms:
        sys.exit("no macros in %s: run paper_numbers.py first" % NUM)
    bad = ambiguous(ms)
    for v, ks in sorted(bad.items()):
        print("  REFUSED, two macros share the value %s: %s. This tool "
              "cannot know which row means which, so both stay literals "
              "and the draft must name them." % (v, ", ".join(ks)))
    for k in [k for ks in bad.values() for k in ks]:
        ms.pop(k, None)
    body = open(BODY).read()

    # longest values first, so 1,548.2 is taken before 548 could be
    order = sorted(ms.items(), key=lambda kv: -len(kv[1]))
    done, skipped, absent, allowed, phrases = [], [], [], [], []
    for name, val in order:
        if len(val) < MIN_LEN and name not in SHORT_ALLOWED:
            skipped.append((name, val))
            continue
        # A macro whose value is not a number is a PHRASE, and a phrase collides with prose.
        # SeedSquareEleven holds the words «not measurable», which is what its cell says, and on
        # 2026-09-22T18:26Z this tool put it into two sentences that were about other seeds
        # entirely: «seed44's row read not measurable in every column» and seed40's «one run»
        # spread. Both read as verified and both named the wrong thing. Substituting by value
        # only works while the value cannot occur for another reason, and a number can hardly
        # occur by accident where a phrase does constantly.
        # A LIST of numbers is allowed as well as a single one: «47.4, 48.6, 48.3» is what the
        # article prints for a series the bench holds as «47.4; 48.6; 48.3», and three runs
        # quoted together cannot occur by accident the way a phrase can. What stays forbidden is
        # anything with a letter in it. Added 2026-09-22T18:45Z, when the middle run of a series
        # turned out to be the only literal left inside a list of three.
        if not re.fullmatch(r"[\d,]+(?:\.\d+)?(?:,\s[\d,]+(?:\.\d+)?)*", val):
            phrases.append((name, val))
            continue
        # a number is only a number: not inside a macro name already placed, and bounded by
        # something that is not a digit, a dot or a comma
        # The trailing lookahead must forbid a character that CONTINUES the number, not a comma
        # that separates a list. `(?![\d.,])` forbade both, so every value quoted in a series,
        # «47.4, 48.6, 48.3», was reported NOT FOUND while sitting in the body three times, and
        # the article ended up with a macro beside literals of its own series. Found
        # 2026-09-22T18:25Z. A comma only continues a number when a digit follows it.
        pat = re.compile(r"(?<![\d.,\\])" + re.escape(val) + r"(?!\d)(?!\.\d)(?!,\d)")
        n = len(pat.findall(body))
        if n == 0:
            absent.append((name, val))
            continue
        body = pat.sub("\\\\" + name + "{}", body)
        done.append((name, val, n))
        if name in SHORT_ALLOWED:
            allowed.append((name, val, n))

    open(BODY, "w").write(body)
    print("%s: %d macro(s) placed, %d occurrence(s)"
          % (os.path.relpath(BODY, S), len(done), sum(n for _, _, n in done)))
    for name, val, n in sorted(done):
        print("   %-34s %-12s x%d" % (name, val, n))
    if phrases:
        print("  not a number, so never substituted: a phrase collides with prose. %s"
              % ", ".join("%s=%r" % (n, v) for n, v in sorted(phrases)))
    if allowed:
        print("  short values placed because SHORT_ALLOWED says so, each read occurrence by")
        print("  occurrence before it was allowed:")
        for name, val, n in sorted(allowed):
            print("   %-28s %-6s x%-3d %s" % (name, val, n, SHORT_ALLOWED[name]))
    if skipped:
        print("  too short to place safely, left as literals: %s"
              % ", ".join("%s=%s" % (n, v) for n, v in sorted(skipped)))
    if absent:
        print("  NOT FOUND in the body, look at each: %s"
              % ", ".join("%s=%s" % (n, v) for n, v in sorted(absent)))


if __name__ == "__main__":
    main()
