"""Start the local-only web dashboard."""

from __future__ import annotations

import sys

DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = 8000


def main() -> None:
    """Run the dashboard server on its fixed loopback address."""
    try:
        import uvicorn
    except ImportError:
        print(
            "Dashboard dependencies are missing. Run "
            "'python3 -m pip install -r requirements.txt'.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None

    try:
        from src.web.app import create_app
    except ImportError:
        print(
            "Dashboard dependencies are missing. Run "
            "'python3 -m pip install -r requirements.txt'.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None

    uvicorn.run(create_app(), host=DASHBOARD_HOST, port=DASHBOARD_PORT)


if __name__ == "__main__":
    main()
