import argparse
import json
import logging
import os
import sys
from typing import Optional

from . import __version__
from .cdp import (
    CDPError,
    clear_cookies,
    dump_pages,
    format_cookies,
    get_all_cookies,
    get_debug_targets,
    load_cookies,
)


def positive_int(text: str) -> int:
    try:
        v = int(text)
        if v <= 0:
            raise ValueError
        return v
    except Exception:
        raise argparse.ArgumentTypeError("must be a positive integer")


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="crumbbum",
        description="Interact with Chrome/Chromium debug port to list pages and manage cookies.",
    )
    p.add_argument(
        "-p",
        "--port",
        type=positive_int,
        default=int(os.environ.get("CRUMBBUM_DEBUG_PORT", 9222)),
        help="Remote debugging port (default: 9222 or $CRUMBBUM_DEBUG_PORT)",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (use -vv for debug)",
    )

    sub = p.add_subparsers(dest="command", required=True)

    pages = sub.add_parser("pages", help="List open targets/pages")
    pages.add_argument("-g", "--grep", help="Filter by substring in title or URL", default=None)
    pages.add_argument("--json", action="store_true", help="Output as JSON")

    cookies = sub.add_parser("cookies", help="Dump cookies")
    cookies.add_argument(
        "-f",
        "--format",
        choices=["human", "raw", "modified"],
        default="human",
        help="Output format",
    )
    cookies.add_argument("-g", "--grep", help="Filter by name/domain substring", default=None)
    cookies.add_argument("-o", "--output", help="Write output to file instead of stdout")

    clear = sub.add_parser("clear", help="Clear all browser cookies")

    load = sub.add_parser("load", help="Load cookies from JSON file")
    load.add_argument("path", help="Path to cookies JSON (raw or modified format)")

    p.add_argument("--version", action="version", version=f"crumbbum {__version__}")
    return p


def setup_logging(verbosity: int):
    level = logging.WARNING
    if verbosity >= 2:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def _write_output(data: str, path: Optional[str]):
    if not path:
        print(data)
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)


def main(argv: Optional[list] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    setup_logging(args.verbose)

    try:
        targets = get_debug_targets(args.port)
    except CDPError as e:
        logging.error(str(e))
        return 2

    try:
        if args.command == "pages":
            items = dump_pages(targets, args.grep)
            if args.json:
                _write_output(json.dumps(items, indent=2), None)
            else:
                if not items:
                    print("No matching pages/targets.")
                for it in items:
                    print(
                        f"Title: {it['title']}\nType: {it['type']}\nURL: {it['url']}\nWebSocket: {it['webSocketDebuggerUrl']}\n"
                    )
            return 0

        if args.command == "cookies":
            cookies = get_all_cookies(targets)
            formatted = format_cookies(cookies, fmt=args.format, grep=args.grep)
            if args.format == "human":
                _write_output(formatted, args.output)
            else:
                payload = json.dumps(formatted)
                _write_output(payload, args.output)
            return 0

        if args.command == "clear":
            clear_cookies(targets)
            print("Cookies cleared.")
            return 0

        if args.command == "load":
            try:
                with open(args.path, "r", encoding="utf-8") as f:
                    content = json.load(f)
            except Exception as e:
                logging.error("Failed to read %s: %s", args.path, e)
                return 2
            # Accept either list[dict] as-is (raw) or list of LightCookie dicts (modified)
            if not isinstance(content, list):
                logging.error("Expected a JSON array of cookies.")
                return 2
            load_cookies(targets, content)
            print(f"Loaded {len(content)} cookies.")
            return 0

    except CDPError as e:
        logging.error(str(e))
        return 3

    # Should not get here
    return 1


if __name__ == "__main__":
    sys.exit(main())

