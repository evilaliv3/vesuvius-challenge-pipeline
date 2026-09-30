#!/usr/bin/env python3
"""Write evidence/prize-eligibility.csv: villa PR 1887 and the two prize lists at villa's main.

One row. Every cell is read from an answer of the public GitHub API, unauthenticated, and the
answers are kept in log/ under the time they were read. Checks are columns beside the values:
the scroll the pull request removes must be absent from the First Letters list at main. The tool
refuses, and writes nothing, when the pull request is not merged, when its diff of
prizeEligibility.json removes anything but exactly one scroll line, or when a list is missing.

Usage: read_prize_eligibility.py [--study DIR]
"""
import argparse, csv, datetime, hashlib, json, os, re, sys, urllib.request

REPO = "ScrollPrize/villa"
PR = 1887
LIST_PATH = "scrollprize.org/src/data/prizeEligibility.json"
DOCS_PATH = "scrollprize.org/docs/34_prizes.md"
API = "https://api.github.com/repos/%s" % REPO
RAW = "https://raw.githubusercontent.com/%s/%s/%s"
TOOL = "prize-eligibility/tools/read_prize_eligibility.py"


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get(url, log_dir, name):
    req = urllib.request.Request(url, headers={"User-Agent": "scrollagent-read-only",
                                               "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
    at = now()
    fn = "%s-%s.json" % (name, at.replace("-", "").replace(":", ""))
    with open(os.path.join(log_dir, fn), "wb") as fh:
        fh.write(body)
    return body, at, "log/" + fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    a = ap.parse_args()
    log_dir = os.path.join(a.study, "log")
    os.makedirs(log_dir, exist_ok=True)

    body, pr_at, pr_log = get("%s/pulls/%d" % (API, PR), log_dir, "villa-pr-%d" % PR)
    pr = json.loads(body)
    if not pr.get("merged"):
        sys.exit("read_prize_eligibility.py: PR %d is not merged, refused" % PR)
    body, files_at, files_log = get("%s/pulls/%d/files" % (API, PR), log_dir, "villa-pr-%d-files" % PR)
    files = [f for f in json.loads(body) if f["filename"] == LIST_PATH]
    if len(files) != 1:
        sys.exit("read_prize_eligibility.py: PR %d touches %s %d times, expected 1"
                 % (PR, LIST_PATH, len(files)))
    patch = files[0].get("patch", "")
    removed = [l[1:] for l in patch.splitlines() if l.startswith("-") and not l.startswith("---")]
    added = [l[1:] for l in patch.splitlines() if l.startswith("+") and not l.startswith("+++")]
    if len(removed) != 1 or added:
        sys.exit("read_prize_eligibility.py: the diff removes %d and adds %d lines, expected 1 and 0"
                 % (len(removed), len(added)))
    m = re.search(r'"scroll":\s*"([^"]+)",\s*"volume":\s*"([^"]+)"', removed[0])
    if not m:
        sys.exit("read_prize_eligibility.py: the removed line names no scroll: %r" % removed[0])
    removed_scroll, removed_volume = m.group(1), m.group(2)
    # The reason, as the same pull request writes it on the prize page: the one added line of
    # docs/34_prizes.md that says which scrolls the First Letters set now excludes. It names no
    # scroll; the removal above is what ties it to one.
    docs = [f for f in json.loads(body) if f["filename"] == DOCS_PATH]
    reason = [l[1:].strip() for f in docs for l in f.get("patch", "").splitlines()
              if l.startswith("+") and "letters have now been found" in l]
    if len(reason) != 1:
        sys.exit("read_prize_eligibility.py: %d added lines of %s give the reason, expected 1"
                 % (len(reason), DOCS_PATH))

    body, main_at, main_log = get("%s/commits/main" % API, log_dir, "villa-main-commit")
    main = json.loads(body)
    main_sha = main["sha"]
    body, list_at, list_log = get(RAW % (REPO, main_sha, LIST_PATH), log_dir, "villa-prizeEligibility")
    lists = json.loads(body)
    for k in ("first-letters-2027", "grand-prize-2027"):
        if k not in lists:
            sys.exit("read_prize_eligibility.py: %s has no list %s" % (LIST_PATH, k))
    fl = [x["scroll"] for x in lists["first-letters-2027"]]
    gp = [x["scroll"] for x in lists["grand-prize-2027"]]
    yn = lambda b: "yes" if b else "no"
    merged_at = pr["merged_at"]
    d = datetime.datetime.strptime(merged_at, "%Y-%m-%dT%H:%M:%SZ")

    row = {
        "pr": PR,
        "title": pr["title"],
        "author": pr["user"]["login"],
        "state": pr["state"],
        "merged": yn(pr["merged"]),
        "merged_at": merged_at,
        "merged_day": d.day,
        "merged_month": d.strftime("%B"),
        "merged_by": (pr.get("merged_by") or {}).get("login", ""),
        "base": pr["base"]["ref"],
        "merge_commit_sha": pr["merge_commit_sha"],
        "list_file": LIST_PATH,
        "removed_line": removed[0].strip(),
        "removed_scroll": removed_scroll,
        "removed_volume": removed_volume,
        "reason_line_added": reason[0],
        "reason_file": DOCS_PATH,
        "main_sha": main_sha,
        "main_committed": main["commit"]["committer"]["date"],
        "list_sha256": hashlib.sha256(body).hexdigest(),
        "first_letters_count_main": len(fl),
        "first_letters_scrolls_main": " ".join(fl),
        "grand_prize_count_main": len(gp),
        "grand_prize_scrolls_main": " ".join(gp),
        "union_count_main": len(set(fl) | set(gp)),
        "PHerc1447_on_first_letters_main": yn("PHerc1447" in fl),
        "PHerc1447_on_grand_prize_main": yn("PHerc1447" in gp),
        "PHerc0139_on_either_main": yn("PHerc0139" in fl or "PHerc0139" in gp),
        "removed_scroll_absent_from_first_letters_main": yn(removed_scroll not in fl),
        "pr_source": "GitHub API, GET /repos/%s/pulls/%d, answered %s, %s" % (REPO, PR, pr_at, pr_log),
        "files_source": "GitHub API, GET /repos/%s/pulls/%d/files, answered %s, %s"
                        % (REPO, PR, files_at, files_log),
        "main_source": "GitHub API, GET /repos/%s/commits/main, answered %s, %s" % (REPO, main_at, main_log),
        "list_source": "%s at %s, read %s, %s" % (LIST_PATH, main_sha, list_at, list_log),
        "tool": TOOL,
    }
    if row["removed_scroll_absent_from_first_letters_main"] != "yes":
        sys.exit("read_prize_eligibility.py: %s is still on the First Letters list at main" % removed_scroll)
    out = os.path.join(a.study, "evidence", "prize-eligibility.csv")
    with open(out, "w", newline="") as fh:
        fh.write('"# villa pull request %d and the two prize lists of %s at the tip of villa main, read '
                 'from the public GitHub API, unauthenticated, nothing of ours sent. One row. '
                 'removed_scroll_absent_from_first_letters_main is the check of the removal against '
                 'main, a column and not a sentence. Written %s by %s."\n' % (PR, LIST_PATH, now(), TOOL))
        w = csv.DictWriter(fh, fieldnames=list(row))
        w.writeheader()
        w.writerow(row)
    print("wrote %s: PR %d merged %s by %s; First Letters %d, Grand Prize %d, union %d; %s on FL: %s"
          % (out, PR, merged_at, row["merged_by"], len(fl), len(gp), row["union_count_main"],
             removed_scroll, row["PHerc1447_on_first_letters_main"]))


if __name__ == "__main__":
    main()
