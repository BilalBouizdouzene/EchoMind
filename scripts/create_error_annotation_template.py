"""Create an auditable, explicitly unreviewed human annotation template."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from echomind.evaluation.benchmark import load_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument(
        "--output",
        default="data/evaluation/annotations/error_annotations.jsonl",
    )
    parser.add_argument(
        "--report",
        help="optional row-level benchmark JSON to include system hypotheses and correction provenance",
    )
    args = parser.parse_args()
    rows = load_manifest(args.manifest)
    report_rows = {}
    if args.report:
        report_data = json.loads(Path(args.report).read_text(encoding="utf-8"))
        report_rows = {
            str(row.get("id", row.get("audio_path"))): row
            for row in report_data.get("rows", [])
        }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            record = build_annotation_record(
                row,
                report_rows.get(str(row.get("id", row.get("audio_path")))),
            )
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Annotation template: {output.resolve()}")
    print(f"Rows requiring manual review: {len(rows)}")
    return 0


def build_annotation_record(row: dict, evaluation: dict | None = None) -> dict:
    """Build an explicitly unreviewed human-annotation record."""
    evaluation = evaluation or {}
    return {
        "id": row.get("id", row.get("audio_path")),
        "audio_path": row.get("audio_path"),
        "speaker_id": row.get("speaker_id", "unknown"),
        "language": row.get("language", "unknown"),
        "reference_text": row.get("reference_text", ""),
        "baseline_hypothesis": evaluation.get("baseline_hypothesis", ""),
        "final_hypothesis": evaluation.get("hypothesis", ""),
        "correction_applied": evaluation.get("correction_applied"),
        "automatic_correction_outcome": evaluation.get("correction_outcome"),
        "system_corrections": evaluation.get("corrections", []),
        "status": "unreviewed",
        "segments": [],
        "reviewer": "",
        "notes": "",
    }


if __name__ == "__main__":
    raise SystemExit(main())
