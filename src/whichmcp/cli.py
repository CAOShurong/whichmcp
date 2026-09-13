"""``whichmcp [dir]`` — which MCP config files each agent will load."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

# Path map, not an emulator. Loaders are the usual readers of that filename.
PROJECT_FILES: tuple[tuple[str, str], ...] = (
    (".mcp.json", "claude,grok"),
    (".cursor/mcp.json", "cursor"),
    (".vscode/mcp.json", "vscode,copilot"),
    (".windsurf/mcp.json", "windsurf"),
    (".gemini/settings.json", "gemini"),
    ("opencode.json", "opencode"),
    (".codex/config.toml", "codex"),
)

HOME_FILES: tuple[tuple[str, str], ...] = (
    (".claude.json", "claude,grok"),
    (".cursor/mcp.json", "cursor"),
    (".gemini/settings.json", "gemini"),
    (".codex/config.toml", "codex"),
)


@dataclass(frozen=True)
class Server:
    name: str
    transport: str
    disabled: bool = False


@dataclass(frozen=True)
class Hit:
    path: Path
    display: str
    loaders: str
    servers: tuple[Server, ...] = ()
    parse_error: bool = False
    notes: tuple[str, ...] = ()


def _git_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / ".git").exists():
            return p
    return start


def _walk_dirs(start: Path) -> list[Path]:
    root = _git_root(start)
    out: list[Path] = []
    cur = start
    while True:
        out.append(cur)
        if cur == root or cur.parent == cur:
            break
        cur = cur.parent
    return out


def _rel(path: Path, git_root: Path, home: Path) -> str:
    try:
        path.relative_to(home)
        return "~/" + path.relative_to(home).as_posix()
    except ValueError:
        pass
    try:
        return path.relative_to(git_root).as_posix()
    except ValueError:
        return path.as_posix()


def _strip_bom(text: str) -> str:
    if text.startswith("\ufeff"):
        return text[1:]
    return text


def _strip_jsonc(text: str) -> str:
    """Drop // and /* */ comments; keep string contents. Then trailing commas."""
    out: list[str] = []
    i = 0
    n = len(text)
    in_str = False
    quote = ""
    escape = False
    while i < n:
        ch = text[i]
        if in_str:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                in_str = False
            i += 1
            continue
        if ch in "\"'":
            in_str = True
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            i += 2
            while i < n and text[i] not in "\r\n":
                i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i = min(n, i + 2)
            continue
        out.append(ch)
        i += 1
    cleaned = "".join(out)
    cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)
    return cleaned


def _load_json(text: str) -> object | None:
    raw = _strip_bom(text)
    for candidate in (raw, _strip_jsonc(raw)):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def _transport(cfg: object) -> str:
    if not isinstance(cfg, dict):
        return "?"
    if cfg.get("disabled") is True or cfg.get("enabled") is False:
        kind = "disabled"
    else:
        kind = ""
    if "url" in cfg or str(cfg.get("type", "")).lower() in {"http", "sse", "streamable-http"}:
        mode = "http"
    elif "command" in cfg or str(cfg.get("type", "")).lower() in {"stdio", "local"}:
        mode = "stdio"
    else:
        mode = "?"
    if kind == "disabled":
        return "disabled"
    return mode


def _servers_from_mapping(obj: object) -> list[Server]:
    if not isinstance(obj, dict):
        return []
    block = None
    for key in ("mcpServers", "servers", "mcp"):
        val = obj.get(key)
        if isinstance(val, dict):
            block = val
            break
    if block is None:
        return []
    out: list[Server] = []
    for name, cfg in block.items():
        if not isinstance(name, str) or not name:
            continue
        trans = _transport(cfg)
        out.append(Server(name=name, transport=trans, disabled=trans == "disabled"))
    return out


def _servers_from_toml(text: str) -> list[Server]:
    names: list[str] = []
    for line in _strip_bom(text).splitlines():
        stripped = line.strip()
        m = re.match(r"^\[mcp_servers\.([^\]]+)\]\s*$", stripped)
        if m:
            names.append(m.group(1).strip().strip("'\""))
    return [Server(name=n, transport="stdio") for n in names if n]


def _collect(path: Path, loaders: str, git_root: Path, home: Path) -> Hit | None:
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    display = _rel(path.resolve(), git_root, home)
    notes: list[str] = []
    if path.suffix.lower() == ".toml" or path.name.endswith(".toml"):
        servers = _servers_from_toml(text)
        parse_error = False
    else:
        obj = _load_json(text)
        if obj is None:
            return Hit(
                path=path.resolve(),
                display=display,
                loaders=loaders,
                servers=(),
                parse_error=True,
                notes=("PARSE",),
            )
        servers = _servers_from_mapping(obj)
        parse_error = False
        if isinstance(obj, dict) and not servers:
            notes.append("empty")
    return Hit(
        path=path.resolve(),
        display=display,
        loaders=loaders,
        servers=tuple(servers),
        parse_error=parse_error,
        notes=tuple(notes),
    )


def scan(start: Path, home: Path | None = None) -> list[Hit]:
    start = start.resolve()
    git_root = _git_root(start)
    home_path = (home if home is not None else Path.home()).resolve()
    hits: list[Hit] = []
    seen: set[Path] = set()

    def add(hit: Hit | None) -> None:
        if hit is None or hit.path in seen:
            return
        seen.add(hit.path)
        hits.append(hit)

    for directory in _walk_dirs(start):
        for rel, loaders in PROJECT_FILES:
            add(_collect(directory / rel, loaders, git_root, home_path))
    for rel, loaders in HOME_FILES:
        add(_collect(home_path / rel, loaders, git_root, home_path))
    return hits


def _dup_names(hits: list[Hit]) -> set[str]:
    counts: dict[str, int] = {}
    for h in hits:
        for s in h.servers:
            counts[s.name] = counts.get(s.name, 0) + 1
    return {name for name, n in counts.items() if n > 1}


def warnings(hits: list[Hit]) -> list[str]:
    project = [h for h in hits if not h.display.startswith("~/")]
    has_claude = any("claude" in h.loaders and h.servers for h in project)
    has_cursor = any(h.loaders == "cursor" and h.servers for h in project)
    out: list[str] = []
    if has_claude and not has_cursor:
        out.append(
            "warn: .mcp.json is not read by Cursor — copy servers into .cursor/mcp.json"
        )
    if has_cursor and not has_claude:
        out.append(
            "warn: .cursor/mcp.json is not read by Claude Code — copy servers into .mcp.json"
        )
    return out


def _server_cell(hit: Hit, dups: set[str]) -> str:
    if hit.parse_error:
        return "PARSE"
    if not hit.servers:
        return "empty" if "empty" in hit.notes else "-"
    parts: list[str] = []
    for s in hit.servers:
        extra = ""
        if s.disabled:
            extra = "/off"
        elif s.transport not in {"stdio", "?"}:
            extra = f"/{s.transport}"
        flag = " DUP" if s.name in dups else ""
        parts.append(f"{s.name}{extra}{flag}")
    return ", ".join(parts)


def render(hits: list[Hit]) -> str:
    warns = warnings(hits)
    dups = _dup_names(hits)
    n_servers = sum(len(h.servers) for h in hits)
    lines = [
        f"whichmcp: {len(hits)} files  {n_servers} servers  "
        f"{len(dups)} duplicate name  {len(warns)} warn",
        "",
    ]
    if not hits:
        lines.append("(no .mcp.json, .cursor/mcp.json, .vscode/mcp.json,")
        lines.append(" .windsurf/mcp.json, .gemini/settings.json, opencode.json,")
        lines.append(" .codex/config.toml, or ~/.claude.json)")
        if warns:
            lines.append("")
            lines.extend(warns)
        return "\n".join(lines) + "\n"
    file_w = max(4, max(len(h.display) for h in hits))
    load_w = max(4, max(len(h.loaders) for h in hits))
    lines.append(f"{'file':<{file_w}}  {'load':<{load_w}}  servers")
    for h in hits:
        lines.append(
            f"{h.display:<{file_w}}  {h.loaders:<{load_w}}  {_server_cell(h, dups)}"
        )
    if warns:
        lines.append("")
        lines.extend(warns)
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="whichmcp",
        description="List which MCP config files coding agents will load from this repo.",
    )
    parser.add_argument(
        "dir",
        nargs="?",
        default=".",
        help="project directory (default: cwd); walks up to the git root",
    )
    args = parser.parse_args(argv)
    root = Path(args.dir)
    if not root.is_dir():
        print(f"whichmcp: not a directory: {args.dir}", flush=True)
        return 2
    home_env = os.environ.get("WHICHHMCP_HOME")
    home = Path(home_env) if home_env else None
    print(render(scan(root, home=home)), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
