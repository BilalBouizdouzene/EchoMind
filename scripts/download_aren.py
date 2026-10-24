"""Download a small, licensed ARen speech-evaluation subset.

ARen provides Arabic/English references in clean, telephony-bandlimited and
telephony-plus-synthetic-noise conditions. Audio stays in the repository under
data/evaluation/corpus/aren; no training data is downloaded.
"""

from __future__ import annotations

import argparse
import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path, PurePosixPath
from urllib.parse import quote

import requests

DATASET = "TNSA/Aren"
ROWS_URL = "https://datasets-server.huggingface.co/rows"
FILE_URL = "https://huggingface.co/datasets/TNSA/Aren/resolve/main/aren/"
CONDITIONS = ("clean", "tel8k", "tel8k_noisy")


def fetch_rows(condition: str) -> list[dict]:
    response = requests.get(
        ROWS_URL,
        params={"dataset": DATASET, "config": condition, "split": "train", "offset": 0, "length": 100},
        timeout=(20, 90),
    )
    response.raise_for_status()
    payload = response.json()
    rows = [item["row"] for item in payload.get("rows", [])]
    if not rows:
        raise RuntimeError(f"ARen returned no rows for condition {condition!r}: {payload}")
    return rows


def select_balanced(rows: list[dict], limit_per_language: int) -> list[dict]:
    """Round-robin source groups so a small English sample is not FLEURS-only."""
    groups: dict[str, list[dict]] = {}
    for row in rows:
        language = str(row.get("language", "")).lower()
        source = str(row.get("source", "unknown"))
        if language in {"ar", "en"} and row.get("transcription"):
            groups.setdefault(f"{language}:{source}", []).append(row)

    selected: list[dict] = []
    languages = sorted({key.split(":", 1)[0] for key in groups})
    for language in languages:
        language_groups = [groups[key] for key in sorted(groups) if key.startswith(language + ":")]
        count = 0
        position = 0
        while count < limit_per_language:
            added = False
            for group in language_groups:
                if position < len(group) and count < limit_per_language:
                    selected.append(group[position])
                    count += 1
                    added = True
            if not added:
                break
            position += 1
    return selected


def _safe_audio_path(file_name: str, condition: str, root: Path) -> tuple[str, Path]:
    relative = PurePosixPath(file_name)
    if relative.is_absolute() or ".." in relative.parts or relative.name != file_name.split("/")[-1]:
        raise ValueError(f"Unsafe ARen audio path: {file_name!r}")
    if relative.suffix.lower() != ".wav":
        raise ValueError(f"Unexpected ARen audio format: {file_name!r}")
    relative_path = Path("data/evaluation/corpus/aren") / condition / relative.name
    return relative_path.as_posix(), root / relative_path


def download_audio(row: dict, condition: str, root: Path) -> tuple[str, Path]:
    file_name = str(row["file_name"])
    relative_path, target = _safe_audio_path(file_name, condition, root)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and target.stat().st_size > 44:
        return relative_path, target

    url = FILE_URL + quote(f"data/{condition}/{PurePosixPath(file_name).name}", safe="/")
    partial = target.with_name(target.name + ".part")
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            received = 0
            with requests.get(url, stream=True, timeout=(20, 120)) as response:
                response.raise_for_status()
                expected = int(response.headers.get("content-length", "0") or 0)
                with partial.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=128 * 1024):
                        if chunk:
                            handle.write(chunk)
                            received += len(chunk)
            if expected and received != expected:
                raise RuntimeError(f"Incomplete download ({received}/{expected} bytes): {url}")
            with partial.open("rb") as handle:
                header = handle.read(12)
            if received <= 44 or header[:4] != b"RIFF" or header[8:12] != b"WAVE":
                raise RuntimeError(f"Downloaded file is not a valid WAV: {url}")
            partial.replace(target)
            return relative_path, target
        except (requests.RequestException, OSError, RuntimeError) as error:
            last_error = error
            partial.unlink(missing_ok=True)
            if attempt < 3:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Could not download {url} after four attempts: {last_error}") from last_error


def write_manifest(root: Path, rows: list[dict], output: str | None) -> Path:
    manifest = (root / output).resolve() if output else root / "data/evaluation/manifests/benchmark_aren.csv"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "id", "audio_path", "reference_text", "language", "speaker_id", "condition",
        "intent", "self_correction", "source_dataset", "source_split", "source_url", "license",
    ]
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Download a small Arabic/English ARen benchmark subset")
    parser.add_argument("--root", default=".")
    parser.add_argument("--samples-per-language", type=int, default=5)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output-manifest")
    args = parser.parse_args()
    if args.samples_per_language < 1 or args.workers < 1:
        parser.error("--samples-per-language and --workers must be positive")

    root = Path(args.root).resolve()
    reference_rows = select_balanced(fetch_rows("clean"), args.samples_per_language)
    selected_ids = {PurePosixPath(str(row["file_name"])).name for row in reference_rows}
    if not selected_ids:
        raise RuntimeError("No Arabic or English reference rows were selected")

    manifest_rows: list[dict] = []
    for condition in CONDITIONS:
        condition_rows = fetch_rows(condition)
        by_name = {PurePosixPath(str(row["file_name"])).name: row for row in condition_rows}
        missing = selected_ids.difference(by_name)
        if missing:
            raise RuntimeError(f"ARen {condition} is missing paired clips: {sorted(missing)[:5]}")
        jobs = [(by_name[name], condition) for name in sorted(selected_ids)]
        downloaded: dict[str, Path] = {}
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(download_audio, row, condition, root): row for row, _ in jobs}
            for future in as_completed(futures):
                relative_path, target = future.result()
                downloaded[relative_path] = target

        for row in reference_rows:
            name = str(row["file_name"])
            relative_path, _ = _safe_audio_path(name, condition, root)
            condition_row = by_name[PurePosixPath(name).name]
            manifest_rows.append({
                "id": f"aren_{Path(name).stem}_{condition}",
                "audio_path": relative_path,
                "reference_text": str(condition_row["transcription"]).strip(),
                "language": str(condition_row["language"]),
                "speaker_id": "unknown",
                "condition": condition,
                "intent": "",
                "self_correction": "",
                "source_dataset": f"TNSA/Aren:{condition_row.get('source', 'unknown')}",
                "source_split": "ARen/train",
                "source_url": "https://huggingface.co/datasets/TNSA/Aren",
                "license": str(condition_row.get("license", "CC-BY-4.0")),
            })
        print(f"{condition}: {len(downloaded)} clips téléchargés/vérifiés", flush=True)

    manifest = write_manifest(root, manifest_rows, args.output_manifest)
    languages = sorted({str(row["language"]) for row in reference_rows})
    print(f"Manifest: {manifest}")
    print(f"Exemples source: {len(reference_rows)} ({', '.join(languages)}); audio évalués: {len(manifest_rows)}")
    print("Attribution: TNSA AI, ARen, CC BY 4.0; voir le README du corpus pour les sources amont.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
