#!/usr/bin/env python3
"""The two generation caps of this work, each read from the tool that ran it, and the freeze of the chain.

The chain as run grew every seed with «$BIN g 36000» and ran its five downstream stages with
SIMPAPER_PATCH_LIMIT 40000; item 95 (square20-0826-95) regrew five capped seeds with «$BIN g 72000» and
80000. The article never pools the two, so each cap is a number of its own, parsed here from the shipped
tool that ran it:
  chain_as_run    tools/studies/chain-0826/run_seed.sh, the pre-install file (copy_evidence.py TOOL_FROM)
  g72000_regrowth tools/studies/square20-0826-95/regrow72.sh
the growth line «$BIN g <n> » (exactly one) and the line «N=C<k>; LIM=<n>» (exactly one). The freeze time
and the seeds in and out of the chain as run are counted from evidence/derived/chain-as-run.csv
(written by copy_evidence.py). Writes evidence/derived/caps.csv.

Usage: caps.py [--out PATH]
"""
import argparse, csv, hashlib, os, re, subprocess, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = {"chain_as_run": "tools/studies/chain-0826/run_seed.sh",
         "g72000_regrowth": "tools/studies/square20-0826-95/regrow72.sh"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(S, "evidence", "derived", "caps.csv"))
    a = ap.parse_args()
    out = []

    def put(scope, q, v, src):
        out.append({"scope": scope, "quantity": q, "value": v, "source": src})
    for scope, rel in TOOLS.items():
        txt = open(os.path.join(S, rel)).read()
        g = re.findall(r"^\s*\$BIN g (\d+) ", txt, re.M)
        lim = re.findall(r"^N=C\d+; LIM=(\d+)", txt, re.M)
        if len(g) != 1 or len(lim) != 1:
            sys.exit("caps.py: %s: %d growth lines and %d LIM lines, expected one each" % (rel, len(g), len(lim)))
        put(scope, "generation_cap", g[0], rel + " line «$BIN g <n>»")
        put(scope, "patch_limit", lim[0], rel + " line «N=C<k>; LIM=<n>»")
        put(scope, "tool_sha256", hashlib.sha256(open(os.path.join(S, rel), "rb").read()).hexdigest(), rel)
    p = os.path.join(S, "evidence", "derived", "chain-as-run.csv")
    with open(p, newline="") as fh:
        rs = list(csv.DictReader(l for l in fh if not l.startswith('"#')))
    fz = {r["freeze_utc"] for r in rs}
    if len(fz) != 1:
        sys.exit("caps.py: chain-as-run.csv names %d freeze times" % len(fz))
    put("freeze", "freeze_utc", fz.pop(), "derived/chain-as-run.csv freeze_utc")
    put("freeze", "seeds_in", sum(r["in_chain_as_run"] == "yes" for r in rs), "derived/chain-as-run.csv in_chain_as_run = yes")
    put("freeze", "seeds_out", sum(r["in_chain_as_run"] == "no" for r in rs), "derived/chain-as-run.csv in_chain_as_run = no")
    put("freeze", "seeds_out_at_g72000", sum(r["in_chain_as_run"] == "no" and r["growth_generation_cap"] == "72000" for r in rs),
        "derived/chain-as-run.csv in_chain_as_run = no and growth_generation_cap = 72000")
    now = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    with open(a.out, "w", newline="") as fh:
        fh.write('"# written by src/tools/caps.py at %s: the generation cap and patch limit of the chain as run and of '
                 'item 95\'s regrowths, parsed from the shipped tools, and the freeze of chain-0826 from chain-as-run.csv"\n' % now)
        w = csv.DictWriter(fh, fieldnames=["scope", "quantity", "value", "source"])
        w.writeheader()
        w.writerows(out)
    print("caps.py: %s" % "; ".join("%s %s %s" % (r["scope"], r["quantity"], str(r["value"])[:12]) for r in out))


if __name__ == "__main__":
    main()
