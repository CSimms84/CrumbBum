import json
from typing import List

import crumbbum.cli as cli


def test_cli_pages_human(monkeypatch, capsys):
    def fake_targets(port):
        return [
            type("T", (), {"title": "Foo", "type": "page", "url": "https://foo", "webSocketDebuggerUrl": "ws://foo"})
        ]

    def fake_dump(targets, grep=None):
        return [
            {"title": "Foo", "type": "page", "url": "https://foo", "webSocketDebuggerUrl": "ws://foo"}
        ]

    monkeypatch.setattr("crumbbum.cli.get_debug_targets", fake_targets)
    monkeypatch.setattr("crumbbum.cli.dump_pages", fake_dump)

    rc = cli.main(["pages"])  # default port
    assert rc == 0
    out = capsys.readouterr().out
    assert "Title: Foo" in out
    assert "URL: https://foo" in out


def test_cli_cookies_raw_and_modified(monkeypatch, capsys):
    cookies = [
        {
            "name": "sid",
            "value": "abc",
            "domain": ".example.com",
            "path": "/",
            "expires": 123,
            "size": 3,
            "httpOnly": True,
            "secure": True,
            "session": False,
            "priority": "Medium",
        }
    ]

    monkeypatch.setattr("crumbbum.cli.get_debug_targets", lambda port: [object()])
    monkeypatch.setattr("crumbbum.cli.get_all_cookies", lambda targets: cookies)

    # raw
    rc = cli.main(["cookies", "-f", "raw"])
    assert rc == 0
    out = capsys.readouterr().out
    parsed: List[dict] = json.loads(out)
    assert parsed and parsed[0]["name"] == "sid"

    # modified
    rc = cli.main(["cookies", "-f", "modified"])
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed and parsed[0]["name"] == "sid"
    assert "expires" in parsed[0]

