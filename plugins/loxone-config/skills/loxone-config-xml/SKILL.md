---
name: loxone-config-xml
description: >-
  A toolkit for reading and safely editing a Loxone Config project file — the .Loxone file
  (export/backup) a Miniserver produces, even when it's just called "my config" rather than "XML".
  It resolves the whole block-and-wire graph and makes careful edits without corrupting the file,
  so you can understand and change your Loxone logic from the config itself: tracing how something
  is wired or what feeds a control (e.g. which blocks feed the kitchen light), working out why an
  automation (blinds, shading, lights, heating) does or doesn't fire, searching or listing
  blocks/pages/types, bulk-renaming or bulk-editing titles and parameters across many blocks (e.g.
  all the blinds at once), moving blocks or tidying page layout, and cross-checking against a live
  Miniserver. It's the quick answer to "what does this actually do?", with the full written
  writeup left to its companion skill, loxone-documentation. It's specific to Loxone .Loxone files
  — not connectivity or hardware questions, and not KNX or generic XML.
---

# Loxone Config XML (.Loxone) — reading and writing

Base skill for working with Loxone Config project files. Higher-level skills (documentation, auto-layout, …) build on top of this one.

## Scope: this skill is the file mechanic, not the tour guide

This skill's job is the *mechanics* — parse the file, resolve the block/wire graph, make safe edits, bridge UUIDs to MCP. It gives you the raw truth of how things are wired.

Turning that into a **narrated explanation of what the automation does** is a different job that belongs to the **loxone-documentation** skill, which is built for exactly this and has three depth levels (1: plain-language behavior → 2: non-default settings → 3: rebuild-level wiring). Keep the two separated so answers stay at the right altitude and don't bury the user in detail they didn't ask for.

So when the user asks something like *"what does this do / explain the shading / how does the kitchen light work"*:

- Answer at **Level 1 first**: two to four plain sentences on the behavior, in the user's language. That is almost always what they actually wanted. Resist the urge to dump every block and pin — an exhaustive trace reads as noise when someone just asked "what does it do."
- Then **offer to go deeper** and name where the depth lives: e.g. *"If you want the full block-by-block wiring or a written spec you could rebuild from, that's the loxone-documentation skill — say the word."* If that skill is available, use it for the deep dive rather than free-handing a long trace here.
- Only when the user has clearly asked for the wiring/rebuild detail (e.g. "walk me through how it's wired") do you produce the full trace. If the documentation skill is available, run the deep dive through it. If it isn't, go ahead and trace it here — you have the parser and the graph; just keep it structured (blocks → their wires → the intent) rather than an undifferentiated pin dump.

The parser commands below are how you find the Level-1 answer quickly; they are not a mandate to report everything they print.

## File format

- XML, **UTF-8 with BOM, CRLF** line endings — preserve both when writing.
- Single root `<ControlList Version="272" NextObj="..." ...>` (verified on Loxone Config 17.x).
- The main file is usually accompanied by `.backup` files and a `*-Backups` folder with history.

## Anatomy

```xml
<ControlList Version="272" ...>
  <C Type="Document" ...>            <!-- address, GPS, NTP, currency, project language -->
    <C Type="Page" Title="...">      <!-- one drawing sheet -->
      <C Type="LightController2" U="uuid" Title="..."
         Px="14208" Py="576" Px2="16896" Py2="2616">  <!-- canvas bbox -->
        <Co K="I1" U="pin-uuid" Nc="2" [Inv="true"]>  <!-- pin (connector) -->
          <In Input="uuid-of-SOURCE-pin"/>            <!-- wire -->
```

Key facts (verified):

- **Blocks** = `<C Type=... U=...>`. Type determines function (`And`, `LightController2`, `AutoJalousie`, `HeatIRoomController2`, …). Physical devices (`TreeSensor`, `DaliActor`, `LoxAIRactor`, …) live outside pages, in the periphery tree (page=None).
- **Pins** = `<Co K="I1|I2|Q|AQ1|…">`, each with its own UUID. `Inv="true"` = inverted input, `Nc` = number of connected wires.
- **Wires** = `<In Input="…">` stored **on the destination side**; `Input` references the UUID of the source pin (occasionally a block UUID directly). The whole graph resolves 100 %.
- **InputRef / OutputRef** = on-page proxy for a block located elsewhere; the `Ref` attribute points to the real block's UUID. All cross-page and device links go through these.
- **Block positions**: `Px, Py, Px2, Py2` (canvas bbox). **Wire geometry is not stored** — Loxone Config auto-routes lines from block positions. Layout can therefore be changed purely by rewriting coordinates; wire crossings can only be influenced by placement.
- `Type="Place"` = rooms, `Type="Category"` = categories, `Type="Mode"` = Operating Modes, `Type="Memory"` = memory flags.
- Block titles often carry the author's intent description — a valuable source during analysis.
- Attribute values may span multiple lines; `<` and `>` inside values are entity-escaped by Loxone.
- Blocks cross-reference other objects in plain attributes too (`Ref`, `SpStates`, `uuidSeqenceIx`, …) — another reason element deletion is risky. **Not every relationship is a wire:** group membership (which blinds belong to a `CentralShade`, which lights to a `CentralLight`) lives in the parent's `rec`/`linkC` attribute as a UUID list, with no `<In>` wire — so tracing IN/OUT links alone will miss it. Some attributes are also behaviour-defining rather than cosmetic (e.g. `Sun="true"` marks a slat-tracking blind). When analysing or documenting logic, read the block's attributes with `show`, don't rely on wires alone.
- Some `<In>` wires carry `FLG="1|2"` — meaning not yet identified; preserve as-is.

## Loxone MCP (optional)

The skill works fully offline over the XML. If a Loxone MCP server is connected, use it for live cross-checking — **the block UUID in the XML == the runtime control UUID == the UUID in the MCP** (verified). Subcontrols use `<parent-uuid>/<slot>` (e.g. `/AI1`).

Division of roles: XML = static truth about wiring and parameters (MCP cannot see logic between blocks). MCP = live state and control (`control_find` name→UUID, `control_describe` verbs+states, `control_state` values+history, `control_command`). Take structure from XML, verify behavior via MCP, join them via UUID.

If no MCP is connected and live verification would help, suggest connecting one; if the user agrees, guide them using `references/mcp-setup.md`.

## Parser and editor

`scripts/loxone_graph.py` — tested, don't rewrite it:

```bash
# read
python3 scripts/loxone_graph.py <config.Loxone> pages     # sheets + block counts
python3 scripts/loxone_graph.py <config.Loxone> stats     # type counts, wire count
python3 scripts/loxone_graph.py <config.Loxone> page "Living room"
python3 scripts/loxone_graph.py <config.Loxone> block "Ceiling light"  # search TITLE substring / UUID prefix + IN/OUT links
python3 scripts/loxone_graph.py <config.Loxone> type AutoJalousie      # ALL blocks of one Type (exact) — use this to enumerate a block kind
python3 scripts/loxone_graph.py <config.Loxone> show <uuid>            # all attributes + child elements
python3 scripts/loxone_graph.py <config.Loxone> json      # full wire dump

# write (surgical text edits; preserves BOM/CRLF/formatting, escapes values, validates by re-parse)
python3 scripts/loxone_graph.py <copy.Loxone> set-attr <uuid> <attr> <value>
python3 scripts/loxone_graph.py <copy.Loxone> set-attr-batch edits.tsv  # many edits in ONE validate/save
python3 scripts/loxone_graph.py <copy.Loxone> move-block <uuid> <Px> <Py>   # keeps block size
```

`block` vs `type`: `block` matches on the **title** (substring) or a UUID prefix, *not* on the Type — so `block "AutoJalousie"` finds nothing. To enumerate every block of a kind (all blinds, all light controllers, …), use `type <TypeName>` with an exact type name from `stats`.

`set-attr-batch` takes a TSV file (one `uuid<TAB>attr<TAB>value` per line; blank and `#`-comment lines ignored; on duplicate uuid+attr lines the last value wins) and applies them all **atomically** in a single load/validate/save — on any error (unknown UUID, malformed result) nothing is written. The right tool for a bulk rename or a mass parameter change, instead of spawning `set-attr` once per block. Note: `block` prints at most 20 matches (it says so when it truncates); use `type` to enumerate a whole block kind.

**Following a link to the real block:** `InputRef`/`OutputRef` are proxies — `show` prints them as `InputRef->[<Type> '<Title>' @ <page>]`, and the proxy's `Ref` attribute holds the real block's UUID. When you need the real source's own inputs/parameters (e.g. is that sensor analog? is the actor DALI/dimmable?), run `show <that-uuid>` to hop to it.

Tip: copy the config to a temp location first (faster, zero risk to the original).

## Writing rules

These apply only when you are **writing**. A pure read/trace/explain task changes nothing, so it needs no backup and no copy — just don't pass the original to a write command. (Making a scratch copy to work on is still fine and cheap.)

1. **Never write to the original.** Work on a copy; leave the original and its backups alone. The user loads the modified copy in Loxone Config and deploys it to the Miniserver — that is also the validation step.
2. **Back up before any write session.** This controls a critical system (heating, security, water). Before the first edit, create a timestamped backup of the source config yourself (e.g. `<name>.Loxone.bak-YYYYMMDD-HHMMSS`) — and don't proceed until one exists. Prefer a location the user confirms; if you can't ask (non-interactive/agent run), put it next to the source with that timestamped name and tell the user where it is. The point is a recoverable copy exists, not where it lives.
3. **Do not serialize through an XML library.** ElementTree/lxml reorder attributes, drop the BOM and reformat → huge diff and real risk. Make targeted text edits (as `set-attr`/`set-attr-batch` do) and validate well-formedness by re-parsing after every change.
4. **Low risk:** changing values of existing attributes — positions (`Px/Py/Px2/Py2`), `Title`, block parameters.
5. **Higher risk (unverified):** adding/removing elements (blocks, wires). UUIDs of new objects and the `NextObj` counter in `<ControlList>` are managed by Loxone Config, and blocks cross-reference each other in attributes — study both before the first attempt, and test on a minimal experiment.
6. After every edit: re-parse with the script (`stats` must pass) + diff against the pre-edit copy.
7. **Verify with the parser, not shell text tools.** Configs are commonly non-English (Czech, German, …) and UTF-8-encoded; `grep`/`wc` on accented titles (Czech `Žaluzie`, `Roleta levá`; German `Außenjalousie`, `Wohnzimmer-Rollläden`) give misleading counts and can make a correct edit look reverted. Read titles back through the script (`type`/`show`/`json`) — that is the source of truth for whether an edit landed.
