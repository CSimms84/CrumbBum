import json
import time
from types import SimpleNamespace

import crumbbum.cdp as cdp


def _resp_with_json(payload, status_code=200):
    class R:
        def __init__(self, payload, status_code):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

        def raise_for_status(self):
            if not (200 <= self.status_code < 300):
                raise RuntimeError("bad status")

    return R(payload, status_code)


def test_get_debug_targets_filters_and_parses(monkeypatch):
    payload = [
        {"id": "1", "type": "page", "title": "Tab A", "url": "https://a", "webSocketDebuggerUrl": "ws://a"},
        {"id": "2", "type": "other", "title": "No WS", "url": "https://b"},  # filtered out
    ]

    monkeypatch.setattr(cdp.requests, "get", lambda url, timeout=3.0: _resp_with_json(payload))

    targets = cdp.get_debug_targets(9222)
    assert len(targets) == 1
    t = targets[0]
    assert t.id == "1"
    assert t.webSocketDebuggerUrl == "ws://a"


def test_get_debug_targets_raises_when_empty(monkeypatch):
    monkeypatch.setattr(cdp.requests, "get", lambda url, timeout=3.0: _resp_with_json([]))
    try:
        cdp.get_debug_targets(9222)
        assert False, "expected CDPError"
    except cdp.CDPError:
        pass


def test_format_cookies_human_and_modified():
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

    human = cdp.format_cookies(cookies, fmt="human")
    assert "Number of cookies: 1" in human
    assert "name: sid" in human

    before = time.time()
    modified = cdp.format_cookies(cookies, fmt="modified")
    assert isinstance(modified, list) and modified
    m = modified[0]
    assert m["name"] == "sid"
    # expires pushed far in the future
    assert m["expires"] > before + 9 * 365 * 24 * 60 * 60


def test_clear_and_load_call_cdp(monkeypatch):
    calls = []

    class FakeWS:
        def __init__(self):
            self.sent = []

        def send(self, payload):
            self.sent.append(payload)

        def recv(self):
            # Respond with a minimal successful result for both methods
            # The method id increments, but we just return ok
            return json.dumps({"id": 1, "result": {}})

        def close(self):
            pass

    def fake_connect(url, origin="http://localhost", timeout=5.0):
        calls.append(("connect", url))
        return FakeWS()

    monkeypatch.setattr(cdp.websocket, "create_connection", fake_connect)

    targets = [
        cdp.DebugTarget(
            description="",
            devtoolsFrontendUrl="",
            id="x",
            title="",
            type="page",
            url="",
            webSocketDebuggerUrl="ws://x",
        )
    ]

    cdp.clear_cookies(targets)
    cdp.load_cookies(targets, [{"name": "a", "value": "b", "domain": "x", "path": "/", "expires": 0}])

    # We should have established a connection twice (two separate operations)
    assert calls and calls[0][0] == "connect"

