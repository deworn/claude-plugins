# claude-market

A collection of my plugins, skills and other stuff for Claude available as the **deworns-claude-market** marketplace.

Everything here is provided **AS IS**, without warranty of any kind. These skills were built for my own setups — review them before use and test on your own data.

## Add as a marketplace

**Claude Code (CLI):**

```shell
/plugin marketplace add deworn/claude-market
/plugin install loxone-config@deworns-claude-market
```

`/plugin install` asks where to install it - pick the scope:

- **user** - available in all your sessions (`~/.claude/settings.json`)
- **project** - shared with anyone who checks out that repo (`.claude/settings.json`, committed)
- **local** - only you, only that repo (`.claude/settings.local.json`, gitignored)

To skip the prompt, pass the scope directly (both commands take `-s`/`--scope`):

```shell
claude plugin marketplace add deworn/claude-market --scope project
claude plugin install loxone-config@deworns-claude-market --scope project
```

Updates: `/plugin marketplace update deworns-claude-market` re-syncs the marketplace from this repo. Each plugin is versioned - see its `CHANGELOG.md` for what changed between versions.

**Claude Desktop (Cowork):** in plugin settings, add a marketplace and point it at this repo (`deworn/claude-market`), then install the plugin from the list.

## Manual install (no marketplace)

Skills are plain folders under `plugins/<plugin>/skills/`. Zip one skill folder (e.g. `loxone-config-xml/`) and upload the zip wherever your Claude client manages skills. Each plugin has its own README with details.
