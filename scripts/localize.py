#!/usr/bin/env python3
"""Build the Spanish (es-419) and Portuguese (pt-BR) copies of the site from the English pages.

English is the source. Each text unit of an English page is looked up in
site/i18n/<lang>.json. A unit is a block of text with its inline tags, for
example a paragraph. In the key, each inline tag becomes <1>...</1>, each
number becomes {n1}, and the content of a code span, a path link or a number
slot stays outside the key. A translation keeps the same tags and numbers, and
may move them. A unit with no translation stops the build.

    python3 scripts/localize.py              # expand the shared header, write the copies
    python3 scripts/localize.py --check      # exit 1 if a file is stale or a text is missing
    python3 scripts/localize.py --missing es-419   # print the keys with no translation
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import site_chrome as chrome  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
I18N = SITE / "i18n"

VOID = {"meta", "link", "br", "img", "input", "hr", "area", "base", "col", "source", "wbr"}
INLINE = {"a", "b", "strong", "em", "code", "span", "small", "br", "abbr", "i", "u", "sup", "sub", "text", "tspan", "cite"}
ASSET_EXT = {".css", ".js", ".png", ".ico", ".json", ".pdf", ".jpg", ".webp", ".svg"}
ATTRS = ("aria-label", "alt", "data-demo", "data-prod", "data-note-demo", "data-note-prod", "placeholder")
META_NAMES = {"description", "og:title", "og:description"}

TOKEN = re.compile(r"<!--.*?-->|<!doctype[^>]*>|<(script|style)\b[^>]*>.*?</\1>|<[^>]+>|[^<]+", re.S | re.I)
NUM = re.compile(r"&#?\w+;|\d+(?:[.,]\d+)*%?")
LETTERS = re.compile(r"[^\W\d_]{2,}")
PATHLIKE = re.compile(r"^[\w./#:-]+$")
ALT_BLOCK = re.compile(r"<!--site:alt-->.*?<!--/site:alt-->\s*", re.S)


# --- tree -------------------------------------------------------------------

class Node:
    def __init__(self, tag: str, start: str):
        self.tag, self.start, self.end, self.kids = tag, start, "", []

    def attr(self, name: str) -> str | None:
        m = re.search(r'\s' + re.escape(name) + r'="([^"]*)"', self.start)
        return m.group(1) if m else None

    def html(self) -> str:
        return self.start + "".join(k.html() if isinstance(k, Node) else k[1] for k in self.kids) + self.end


def parse(text: str) -> Node:
    root = Node("#root", "")
    stack = [root]
    for m in TOKEN.finditer(text):
        tok = m.group(0)
        if tok.startswith("<!--") or tok.lower().startswith("<!doctype") or m.group(1):
            stack[-1].kids.append(("r", tok))
        elif tok.startswith("</"):
            name = re.match(r"</\s*([\w:-]+)", tok).group(1).lower()
            for i in range(len(stack) - 1, 0, -1):
                if stack[i].tag == name:
                    stack[i].end = tok
                    del stack[i:]
                    break
        elif tok.startswith("<"):
            name = re.match(r"<\s*([\w:-]+)", tok).group(1).lower()
            node = Node(name, tok)
            stack[-1].kids.append(node)
            if not (tok.endswith("/>") or name in VOID):
                stack.append(node)
        else:
            stack[-1].kids.append(("t", tok))
    return root


# --- units ------------------------------------------------------------------

def is_opaque(n: Node) -> bool:
    if n.tag in {"code", "br"} or (n.attr("lang") is not None and n.tag != "html"):
        return True
    cls = n.attr("class") or ""
    if "src" in cls.split() or any(n.attr(a) is not None for a in ("data-num", "data-num-round", "data-num-type", "data-num-den")):
        return True
    if n.tag == "a" and n.kids:
        inner = re.sub(r"<[^>]+>", "", n.html()[len(n.start):-len(n.end) or None]).strip()
        return bool(inner) and bool(PATHLIKE.match(inner)) and ("/" in inner or "." in inner)
    return False


def inline_only(n: Node) -> bool:
    return all(not isinstance(k, Node) or (k.tag in INLINE and inline_only(k)) for k in n.kids)


def skipped(n: Node) -> bool:
    cls = (n.attr("class") or "").split()
    return (
        n.tag in {"script", "style", "pre", "code"}
        or (n.attr("lang") is not None and n.tag != "html")
        or n.attr("data-t") == "skip"
        or "src" in cls
        or any(n.attr(a) is not None for a in ("data-num", "data-num-round", "data-num-type", "data-num-den"))
    )


class Store:
    def __init__(self):
        self.tags: dict[int, tuple[str, str, str | None]] = {}
        self.nums: dict[int, str] = {}

    def num(self, token: str) -> str:
        k = len(self.nums) + 1
        self.nums[k] = token
        return "{n%d}" % k


def abstract(kids: list, st: Store) -> str:
    out = []
    for k in kids:
        if isinstance(k, tuple):
            if k[0] == "t":
                out.append(NUM.sub(lambda m: m.group(0) if m.group(0).startswith("&") else st.num(m.group(0)), k[1]))
            continue
        i = len(st.tags) + 1
        if is_opaque(k):
            inner = "".join(x.html() if isinstance(x, Node) else x[1] for x in k.kids)
            st.tags[i] = (k.start, k.end, inner)
            out.append(f"<{i}/>" if k.tag == "br" else f"<{i}></{i}>")
        else:
            st.tags[i] = (k.start, k.end, None)
            out.append(f"<{i}>" + abstract(k.kids, st) + f"</{i}>")
    return "".join(out)


def norm(key: str) -> str:
    return re.sub(r"\s+", " ", key).strip()


def has_letters(key: str) -> bool:
    return bool(LETTERS.search(re.sub(r"<[^>]+>|\{n\d+\}|&\w+;", "", key)))


def locnum(token: str, lang: str) -> str:
    # A version such as 5.3 keeps its point. A decimal with a percent sign or more digits changes.
    if lang == "pt-br" and ("." in token or "," in token) and not re.fullmatch(r"\d\.\d", token):
        return token.translate(str.maketrans(",.", ".,"))
    return token


class Translator:
    def __init__(self, lang: str, table: dict[str, str]):
        self.lang, self.table = lang, table
        self.keep = set(table.get("_keep", []))
        self.missing: set[str] = set()
        self.errors: list[str] = []

    def lookup(self, key: str) -> str | None:
        if key in self.keep:
            return None
        if key in self.table:
            return self.table[key]
        self.missing.add(key)
        return None

    def restore(self, tr: str, st: Store, key: str) -> str | None:
        tags = sorted(re.findall(r"</?(\d+)", re.sub(r"<(\d+)></\1>", r"<\1/>", tr)))
        want = sorted(re.findall(r"</?(\d+)", re.sub(r"<(\d+)></\1>", r"<\1/>", key)))
        if tags != want or sorted(re.findall(r"\{n\d+\}", tr)) != sorted(re.findall(r"\{n\d+\}", key)):
            self.errors.append(f"tags or numbers differ: {key!r} -> {tr!r}")
            return None

        def opaque(m: re.Match) -> str:
            s, e, inner = st.tags[int(m.group(1))]
            return s + (inner or "") + e

        out = re.sub(r"<(\d+)></\1>", opaque, tr)
        out = re.sub(r"<(\d+)/>", lambda m: st.tags[int(m.group(1))][0], out)
        out = re.sub(r"<(\d+)>", lambda m: st.tags[int(m.group(1))][0], out)
        out = re.sub(r"</(\d+)>", lambda m: st.tags[int(m.group(1))][1], out)
        return re.sub(r"\{n(\d+)\}", lambda m: locnum(st.nums[int(m.group(1))], self.lang), out)

    def unit(self, kids: list) -> str | None:
        st = Store()
        raw = abstract(kids, st)
        key = norm(raw)
        if not has_letters(key):
            return None
        tr = self.lookup(key)
        if tr is None:
            return None
        res = self.restore(tr, st, key)
        if res is None:
            return None
        lead = re.match(r"\s*", "".join(k.html() if isinstance(k, Node) else k[1] for k in kids)).group(0)
        trail = re.search(r"\s*$", "".join(k.html() if isinstance(k, Node) else k[1] for k in kids)).group(0)
        return lead + res + trail

    def attr_value(self, value: str) -> str:
        st = Store()
        key = norm(NUM.sub(lambda m: m.group(0) if m.group(0).startswith("&") else st.num(m.group(0)), value))
        if not has_letters(key):
            return value
        tr = self.lookup(key)
        if tr is None:
            return value
        res = self.restore(tr, st, key)
        return value if res is None else res

    def start_tag(self, n: Node) -> str:
        s = n.start
        for a in ATTRS:
            s = re.sub(r'(\s' + re.escape(a) + r'=")([^"]*)(")', lambda m: m.group(1) + self.attr_value(m.group(2)) + m.group(3), s)
        if n.tag == "meta":
            name = n.attr("name") or n.attr("property")
            if name in META_NAMES:
                s = re.sub(r'(\scontent=")([^"]*)(")', lambda m: m.group(1) + self.attr_value(m.group(2)) + m.group(3), s)
        return s

    def walk(self, n: Node) -> None:
        if n.tag != "#root":
            if skipped(n):
                return
            n.start = self.start_tag(n)
            if n.attr("data-t") == "keep":
                return
            if inline_only(n) and n.tag not in {"html", "body", "head"}:
                res = self.unit(n.kids)
                if res is not None:
                    n.kids = [("r", res)]
                return
        for i, k in enumerate(n.kids):
            if isinstance(k, Node):
                self.walk(k)
            elif k[0] == "t":
                key = norm(k[1])
                if has_letters(key):
                    res = self.unit([k])
                    if res is not None:
                        n.kids[i] = ("r", res)


# --- fit of labels in SVG nodes ---------------------------------------------

def descendants(n: Node):
    for k in n.kids:
        if isinstance(k, Node):
            yield k
            yield from descendants(k)


def fit_svg(root: Node) -> None:
    """Squeeze a node label that the translation made wider than its node.

    The width is an estimate. On an interactive page, the script of the page
    measures again and replaces it. English never needs this.
    """
    import html as htmllib

    for g in descendants(root):
        if g.tag != "g" or "node" not in (g.attr("class") or "").split():
            continue
        kids = list(descendants(g))
        box = next((k for k in kids if k.tag == "rect" and "box" in (k.attr("class") or "").split()), None)
        if box is None or not box.attr("width"):
            continue
        w = float(box.attr("width"))
        chip = next((k for k in kids if k.tag == "circle" and "chip" in (k.attr("class") or "").split()), None)
        chip_left = float(chip.attr("cx")) - float(chip.attr("r")) if chip else w
        for t in kids:
            cls = (t.attr("class") or "").split()
            if t.tag != "text" or not {"t1", "t2", "t3"} & set(cls):
                continue
            text = htmllib.unescape(re.sub(r"<[^>]+>", "", "".join(k.html() if isinstance(k, Node) else k[1] for k in t.kids)))
            m = re.search(r"font-size:\s*([\d.]+)px", t.attr("style") or "")
            size = float(m.group(1)) if m else (15.0 if "t1" in cls else 12.0)
            bold = "t1" in cls or "t2" in cls
            avail = (chip_left - 4 if "t1" in cls else w - 8) - float(t.attr("x") or 0)
            if len(text) * size * (0.53 if bold else 0.50) > avail and "textLength=" not in t.start:
                t.start = t.start[:-1] + f' textLength="{avail:.1f}" lengthAdjust="spacingAndGlyphs">'


# --- pages ------------------------------------------------------------------

def sources() -> list[str]:
    pages = []
    for p in sorted(SITE.rglob("*.html")):
        rel = p.relative_to(SITE).as_posix()
        if rel.split("/")[0] in chrome.LANG_DIRS or rel in {"404.html"} or rel.startswith("i18n/"):
            continue
        pages.append(rel)
    pages += ["diagrams/architecture.svg", "diagrams/architecture-light.svg"]
    return pages


def resolve(page: str, value: str) -> str:
    path = value.split("#")[0].split("?")[0]
    base = posixpath.dirname(page)
    target = posixpath.normpath(posixpath.join(base, path)) if path else page
    if not posixpath.splitext(target)[1]:
        target = posixpath.join(target, "index.html") if target != "." else "index.html"
    return target


def finalize(html: str, page: str, lang: str, mirrored: set[str]) -> str:
    out_page = page if lang == "en" else f"{lang}/{page}"
    out_dir = posixpath.dirname(out_page) or "."

    def fix(m: re.Match) -> str:
        attr, val = m.group(1), m.group(2)
        if re.match(r"(?:[a-z][a-z0-9+.-]*:|//|#)", val, re.I) or not val:
            return m.group(0)
        target = resolve(page, val)
        if target in mirrored or posixpath.splitext(target)[1] not in ASSET_EXT:
            return m.group(0)
        return f'{attr}="{posixpath.relpath(target, out_dir)}' + (val[len(val.split("#")[0].split("?")[0]):]) + '"'

    if lang != "en":
        html = re.sub(r'\b(href|src)="([^"]*)"', fix, html)
    # Language links and the current language.
    for d, _label, _name, htmllang in chrome.LANGS:
        dest = page if d == "en" else f"{d}/{page}"
        href = posixpath.relpath(dest, out_dir)
        cur = ' aria-current="true"' if d == lang else ""
        html = re.sub(
            r'(<a [^>]*data-lang="' + re.escape(d) + r'"[^>]*?)(?: aria-current="true")?( href=")[^"]*(")',
            lambda m: m.group(1) + cur + m.group(2) + href + m.group(3),
            html,
        )
    html = re.sub(r'(<html lang=")[^"]*(")', lambda m: m.group(1) + dict((d, h) for d, _l, _n, h in chrome.LANGS)[lang] + m.group(2), html, count=1)
    if "</head>" in html:
        alts = "".join(
            f'<link rel="alternate" hreflang="{h}" data-lang="{d}" href="{posixpath.relpath(page if d == "en" else f"{d}/{page}", out_dir)}">'
            for d, _l, _n, h in chrome.LANGS
        ) + f'<script src="{posixpath.relpath("lang.js", out_dir)}"></script>'
        html = ALT_BLOCK.sub("", html)
        html = html.replace("</head>", f"<!--site:alt-->{alts}<!--/site:alt-->\n</head>", 1)
    return html


def en_page(html: str, page: str) -> str:
    """The English page with its shared header, footer and language links."""
    return finalize(chrome.expand(html, page), page, "en", set(sources()))


def load_table(lang: str) -> dict:
    p = I18N / f"{lang}.json"
    return json.loads(p.read_text()) if p.exists() else {}


def build(write: bool = True) -> tuple[dict[Path, str], dict[str, Translator]]:
    pages = sources()
    mirrored = set(pages)
    outputs: dict[Path, str] = {}
    tr = {d: Translator(d, load_table(d)) for d in chrome.LANG_DIRS}
    for page in pages:
        src = (SITE / page).read_text()
        if page.endswith(".html"):
            src = chrome.expand(src, page)
        base = finalize(src, page, "en", mirrored) if page.endswith(".html") else src
        outputs[SITE / page] = base
        for d in chrome.LANG_DIRS:
            root = parse(base)
            tr[d].walk(root)
            fit_svg(root)
            text = root.html()
            if page.endswith(".html"):
                text = finalize(text, page, d, mirrored)
            outputs[SITE / d / page] = text
    # Fill the number slots of each language (format and type names).
    import site_numbers as sn
    numbers = json.loads(sn.OUT.read_text())["numbers"] if sn.OUT.exists() else sn.build()["numbers"]
    for path in list(outputs):
        if path.suffix == ".html":
            lang = path.relative_to(SITE).parts[0]
            lang = lang if lang in chrome.LANG_DIRS else "en"
            outputs[path] = sn.SLOT.sub(
                lambda m: m.group(1) + sn.slot_text(numbers, m.group(3), m.group(4), lang) + m.group(6), outputs[path]
            )
    return outputs, tr


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--missing", metavar="LANG")
    args = parser.parse_args()
    outputs, tr = build()
    if args.missing:
        print(json.dumps({k: "" for k in sorted(tr[args.missing].missing)}, ensure_ascii=False, indent=1))
        return 0
    problems = []
    for d, t in tr.items():
        problems += [f"{d}: missing {len(t.missing)} text(s)"] if t.missing else []
        problems += [f"{d}: {e}" for e in t.errors]
    if args.check:
        stale = [p for p, text in outputs.items() if not p.exists() or p.read_text() != text]
        for p in stale:
            problems.append(f"stale: {p.relative_to(ROOT)}")
        for p in problems:
            print(p)
        if not problems:
            print("The language copies are current.")
        return 1 if problems else 0
    for p in problems:
        print(p)
    if any("missing" in p or "differ" in p for p in problems):
        print("Write the missing translations in site/i18n/*.json, then run again. Files not written.")
        return 1
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    print(f"wrote {len(outputs)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
