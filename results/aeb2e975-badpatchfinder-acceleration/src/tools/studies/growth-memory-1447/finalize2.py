#!/usr/bin/env python3
"""finalize2.py <attempt> <cap> [<cap> ...]: growth-memory-1447's summary of lever (ii), the shared chunk store cap.

Reads evidence/growth-<tag>.csv for unchanged (the delivered binary, store uncapped), memstore (instrumented, uncapped)
and unchanged-cap<cap> for each cap given, and evidence/memlog-memstore.txt (SA_MEM lines, fields in
tools/make_variants.py: ..., VmRSS kB at 11, VmHWM kB at 12, unix time 13, store held 14, hits 15, misses 16).
Writes evidence/summary-cap.csv (tool,quantity,value,source). Where the memory lives, at the SA_MEM line with the largest
VmRSS: store chunks held times 7,077,888 bytes (192^3 uint8, zarr_1.h), the patch grid estimate, and the rest.
Bar of DECLARATION.md per cap: growth_peak_rss_kb at most half of unchanged's, sheets identical to the delivered ones.
Then the queue item and one ledger row (csv.writer, ten fields). A missing number is «not measurable».
SA_CHECK_ONLY=1: prints the rows, writes nothing.
"""
import csv, os, subprocess, sys

M = "/data/scrollagent/runs/rev1/growth-memory-1447"
HOME = "/data/scrollagent"
TOOL = "growth-memory-1447/tools/finalize2.py"
NM = "not measurable"
CHUNK = 192 ** 3


def g(tag):
    p = M + "/evidence/growth-%s.csv" % tag
    return {r["quantity"]: r["value"] for r in csv.DictReader(open(p))} if os.path.exists(p) else {}


def main():
    a, caps = sys.argv[1], sys.argv[2:]
    check = os.environ.get("SA_CHECK_ONLY") == "1"
    now = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    rows = []

    def add(q, v, src):
        rows.append([TOOL, q, str(v), src])

    U = g("unchanged")
    tags = ["unchanged", "memstore", "streamfree"] + ["unchanged-cap%s" % c for c in caps]
    for t in tags:
        d = g(t)
        for q in ("shared_chunks_cap", "mem_available_gb_at_start", "growth_return_code", "growth_wall_clock_seconds",
                  "growth_peak_rss_kb", "growth_identity", "downstream", "sheets_identity"):
            add("%s_%s" % (t, q), d.get(q, NM), "evidence/growth-%s.csv" % t)
    ml = M + "/evidence/memlog-memstore.txt"
    L = [l.strip().split(",") for l in open(ml) if l.startswith("SA_MEM,")] if os.path.exists(ml) else []
    if L and len(L[0]) >= 17:
        pk = max(L, key=lambda x: int(x[11]))
        rss = int(pk[11]) * 1024
        store = int(pk[14]) * CHUNK
        patches = int(pk[5])
        add("memstore_peak_line_vmrss_bytes", rss, ml)
        add("memstore_peak_line_store_chunks_held", pk[14], ml)
        add("memstore_peak_line_store_bytes", store, "chunks held times 7,077,888")
        add("memstore_peak_line_store_share_of_rss", "%.3f" % (store / rss), "store bytes over VmRSS")
        add("memstore_peak_line_patch_grid_bytes_estimate", patches, ml)
        add("memstore_peak_line_patch_share_of_rss", "%.3f" % (patches / rss), "patch estimate over VmRSS")
        add("memstore_peak_line_accepted_patches", pk[2], ml)
        add("memstore_peak_line_uordblks", pk[8], ml)
        add("memstore_peak_line_hblkhd", pk[10], ml)
        add("memstore_last_line_store_hits", L[-1][15], ml)
        add("memstore_last_line_store_misses", L[-1][16], ml)
    else:
        add("memstore_peak_line", NM, "no SA_MEM line with store fields")
    verdicts = []
    for c in caps:
        d = g("unchanged-cap%s" % c)
        try:
            r = int(d["growth_peak_rss_kb"]) / int(U["growth_peak_rss_kb"])
            tr = float(d["growth_wall_clock_seconds"]) / float(U["growth_wall_clock_seconds"])
            ok = d.get("sheets_identity", "").startswith("identical") and d.get("growth_identity", "").startswith("identical")
            v = "pass" if (r <= 0.5 and ok) else "fail"
            r, tr = "%.3f" % r, "%.3f" % tr
        except (KeyError, ValueError, ZeroDivisionError):
            r = tr = v = NM
        add("cap%s_peak_ratio_over_unchanged" % c, r, "growth_peak_rss_kb of the two CSVs")
        add("cap%s_wall_clock_ratio_over_unchanged" % c, tr, "growth_wall_clock_seconds of the two CSVs; the machine carried other growths")
        add("cap%s_bar_verdict" % c, v, "peak ratio <= 0.5, growth tree and sheets identical (DECLARATION.md)")
        verdicts.append((c, r, tr, v))
    if check:
        for x in rows:
            print(",".join(x))
        return
    with open(M + "/evidence/summary-cap.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tool", "quantity", "value", "source"])
        w.writerows(rows)
    b = {r["quantity"]: r["value"] for r in csv.DictReader(open(M + "/evidence/summary-cap.csv"))}
    best = [v for v in verdicts if v[3] == "pass"]
    slug = "chunk-store-cap-" + ("halves-peak" if best else "bar-not-met")
    q = HOME + "/context/coordinator/to-be-reviewed/%s-growth-memory-1447-%s.md" % (now[:10], slug)
    capline = "; ".join("cap %s chunks: peak ratio %s, wall clock ratio %s, growth tree %s, sheets %s, bar %s" % (
        c, b["cap%s_peak_ratio_over_unchanged" % c], b["cap%s_wall_clock_ratio_over_unchanged" % c],
        b["unchanged-cap%s_growth_identity" % c], b["unchanged-cap%s_sheets_identity" % c], b["cap%s_bar_verdict" % c])
        for c in caps)
    text = """# The growth's memory is the shared store of decompressed chunks, and capping it with SIMPAPER_SHARED_CHUNKS %s on %s

- study: runs/rev1/growth-memory-1447/
- claim: on %s (g 36000), at the instrumented growth's largest VmRSS (%s bytes) the shared chunk store of zarr_1.c holds %s chunks, %s bytes, a share %s of VmRSS, while the accepted patches' grids are %s bytes (share %s); the delivered binary unchanged peaks at %s kB ru_maxrss (store uncapped, a quarter of MemAvailable at start: %s GB available); with the same binary and SIMPAPER_SHARED_CHUNKS set: %s. Lever (i), writing patches as they finish (streamfree), is filed apart.
- evidence: runs/rev1/growth-memory-1447/evidence/summary-cap.csv, column value, rows memstore_peak_line_store_share_of_rss, cap<k>_peak_ratio_over_unchanged, cap<k>_bar_verdict; SA_MEM lines in evidence/memlog-memstore.txt; per file identity in evidence/growth-identity-unchanged-cap<k>.csv and evidence/sheets-identity-unchanged-cap<k>.csv; binary identity in evidence/binary-gate.csv
- request: verify
- filed: %s, by the coordinator
""" % ("halves the peak with identical sheets" if best else "does not meet the bar", a, a,
       b.get("memstore_peak_line_vmrss_bytes", NM), b.get("memstore_peak_line_store_chunks_held", NM),
       b.get("memstore_peak_line_store_bytes", NM), b.get("memstore_peak_line_store_share_of_rss", NM),
       b.get("memstore_peak_line_patch_grid_bytes_estimate", NM), b.get("memstore_peak_line_patch_share_of_rss", NM),
       b["unchanged_growth_peak_rss_kb"], b["unchanged_mem_available_gb_at_start"], capline, now)
    open(q, "w").write(text)
    with open(HOME + "/ledger/ledger.csv", "a", newline="") as f:
        csv.writer(f).writerow([now, "rev1", "coordinator-agent", "growth-memory-chunk-store-cap-measured",
                                "%s: store share of peak VmRSS %s; %s" % (a, b.get("memstore_peak_line_store_share_of_rss", NM), capline),
                                TOOL, "", "", "0",
                                "runs/rev1/growth-memory-1447/evidence/summary-cap.csv " + q.replace(HOME + "/", "")])
    print("summary-cap, queue item %s and ledger row written" % q)


if __name__ == "__main__":
    main()
