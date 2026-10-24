"""Evaluate a local annotated CSV/JSONL manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from echomind.evaluation.ablation import run_ablation
from echomind.evaluation.benchmark import run_benchmark
from echomind.pipeline.orchestrator import EchoMindPipeline, PipelineOptions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--ablation", action="store_true")
    parser.add_argument(
        "--model",
        choices=("tiny", "base", "small"),
        default="tiny",
        help="local faster-whisper model used for every evaluation condition (default: tiny)",
    )
    parser.add_argument("--output", type=Path, help="write the JSON report to this local path")
    args = parser.parse_args()
    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        parser.error(
            f"Manifest introuvable: {manifest_path}. "
            "Téléchargez d'abord le corpus avec scripts/download_corpus.py."
        )
    options = PipelineOptions(model_name=args.model)
    report = (
        run_ablation(manifest_path, base_options=options)
        if args.ablation
        else run_benchmark(manifest_path, pipeline=EchoMindPipeline(options=options))
    )
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Report written to {args.output.resolve()}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
