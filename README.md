# claude-plugins

A collection of my skills for Claude, packaged as plugins and available as the **deworns-claude-plugins** Claude plugin marketplace.

Everything here is provided **AS IS**, without warranty of any kind. These skills were built for my own setups — review them before use and test on your own data.

## Add as a marketplace

**Claude Code (CLI):**

```shell
/plugin marketplace add deworn/claude-plugins
/plugin install loxone-config@deworns-claude-plugins
```

Updates: `/plugin marketplace update deworns-claude-plugins` (with no pinned versions, every new commit counts as a new plugin version).

**Claude Desktop (Cowork):** in plugin settings, add a marketplace and point it at this repo (`deworn/claude-plugins`), then install the plugin from the list.

## Manual install (no marketplace)

Skills are plain folders under `plugins/<plugin>/skills/`. Zip one skill folder (e.g. `loxone-config-xml/`) and upload the zip wherever your Claude client manages skills. Each plugin has its own README with details.
