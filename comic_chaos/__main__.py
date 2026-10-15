"""
Comic Chaos - Interactive Comic Strip Generator

Start the web server:                             python -m comic_chaos
Check the configuration (offline, no API calls): python -m comic_chaos --check
"""

import argparse
import os
import sys

from .config import DEFAULT_HOST, DEFAULT_PORT, check_config

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def report_config() -> bool:
    """Print configuration problems. Returns True if comics can be generated."""
    errors, warnings = check_config()
    for warning in warnings:
        print(f"  WARNING: {warning}")
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

    host = os.getenv("HOST", DEFAULT_HOST)
    debug = os.getenv("DEBUG", "false").lower() == "true"
    try:
        port = int(os.getenv("PORT", str(DEFAULT_PORT)))
    except ValueError:
        print(f"ERROR: PORT must be a number, got {os.getenv('PORT')!r}")
        return 1

    if debug and host not in LOOPBACK_HOSTS:
        print("ERROR: DEBUG=true enables an interactive debugger and is only allowed with HOST=127.0.0.1.")
        return 1

    print("Starting Comic Chaos...")
    report_config()
    if host not in LOOPBACK_HOSTS:
        print(f"  WARNING: Listening on {host}. Comic Chaos has no login: anyone who can reach this "
              "port can start comics that are billed to your OpenAI account.")

    browser_host = "localhost" if host in ("0.0.0.0", "::") else host
    if ":" in browser_host:
        browser_host = f"[{browser_host}]"  # IPv6 literal
    print(f"Open http://{browser_host}:{port} in your browser")

    from .app import app

    app.run(debug=debug, host=host, port=port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
