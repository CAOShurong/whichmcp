from pathlib import Path

from whichmcp.cli import main, render, scan, warnings


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


MCP = """{
  "mcpServers": {
    "github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]}
  }
}
"""


def test_mcp_json_without_cursor_warns(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    _write(tmp_path / ".mcp.json", MCP)
    hits = scan(tmp_path, home=tmp_path / "no-home")
    assert len(hits) == 1
    assert hits[0].servers[0].name == "github"
    assert "claude" in hits[0].loaders
    text = render(hits)
    assert "copy servers into .cursor/mcp.json" in text
    assert "1 warn" in text


def test_both_claude_and_cursor_is_quiet(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    _write(tmp_path / ".mcp.json", MCP)
    _write(tmp_path / ".cursor" / "mcp.json", MCP)
    hits = scan(tmp_path, home=tmp_path / "no-home")
    assert warnings(hits) == []
    assert len(hits) == 2


def test_cursor_without_claude_warns(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    _write(tmp_path / ".cursor" / "mcp.json", MCP)
    text = render(scan(tmp_path, home=tmp_path / "no-home"))
    assert "copy servers into .mcp.json" in text


def test_duplicate_server_name(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    _write(tmp_path / ".mcp.json", MCP)
    vscode = """{"servers": {"github": {"command": "npx"}, "playwright": {"command": "npx"}}}"""
    _write(tmp_path / ".vscode" / "mcp.json", vscode)
    hits = scan(tmp_path, home=tmp_path / "no-home")
    text = render(hits)
    assert "DUP" in text
    assert "1 duplicate name" in text
    assert "playwright" in text


def test_home_override_and_vscode_servers_key(tmp_path: Path, monkeypatch):
    proj = tmp_path / "proj"
    home = tmp_path / "home"
    proj.mkdir()
    (proj / ".git").mkdir()
    _write(
        home / ".claude.json",
        '{"mcpServers": {"gmail": {"command": "uvx", "args": ["mcp-gmail"]}}}',
    )
    monkeypatch.setenv("WHICHHMCP_HOME", str(home))
    hits = scan(proj, home=home)
    assert any(h.display.startswith("~/") and h.servers[0].name == "gmail" for h in hits)


def test_disabled_and_http_transport(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    body = """{
      "mcpServers": {
        "remote": {"url": "https://example.invalid/mcp"},
        "old": {"command": "npx", "disabled": true}
      }
    }"""
    _write(tmp_path / ".mcp.json", body)
    hits = scan(tmp_path, home=tmp_path / "no-home")
    names = {s.name: s.transport for s in hits[0].servers}
    assert names["remote"] == "http"
    assert names["old"] == "disabled"
    text = render(hits)
    assert "remote/http" in text
    assert "old/off" in text


def test_bom_and_jsonc(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    _write(
        tmp_path / ".vscode" / "mcp.json",
        "\ufeff{\n  // comment\n  \"servers\": { \"github\": { \"command\": \"npx\", } }\n}\n",
    )
    hits = scan(tmp_path, home=tmp_path / "no-home")
    assert hits[0].servers[0].name == "github"
    assert not hits[0].parse_error


def test_parse_error(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    _write(tmp_path / ".mcp.json", "{not json")
    hits = scan(tmp_path, home=tmp_path / "no-home")
    assert hits[0].parse_error
    assert "PARSE" in render(hits)


def test_codex_toml(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    _write(tmp_path / ".codex" / "config.toml", "[mcp_servers.docs]\ncommand = \"npx\"\n")
    hits = scan(tmp_path, home=tmp_path / "no-home")
    assert hits[0].servers[0].name == "docs"
    assert "codex" in hits[0].loaders


def test_missing_dir_exits_2(tmp_path: Path):
    assert main([str(tmp_path / "nope")]) == 2


def test_empty_tree(tmp_path: Path, capsys, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.setenv("WHICHHMCP_HOME", str(tmp_path / "empty-home"))
    assert main([str(tmp_path)]) == 0
    assert "0 files" in capsys.readouterr().out
