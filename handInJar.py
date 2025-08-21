"""
Compatibility wrapper for legacy script usage.

Prefer installing and using the package CLI:

  pip install .
  crumbbum --help

This module delegates to the new CLI entrypoint when executed directly.
"""

from crumbbum.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
