# claude-skills

A collection of my skills for Claude, packaged as plugins. The repo doubles as a **Claude plugin marketplace** — add it once and you can install and update the plugins from inside Claude.

Everything here is provided **AS IS**, without warranty of any kind. These skills were built for my own setups — review them before use and test on your own data.

## Add as a marketplace

**Claude Code (CLI):**

```shell
/plugin marketplace add deworn/claude-skills
/plugin install loxone-config@deworn-skills
```

Updates: `/plugin marketplace update deworn-skills` (with no pinned versions, every new commit counts as a new plugin version).

**Claude Desktop (Cowork):** in plugin settings, add a marketplace and point it at this repo (`deworn/claude-skills`), then install the plugin from the list.

## Manual install (no marketplace)

Skills are plain folders under `plugins/<plugin>/skills/`. Zip one skill folder (e.g. `loxone-config-xml/`) and upload the zip wherever your Claude client manages skills.

## Plugins

Each plugin lives in `plugins/` and has its own README with details.
