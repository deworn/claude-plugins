---
name: loxone-documentation
description: >-
  A methodology for turning a Loxone installation's .Loxone config into clear written
  documentation a person can actually use — in three layers: plain-language use cases, the
  non-default settings, and rebuild-level wiring detailed enough to recreate the system without
  the file. It documents consistently room by room and never invents values it can't confirm. It
  covers the written deliverables people ask for around a Loxone system, whether or not they call
  it "documentation": a handover document for a new owner or electrician, a room-by-room
  description of what the automations do, a plain-language writeup a family can follow, or a
  rebuild spec a colleague could recreate the system from without the original file, even when the
  installer left no docs. Where its companion skill loxone-config-xml just traces a single wire,
  searches blocks, or edits the file, this one is for producing the finished document. Built on
  loxone-config-xml. Not for connectivity, hardware advice, or general Loxone concepts.
---

# Documenting a Loxone installation

Extension of the **loxone-config-xml** skill — that one covers how to read a .Loxone file and how its UUIDs map to MCP. This skill covers what to document and how.

## Goal

The documentation must enable a **complete rebuild of the configuration without the config file** — or handing a clear build spec to a third party without giving them the file. Written in Markdown, in layers, from behavior down to wiring.

## Layers

### 1. Use cases (high level)

Plain language, short and to the point — one to three sentences per use case, no blocks. Structure: a section per room + a section for whole-home functions (central logic, service modes). Example phrasing: "The air conditioning switches off automatically when a window in the room is opened." "Strong wind automatically raises the exterior blinds." Describe repeated patterns (standard light switch, standard shading) once as a standard use case and just link to it from the rooms.

### 2. Miniserver, device and block settings

Parameters that **differ from the block-type default** (deviations only — a default value carries no information for a rebuild), plus device identification. Source: block attributes in the XML (`show <uuid>`); the periphery tree.

**The hard part is knowing what the default *is*.** `show` prints raw attribute values with no marker for which equal the factory default, and guessing from memory is how you get a doc that's confidently wrong. So don't guess — establish the default from a real source, in this order of preference:

1. **A fresh-defaults file (most reliable, fully offline).** Ask the user to drop one unconfigured block of each relevant type onto a page in Loxone Config, save, and hand you that file. Then a parameter is non-default exactly when it differs from the same block type there — a mechanical diff (`show` both, compare), not a judgment call. This is the gold standard for *consistent, precise* docs; recommend it whenever Layer 2 accuracy matters.
2. **The Loxone MCP**, if connected — it may report a block's current parameters and can help confirm values live (it isn't guaranteed to expose factory defaults; check).
3. **The Loxone knowledge base** — https://www.loxone.com/enen/kb/ documents per-block-type parameters and their defaults. Use it when you have connectivity.
4. **The user** — they, or their installer, often just know ("the storm threshold is stock").

If none of these is available, **do not silently drop the value and do not invent a default**: list the parameter and mark it *"deviation unverified — default not confirmed"* so the reader knows to check. An honest "unverified" beats a wrong omission in a rebuild spec.

### 3. Block wiring (rebuild level)

Detailed wiring per use case: blocks used (type + title), their inputs/outputs and the wires between them, including InputRef/OutputRef links and inverted inputs. Source: the graph from `loxone_graph.py` (`block`, `type`, `page`, `json`). **Pilot the format on 1–2 use cases first and have the user verify completeness** (could they rebuild from it?) before documenting the rest.

**Not every relationship is a wire.** Walking IN/OUT links is necessary but not sufficient for a rebuild — some connections live in plain attributes with no `<In>` wire at all, and a spec that only follows wires will silently omit them:

- **Group membership** (e.g. which blinds belong to a `CentralShade`, which lights to a `CentralLight`) is stored in the parent block's `rec`/`linkC` attribute as a UUID list, not as wires. A rebuilder must recreate these groupings explicitly. Always check the central/group blocks' attributes with `show`.
- **Behaviour-defining flags on the block tag** — e.g. `Sun="true"` marks a slat-tracking (venetian) blind vs a plain roller. These change what the block *does* and belong in the spec even though they aren't parameters you'd "wire".
- **Per-instance data in `IoData`/`<Co>` children** (blind travel times, analog thresholds, watchdog limits) is real rebuild input but the parser surfaces child elements only as counts. Read the raw child values (`show` the block, then inspect the `<Co>`/`IoData` children in the XML directly) when the rebuild genuinely needs them, and treat unknowns per the Layer-2 defaults rule above rather than inventing numbers.

## Workflow for one use case

1. Find the entry point (block, button, sensor) in the XML — `block "<title>"` — and walk the IN/OUT links in both directions until the chain closes.
2. Mine the block titles — they often carry the author's intent.
3. If a Loxone MCP is connected, verify the described behavior against reality (`control_describe`, `control_state`, state history). Without MCP, work purely from the XML; optionally suggest connecting one (setup guide: `references/mcp-setup.md` in the loxone-config-xml skill — available only when that skill is installed too).
4. Write layer 1 (behavior), then layer 3 (wiring); add any non-default parameters you encountered to layer 2.
5. New file per topic; do not rewrite existing documents unless asked.

## Piloting, repeated use cases, and shared infrastructure

The pilot step is the mechanism that makes documentation **consistent and precise across every room and block** — it locks the format on a small slice, the user confirms it's rebuild-complete, and then the *same* structure is applied uniformly to the rest. Never skip it in the name of "just doing all of them"; a fast full pass in the wrong format is slower overall and, as observed, tends to trade accuracy for volume (unverified cross-room claims, invented numbers). Consistency comes from piloting once and repeating faithfully, not from documenting everything in one burst.

If you can't actually pause for the user's confirmation (a non-interactive or automated run), don't let that push you into finalizing all instances unconfirmed — that defeats the guardrail. Produce the pilot slice plus an explicit "verify this before I roll it out" note and stop there, leaving the rest listed but pending. A deliberately-incomplete-but-correct pilot is the right outcome; a fully-rolled-out doc built on an unverified format is not.

Two shapes come up constantly in real configs — handle them explicitly:

- **One use case that repeats N times** (15 blinds, 21 light circuits, per-room heating). Don't treat this as N separate use cases. Pilot **2 representative instances** — pick ones that span the variation (e.g. a plain roller *and* a slat-tracking venetian) plus the shared logic they all depend on. Confirm with the user, then document the rest as a **table of instances against the piloted template** (per-instance: room, title, the few attributes that differ — orientation, travel time, group), not as 15 repeated prose blocks. That is what keeps a large config's doc short *and* uniform.
- **Shared central infrastructure** built once and referenced by many use cases (a storm sensor feeding every blind's Safety, a room controller driving AutoShade, central modes). Document each such source **once** in its own section and link to it from the instances, exactly as with standard patterns. Don't re-describe the storm sensor 15 times.

## Use case document template

```markdown
# <Use case name>

## Behavior
<1-3 sentences on what it does, when and why; edge scenarios as bullets>

## Wiring
<list of blocks: Type "Title" (page) + a table/list of wires:
Source.pin -> Target.pin, noting inverted inputs and Ref links>

## Non-default parameters
<block: parameter = value (why)>

## Verification
<how to tell it works - what the app/MCP should show>
```

## Principles

- Write in the language of the documentation's audience; keep block and pin names in the config's language.
- Do not document default values — deviations only.
- For every non-trivial wiring, state *why* (the intent), not just *what* — block titles and the user's notes are the source.
- **Keep secrets and personal data out of the documentation.** Passwords and PINs are the obvious case, but a real config also carries an app/cloud key (`APPKEY` in the Document block), the Miniserver serial, and owner PII in the User/Document blocks — full name, street address, GPS coordinates, emails, phone numbers, access codes (`CodeArr`/`NFCArr`). None of that belongs in a doc, and it matters most in exactly the situation where docs get shared: a **handover to a new owner or a third-party builder**. When you meet any of it, leave it out and tell the user what you withheld and where it lives. For a handover specifically, a credential/PIN reset and re-issue is a separate transfer step worth flagging — not something to paper over by copying the current secrets into a document.
