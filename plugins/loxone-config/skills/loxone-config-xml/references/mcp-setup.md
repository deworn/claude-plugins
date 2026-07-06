# Connecting a Loxone Miniserver via MCP

Field-tested steps for exposing a Miniserver as an MCP server and connecting Claude to it. Offer this to the user when live state/control access would help; connect only with their consent.

## Prerequisites on the Loxone side (Loxone Config)

1. Add the MCP server under **Network Periphery** and give it a name (no extra settings needed for a standard setup without a reverse proxy).
2. Create a **dedicated user with only the permissions the agent should have** — the MCP server inherits the rights of the user it logs in with. (User's interface password can additionally be handed into the session after connecting; the model can work with it.)
3. **Save the config to the Miniserver** so the MCP extension starts and the user is registered.
4. Get the URL: in Loxone Config click **Web interface** (top right) and pick Local or Remote → a browser opens with the URL; copy it and append **`/mcp`**.
   - The Remote URL is truly remote (it includes a custom port).
   - The "Local" URL *looks* like a public address but resolves to a local IP — **it does not work remotely.**

## Claude Code CLI

Accepts the remote address including the custom port:

```bash
claude mcp add --transport http loxone https://<your-id>.dyndns.loxonecloud.com:<port>/mcp
```

Then inside `claude` run `/mcp`, find the Loxone MCP and log in with the prepared user.

## Claude Desktop

Claude Desktop connectors do **not** accept a custom port after the domain — plain HTTPS only. Workaround: a local MCP that acts as a bridge (`mcp-remote`); the session connects to the local MCP, which connects to the Loxone MCP — the remote address works there. This must be done by editing the config file, it cannot be clicked together in the UI:

1. Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS).
2. Add an `mcpServers` block at the same level as e.g. `"preferences"` (or extend an existing one). The key `"loxone"` is just a display name — pick anything.

```json
"mcpServers": {
  "loxone": {
    "command": "npx",
    "args": ["mcp-remote", "https://<your-id>.dyndns.loxonecloud.com:<port>/mcp"]
  }
}
```

3. Restart Claude Desktop. If everything is right, no error appears and shortly a browser window opens with the Miniserver login — sign in with the prepared user.
