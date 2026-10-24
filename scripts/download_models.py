"""Documented opt-in model downloader for faster-whisper."""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in faster-whisper model check/download")
    parser.add_argument("--model", default="tiny", choices=["tiny", "base", "small"])
    parser.add_argument("--download", action="store_true", help="instantiate the model and allow the package to download weights")
    args = parser.parse_args()
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("faster-whisper is not installed. Install with: pip install 'echomind[asr]'")
        return 2
    if not args.download:
        print(f"faster-whisper is available. No weights downloaded. Re-run with --download --model {args.model} to opt in.")
        return 0
    print(f"Opting in to local model preparation for {args.model}; this may download model files.")
    WhisperModel(args.model, device="cpu", compute_type="int8")
    print("Model is ready for local CPU inference.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
