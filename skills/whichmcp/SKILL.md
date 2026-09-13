---
name: whichmcp
description: Show which MCP config files Claude, Cursor, VS Code, Codex and Gemini will actually load from this repo. Use when an MCP server is missing in one agent or you are unsure whether to use .mcp.json or .cursor/mcp.json.
---

# whichmcp

Use this when a server "should" exist but one agent has no tools. Do not
open every vendor MCP file by hand.

```bash
whichmcp
whichmcp /path/to/repo
```

The printed block is: counts (files, servers, duplicate names, warns), then
one row per config. Server names only — never env values or tokens.

`.mcp.json` is Claude Code (and Grok). Cursor reads `.cursor/mcp.json`.
VS Code / Copilot read `.vscode/mcp.json`. They are not the same file.

This is a path map, not a live MCP client. It does not start servers.
