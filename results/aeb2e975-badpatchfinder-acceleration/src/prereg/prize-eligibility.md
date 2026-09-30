# Declaration: prize-eligibility, the state of the two prize lists after villa PR 1887

Written 2026-09-26T08:20:28Z (`date -u`), before the tool below was run.

What is read, and nothing else: the pull request 1887 of ScrollPrize/villa (its metadata and its
file diff) and the file `scrollprize.org/src/data/prizeEligibility.json` at the tip of villa's
main branch, both from the public GitHub API, unauthenticated, nothing of ours sent. The raw
answers are kept in `log/`.

What is written: `evidence/prize-eligibility.csv`, one row, by `tools/read_prize_eligibility.py`.
The row carries who merged the pull request and when, the one line it removes from the list, the
counts of the First Letters list and of the 2027 Grand Prize list at main, whether PHerc1447 and
PHerc0139 are on each, and the count of the union of the two lists. Checks are columns: the
removed scroll must be absent from the First Letters list at main, and the tool refuses when the
pull request is not merged or removes more than one scroll.

Why: the works of this laboratory say PHerc. 1447 is eligible for First Letters. The coordinator
found on 2026-09-26 that it is not on the list any more; the director named the pull request.
Every sentence corrected on this reading takes its date, pull request number and counts from the
row, as macros where the work uses macros.

This is not a measurement of papyrus and changes no measurement of any work.
