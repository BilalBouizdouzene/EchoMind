"""Launch EchoMind's local dashboard or its FastAPI API."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def main() -> None:
    parser = argparse.ArgumentParser(description="EchoMind local speech intelligence")
    parser.add_argument("--api", action="store_true", help="launch FastAPI instead of Gradio when both are installed")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()
    from echomind.logging_config import configure_logging

    configure_logging()
    if args.api:
        import uvicorn

        uvicorn.run("echomind.api.main:app", host=args.host, port=args.port, reload=False)
        return
    try:
        from echomind.ui.dashboard import create_dashboard

        create_dashboard().launch(server_name=args.host, server_port=args.port, show_error=True)
    except RuntimeError as error:
        print(error)
        print("Starting the dependency-light FastAPI service instead.")
        print(f"Open the interactive dashboard at http://{args.host}:{args.port}/dashboard")
        print("Install `pip install 'echomind[ui]'` if you prefer the Gradio dashboard.")
        import uvicorn

        uvicorn.run("echomind.api.main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
