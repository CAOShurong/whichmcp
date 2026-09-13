# whichmcp

[![ci](https://github.com/CAOShurong/whichmcp/actions/workflows/ci.yml/badge.svg)](https://github.com/CAOShurong/whichmcp/actions/workflows/ci.yml)

**You added `.mcp.json`. Cursor still has no tools.** Different agents read different MCP files. This command lists what will actually load.

```bash
pip install git+https://github.com/CAOShurong/whichmcp.git
whichmcp
```

Captured locally on the `demo/` tree in this repo (`WHICHHMCP_HOME=demo/home whichmcp demo`):

```text
whichmcp: 3 files  5 servers  1 duplicate name  1 warn

file                   load            servers
demo/.mcp.json         claude,grok     github DUP, gmail
demo/.vscode/mcp.json  vscode,copilot  github DUP, playwright
~/.claude.json         claude,grok     github DUP

warn: .mcp.json is not read by Cursor — copy servers into .cursor/mcp.json
```

Claude Code reads `.mcp.json`. Cursor reads `.cursor/mcp.json`. VS Code / Copilot read `.vscode/mcp.json`. They are **not** aliases. `DUP` is the same server name in more than one file — often copy-paste, not a merge.

Only **server names** are printed. Command args, env, and tokens stay on disk.

## What it scans

From the given directory up to the git root, plus a few user-level files:

| File | Typical loaders |
|------|-----------------|
| `.mcp.json` | Claude Code, Grok |
| `.cursor/mcp.json` | Cursor |
| `.vscode/mcp.json` | VS Code, Copilot |
| `.windsurf/mcp.json` | Windsurf |
| `.gemini/settings.json` (`mcpServers`) | Gemini CLI |
| `opencode.json` (`mcp`) | OpenCode |
| `.codex/config.toml` (`[mcp_servers.*]`) | Codex |
| `~/.claude.json` | Claude Code, Grok |

Override the home directory with `WHICHHMCP_HOME` (tests and the capture above).

This is a **path map**, not an MCP client. It does not start servers or call tools.

Skill file: [`skills/whichmcp/SKILL.md`](skills/whichmcp/SKILL.md) — copy it into a vendor skills folder (`whichskills` explains why).

## Install the skill

Copy `skills/whichmcp/SKILL.md` into `.agents/skills/whichmcp/` (Grok),
`.claude/skills/whichmcp/` (Claude Code), or your agent's skill directory.
