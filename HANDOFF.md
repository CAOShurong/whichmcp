---
schema_version: portable-project-memory/v1
handoff_revision: 1
updated_at: "2026-09-13T12:20:00+08:00"
updated_by: "grok-unattended"
base_revision: git:pending
status: active
---

# Project Handoff

## Current objective

AI **harness** tool: `whichmcp` lists `.mcp.json` / `.cursor/mcp.json` /
`.vscode/mcp.json` each coding agent will load, and warns when Cursor
will miss Claude's file.

## Confirmed state

- https://github.com/CAOShurong/whichmcp public; CI green on `740b5f9`
- Tests: cursor-miss, both-quiet, DUP names, home override,
  disabled/http, BOM+JSONC, PARSE, Codex TOML, missing dir,
  project-under-home paths, skip gemini settings without MCP, empty .mcp.json
- README capture is a real `whichmcp demo` run (unchanged)
- No extra flags. `WHICHHMCP_HOME` is an env override only.
- Does not print env/tokens from MCP configs.

## Next actions

1. Confirm CI green after the path/settings skip fix.
2. Stop grinding flags. Do not add JSON/MCP-client/symlink-writer.
   Do not open a fifth `which*` CLI.

## User decisions required

None.
