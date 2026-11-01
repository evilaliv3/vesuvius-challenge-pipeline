#!/usr/bin/env python3
"""Count the pages of a PDF three independent ways and refuse to answer when they disagree.

Written on 2026-09-18 because one file was reported as nine, ten and eleven pages by three
different readers on the same day, and two of the three answers were wrong for two different
reasons. Both reasons are worth keeping in the tool:

  the ten   came from grepping for `/Count` near a `/Type /Pages` token. In the file in question
            object 442 is the page tree root with `/Count 9` and object 443, immediately after it,
            is `/Type /Outlines` with `/Count 10`, the bookmark entries. A wide window or a "largest
            /Count in the file" rule returns the table of contents instead of the page count.
  the eleven came from reading a different file with the same name. The working copy and the
            published copy of a paper live at the same relative path, one on disk and one on a
            remote, and only the digest tells them apart. This tool therefore prints the size and
            the sha256 of what it actually read, so the answer names its own input.

`build_papers.sh` already reports the page count of a paper it just built, by reading "Output
written on" out of the LaTeX log. That is the right source for a file we compiled and no use at all
for a file we downloaded, which is what this is for.

Usage:  python3 tools/pdf_pages.py FILE [FILE ...]
Exit code 1 if any file fails to parse or if the three methods disagree about one.
"""
import hashlib
import re
import sys
import zlib


class Document:
    """Just enough PDF to reach the page tree: top level objects plus object streams."""

    def __init__(self, data):
        self.data = data
        self.objs = {}
        for m in re.finditer(rb'(?<![0-9])(\d+)\s+(\d+)\s+obj\b', data):
            end = data.find(b'endobj', m.end())
            # a later definition of the same number wins, which is what an incremental update means
            self.objs[int(m.group(1))] = data[m.end(): end if end > 0 else m.end() + 4000]
        self._expand_object_streams()

    def _expand_object_streams(self):
        """A /Type /ObjStm holds other objects, compressed, behind a table of number and offset."""
        for body in list(self.objs.values()):
            if b'/ObjStm' not in body:
                continue
            m = re.search(rb'stream\r?\n', body)
            n = re.search(rb'/N\s+(\d+)', body)
            first = re.search(rb'/First\s+(\d+)', body)
            if not (m and n and first):
                continue
            raw = body[m.end():]
            cut = raw.find(b'endstream')
            if cut >= 0:
                raw = raw[:cut]
            try:
                dec = zlib.decompress(raw)
            except zlib.error:
                continue
            n, first = int(n.group(1)), int(first.group(1))
            head = dec[:first].split()
            for i in range(n):
                num, off = int(head[2 * i]), int(head[2 * i + 1])
                nxt = int(head[2 * i + 3]) + first if i + 1 < n else len(dec)
                self.objs[num] = dec[first + off: nxt]

    def get(self, num):
        return self.objs.get(num, b'')


def _is_leaf(body):
    """A page, and not the /Pages node above it."""
    return re.search(rb'/Type\s*/Page\b(?!s)', body) is not None


def _kids(body):
    m = re.search(rb'/Kids\s*\[(.*?)\]', body, re.S)
    return [int(x) for x in re.findall(rb'(\d+)\s+\d+\s+R', m.group(1))] if m else []


def _walk(doc, num, seen):
    if num in seen:
        return 0
    seen.add(num)
    body = doc.get(num)
    if _is_leaf(body):
        return 1
    return sum(_walk(doc, k, seen) for k in _kids(body))


def counts(path):
    """(declared, walked, leaves), any of which may be None when the file does not say."""
    data = open(path, 'rb').read()
    doc = Document(data)

    roots = {int(m.group(1)) for m in re.finditer(rb'/Root\s+(\d+)\s+(\d+)\s+R', data)}
    roots |= {n for n, b in doc.objs.items() if re.search(rb'/Type\s*/Catalog\b', b)}

    declared = walked = None
    for r in sorted(roots):
        m = re.search(rb'/Pages\s+(\d+)\s+\d+\s+R', doc.get(r))
        if not m:
            continue
        node = int(m.group(1))
        c = re.search(rb'/Count\s+(\d+)', doc.get(node))
        # the /Count of the page tree ROOT, reached through the catalogue: never a loose grep
        declared = int(c.group(1)) if c else None
        walked = _walk(doc, node, set())
        break

    leaves = sum(1 for b in doc.objs.values() if _is_leaf(b))
    return data, declared, walked, leaves


def main(argv):
    if not argv:
        print(__doc__.strip().splitlines()[-3])
        return 2
    bad = False
    for path in argv:
        try:
            data, declared, walked, leaves = counts(path)
        except Exception as exc:                       # noqa: BLE001, a bad PDF is an answer too
            print(f"{path}: unreadable, {exc}")
            bad = True
            continue
        got = {declared, walked, leaves} - {None}
        digest = hashlib.sha256(data).hexdigest()
        agree = len(got) == 1
        bad = bad or not agree
        print(f"{path}\n  {len(data)} bytes  sha256 {digest}")
        print(f"  page tree /Count {declared}   walked leaves {walked}   /Type /Page objects {leaves}")
        print(f"  pages: {got.pop() if agree else 'DISAGREEMENT, do not quote any of them'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
