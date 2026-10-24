"""Manifest validation and speaker-aware split helpers."""

from __future__ import annotations

import random
from collections import defaultdict
from pathlib import Path

REQUIRED_COLUMNS = {"audio_path", "reference_text"}


def validate_manifest(rows: list[dict], check_files: bool = True, base_dir: str | Path | None = None) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    root = Path(base_dir).resolve() if base_dir else Path.cwd()
    for index, row in enumerate(rows, 1):
        missing = sorted(column for column in REQUIRED_COLUMNS if not row.get(column))
        if missing:
            errors.append(f"row {index}: missing {', '.join(missing)}")
        row_id = str(row.get("id", index))
        if row_id in seen_ids:
            errors.append(f"row {index}: duplicate id {row_id}")
        seen_ids.add(row_id)
        if check_files and row.get("audio_path"):
            audio_path = Path(row["audio_path"])
            candidates = [audio_path] if audio_path.is_absolute() else [root / audio_path, Path.cwd() / audio_path]
            if not any(candidate.is_file() for candidate in candidates):
                errors.append(f"row {index}: audio file does not exist: {row['audio_path']}")
    return errors


def speaker_aware_split(rows: list[dict], seed: int = 0, test_fraction: float = 0.2) -> dict[str, list[dict]]:
    """Split complete speaker groups, preventing augmented-source leakage."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        speaker = str(row.get("speaker_id") or "").strip()
        if speaker.casefold() in {"", "unknown", "none", "null", "n/a", "na"}:
            raise ValueError(
                "Cannot make a speaker-disjoint split: at least one row has no verified speaker_id. "
                "Keep the source-provided split or obtain speaker annotations."
            )
        groups[speaker].append(row)
    speakers = list(groups)
    random.Random(seed).shuffle(speakers)
    test_count = max(1, round(len(speakers) * test_fraction)) if speakers else 0
    test_speakers = set(speakers[:test_count])
    test = [row for speaker in test_speakers for row in groups[speaker]]
    train = [row for speaker in speakers if speaker not in test_speakers for row in groups[speaker]]
    return {"train": train, "test": test}
