import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import requests
import websocket


LOG = logging.getLogger(__name__)


@dataclass
class DebugTarget:
    description: str
    devtoolsFrontendUrl: str
    id: str
    title: str
    type: str
    url: str
    webSocketDebuggerUrl: str
    faviconUrl: str = ""


@dataclass
class LightCookie:
    name: str
    value: str
    domain: str
    path: str
    expires: float


class CDPError(RuntimeError):
    pass


def get_debug_targets(port: int, timeout: float = 3.0) -> List[DebugTarget]:
    url = f"http://localhost:{port}/json"
    LOG.debug("Fetching targets from %s", url)
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except Exception as e:
        raise CDPError(
            f"Failed to fetch debug targets from {url}. Is the browser started with --remote-debugging-port={port}?"
        ) from e

    data = resp.json()
    targets: List[DebugTarget] = []
    for item in data:
        # Only include entries that have a WebSocket URL
        ws = item.get("webSocketDebuggerUrl")
        if not ws:
            continue
        targets.append(
            DebugTarget(
                description=item.get("description", ""),
                devtoolsFrontendUrl=item.get("devtoolsFrontendUrl", ""),
                id=item.get("id", ""),
                title=item.get("title", ""),
                type=item.get("type", ""),
                url=item.get("url", ""),
                webSocketDebuggerUrl=ws,
                faviconUrl=item.get("faviconUrl", ""),
            )
        )
    LOG.debug("Found %d targets", len(targets))
    if not targets:
        raise CDPError("No debug targets found. Open at least one tab/window.")
    return targets


def _pick_target(targets: Iterable[DebugTarget], prefer_type: str = "page") -> DebugTarget:
    for t in targets:
        if t.type == prefer_type:
            return t
    # Fallback to the first target available
    return list(targets)[0]


class CDPClient:
    def __init__(self, ws_url: str, origin: str = "http://localhost", timeout: float = 5.0):
        self.ws_url = ws_url
        self.origin = origin
        self.timeout = timeout
        self._ws: Optional[websocket.WebSocket] = None
        self._id = 0

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def connect(self):
        try:
            LOG.debug("Connecting WebSocket: %s", self.ws_url)
            self._ws = websocket.create_connection(self.ws_url, origin=self.origin, timeout=self.timeout)
        except Exception as e:
            raise CDPError(f"Failed to connect to {self.ws_url}") from e

    def close(self):
        if self._ws is not None:
            try:
                self._ws.close()
            finally:
                self._ws = None

    def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self._ws is None:
            raise CDPError("WebSocket not connected")
        self._id += 1
        msg = {"id": self._id, "method": method}
        if params:
            msg["params"] = params
        payload = json.dumps(msg)
        LOG.debug("-> %s", payload)
        self._ws.send(payload)
        raw = self._ws.recv()
        LOG.debug("<- %s", raw[:1000])
        data = json.loads(raw)
        if "error" in data:
            raise CDPError(f"CDP error for {method}: {data['error']}")
        return data


def dump_pages(targets: List[DebugTarget], grep: Optional[str] = None) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    query = grep.lower() if grep else None
    for t in targets:
        if query and not ((t.title and query in t.title.lower()) or (t.url and query in t.url.lower())):
            continue
        items.append(
            {
                "title": t.title,
                "type": t.type,
                "url": t.url,
                "webSocketDebuggerUrl": t.webSocketDebuggerUrl,
            }
        )
    return items


def get_all_cookies(targets: List[DebugTarget]) -> List[Dict[str, Any]]:
    target = _pick_target(targets, prefer_type="page")
    LOG.debug("Using target %s (%s)", target.id, target.type)
    with CDPClient(target.webSocketDebuggerUrl) as cdp:
        data = cdp.call("Network.getAllCookies")
    cookies = data.get("result", {}).get("cookies", [])
    return cookies


def format_cookies(
    cookies: List[Dict[str, Any]],
    fmt: str = "human",
    grep: Optional[str] = None,
    extended_expiry_years: int = 10,
) -> Any:
    query = grep.lower() if grep else None
    filtered = []
    for c in cookies:
        if query and not (query in c.get("name", "").lower() or query in c.get("domain", "").lower()):
            continue
        filtered.append(c)

    if fmt == "raw":
        return filtered

    if fmt == "modified":
        horizon = time.time() + extended_expiry_years * 365 * 24 * 60 * 60
        light = [
            LightCookie(
                name=c.get("name", ""),
                value=c.get("value", ""),
                domain=c.get("domain", ""),
                path=c.get("path", "/"),
                expires=horizon,
            ).__dict__
            for c in filtered
        ]
        return light

    # human
    lines: List[str] = []
    lines.append(f"Number of cookies: {len(filtered)}")
    for c in filtered:
        lines.extend(
            [
                f"name: {c.get('name')}",
                f"value: {c.get('value')}",
                f"domain: {c.get('domain')}",
                f"path: {c.get('path')}",
                f"expires: {c.get('expires')}",
                f"size: {c.get('size')}",
                f"httpOnly: {c.get('httpOnly')}",
                f"secure: {c.get('secure')}",
                f"session: {c.get('session')}",
                f"sameSite: {c.get('sameSite', 'N/A')}",
                f"priority: {c.get('priority')}",
                "",
            ]
        )
    return "\n".join(lines)


def clear_cookies(targets: List[DebugTarget]) -> None:
    target = _pick_target(targets, prefer_type="page")
    with CDPClient(target.webSocketDebuggerUrl) as cdp:
        cdp.call("Network.clearBrowserCookies")


def load_cookies(targets: List[DebugTarget], cookies: List[Dict[str, Any]]) -> None:
    target = _pick_target(targets, prefer_type="page")
    with CDPClient(target.webSocketDebuggerUrl) as cdp:
        cdp.call("Network.setCookies", {"cookies": cookies})

