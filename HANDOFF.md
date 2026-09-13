---
schema_version: portable-project-memory/v1
handoff_revision: 1
updated_at: "2026-09-13T12:20:00+08:00"
updated_by: "grok-unattended"
base_revision: git:44ad4fd
status: active
---

# Project Handoff

## Current objective

AI **harness** tool: `whichmcp` lists `.mcp.json` / `.cursor/mcp.json` /
`.vscode/mcp.json` each coding agent will load, and warns when Cursor
will miss Claude's file.

## Confirmed state

- https://github.com/CAOShurong/whichmcp public, `44ad4fd`
- Tests: cursor-miss, both-quiet, DUP names, home override,
  disabled/http, BOM+JSONC, PARSE, Codex TOML, missing dir
- README capture is a real `whichmcp demo` run
- No extra flags. `WHICHHMCP_HOME` is an env override only.
- Does not print env/tokens from MCP configs.

## Next actions

1. Confirm CI green on `main`.
2. Stop grinding flags. Do not add JSON/MCP-client/symlink-writer.

## User decisions required

None.
