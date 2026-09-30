#!/usr/bin/env python3
"""Refuse a paper whose date was taken from the clock instead of being declared.

Every paper of this series prints a date in the stripe down the margin of its first page, and
pdfTeX stamps the same instant into /CreationDate and /ModDate. Both come from SOURCE_DATE_EPOCH,
which the build exports: it is the date of the revision, chosen and written down, and it is bumped
whenever the paper is revised.

The failure this check exists for is silence. If SOURCE_DATE_EPOCH is not exported, pdfTeX does not
stop and does not warn: it reads the clock, stamps the moment of the build, and the paper ships
with a date nobody declared, which looks exactly like a declared one. That is what had happened to
the reading bench paper, whose build set no epoch and whose published PDF carried 08:29:51 of the
day it was built. A date that says when a machine happened to run is not the date of the revision,
and two builds of one unchanged source disagree in their bytes, so the file cannot be checked
against a published sha256 either.

So the build asks this tool, after LaTeX, whether the dates in the file are the declared ones. They
are the same for both keys and exact to the second, so there is nothing to tolerate: either the
epoch reached pdfTeX or it did not.

    check_build_date.py <pdf> <epoch>

Exit 0 if /CreationDate and /ModDate are both the given epoch, 1 otherwise, or if the file carries
no date at all, or if the epoch given is not a number.
"""
import datetime as dt
import re
import sys


def declared(epoch):
    return dt.datetime.fromtimestamp(epoch, dt.timezone.utc)


def stamped(raw):
    """The instant of a PDF date string, D:YYYYMMDDHHmmSS followed by Z or an offset."""
    m = re.match(r"D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(Z|[+-]\d{2}'\d{2}')?", raw)
    if not m:
        return None
    y, mo, d, h, mi, s = (int(x) for x in m.groups()[:6])
    zone = m.group(7) or "Z"
    off = dt.timedelta(0)
    if zone != "Z":
        hh, mm = int(zone[1:3]), int(zone[4:6])
        off = dt.timedelta(hours=hh, minutes=mm)
        if zone[0] == "-":
            off = -off
    return dt.datetime(y, mo, d, h, mi, s, tzinfo=dt.timezone.utc) - off


def main():
    if len(sys.argv) != 3:
        print(__doc__.strip().splitlines()[-4])
        return 1
    path, raw_epoch = sys.argv[1], sys.argv[2]
    try:
        epoch = int(raw_epoch)
    except ValueError:
        print(f"  !! the build date is not declared: SOURCE_DATE_EPOCH is {raw_epoch!r}")
        return 1
    want = declared(epoch)
    blob = open(path, "rb").read()
    found = {}
    for key in ("CreationDate", "ModDate"):
        m = re.search(rb"/" + key.encode() + rb"\s*\((D:[^)]*)\)", blob)
        found[key] = m.group(1).decode("latin-1") if m else None
    bad = False
    for key, raw in found.items():
        if raw is None:
            print(f"  !! the PDF carries no /{key}")
            bad = True
            continue
        got = stamped(raw)
        if got is None:
            print(f"  !! /{key} is not a date this tool can read: {raw}")
            bad = True
        elif got != want:
            print(f"  !! /{key} is {got:%Y-%m-%d %H:%M:%S}Z and the declared date is "
                  f"{want:%Y-%m-%d %H:%M:%S}Z")
            print("     The build did not export SOURCE_DATE_EPOCH and FORCE_SOURCE_DATE to "
                  "pdfTeX, so the date in this file was read from the clock.")
            bad = True
    if not bad:
        print(f"  build date in the PDF: {want:%Y-%m-%d} as declared, in /CreationDate and /ModDate")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
