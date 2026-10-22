"""
Comic Chaos - Interactive Comic Strip Generator

Start the web server:                             python -m comic_chaos
Check the configuration (offline, no API calls): python -m comic_chaos --check
"""

import argparse
import os
import sys

from .config import DEFAULT_PORT, HOST, check_config


def report_config() -> bool:
    """Print configuration problems. Returns True if comics can be generated."""
    errors = check_config()
    for error in errors:
        print(f"  ERROR: {error}")
    return not errors


def main(argv: list[str] | None = None) -> int:
    """Entry point - starts the web server."""
    parser = argparse.ArgumentParser(prog="python -m comic_chaos", description="Comic Chaos web server")
    parser.add_argument(
        "--check", action="store_true",
        help="validate configuration and comics without starting the server or calling any API",
    )
    args = parser.parse_args(argv)

    if args.check:
        ok = report_config()
        print("Configuration OK." if ok else "Configuration has problems (see above).")
        return 0 if ok else 1

    try:
        port = int(os.getenv("PORT", str(DEFAULT_PORT)))
    except ValueError:
        print(f"ERROR: PORT must be a number, got {os.getenv('PORT')!r}")
        return 1

    print("Starting Comic Chaos...")
    report_config()
    print(f"Open http://{HOST}:{port} in your browser")

    from .app import app

    app.run(host=HOST, port=port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
