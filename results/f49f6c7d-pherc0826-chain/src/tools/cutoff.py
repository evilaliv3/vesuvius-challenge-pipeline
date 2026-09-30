#!/usr/bin/env python3
"""The cut off of 2026-09-29T03:30:00Z, declared before it (director 2026-09-28T12:21:38Z, owner's word).

THE RULE, written 2026-09-28T12:3xZ, before the cut off:
  road 1b   if area-0826-90/collection-eight-6365.csv is not in this work's snapshot at the cut off, the
            article uses the four seed collection and says the eight seed run did not finish in time;
            if it is there, the eight seed paragraph is used. Decided once, at the first run of this
            tool at or after the cut off, and never changed after: a file that lands later does not
            reopen the decision.
  item 91   each arm A to D of stevens-changes-0826-91/arms.csv is decided the same way, once, at the
            cut off: an arm with at least one completed seed prints its row as aggregate91.py wrote it
            (medians over its completed seeds), with the count of completed seeds beside it; an arm with
            none prints «not run in time» in every cell.
  square95  the checks of the 21.7474 mm sheet (item 95, declared 2026-09-28T14:3xZ, before the cut off):
            square20-0826-95/checks-PHerc0826-seed2604.csv in the snapshot at the cut off with a row
            v2_crossing and a row one_lamina, both verdict «clean», gives «clean»; any verdict «crossing
            found» gives «crossing found»; the file absent, a row missing or a verdict «not measurable»
            gives «not complete». The text says which, and nothing more. Amended 2026-09-28T14:5xZ (director
            14:50:30Z), before the cut off: in EVERY branch the square is called «hole free, not certified one
            lamina» and never a 20 mm sheet or result; the crossing branch adds the largest square avoiding the
            flagged cells of each check, from the same file. The chain as run delivers no 20 mm square.
Column state_now is what the rule would give if it were decided now; a PREVIEW before the cut off may print
the square95 sentence from it (the files it reads are the same), never the road 1b or item 91 ones.
Before the cut off every undecided item is «open» and the article build refuses on its pending macros,
as it always has. The decision is a row of src/evidence/derived/cutoff.csv, with the time it was taken.

Usage: cutoff.py [--at ISO]    --at is for testing the rule only; the file it writes then says so
"""
import argparse, csv, datetime, os, re, subprocess, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(S, "evidence", "studies")
OUT = os.path.join(S, "evidence", "derived", "cutoff.csv")
CUTOFF = "2026-09-29T03:30:00Z"


def rd(p):
    with open(p, newline="") as fh:
        return list(csv.DictReader(l for l in fh if not l.lstrip().startswith(('"#', "#"))))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--at", default=None)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    now = a.at or subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    past = now >= CUTOFF
    old = {r["item"]: r for r in rd(a.out)} if os.path.exists(a.out) else {}
    rows = []

    def decide(item, present, used, fallback, note, completed="", of=""):
        if item in old and old[item]["decision"] != "open":
            rows.append(old[item]); return
        d = ("open" if not past else (used if present else fallback))
        rows.append({"item": item, "decision": d, "decided_utc": now if past else "", "cutoff": CUTOFF,
                     "state_now": used if present else fallback,
                     "completed": completed, "of": of,
                     "note": note + (" (test run with --at)" if a.at else "")})

    eight = os.path.exists(os.path.join(EV, "area-0826-90", "collection-eight-6365.csv"))
    decide("road1b", eight, "eight seed run", "four seed collection, eight seed run not finished in time",
           "collection-eight-6365.csv %s in the snapshot" % ("is" if eight else "is not"))
    arms_p = os.path.join(EV, "stevens-changes-0826-91", "arms.csv")
    arms = {r["arm"]: r for r in rd(arms_p)} if os.path.exists(arms_p) else {}
    for arm in "ABCD":
        r = arms.get(arm, {})
        m = re.search(r"completed (\d+)", r.get("note", ""))
        done = int(m.group(1)) if m else 0
        seeds_p = os.path.join(EV, "stevens-changes-0826-91", "seeds.csv")
        of = len(rd(seeds_p)) if os.path.exists(seeds_p) else ""
        decide("arm" + arm, done > 0, "row as written, completed seeds beside it", "not run in time",
               "arms.csv row %s: %s; of = rows of seeds.csv" % (arm, r.get("note", "no row")), done, of)
    ck = os.path.join(EV, "square20-0826-95", "checks-PHerc0826-seed2604.csv")
    verdicts = {r["check"]: r["verdict"] for r in rd(ck)} if os.path.exists(ck) else {}
    need = ("v2_crossing", "one_lamina")
    if any(verdicts.get(k) == "crossing found" for k in need):
        state = "crossing found"
    elif all(verdicts.get(k) == "clean" for k in need):
        state = "clean"
    else:
        state = "not complete"
    decide("square95", True, state, state, "checks file %s; verdicts %s" % ("present" if verdicts else "absent", verdicts or "none"))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        fh.write('"# written by src/tools/cutoff.py: the decisions of the declared cut off %s; a decision once taken is '
                 'kept; open means before the cut off"\n' % CUTOFF)
        w = csv.DictWriter(fh, fieldnames=["item", "decision", "decided_utc", "cutoff", "state_now", "completed", "of", "note"])
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print("  cutoff %-7s %s" % (r["item"], r["decision"]))


if __name__ == "__main__":
    main()
