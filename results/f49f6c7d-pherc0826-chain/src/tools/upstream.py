#!/usr/bin/env python3
"""The state of every upstream issue and pull request the article names, from the raw GitHub API.

It reads the JSON saved in src/inputs/github-api/ (one file per item, fetched anonymously from
api.github.com/repos/<owner>/<repo>/issues/<n>, at the time in read-at.txt) and writes one row per
item: repository, number, kind, state, whether merged is known, title, author, opened. A state is
never assumed from memory: a claim of «open» or «merged» in the article is a cell of this file.

Usage: upstream.py [--out PATH]
"""
import argparse, csv, glob, json, os, subprocess, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(S, "inputs", "github-api")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=os.path.join(S, "evidence", "derived", "upstream.csv"))
    a = ap.parse_args()
    rows = []
    for p in sorted(p for p in glob.glob(os.path.join(IN, "*.json")) if not p.endswith("-events.json")):
        d = json.load(open(p))
        if "number" not in d:
            sys.exit("upstream.py: %s is not an issue (%s)" % (p, d.get("message")))
        h = p[:-5] + ".headers.txt"
        if not os.path.exists(h):
            sys.exit("upstream.py: %s has no headers file: the time of its reading is unknown" % p)
        dh = [l.split(":", 1)[1].strip() for l in open(h) if l.lower().startswith("date:")]
        if len(dh) != 1:
            sys.exit("upstream.py: %s has %d Date headers" % (h, len(dh)))
        import email.utils
        read_at = email.utils.parsedate_to_datetime(dh[0]).strftime("%Y-%m-%dT%H:%M:%SZ")
        repo = d["repository_url"].split("/repos/")[1]
        pr = "pull_request" in d
        merged = (d["pull_request"].get("merged_at") or "not merged") if pr else "not a pull request"
        rows.append({"repo": repo, "number": d["number"], "kind": "pull request" if pr else "issue",
                     "state": d["state"], "merged_at": merged, "title": d["title"],
                     "author": d["user"]["login"], "opened": d["created_at"][:10],
                     "closed": (d.get("closed_at") or "not closed")[:10], "read_at": read_at,
                     "file": os.path.basename(p)})
    rows.sort(key=lambda r: (r["repo"], int(r["number"])))
    now = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    with open(a.out, "w", newline="") as fh:
        fh.write('"# written by src/tools/upstream.py at %s from src/inputs/github-api/*.json; the time of each '
                 'reading is the Date header of its answer, column read_at"\n' % now)
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print("  %s#%s %s %s: %s" % (r["repo"], r["number"], r["kind"], r["state"], r["title"][:60]))


if __name__ == "__main__":
    main()
