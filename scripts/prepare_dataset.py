"""Validate a local manifest and optionally report a speaker-aware split."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from echomind.evaluation.benchmark import load_manifest
from echomind.evaluation.dataset import speaker_aware_split, validate_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--allow-missing-files", action="store_true")
    args = parser.parse_args()
    rows = load_manifest(args.manifest)
    errors = validate_manifest(rows, check_files=not args.allow_missing_files)
    try:
        split = speaker_aware_split(rows)
        split_summary = {
            "speaker_split_available": True,
            "train": len(split["train"]),
            "test": len(split["test"]),
        }
    except ValueError as error:
        split_summary = {
            "speaker_split_available": False,
            "train": 0,
            "test": 0,
            "warning": str(error),
        }
    print(json.dumps({"rows": len(rows), "errors": errors, **split_summary}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
