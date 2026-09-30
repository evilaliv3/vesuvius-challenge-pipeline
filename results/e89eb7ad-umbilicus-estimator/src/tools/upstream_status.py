#!/usr/bin/env python3
"""Where the pull requests this work leads to stand upstream, asked of the clone.

The dated addition at the end of the article says which of the author's pull requests to
ScrollPrize/villa are in the main branch. That is a fact about a repository and it moves, so it
is read here from git and written to a CSV, and the article prints it through macros, never
from memory and never from a message that said so.

It reads the clone and never changes it: no fetch, no checkout. Fetch first, anonymously, the
main branch and the head of each pull request, into the refs this tool reads:

    git -C <clone> fetch upstream main \\
        refs/pull/<n>/head:refs/remotes/upstream-pr/<n>   (once per pull request)

For each pull request it records its head commit, whether that head is an ancestor of the main
branch (a merge commit would make it one), and, because the repository squashes, the commit on
the main branch whose subject ends in «(#<n>)», with its commit time and whether the files it
changes are, file by file, the same as at the head of the pull request. A pull request that has
neither is written as not in the main branch. Whether it is open or closed is not something the
clone knows, and the clone is not asked it.

That state is read, with --api DIR, from the answers of the GitHub API saved in DIR, one pair of
files per pull request, fetched anonymously and never by this tool:

    curl -s -D DIR/villa-pr-<n>.headers.txt -o DIR/villa-pr-<n>.json \\
        https://api.github.com/repos/ScrollPrize/villa/pulls/<n>

The column is named for the day the answers were given, state_as_of_YYYY_MM_DD, from the Date
header of the response, because a state is true on a day and not after it; state_source names
the request, the time and the file. A pull request that was merged is written merged, not
closed. api_head_same_as_clone is the check that the API and the clone speak of the same head.

Version 2, 2026-09-23T20Z: who closed a pull request, and whether a comment came with it. With
--stamp STAMP the answers are read from files that carry the time they were fetched in their
name, so that a later fetch is added beside an earlier one and never over it, and two more
requests are read per pull request:

    curl -s -D DIR/villa-pr-<n>-STAMP.headers.txt -o DIR/villa-pr-<n>-STAMP.json \
        https://api.github.com/repos/ScrollPrize/villa/pulls/<n>
    curl -s -D DIR/villa-pr-<n>-events-STAMP.headers.txt -o DIR/villa-pr-<n>-events-STAMP.json \
        'https://api.github.com/repos/ScrollPrize/villa/issues/<n>/events?per_page=100'
    curl -s -D DIR/villa-pr-<n>-comments-STAMP.headers.txt -o DIR/villa-pr-<n>-comments-STAMP.json \
        'https://api.github.com/repos/ScrollPrize/villa/issues/<n>/comments?per_page=100'

A listing with a next page is refused, since a closing event or comment could sit on the page
not read. The columns added:

  merged                  yes or no, the merged field of the pull request
  closed_at               closed_at of the pull request, or «not closed»
  closed_by               the actor of the last closed event, or «not closed»
  closed_by_is_author     yes or no against the author of the pull request, or «not closed»
  closed_at_same_in_events  the check: closed_at of the pull request is the time of that event
  closed_source           the request, the time it was answered and the file of the events
  comment_at_closing      yes when a comment by the closer, not by a bot, was created within
                          60 seconds of the closed event; no otherwise; or «not closed»
  comment_at_closing_at   its created_at, or «none»
  comment_at_closing_body its body, exactly, or «none»
  comment_source          the request, the time it was answered and the file of the comments

The header is checked: every row must carry exactly the columns of the version it was written
by, in that order, and the tool refuses otherwise.

Version 3, 2026-09-26T05Z: with --merged-at (which needs --stamp) one more column, merged_at, the
merged_at field of the pull request as the API gives it, or «not merged». closed_at of a merged pull
request is the same second on every answer read so far, but the merge time is its own field and the
opening of the article quotes that field, so it is read and not inferred. Files written without the
flag keep the version 2 header byte for byte.

Usage: upstream_status.py [--clone DIR] [--main REF] [--api DIR [--stamp STAMP]]
                          [--out evidence/upstream-status.csv] N ...
"""
import argparse
import csv
import datetime
import email.utils
import json
import os
import re
import subprocess

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def git(clone, *args, check=True):
    r = subprocess.run(["git", "-C", clone, *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit("upstream_status.py: git %s failed: %s" % (" ".join(args), r.stderr.strip()))
    return r


HEADER_V1 = ["pr", "head", "head_ancestor_of_main", "squash_commit", "squash_committed",
             "squash_files_same_as_head", "in_main", "main_tip", "main_tip_committed"]
HEADER_API = ["state_as_of_", "state_source", "api_head_same_as_clone"]
HEADER_V2 = ["merged", "closed_at", "closed_by", "closed_by_is_author", "closed_at_same_in_events",
             "closed_source", "comment_at_closing", "comment_at_closing_at",
             "comment_at_closing_body", "comment_source"]
HEADER_V3 = ["merged_at"]
NOT_CLOSED = "not closed"


def saved(base, request):
    """A saved answer of the GitHub API: its JSON, and the time it was answered from its Date."""
    for ext in (".json", ".headers.txt"):
        if not os.path.exists(base + ext):
            raise SystemExit("upstream_status.py: no %s%s: fetch it first" % (base, ext))
    lines = open(base + ".headers.txt").read().splitlines()
    status = lines[0].split() if lines else []
    if len(status) < 2 or status[1] != "200":
        raise SystemExit("upstream_status.py: %s.headers.txt is not a 200 answer" % base)
    dates = [ln.split(":", 1)[1].strip() for ln in lines if ln.lower().startswith("date:")]
    if len(dates) != 1:
        raise SystemExit("upstream_status.py: %s.headers.txt carries %d Date headers"
                         % (base, len(dates)))
    links = [ln for ln in lines if ln.lower().startswith("link:")]
    if any('rel="next"' in ln for ln in links):
        raise SystemExit("upstream_status.py: %s has a next page, which was not fetched" % base)
    when = email.utils.parsedate_to_datetime(dates[0])
    source = ("GitHub API, GET %s, answered %s, %s.json"
              % (request, when.strftime("%Y-%m-%dT%H:%M:%SZ"), os.path.relpath(base, SRC)))
    return json.load(open(base + ".json")), when, source


def ts(iso):
    return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))


def api_state(api, n, stamp=None):
    """The state of pull request n as the saved answer of the GitHub API gives it."""
    base = os.path.join(api, "villa-pr-%d" % n + ("-" + stamp if stamp else ""))
    d, when, source = saved(base, "/repos/ScrollPrize/villa/pulls/%d" % n)
    if d["number"] != n:
        raise SystemExit("upstream_status.py: %s.json is pull request %s" % (base, d["number"]))
    state = "merged" if d["merged"] else d["state"]
    return when.strftime("%Y_%m_%d"), state, d["head"]["sha"], source, d


def api_closing(api, n, stamp, pr):
    """Who closed pull request n, when, and whether the closer left a comment at that time."""
    ev, _, ev_source = saved(os.path.join(api, "villa-pr-%d-events-%s" % (n, stamp)),
                             "/repos/ScrollPrize/villa/issues/%d/events" % n)
    cm, _, cm_source = saved(os.path.join(api, "villa-pr-%d-comments-%s" % (n, stamp)),
                             "/repos/ScrollPrize/villa/issues/%d/comments" % n)
    row = {"merged": "yes" if pr["merged"] else "no",
           "closed_source": ev_source, "comment_source": cm_source}
    closes = [e for e in ev if e["event"] == "closed"]
    if pr["state"] != "closed":
        if pr["closed_at"] is not None:
            raise SystemExit("upstream_status.py: %d is %s with a closed_at" % (n, pr["state"]))
        row.update({"closed_at": NOT_CLOSED, "closed_by": NOT_CLOSED,
                    "closed_by_is_author": NOT_CLOSED, "closed_at_same_in_events": NOT_CLOSED,
                    "comment_at_closing": NOT_CLOSED, "comment_at_closing_at": "none",
                    "comment_at_closing_body": "none"})
        return row
    if not closes:
        raise SystemExit("upstream_status.py: %d is closed and its events have no closed event" % n)
    last = max(closes, key=lambda e: ts(e["created_at"]))
    if any(e["event"] == "reopened" and ts(e["created_at"]) > ts(last["created_at"]) for e in ev):
        raise SystemExit("upstream_status.py: %d was reopened after its last closed event" % n)
    closer = last["actor"]["login"]
    near = [c for c in cm if c["user"]["login"] == closer and c["user"]["type"] != "Bot"
            and abs((ts(c["created_at"]) - ts(last["created_at"])).total_seconds()) <= 60]
    if len(near) > 1:
        raise SystemExit("upstream_status.py: %d has %d comments by the closer at closing"
                         % (n, len(near)))
    row.update({"closed_at": pr["closed_at"], "closed_by": closer,
                "closed_by_is_author": "yes" if closer == pr["user"]["login"] else "no",
                "closed_at_same_in_events": "yes" if ts(pr["closed_at"]) == ts(last["created_at"]) else "no",
                "comment_at_closing": "yes" if near else "no",
                "comment_at_closing_at": near[0]["created_at"] if near else "none",
                "comment_at_closing_body": near[0]["body"] if near else "none"})
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clone", default=os.environ.get("VILLA_UPSTREAM", "/data/repositories/villa"))
    ap.add_argument("--main", default="upstream/main")
    ap.add_argument("--api", help="folder of saved GitHub API answers, for the open or closed state")
    ap.add_argument("--stamp", help="the fetch time in the names of the saved answers; with it the "
                    "closing columns of version 2 are written")
    ap.add_argument("--merged-at", action="store_true", help="version 3: add the merged_at column")
    ap.add_argument("--out", default=os.path.join(SRC, "evidence", "upstream-status.csv"))
    ap.add_argument("prs", nargs="+", type=int)
    a = ap.parse_args()

    tip = git(a.clone, "rev-parse", a.main).stdout.strip()
    tip_time = git(a.clone, "log", "-1", "--format=%cI", tip).stdout.strip()
    subjects = git(a.clone, "log", "--format=%H%x09%cI%x09%s", a.main).stdout.splitlines()
    rows = []
    for n in a.prs:
        ref = "refs/remotes/upstream-pr/%d" % n
        head = git(a.clone, "rev-parse", "--verify", "-q", ref, check=False).stdout.strip()
        if not head:
            raise SystemExit("upstream_status.py: no %s in %s: fetch it first" % (ref, a.clone))
        ancestor = git(a.clone, "merge-base", "--is-ancestor", head, tip, check=False).returncode == 0
        hits = [s.split("\t", 2) for s in subjects if re.search(r"\(#%d\)$" % n, s.split("\t", 2)[2])]
        if len(hits) > 1:
            raise SystemExit("upstream_status.py: %d commits on %s name #%d" % (len(hits), a.main, n))
        squash, squash_time, same = "", "", ""
        if hits:
            squash, squash_time = hits[0][0], hits[0][1]
            files = git(a.clone, "diff", "--name-only", squash + "^", squash).stdout.split()
            differ = [f for f in files
                      if git(a.clone, "diff", "--quiet", squash, head, "--", f, check=False).returncode]
            same = "yes" if files and not differ else "no"
        in_main = "yes" if (ancestor or (hits and same == "yes")) else "no"
        row = {"pr": n, "head": head, "head_ancestor_of_main": "yes" if ancestor else "no",
               "squash_commit": squash, "squash_committed": squash_time,
               "squash_files_same_as_head": same, "in_main": in_main,
               "main_tip": tip, "main_tip_committed": tip_time}
        if a.api:
            day, state, api_head, source, pr = api_state(a.api, n, a.stamp)
            row["state_as_of_" + day] = state
            row["state_source"] = source
            row["api_head_same_as_clone"] = "yes" if api_head == head else "no"
            if a.stamp:
                closing = api_closing(a.api, n, a.stamp, pr)
                row.update((k, closing[k]) for k in HEADER_V2)
                if a.merged_at:
                    row["merged_at"] = pr["merged_at"] if pr["merged"] else "not merged"
        rows.append(row)
    if a.merged_at and not a.stamp:
        raise SystemExit("upstream_status.py: --merged-at needs --stamp")
    if a.stamp and not a.api:
        raise SystemExit("upstream_status.py: --stamp names files in --api, which was not given")
    if len({tuple(r) for r in rows}) != 1:
        raise SystemExit("upstream_status.py: the API answers were given on different days, "
                         "and one column cannot hold them")
    # The header check: the columns written are exactly the columns of the version asked for.
    want = HEADER_V1 + (HEADER_API if a.api else []) + (HEADER_V2 if a.stamp else []) + \
        (HEADER_V3 if a.merged_at else [])
    got = [c[:len("state_as_of_")] if c.startswith("state_as_of_") else c for c in rows[0]]
    if got != want:
        raise SystemExit("upstream_status.py: the header is %s, not %s" % (got, want))
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("wrote %s, %d rows" % (a.out, len(rows)))


if __name__ == "__main__":
    main()
