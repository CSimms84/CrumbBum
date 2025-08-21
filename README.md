# CrumbBum
Tired of websites hogging all the cookie control? CrumbBum puts you in charge of your digital dessert tray. 🍪👨‍🍳

CrumbBum is a tiny CLI that talks to Chrome/Chromium's DevTools Protocol to list pages and manage cookies: dump them, clear them, and load them back.

Note: you must start your Chromium-based browser with the remote debugging port enabled.

## Quick Start

1) Start your browser with DevTools remote debugging enabled (pick one):

- macOS (Chrome): `open -na "/Applications/Google Chrome.app" --args --remote-debugging-port=9222`
- macOS (Edge): `open -na "/Applications/Microsoft Edge.app" --args --remote-debugging-port=9222`
- macOS (Brave): `open -na "/Applications/Brave Browser.app" --args --remote-debugging-port=9222`
- Linux (Chrome): `google-chrome --remote-debugging-port=9222`
- Linux (Chromium): `chromium --remote-debugging-port=9222`
- Windows (Chrome): `"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222`

2) Install CrumbBum from this repo:

```
python3 -m pip install .
```

3) Verify it can see your tabs:

```
crumbbum pages -p 9222
```

4) Dump cookies to a file (modified format):

```
crumbbum cookies -p 9222 -f modified -o cookies.json
```

5) Load cookies back later:

```
crumbbum load -p 9222 cookies.json
```

Examples (choose one):
- Google Chrome: `open -na "/Applications/Google Chrome.app" --args --remote-debugging-port=9222`
- Microsoft Edge: `open -na "/Applications/Microsoft Edge.app" --args --remote-debugging-port=9222`
- Brave: `open -na "/Applications/Brave Browser.app" --args --remote-debugging-port=9222`

Alternatively on Linux/Windows start the browser binary with the `--remote-debugging-port=9222` flag.

## Install

This project uses a modern `pyproject.toml` layout.

- From source: `python3 -m pip install .` (inside the repo)

Requires Python 3.8+.

## Usage

Environment:
- `CRUMBBUM_DEBUG_PORT`: default remote debug port (defaults to 9222)

Commands:

```
crumbbum --help
crumbbum pages [-g SUBSTR] [--json]
crumbbum cookies [-f human|raw|modified] [-g SUBSTR] [-o FILE]
crumbbum clear
crumbbum load path/to/cookies.json
```

Common options:
- `-p, --port`: remote debugging port (default: 9222)
- `-v, -vv`: increase verbosity
  - example: `crumbbum -vv cookies` shows debug logs

### Pages

List open DevTools targets (tabs, pages, extensions, etc.).

```
crumbbum pages -p 9222 -g youtube
```

### Cookies

Dump cookies in various formats:

- `human`: pretty printed to stdout
- `raw`: JSON array exactly as returned by CDP
- `modified`: JSON array of simplified cookies with extended expiry (useful for import)

Examples:

```
# Human-readable dump
crumbbum cookies

# Raw JSON
crumbbum cookies -f raw -o cookies.json

# Modified format extended ~10 years
crumbbum cookies -f modified -o cookies_modified.json
```

### Clear cookies

```
crumbbum clear
```

### Load cookies

Accepts a JSON array of cookie dicts (either the `raw` or `modified` output):

```
crumbbum load cookies.json
```

## Notes

- Works with Chrome/Chromium, Edge, Brave, etc., via the DevTools Protocol.
- You must have at least one page/tab open for cookie operations.
- Be mindful of the security implications of exporting/importing cookies.

## Troubleshooting

- Connection error / cannot fetch targets:
  - Ensure the browser was started with `--remote-debugging-port=9222` (or your chosen port).
  - Pass the correct port using `-p PORT` or set `CRUMBBUM_DEBUG_PORT`.
  - Make sure at least one tab/page is open.
  - Try another port if 9222 is in use.
- `crumbbum: command not found` after install:
  - Ensure your Python Scripts/bin directory is on `PATH` (e.g., `~/.local/bin` on Linux/macOS).
  - Alternatively run as a module: `python3 -m crumbbum.cli --help`.
- Legacy usage: `python handInJar.py` still works and delegates to the new CLI.

## Example Output

Pages (human):

```
$ crumbbum pages
Title: New Tab
Type: page
URL: chrome://newtab/
WebSocket: ws://localhost:9222/devtools/page/123...

Title: Example Domain
Type: page
URL: https://example.com/
WebSocket: ws://localhost:9222/devtools/page/456...
```

Cookies (human):

```
$ crumbbum cookies -g example
Number of cookies: 2
name: sid
value: abc123
domain: .example.com
path: /
expires: 1735689600
size: 42
httpOnly: True
secure: True
session: False
sameSite: Lax
priority: Medium

name: lang
value: en-US
domain: .example.com
path: /
expires: 1735689600
size: 12
httpOnly: False
secure: False
session: False
sameSite: Lax
priority: Medium
```

Cookies (raw JSON, truncated):

```
$ crumbbum cookies -f raw | head -n 5
[{"domain": ".example.com", "expirationDate": 1735689600, "name": "sid", ...}, ...]
```

Cookies (modified JSON, simplified + extended expiry):

```
$ crumbbum cookies -f modified | jq '.[0]'
{
  "name": "sid",
  "value": "abc123",
  "domain": ".example.com",
  "path": "/",
  "expires": 204...  
}
```

## Recipes

- Filter cookies by domain:
  - `crumbbum cookies -g example.com`

- Export cookies for a site and import into another profile/instance:
  - Start Profile A on port 9222 and Profile B on port 9333 (use `--user-data-dir` when launching Chrome if needed).
  - Export from A: `crumbbum cookies -p 9222 -g example.com -f modified -o example_cookies.json`
  - (Optional) Clear on B: `crumbbum clear -p 9333`
  - Import on B: `crumbbum load -p 9333 example_cookies.json`

- Extend cookie lifetime for long-lived sessions:
  - Use the `modified` format when exporting; expirations are pushed ~10 years forward.

- Set a default port for convenience:
  - `export CRUMBBUM_DEBUG_PORT=9222` then run `crumbbum cookies` without `-p`.
