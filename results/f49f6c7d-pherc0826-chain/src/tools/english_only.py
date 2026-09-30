"""Sweep a published folder for anything that is not English, in names and in text.

The repository rule is that everything inside it is in English: code, comments, file and folder
names, test names, reports, papers, pre-registrations, captions and the text inside figures. The
rule exists so the work can be published without translating and sent upstream without reworking,
and a rule with no check is a rule that comes back. This is the check.

What it looks at
  names   every path component under the root, split into words, matched against an Italian
          lexicon, plus any non-ASCII character in a name.
  text    every file that decodes as UTF-8 and is not exempt, line by line, matched against the
          same lexicon plus the truncated accent forms Italian writes on an ASCII keyboard
          (e', piu', gia', perche') and the accented forms it writes elsewhere.
  figures a figure's caption and the code that draws it are text and are read as text. A figure
          whose letters are outlines carries no text to read, and the tool says so for each
          binary it could not read rather than passing over it in silence, so that the reader
          knows which files the sweep did not cover.
  traces  the sentences that say the folder was once in another language even when every word of
          them is English: a header declaring a translation, another language named as the one
          the work was written in, a commit named as the place an original went, a table pairing
          an old name with a new one, and an exemption excused by the language of a file or by a
          rename. These run against the text with its line breaks turned into spaces, because
          such a sentence wraps.

What it skips, and says it skipped
  Files git ignores are not in the repository, so they are not swept: build outputs, caches, the
  cut grid slices. The count is printed. When the folder is not in a git work tree, or git is not
  installed, nothing is skipped on this ground and the line says so. The file the tool is running
  from is skipped too, because its lexicon is a list of Italian words by construction.

What it does not do
  It does not detect every language. It detects Italian, which is the language this repository is
  written around, and it reports any non-ASCII letter in a name or in a line, which is how a third
  language would show up. It is a net with a known mesh, not an oracle.

Exemptions
  A file of exemptions carries one `<glob><tab><reason>` per line, `#` for a comment. An exemption
  with no reason is refused. Exemptions that match nothing are reported: a stale exemption is how a
  sweep quietly stops covering something. The default file is `english_only_exempt.txt` beside this
  script; `--exempt` points it elsewhere and `--no-exempt` runs with none, which is the way to see
  what the exemptions are hiding.

Usage
  python3 tools/english_only.py [ROOT] [--exempt FILE] [--no-exempt] [--quiet]
  ROOT defaults to the published folder of research/00001.
  python3 tools/english_only.py --selftest

  --selftest builds a folder carrying one instance of each thing the tool is meant to catch and
  fails unless every rule fires on it. A check nobody has seen fail is worth nothing.

  ROOT defaults to the folder two levels above this file, which is the published folder when the
  script sits in `<folder>/src/tools/`. It is a plain argument so the tool can be pointed at any
  folder.

Exit status
  0 nothing found, 1 something found, 2 the tool could not run.
"""
import argparse
import fnmatch
import os
import re
import subprocess
import sys
import unicodedata
import zlib

# Words that are Italian and are not also English, not an English abbreviation, and not a token a
# programme is likely to spell. Short words are left out on purpose: `la`, `il`, `un`, `di`, `si`,
# `e`, `no`, `per`, `come`, `non`, `media`, `figure`, `state`, `solo` and their like either are
# English or appear inside code, and a lexicon that flags them flags everything.
LEXICON = """
abbastanza accanto accuratezza adesso affermazione aggiornamento aggiunta allora altezza altre
altri altro annotatore appaiare appaiata appaiate appaiati appaiato apposta argomento arrivare
arrotonda attorno attraversa avanti avere avevo avrebbe basta bersaglio bisogno bordo braccio
buttare buttarla calcolata calcolate calcolato cambia cambiamento cambiano cambiare
campionamento campionate campione cancella cancellando capitolo cartella cartelle caso catena
centroide cerchi cerchio che chiamata chiamate chiamato chiunque cioe ciascuno codice colonna
colonne compilata compilate compilati compilato comune conferma confinata confronta confrontano
confronto congelata congelate congelati congelato conclusione conseguenza conservata contiene
conteggio conteggi continua controllo copertura copia corretta corrette corretti corretto corsa
corse cosa cose costruire costruisce costruita costruito credo criterio criteri decisa decise
decisi deciso dedotto degli della delle dello dentro dicono didascalia dieci differenza
difficile dipende diretta dischi discussione disegno dispersione distanza distrugge diventa
diventi divergenza divisione dopo dovuta durante entra entrambi entrambe entro errore errori
esattamente esatta esatto escluso esegue eseguita eseguito esempio esiste esistono esito esiti
esponente essere estrae fallisce famiglia fatta fatte fatti fatto fedele ferma fermare fermarsi
fetta fette figlio filone finche finestra finiva fissa fissata fissate fissato fisso funziona
funzione fuori garanzia gia giorno griglia griglie guarda guardare guardata guardia hanno ieri
imbattibile impossibile incompleta incompleto indietro infatti ingresso insieme intatto intero
interna interno intervallo invece lasciato lavorare lavoro leggere lettura libere libero limite
linea linee lontano lunghezza macchina maggioranza mancanti massimo mediana mediane meglio
mentre meno metrica mettere mezzo migliora migliore milioni millimetri minuti misura misurabile
misurare misurata misurate misurati misurato misure modifica modificata molte molti molto
mostra motivo nascosto nessun nessuna nessuno niente nome nomi nostra nostre nostri nostro
notte nucleo numero numeri nuova nuove nuovi nuovo obiettivo occhio oggi ogni oltre ordine
originale ovunque ovvero pagina parola parole passaggio passeggiata peggiore pensare perche
percorso perde persa perso piccolo piu poco polilinea possono posizione prendere presenta prima
primo produrre proposta proprieta prova prove provare punteggio puo qualcosa qualunque
quale quali quando quantita quattro quello quella quelli quelle questa queste questi questo qui
quindi quindici quinta raffinato rampa ragione regola regole restano resta riferimento riferire
riga righe rilanciano rimane ripara riparazione riportare riporta riprodotta riprodotte risposta
risultato risultati ritirato rotolo rotoli rottura rumore salire saliva sapere sbagliata
sbagliato scarto scegliere scelta scelte scelto schermo scritta scritte scritti scritto
scrivere seconda secondo segnala segnalazione segmenti seguente seme sempre senza servono
sezione sfondo siamo significa singola singolo soglia solamente soltanto somma sonda sopra
sorgente sorprende sospetto sotto spedita spedito spesa spiegare sposta squadra stampa stanno
stata stati stato stessa stesse stessi stesso stima stime strumento strumenti struttura
successivo sufficiente tabella tabelle taglia tanto tetto togliere toglie tolta tolto tornare
torna tornata tramite trascrizione trattino trova trovare tutta tutte tutti tutto ultima ultimo
umbilico unita uscita usare usata usate usati usato utile vale valgono valore valori variante
varianti vecchia vecchio vedere vedi venti ventitre ventiquattro verdetto verdetti verificare
verita vince vinta virgola vuota vuoto
densita dichiarazione dichiarazioni disaccordo incertezza obiettivo obiettivi
preregistrazione preregistrazioni riferimenti sintetica sintetiche sintetici sintetico
versione versioni
""".split()

# The same lexicon written the way Italian is typed on an ASCII keyboard, with a trailing
# apostrophe where the accent belongs. Anchored on a word boundary so a C or shell quote does not
# raise them.
APOSTROPHE = r"""(?<![A-Za-z0-9_])(?:e|ne|se|piu|gia|cio|pero|puo|cosi|perche|poiche|finche|meta
|citta|verita|qualita|liberta|proprieta|possibilita|attivita|unita|puo|sara|saranno|faro|dara
|cosi|percio|affinche|benche|sicche|piu)'""".replace("\n", "")

# Italian words carrying their accents, which is the other way the same words are written.
ACCENTED = (r"(?<![A-Za-z0-9_])(?:è|perché|più|già|cioè|però|può|così|né|sé|poiché|finché|"
            r"metà|città|verità|qualità|libertà|proprietà|possibilità|attività|unità|sarà|"
            r"perciò|affinché|benché|sicché|università|realtà|società)(?![A-Za-zÀ-ÿ])")

# A long unbroken run of base64 is data, not prose: an image inlined in an SVG, a key, a blob.
BASE64 = re.compile(r"[A-Za-z0-9+/]{60,}={0,2}")
NAME_SPLIT = re.compile(r"[^A-Za-zÀ-ÿ]+")
WORD = re.compile(r"[A-Za-zÀ-ÿ]+")
APOSTROPHE_RE = re.compile(APOSTROPHE, re.I)
ACCENTED_RE = re.compile(ACCENTED, re.I)

SKIP_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", "node_modules", ".venv"}
# Extensions whose bytes are not text and whose letters, if any, are drawn as outlines.
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".bin", ".so", ".o", ".a", ".zip", ".gz",
              ".xz", ".lz4", ".npy", ".npz", ".pyc", ".ttf", ".otf", ".woff", ".woff2"}

LEXICON_SET = frozenset(LEXICON)

# Words of the lexicon that are also ordinary English words. They are kept in the lexicon,
# because they are real Italian, but they do not convict a line unless something else on it
# does. Add to this only after checking the word really is English: the list is short on
# purpose, and a long one would empty the sweep.
HOMOGRAPHS = frozenset({"prove"})

# --------------------------------------------------------------------------- traces of a rewrite
#
# A folder can be word for word English and still carry, in plain English, the fact that it was not
# written that way: a header announcing that the file is a translation, a commit named as the place
# the original went, a table pairing an old name with a new one, an exemption excused by the
# language a file is in. None of those is a foreign word, so the lexicon cannot see them, and each
# one tells a reader something the folder does not otherwise say. They are findings like any other.
#
# The rules run against the file's text with its line breaks turned into spaces, because these
# sentences wrap: "Both are in commit" at the end of one line and the digest at the start of the
# next is the shape the check exists for. The line a finding is reported on is the line the match
# starts on.

HEX = r"`?[0-9a-f]{7,40}`?"
OTHER_LANGUAGE = r"Italian|Italiano|French|German|Spanish|Portuguese|Russian|Dutch|Polish"

TRACE_RULES = [
    ("a header that declares a translation", re.compile(
        r"\btranslation\s+from\b"
        r"|\btranslated\s+from\b"
        r"|\b(?:is|as|was)\s+an?\s+translation\b"
        r"|\brenders?\s+the\s+original\s+sentence\s+by\s+sentence\b"
        r"|\bpublished\s+here\s+in\s+English\s+alone\b", re.I)),
    # Narrowed 2026-09-22T17:27Z. This fired on ANY mention of a language name, so build.sh
    # tripped it with the English comment that describes this very check («a paper with an
    # Italian sentence in it»). A rule that flags a tool for naming what the tool looks for is
    # not measuring the document. What it is actually for is a file that DECLARES itself to be
    # in another language, so it now wants a declaring construction around the name and not the
    # bare name.
    # This rule is about THIS document declaring itself to be in another language. It is not
    # about a document that truthfully says a data file it cites is in one: work A discloses
    # exactly that about a CSV, in English, and on 2026-09-22T17:37Z the rule fired on the
    # disclosure three times. So a match whose sentence names a file before it is not a
    # declaration about this document, and is left alone; see subject_is_this_document below.
    ("names another language as the language this was written in", re.compile(
        r"\b(?:written|drafted|typeset|kept|published|composed)\s+(?:here\s+)?in\s+"
        r"(?:" + OTHER_LANGUAGE + r")\b"
        r"|\b(?:the|this|its)\s+(?:" + OTHER_LANGUAGE + r")\s+"
        r"(?:version|text|original|wording|edition|copy)\b"
        r"|\b(?:in|from|into)\s+(?:" + OTHER_LANGUAGE + r")\s+(?:above|below|throughout)\b",
        re.I)),
    ("a commit named as the home of an original", re.compile(
        # same sentence: an original, an earlier version, and a commit hash together
        r"\b(?:original|originals|earlier wording|earlier version|previous version)\b"
        r"[^.]{0,160}?\bcommit\s+" + HEX
        # or the phrasing that says the earlier text went somewhere, which spans sentences
        + r"|\b(?:originals?\s+(?:is|are|has|have)|(?:it|they)\s+(?:has|have)\s+moved"
        r"|(?:is|are)\s+not\s+lost|(?:was|were)\s+published\s+beside)\b"
        r".{0,220}?\bcommit\s+" + HEX
        + r"|\bcommit\s+" + HEX + r"[^.]{0,160}?\b(?:original|originals"
        r"|where (?:it|they) (?:was|were) published)\b", re.I)),
    ("a rename table or a former name", re.compile(
        r"\|\s*working tree\s*\|"
        r"|\|\s*(?:old|former|previous)\s+(?:name|file)\s*\|"
        r"|\|\s*there\s*\|\s*here\s*\|"
        r"|\|\s*here\s*\|\s*there\s*\|"
        r"|\bformerly\s+(?:called|named|known as)\b"
        r"|\bused to be (?:called|named)\b"
        r"|\bthe name it (?:had|used to have|was written under)\b"
        # Narrowed 2026-09-22T17:47:25Z on the director's ruling: this rule is about a PAIR,
        # an old name beside a new one, because that pair is how a former name is quietly
        # carried along. «renamed TO x» names only the new one and hides nothing: prereg/
        # MANIFEST.md says the declarations are «renamed to the study they belong to, with
        # their sha256 below», which is the opposite of hiding a history, and this rule used to
        # flag it. «renamed FROM x» still fires, because that does name the old one.
        r"|\brenamed\s+(?:here\s+)?from\b"
        r"|\brename\s+(?:rule|table|map)\b", re.I)),
]

# The same question asked of an exemption's reason: an exemption is a hole in the sweep, and a hole
# excused by the language a file is in, or by a rename, is the sweep being told not to look at the
# one thing it is for. The only reason left is that somebody else wrote the file.
EXEMPT_REASON_RULES = [
    ("its reason names another language", re.compile(
        r"(?<![A-Za-z0-9_])(?:" + OTHER_LANGUAGE + r")(?![A-Za-z0-9_])"
        r"|\blanguage\s+(?:its|their|the)\b|\btranslat", re.I)),
    ("its reason is about renaming", re.compile(r"\brenam|\brename\b", re.I)),
]


def flatten(lines):
    """The text as one string with the breaks turned into spaces, plus offset -> line number."""
    text = " ".join(lines)
    where, pos = [], 0
    for n, line in enumerate(lines, 1):
        where.append((pos, n))
        pos += len(line) + 1
    return text, where


def line_of(where, offset):
    lo, hi = 0, len(where) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if where[mid][0] <= offset:
            lo = mid
        else:
            hi = mid - 1
    return where[lo][1]


def traces(lines):
    """[(line number, what it is, the text that matched)] for every trace rule that fires."""
    text, where = flatten(lines)
    out = []
    for what, rx in TRACE_RULES:
        for m in rx.finditer(text):
            a = max(0, m.start() - 40)
            if what.startswith("names another language") and names_a_file_first(text, m.start()):
                continue
            out.append((line_of(where, m.start()), what, text[a:m.end() + 40].strip()))
    return sorted(out)


# A path or a file name in the 90 characters before the match means the sentence is ABOUT that
# file, not about the document doing the saying. Work A tells the reader, in English, that a CSV
# it cites was written in Italian and was translated before it was shipped; that is the sweep's
# own rule being obeyed out loud, and flagging it taught nobody anything. A bare declaration
# with no file named before it still fires, which is the case this rule exists for.
FILE_BEFORE = re.compile(
    r"[\w./-]+\.(?:csv|md|tex|py|sh|txt|json|tsv|c|h|cpp|obj|tif|pdf|png)\b"
    r"|\\path\{[^}]*\}|\\texttt\{[^}]*\}|`[^`]+`")


def names_a_file_first(text, start):
    window = text[max(0, start - 90):start]
    return FILE_BEFORE.search(window) is not None


def strip_accents(word):
    return "".join(c for c in unicodedata.normalize("NFD", word) if not unicodedata.combining(c))


def italian_words(text):
    """The Italian words of a piece of text, in the order they appear, without repeats."""
    found = []
    for w in WORD.findall(text):
        low = w.lower()
        if low in LEXICON_SET or strip_accents(low) in LEXICON_SET:
            if low not in found:
                found.append(low)
    return found


def non_ascii(text):
    return sorted({c for c in text if ord(c) > 127 and c.isalpha()})


def git_ignored(root, paths):
    """The subset of `paths` (relative to root) that git ignores, or None when git cannot say."""
    if not paths:
        return set()
    try:
        p = subprocess.run(["git", "-C", root, "check-ignore", "--stdin", "-z"],
                           input="\0".join(paths) + "\0", capture_output=True, text=True,
                           timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode not in (0, 1):          # 128 means "not a git work tree"
        return None
    return {x for x in p.stdout.split("\0") if x}


# --------------------------------------------------------------------------- exemptions

class Exemptions:
    def __init__(self, path):
        self.rules = []          # (glob, reason)
        self.used = set()
        self.path = path
        if not path:
            return
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                line = line.rstrip("\n")
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                if "\t" not in line:
                    raise SystemExit(f"{path}:{n}: an exemption needs a reason after a tab")
                glob, reason = line.split("\t", 1)
                glob, reason = glob.strip(), reason.strip()
                if not glob or not reason:
                    raise SystemExit(f"{path}:{n}: an exemption needs both a path and a reason")
                self.rules.append((glob, reason))

    def reason(self, rel):
        for glob, reason in self.rules:
            if fnmatch.fnmatch(rel, glob) or rel.startswith(glob.rstrip("/") + "/"):
                self.used.add(glob)
                return reason
        return None

    def stale(self):
        return [(g, r) for g, r in self.rules if g not in self.used]


# --------------------------------------------------------------------------- reading files

PDF_STRING = re.compile(rb"\((?:\\.|[^\\()])*\)", re.S)
PDF_BLOCK = re.compile(rb"BT\b(.*?)\bET\b", re.S)


def _is_content_stream(dictionary, chunk):
    """A page's drawing instructions, and not an image, a font or a colour profile.

    Three tests, because two are not enough. The stream's own dictionary must not call it an
    image or a font file; it must hold a text object; and it must be mostly printable ASCII.
    The third is the one that matters: a compressed image decompresses to bytes that contain
    `BT` and parentheses often enough, and without this test a photograph reads as prose in
    whatever language the reader is looking for.
    """
    if re.search(rb"/Subtype\s*/(?:Image|Type1C|CIDFontType0C|OpenType)|/FontFile", dictionary):
        return False
    if b"BT" not in chunk:
        return False
    sample = chunk[:20000]
    if not sample:
        return False
    printable = sum(32 <= b < 127 or b in (9, 10, 13) for b in sample)
    return printable / len(sample) > 0.90


def pdf_text(path):
    """The letters a PDF shows, read out of the text objects of its content streams.

    A PDF written by matplotlib or by pdfTeX keeps its letters as text and this reads them; a PDF
    rendered from SVG by cairo keeps them as outlines and this returns nothing, which the caller
    reports as a file it could not read rather than as a file that passed.
    """
    data = open(path, "rb").read()
    pieces = []
    for m in re.finditer(rb"stream\r?\n", data):
        start = m.end()
        end = data.find(b"endstream", start)
        if end < 0:
            continue
        chunk = data[start:end]
        try:
            chunk = zlib.decompress(chunk)
        except zlib.error:
            pass
        if not _is_content_stream(data[max(0, start - 1000):start], chunk):
            continue
        for block in PDF_BLOCK.findall(chunk):
            for s in PDF_STRING.findall(block):
                pieces.append(s[1:-1])
    text = b"".join(pieces)
    text = re.sub(rb"\\([()\\])", rb"\1", text)
    return text.decode("latin-1")


# A token that looks like the name or the path of a file. A name is not prose: the repository's
# own rule is that a name quoted inside a file is left as it was written when it names a file that
# exists under that name somewhere else, and is rewritten when it names a file of this folder. So
# these are pulled out of the line and judged separately rather than read as words.
PATHLIKE = re.compile(r"[A-Za-z0-9_./\\*-]*[A-Za-z0-9_*-]\.(?:py|md|csv|json|sh|cpp|hpp|h|tex|txt"
                      r"|patch|log|bin|so|pdf|svg|png|npz|cls|bst|yml|yaml|toml|cfg|ini)\b"
                      r"|[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+")


def resolves_under(root, filedir, token):
    """True when the token names something that exists in the scanned tree."""
    token = token.strip("`'\"(),;:")
    if "*" in token:
        token = os.path.dirname(token)
        if not token:
            return False
    for base in (filedir, root, os.path.join(root, "src")):
        cand = os.path.normpath(os.path.join(base, token))
        if cand.startswith(root) and os.path.exists(cand):
            return True
    return False


def read_text(path):
    """(lines, note). `lines` is None when the file carries no text this tool can read."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        text = pdf_text(path)
        letters = sum(c.isalpha() for c in text)
        if letters < 20:
            return None, "PDF whose letters are outlines and not text"
        return text.splitlines(), None
    if ext in BINARY_EXT:
        return None, "binary, letters not readable as text"
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        return None, f"could not be opened: {exc}"
    if b"\0" in raw:
        return None, "binary, letters not readable as text"
    try:
        return raw.decode("utf-8").splitlines(), None
    except UnicodeDecodeError:
        return None, "not valid UTF-8"


# The folder's own built article is skipped by name, and reported among the files not read. Its
# sources are swept line by line above it, so skipping it hides no text of ours; reading it found
# only the side stripe, whose words the PDF runs together («...notyetpublished·lastupdated...»),
# and flagged «stime» out of them, a false positive that failed the build of a folder whose
# article.pdf already existed (director, 2026-09-29T04:21:26Z). Its name is still checked.
BUILT_ARTICLE = "article.pdf"
BUILT_ARTICLE_WHY = ("the folder's own built article, skipped by name: its sources are swept; its side "
                     "stripe's run together words gave a false positive (director 2026-09-29T04:21:26Z)")


# --------------------------------------------------------------------------- the sweep

class Result:
    """What one sweep found, and what it did not look at."""

    def __init__(self):
        self.findings = []   # (rel, where, detail), any one of which fails the run
        self.unread = []     # (rel, why it could not be read as text)
        self.quoted = []     # (rel, line, an Italian name of a file not in this folder)
        self.scanned = 0
        self.ignored = 0     # paths git ignores, therefore not in the repository
        self.git_says = False


def sweep(root, exemptions):
    out = Result()
    myself = os.path.abspath(__file__)

    entries = []             # (full, rel, is_dir), in a fixed order
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(dirnames):
            full = os.path.join(dirpath, name)
            entries.append((full, os.path.relpath(full, root), True))
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            entries.append((full, os.path.relpath(full, root), False))

    ignored = git_ignored(root, [rel for _, rel, _ in entries])
    out.git_says = ignored is not None
    ignored = ignored or set()
    out.ignored = len(ignored)

    def looked_at(rel, full):
        return (rel not in ignored and os.path.abspath(full) != myself
                and exemptions.reason(rel) is None)

    for full, rel, _ in entries:
        if not looked_at(rel, full):
            continue
        name = os.path.basename(rel)
        words = [w.lower() for w in NAME_SPLIT.split(name) if w]
        hits = [w for w in words if w in LEXICON_SET or strip_accents(w) in LEXICON_SET]
        odd = non_ascii(name)
        if hits:
            out.findings.append((rel, "name", "Italian in the name: " + ", ".join(hits)))
        if odd:
            out.findings.append((rel, "name", "non ASCII letter in the name: " + " ".join(odd)))

    for full, rel, is_dir in entries:
        if is_dir or not looked_at(rel, full):
            continue
        if rel == BUILT_ARTICLE:
            out.unread.append((rel, BUILT_ARTICLE_WHY))
            continue
        lines, why = read_text(full)
        if lines is None:
            out.unread.append((rel, why))
            continue
        out.scanned += 1
        filedir = os.path.dirname(full)
        for n, line in enumerate(lines, 1):
            prose = BASE64.sub(lambda m: " " * len(m.group(0)), line)
            for m in PATHLIKE.finditer(prose):
                token = m.group(0)
                blank = " " * len(token)
                if not italian_words(token):
                    prose = prose.replace(token, blank)
                    continue
                prose = prose.replace(token, blank)
                if resolves_under(root, filedir, token):
                    out.findings.append((rel, f"line {n}",
                                         f"Italian in a name of this folder: {token}"))
                else:
                    out.quoted.append((rel, n, token))
            hits = italian_words(prose)
            # A word that is ordinary English as well as Italian does not convict a line on its
            # own. Of the 486 words in the lexicon exactly one is like this, «prove», and on
            # 2026-09-22T17:35Z it flagged three English sentences, among them «read before and
            # after to prove it». A sweep that fires on correct English is a sweep people learn
            # to wave through. A homograph still counts when the line carries another Italian
            # word, which is the case the lexicon is really for.
            if hits and all(h in HOMOGRAPHS for h in hits):
                hits = []
            hits += [m.group(0).lower() for m in APOSTROPHE_RE.finditer(prose)]
            hits += [m.group(0).lower() for m in ACCENTED_RE.finditer(prose)]
            if hits:
                seen = []
                for h in hits:
                    if h not in seen:
                        seen.append(h)
                out.findings.append((rel, f"line {n}",
                                     ", ".join(seen) + "  |  " + line.strip()[:120]))
        for n, what, quote in traces(lines):
            out.findings.append((rel, f"line {n}", f"{what}  |  {quote[:160]}"))

    for glob, reason in exemptions.rules:
        for what, rx in EXEMPT_REASON_RULES:
            if rx.search(reason):
                out.findings.append((exemptions.path, f"exemption {glob}",
                                     f"{what}: an exemption may only say that the file is "
                                     f"somebody else's, kept as published"))
                break
    return out


SELFTEST_FILES = {
    # one file per rule, each carrying exactly the shape the rule is for, and each written the way
    # the thing it imitates was really written: wrapped over two lines, so that a check that only
    # ever looks at one line at a time fails this test instead of passing it quietly.
    "a-translation-header.md":
        "> **Translation from Another Tongue.** This note was drafted elsewhere and is\n"
        "> published here in English alone.\n",
    "b-language-named.md":
        "The two pre-registrations the paper cites were written in Italian, the language\n"
        "they were discussed in.\n",
    "c-commit-as-home.md":
        "The originals have moved, they are not gone. Both are in commit\n"
        "`4c7fca95f73bc5054660c2b8b6e4d4409fe1482b` of this repository.\n",
    "d-rename-table.md":
        "| working tree | here |\n|---|---|\n| `something.py` | `other.py` |\n"
        "It was formerly called something else, and the folder was renamed from the old\n"
        "name on the day of the refresh.\n",
}
SELFTEST_EXEMPTIONS = (
    "keep-me.md\tthird party, kept as published: somebody else's file.\n"
    "bad-language.md\tours, but its subject is the Italian names, which cannot be written down "
    "without them.\n"
    "bad-rename.md\tours: it is the table the folder is renamed by.\n"
)


def selftest():
    """Build a folder carrying one of each trace and fail unless every rule fires on it."""
    import tempfile
    with tempfile.TemporaryDirectory(prefix="english_only-selftest-") as d:
        for name, body in SELFTEST_FILES.items():
            with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                fh.write(body)
        for name in ("keep-me.md", "bad-language.md", "bad-rename.md"):
            with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                fh.write("nothing to see here\n")
        exempt = os.path.join(d, "exempt.txt")
        with open(exempt, "w", encoding="utf-8") as fh:
            fh.write(SELFTEST_EXEMPTIONS)
        r = sweep(d, Exemptions(exempt))

    want = [what for what, _ in TRACE_RULES] + [what for what, _ in EXEMPT_REASON_RULES]
    got = [detail.split("  |  ")[0].split(":")[0] for _, _, detail in r.findings]
    missed = [w for w in want if not any(w in g for g in got)]
    print(f"english_only --selftest: {len(r.findings)} finding(s) on the fixture")
    for rel, where, detail in r.findings:
        print(f"  {os.path.basename(str(rel))}: {where}: {detail[:110]}")
    if missed:
        print("\nFAIL: these rules did not fire on a fixture built for them:")
        for w in missed:
            print(f"  {w}")
        return 1
    print(f"\nOK: all {len(want)} rules fired on the fixture built for them")
    return 0


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    # The folder this sweep is for is the published one: research/00001, which is where
    # the rule has to hold for a reader. PAPER_PUBLIC moves it, and any folder can be
    # given as the argument, this one included.
    default_root = os.environ.get("PAPER_PUBLIC",
                                  "/data/vesuviuschallenge/research/00001")
    ap = argparse.ArgumentParser(description="report anything under a folder that is not English")
    ap.add_argument("root", nargs="?", default=default_root)
    ap.add_argument("--exempt", default=os.path.join(here, "english_only_exempt.txt"),
                    help="file of <glob><tab><reason> exemptions")
    ap.add_argument("--no-exempt", action="store_true", help="run with no exemptions at all")
    ap.add_argument("--quiet", action="store_true", help="print the counts and the findings only")
    ap.add_argument("--selftest", action="store_true",
                    help="run every rule against a fixture built to trip it")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"not a folder: {root}", file=sys.stderr)
        return 2
    path = None if args.no_exempt else (args.exempt if os.path.exists(args.exempt) else None)
    if not args.no_exempt and path is None and args.exempt:
        print(f"no exemption file at {args.exempt}, running with none")
    exemptions = Exemptions(path)

    r = sweep(root, exemptions)

    print(f"english_only: {root}")
    print(f"  scanned {r.scanned} files as text, {len(exemptions.rules)} exemptions"
          f" from {path or 'none'}")
    if r.git_says:
        print(f"  skipped {r.ignored} paths git ignores: not in the repository, not swept")
    else:
        print("  git could not say what is ignored here, so nothing was skipped on that ground")
    if not args.quiet:
        for glob, reason in exemptions.rules:
            mark = "used" if glob in exemptions.used else "MATCHED NOTHING"
            print(f"  exempt [{mark}] {glob}: {reason}")
        for rel, why in r.unread:
            print(f"  not read as text: {rel}: {why}")
    if r.quoted:
        names = sorted({t for _, _, t in r.quoted})
        print(f"\n  {len(r.quoted)} quotation(s) of {len(names)} Italian name(s) of files that are "
              f"not in this folder, kept as written because they name a file that exists "
              f"elsewhere under that name:")
        for name in names:
            where = [f"{rel}:{n}" for rel, n, t in r.quoted if t == name]
            print(f"    {name}  ({len(where)}x, first at {where[0]})")
    stale = exemptions.stale()
    if stale:
        print(f"\n  warning: {len(stale)} exemption(s) matched nothing and may be stale")
    if r.findings:
        print(f"\n{len(r.findings)} finding(s):")
        for rel, where, detail in r.findings:
            print(f"  {rel}: {where}: {detail}")
        print(f"\nFAIL: {len(r.findings)} thing(s) under {root} are not English")
        return 1
    print("\nOK: names and text under this folder are English")
    return 0


if __name__ == "__main__":
    sys.exit(main())
