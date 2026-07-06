#!/usr/bin/env python3
"""Read and write Loxone Config project files (.Loxone XML) as a block/wire graph.

READ:
  loxone_graph.py <config.Loxone> pages
  loxone_graph.py <config.Loxone> stats
  loxone_graph.py <config.Loxone> page "Living room"
  loxone_graph.py <config.Loxone> block "Ceiling light"    # title substring or UUID prefix
  loxone_graph.py <config.Loxone> type AutoJalousie        # ALL blocks of one Type (exact)
  loxone_graph.py <config.Loxone> show <uuid>              # all attributes + child elements
  loxone_graph.py <config.Loxone> json > graph.json        # full wire dump

WRITE (surgical text edits — preserve BOM, CRLF, formatting; work on a copy!):
  loxone_graph.py <copy.Loxone> set-attr <uuid> <attr> <value>
  loxone_graph.py <copy.Loxone> set-attr-batch edits.tsv  # many edits, one validate/save
                                                          # each line: uuid<TAB>attr<TAB>value
  loxone_graph.py <copy.Loxone> move-block <uuid> <newPx> <newPy>   # keeps block size

XML anatomy (verified on ControlList Version=272, Loxone Config 17.x):
  <C Type="..." U="uuid" Title="..." Px Py Px2 Py2>   block/device/page/place; Px..Py2 = canvas bbox
      <Co K="I1|Q|AQ1|..." U="pin-uuid" [Inv="true"] [Nc=n]>   pin (connector)
          <In Input="uuid-of-SOURCE-pin-or-block"/>            wire (stored on the DESTINATION side)
  Pages: Type="Page". Rooms: Type="Place". Categories: Type="Category".
  InputRef/OutputRef: on-page proxy for a block elsewhere; Ref="uuid of the real block".
  No wire waypoints are stored — Loxone Config auto-routes lines from block positions.
  Block U == runtime control UUID (== UUID seen by a Loxone MCP server).
  Notes: attribute values may span multiple lines; < > are entity-escaped by Loxone.
  Some <In> wires carry FLG="1|2" — meaning not yet identified; preserve as-is.
"""
import sys, json, re
import xml.etree.ElementTree as ET

STRUCTURAL = {"Document", "Page", "Place", "Category", "LoxCaption", "CategoryCaption",
              "PlaceCaption", "RightGroup", "User", "Permission", "CalendarEntry"}

class Graph:
    def __init__(self, path):
        self.root = ET.parse(path).getroot()
        self.parent = {}
        for p in self.root.iter():
            for ch in p:
                self.parent[ch] = p
        self.blocks = {}      # U -> element (any <C> with Type)
        self.pin_owner = {}   # pin U -> (block_el, pin K)
        for c in self.root.iter("C"):
            u = c.get("U")
            if c.get("Type") and u:
                self.blocks[u] = c
            for co in c.findall("Co"):
                if co.get("U"):
                    self.pin_owner[co.get("U")] = (c, co.get("K"))
        # wires: (src_block, src_pin, dst_block, dst_pin, inverted)
        self.wires = []
        self.in_by_dst = {}
        self.out_by_src = {}
        for c in self.root.iter("C"):
            for co in c.findall("Co"):
                for i in co.findall("In"):
                    src = i.get("Input")
                    if src in self.pin_owner:
                        sblk, sk = self.pin_owner[src]
                    elif src in self.blocks:
                        sblk, sk = self.blocks[src], ""
                    else:
                        sblk, sk = None, src
                    w = (sblk, sk, c, co.get("K"), co.get("Inv") == "true")
                    self.wires.append(w)
                    self.in_by_dst.setdefault(c.get("U"), []).append(w)
                    if sblk is not None:
                        self.out_by_src.setdefault(sblk.get("U"), []).append(w)

    def page_of(self, el):
        a = el
        while a in self.parent:
            if a.tag == "C" and a.get("Type") == "Page":
                return a.get("Title")
            a = self.parent[a]
        return None

    def label(self, el):
        if el is None:
            return "???"
        t, title = el.get("Type"), el.get("Title") or ""
        ref = el.get("Ref")
        if t in ("InputRef", "OutputRef") and ref in self.blocks:
            real = self.blocks[ref]
            return f"{t}->[{real.get('Type')} '{real.get('Title')}' @ {self.page_of(real)}]"
        return f"{t} '{title}'"

    def find(self, q):
        ql = q.lower()
        return [c for u, c in self.blocks.items()
                if ql in (c.get("Title") or "").lower() or u.startswith(ql)]

    def show_block(self, c):
        u = c.get("U")
        print(f"{c.get('Type')} '{c.get('Title')}'  U={u}")
        print(f"  page={self.page_of(c)}  pos=({c.get('Px')},{c.get('Py')})-({c.get('Px2')},{c.get('Py2')})")
        if c.get("Ref"):
            print(f"  Ref -> {self.label(self.blocks.get(c.get('Ref')))}")
        for w in self.in_by_dst.get(u, []):
            sblk, sk, _, dk, inv = w
            print(f"  IN  {dk}{' (inv)' if inv else ''} <- {self.label(sblk)}.{sk} @ {self.page_of(sblk) if sblk is not None else '?'}")
        for w in self.out_by_src.get(u, []):
            _, sk, dblk, dk, inv = w
            print(f"  OUT {sk} -> {self.label(dblk)}.{dk}{' (inv)' if inv else ''} @ {self.page_of(dblk)}")

# ---------- write support: surgical edits on raw text ----------

BOM = "﻿"
# A complete opening <C ...> tag: quoted strings may contain '>' and newlines.
C_TAG = re.compile(r'<C\b(?:"[^"]*"|[^">])*>')

def _load_raw(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()   # keeps BOM and CRLF as-is

def _save_raw(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)

def _escape(value):
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))

def _find_block_tag(text, uuid):
    """Return (start, end) span of the opening <C ... U="uuid" ...> tag."""
    needle = f'U="{uuid}"'
    matches = [m for m in C_TAG.finditer(text) if needle in m.group(0)]
    if not matches:
        sys.exit(f'error: no <C> tag with U="{uuid}" found (use the full UUID)')
    if len(matches) > 1:
        sys.exit(f'error: UUID "{uuid}" is not unique ({len(matches)} matches)')
    return matches[0].span()

def _apply_to_text(text, uuid, updates):
    """Apply attribute updates to the <C U=uuid> tag in `text`; return new text."""
    s, e = _find_block_tag(text, uuid)
    tag = text[s:e]
    for attr, value in updates.items():
        value = _escape(value)
        pat = re.compile(r'\b%s="[^"]*"' % re.escape(attr))
        if pat.search(tag):
            tag = pat.sub(lambda m: f'{attr}="{value}"', tag, count=1)
        else:  # insert before closing '>' or '/>'
            closer = "/>" if tag.endswith("/>") else ">"
            tag = tag[: -len(closer)].rstrip() + f' {attr}="{value}"' + closer
    return text[:s] + tag + text[e:]

def _set_attrs(path, uuid, updates):
    _set_attrs_many(path, {uuid: updates})

def _set_attrs_many(path, edits):
    """Atomic multi-block edit: one load, all edits in memory, one validate, one save.
    If anything fails (unknown/non-unique UUID, malformed result), nothing is written."""
    text = _load_raw(path)
    for uuid, updates in edits.items():
        text = _apply_to_text(text, uuid, updates)
    ET.fromstring(text.lstrip(BOM))   # sanity: still well-formed XML
    _save_raw(path, text)
    for uuid, updates in edits.items():
        print(f"ok: {uuid}: " + ", ".join(f"{k}={v}" for k, v in updates.items()))

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    path, cmd = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]

    if cmd == "set-attr":
        if len(args) != 3:
            sys.exit("usage: set-attr <uuid> <attr> <value>")
        uuid, attr, value = args
        _set_attrs(path, uuid, {attr: value}); return
    if cmd == "set-attr-batch":
        # Bulk edits in ONE load/validate/save cycle — for renaming many blocks etc.
        # Reads TSV from a file (arg) or stdin ('-'): each line  uuid<TAB>attr<TAB>value
        # (blank lines and #-comments ignored). Re-parses once at the end.
        # Duplicate uuid+attr lines: the LAST value wins.
        src = sys.stdin if (not args or args[0] == "-") else open(args[0], encoding="utf-8")
        edits = {}   # uuid -> {attr: value}
        n = 0
        for raw in src:
            line = raw.rstrip("\n").rstrip("\r")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 3:
                sys.exit(f"error: expected 3 tab-separated fields, got {len(parts)}: {line!r}")
            u, attr, value = parts
            edits.setdefault(u, {})[attr] = value
            n += 1
        _set_attrs_many(path, edits)   # atomic: on any error nothing is written
        n_applied = sum(len(v) for v in edits.values())
        print(f"ok: applied {n_applied} edit(s) across {len(edits)} block(s)")
        return
    if cmd == "move-block":
        if len(args) != 3:
            sys.exit("usage: move-block <uuid> <newPx> <newPy>")
        uuid, npx, npy = args[0], int(args[1]), int(args[2])
        g = Graph(path)
        c = g.blocks.get(uuid)
        if c is None:
            sys.exit(f"error: unknown block UUID {uuid}")
        if not all(c.get(a) for a in ("Px", "Py", "Px2", "Py2")):
            sys.exit(f"error: block {uuid} ({c.get('Type')}) has no canvas position "
                     "(peripheral-tree items cannot be moved)")
        w = int(c.get("Px2")) - int(c.get("Px"))
        h = int(c.get("Py2")) - int(c.get("Py"))
        _set_attrs(path, uuid, {"Px": npx, "Py": npy, "Px2": npx + w, "Py2": npy + h})
        return

    g = Graph(path)
    arg = args[0] if args else ""
    if cmd == "pages":
        for c in g.root.iter("C"):
            if c.get("Type") == "Page":
                n = sum(1 for x in c.iter("C") if x.get("Type"))
                print(f"{n:4d}  {c.get('Title')}")
    elif cmd == "stats":
        from collections import Counter
        cnt = Counter(c.get("Type") for c in g.blocks.values())
        for k, v in cnt.most_common():
            print(f"{v:5d}  {k}")
        print(f"\nwires: {len(g.wires)}")
    elif cmd == "page":
        for c in g.root.iter("C"):
            if c.get("Type") == "Page" and arg.lower() in (c.get("Title") or "").lower():
                for b in c.iter("C"):
                    if b.get("Type") and b.get("Type") not in STRUCTURAL:
                        print("-" * 60)
                        g.show_block(b)
    elif cmd == "block":
        hits = g.find(arg)
        for c in hits[:20]:
            print("=" * 60)
            g.show_block(c)
        if not hits:
            print("no match")
        elif len(hits) > 20:
            print(f"\n(showing 20 of {len(hits)} matches — refine the query, "
                  "or use `type <TypeName>` to enumerate a block kind)")
    elif cmd == "type":
        # List every block of a given Type (exact, case-insensitive). `block` only
        # searches Title/UUID, so this is how you enumerate e.g. all AutoJalousie.
        want = arg.lower()
        hits = [c for c in g.blocks.values() if (c.get("Type") or "").lower() == want]
        for c in hits:
            print(f"{c.get('U')}  {c.get('Type')} '{c.get('Title')}'  @ {g.page_of(c)}")
        print(f"\n{len(hits)} block(s) of type {arg!r}"
              + ("" if hits else "  (run `stats` to see the available Type names)"))
    elif cmd == "show":
        c = g.blocks.get(arg)
        if c is None:
            found = g.find(arg)
            c = found[0] if found else None
        if c is None:
            print("no match"); return
        g.show_block(c)
        print("  attributes:")
        for k, v in sorted(c.attrib.items()):
            print(f"    {k} = {v}")
        kids = [ch.tag for ch in c if ch.tag != "Co"]
        if kids:
            from collections import Counter
            print("  child elements:", dict(Counter(kids)))
    elif cmd == "json":
        out = []
        for sblk, sk, dblk, dk, inv in g.wires:
            out.append({
                "src": sblk.get("U") if sblk is not None else None, "src_pin": sk,
                "src_type": sblk.get("Type") if sblk is not None else None,
                "src_title": sblk.get("Title") if sblk is not None else None,
                "src_page": g.page_of(sblk) if sblk is not None else None,
                "dst": dblk.get("U"), "dst_pin": dk, "dst_type": dblk.get("Type"),
                "dst_title": dblk.get("Title"), "dst_page": g.page_of(dblk), "inv": inv})
        json.dump({"wires": out}, sys.stdout, ensure_ascii=False, indent=1)
    else:
        print(__doc__); sys.exit(1)

if __name__ == "__main__":
    main()
