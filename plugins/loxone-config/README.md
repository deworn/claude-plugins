# Loxone Config skills

Claude skills for working with [Loxone](https://www.loxone.com) Miniserver configurations. They are independent of any particular installation — no personal data inside. Each subfolder is one skill.

## Skills

### loxone-config-xml

Base skill: read and write Loxone Config project files (`.Loxone` XML).

- Documented file anatomy: blocks, pins, wires, InputRef/OutputRef proxies, block positions
- Ready-made parser/editor `scripts/loxone_graph.py` (pages, stats, block search with resolved IN/OUT links, full JSON wire dump, surgical attribute edits that preserve BOM/CRLF/formatting)
- UUID bridge: block UUID in the XML == runtime control UUID == UUID in a Loxone MCP server
- Safety rules for writing: never touch the original, mandatory backup, no XML-library serialization, re-parse validation
- `references/mcp-setup.md`: field-tested steps for connecting a Miniserver as an MCP server (Claude Code CLI and Claude Desktop)

Works fully offline over the XML; a connected Loxone MCP is optional and used only for live cross-checking.

### loxone-documentation

Extension skill: methodology for documenting a Loxone installation so it can be **rebuilt without the config file** — three layers (use cases → non-default settings → rebuild-level block wiring), a workflow for tracing one use case through the graph, and a document template.

## Why use these skills instead of a plain agent session

A general agent can open a `.Loxone` file and figure a lot out on its own — but the `.Loxone` format is undocumented, and on a real config the details that bite are subtle. These skills exist to give the agent the hard-won knowledge up front, so you get the same result faster and, more importantly, without the failure modes. They were built and refined through repeated real-config testing, and each carries the lessons from it:

- **Safe edits.** The parser preserves the file's exact byte format (BOM, CRLF, attribute order) and validates every change, so a bulk rename or parameter tweak can't silently corrupt the file that controls your heating, blinds and alarm. A from-scratch agent tends to reach for an XML library that quietly reorders everything.
- **Reads what wires don't show.** Some relationships (blind→central-shading group membership, behaviour flags) live in attributes, not wires — easy to miss and enough to break a rebuild. The skills know to look there.
- **Doesn't guess.** For documentation, values that can't be confirmed are marked "unverified" rather than invented — no confident-but-wrong numbers in a spec someone will build from.
- **Right level of detail.** A quick "what does this do?" gets a short plain answer; a handover or rebuild spec gets the full layered writeup — instead of one wall of text either way.
- **Keeps your data safe.** Handover docs leave out secrets and personal data (app keys, PINs, address, serial) by default.
- **Less back-and-forth for you.** Ready-made parser commands and a clear method mean the agent spends its effort on your question, not on re-deriving the file format every session.
- **Cheaper to run.** Because the agent isn't reinventing a parser or exploring the format from scratch each time, it uses noticeably fewer tokens to reach the same answer — in testing, a from-scratch session often burned well over half as many tokens again on that groundwork alone.

## Install

Preferred: add the repo as a plugin marketplace and install the `loxone-config` plugin — you get both skills at once and updates via the marketplace (see the root README).

Manual alternative: zip each skill's folder under `skills/` separately (e.g. `skills/loxone-config-xml/`) and upload the zip wherever your Claude client manages skills.

## Compatibility

Developed and tested against a real-world config from **Loxone Config / Miniserver 17.1** (`ControlList Version="272"`, ~2 200 objects, ~1 600 wires). The format is undocumented by Loxone; verify on your own config before writing.
