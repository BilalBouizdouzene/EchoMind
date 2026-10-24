"""Download a deterministic, small FLEURS subset from official Hugging Face files.

Development audio is fetched one clip at a time from the dataset viewer. For the
test split, the official archive is streamed and only the requested WAV files
are retained, avoiding a full multi-hundred-MiB extraction.
"""

from __future__ import annotations

import argparse
import csv
import io
import shutil
import sys
import tarfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
import soundfile as sf

FLEURS_REPO = "google/fleurs"
FLEURS_RESOLVE_URL = "https://huggingface.co/datasets/google/fleurs/resolve/main"
FLEURS_LANGUAGES = {"en_us": "en", "fr_fr": "fr", "ar_eg": "ar"}
DATASET_VIEWER_ROWS_URL = "https://datasets-server.huggingface.co/rows"
PAGE_SIZE = 100
FIELDS = [
    "id",
    "audio_path",
    "reference_text",
    "language",
    "speaker_id",
    "condition",
    "intent",
    "self_correction",
    "source_dataset",
    "source_split",
    "source_url",
    "license",
]


def _request_page(
    session: requests.Session, config: str, split: str, offset: int, length: int
) -> dict:
    params = {
        "dataset": FLEURS_REPO,
        "config": config,
        "split": split,
        "offset": offset,
        "length": length,
    }
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = session.get(DATASET_VIEWER_ROWS_URL, params=params, timeout=(15, 90))
            payload = response.json()
            if response.status_code >= 500:
                detail = str(payload.get("error", response.text))
                if "Scan size limit exceeded" in detail:
                    raise RuntimeError(
                        f"FLEURS {config}/{split}: the public viewer cannot slice this split "
                        "because its Parquet row group exceeds the server scan limit. "
                        "No substitute split was downloaded."
                    )
                raise requests.HTTPError(f"HTTP {response.status_code}: {detail}")
            response.raise_for_status()
            if payload.get("error"):
                raise RuntimeError(f"FLEURS viewer error for {config}/{split}: {payload['error']}")
            return payload
        except RuntimeError:
            raise
        except (requests.RequestException, ValueError) as error:
            last_error = error
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(
        f"Could not read FLEURS metadata for {config}/{split} after three attempts: {last_error}"
    )


def _fetch_split_rows(session: requests.Session, config: str, split: str) -> list[dict]:
    first = _request_page(session, config, split, offset=0, length=PAGE_SIZE)
    total = int(first.get("num_rows_total", 0))
    rows = [item["row"] for item in first.get("rows", [])]
    for offset in range(len(rows), total, PAGE_SIZE):
        page = _request_page(
            session,
            config,
            split,
            offset=offset,
            length=min(PAGE_SIZE, total - offset),
        )
        rows.extend(item["row"] for item in page.get("rows", []))
    if not rows:
        raise RuntimeError(f"No FLEURS rows returned for {config}/{split}")
    return rows


def _read_fleurs_tsv(session: requests.Session, config: str, split: str) -> dict[str, dict]:
    """Read FLEURS' small TSV metadata file, keyed by the audio filename."""
    url = f"{FLEURS_RESOLVE_URL}/data/{config}/{split}.tsv?download=true"
    response = session.get(url, timeout=(15, 90))
    response.raise_for_status()
    rows = csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter="\t")
    metadata: dict[str, dict] = {}
    for fields in rows:
        # FLEURS TSV columns are id, filename, transcript, normalized transcript,
        # character sequence, sample count, and gender. Some mirrors add a header.
        if len(fields) < 3 or fields[0].strip().lower() == "id":
            continue
        filename = fields[1].strip()
        transcript = fields[2].strip()
        if filename and transcript:
            metadata[Path(filename).name] = {
                "id": Path(filename).stem,
                "raw_transcription": transcript,
            }
    if not metadata:
        raise RuntimeError(f"FLEURS {config}/{split}: no transcript rows found in the official TSV")
    return metadata


def _download_archive_subset(
    root: Path,
    session: requests.Session,
    config: str,
    language: str,
    split: str,
    limit: int,
) -> list[dict[str, str]]:
    """Stream a FLEURS tarball and retain only up to `limit` unique utterances."""
    metadata = _read_fleurs_tsv(session, config, split)
    archive_url = f"{FLEURS_RESOLVE_URL}/data/{config}/audio/{split}.tar.gz"
    output_dir = root / "data" / "evaluation" / "corpus" / "fleurs" / language / split
    output_dir.mkdir(parents=True, exist_ok=True)
    seen_transcripts: set[str] = set()
    rows_out: list[dict[str, str]] = []

    def append_manifest_row(filename: str, item: dict, target: Path) -> None:
        transcript = item["raw_transcription"]
        seen_transcripts.add(transcript)
        rows_out.append(
            {
                "id": f"fleurs_{language}_{split}_{Path(filename).stem}",
                "audio_path": target.relative_to(root).as_posix(),
                "reference_text": transcript,
                "language": language,
                "speaker_id": "unknown",
                "condition": "clean",
                "intent": "",
                "self_correction": "",
                "source_dataset": f"{FLEURS_REPO}:{config}",
                "source_split": split,
                "source_url": "https://huggingface.co/datasets/google/fleurs",
                "license": "CC-BY-4.0",
            }
        )

    with session.get(archive_url, stream=True, timeout=(15, 180)) as response:
        response.raise_for_status()
        with tarfile.open(fileobj=response.raw, mode="r|gz") as archive:
            for member in archive:
                filename = Path(member.name).name
                item = metadata.get(filename)
                if not member.isfile() or not filename.lower().endswith(".wav") or not item:
                    continue
                transcript = item["raw_transcription"]
                if transcript in seen_transcripts:
                    continue
                target = output_dir / filename
                already_valid = False
                if target.is_file():
                    try:
                        already_valid = sf.info(target).frames > 0
                    except (OSError, RuntimeError):
                        already_valid = False
                if not already_valid:
                    source = archive.extractfile(member)
                    if source is None:
                        continue
                    partial = target.with_name(target.name + ".part")
                    try:
                        with source, partial.open("wb") as handle:
                            shutil.copyfileobj(source, handle)
                        info = sf.info(partial)
                        if info.frames <= 0 or info.samplerate <= 0 or info.channels <= 0:
                            raise ValueError(f"Invalid audio member: {filename}")
                        partial.replace(target)
                    except (OSError, RuntimeError, ValueError) as error:
                        partial.unlink(missing_ok=True)
                        raise RuntimeError(f"Could not extract/validate {filename}: {error}") from error

                append_manifest_row(filename, item, target)
                print(f"  {language}: extrait test {len(rows_out)}/{limit}", flush=True)
                if len(rows_out) >= limit:
                    break

    if not rows_out:
        raise RuntimeError(f"FLEURS {config}/{split}: no matching audio found in the official archive")
    return rows_out


def _select_rows(rows: list[dict], limit: int) -> list[dict]:
    """Choose unique transcript rows evenly across a source split."""
    if limit < 1:
        raise ValueError("limit must be at least one")
    unique: list[dict] = []
    seen_text: set[str] = set()
    for row in rows:
        text = str(row.get("raw_transcription") or row.get("transcription") or "").strip()
        if text and text not in seen_text:
            unique.append(row)
            seen_text.add(text)
    if len(unique) <= limit:
        return unique
    if limit == 1:
        return [unique[len(unique) // 2]]
    indices = [round(index * (len(unique) - 1) / (limit - 1)) for index in range(limit)]
    return [unique[index] for index in indices]


def _audio_source(row: dict) -> str:
    audio = row.get("audio")
    if isinstance(audio, list):
        audio = next((item for item in audio if isinstance(item, dict)), None)
    if isinstance(audio, dict) and audio.get("src"):
        return str(audio["src"])
    raise ValueError(f"FLEURS row {row.get('id')} has no downloadable audio URL")


def _download_audio(session: requests.Session, url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        try:
            info = sf.info(target)
            if info.frames > 0:
                return
        except (OSError, RuntimeError):
            target.unlink(missing_ok=True)
    partial = target.with_name(target.name + ".part")
    try:
        with session.get(url, stream=True, timeout=(15, 90)) as response:
            response.raise_for_status()
            with partial.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=128 * 1024):
                    if chunk:
                        handle.write(chunk)
        info = sf.info(partial)
        if info.frames <= 0 or info.samplerate <= 0 or info.channels <= 0:
            raise ValueError(f"Downloaded audio is empty or invalid: {target.name}")
        partial.replace(target)
    except (requests.RequestException, OSError, RuntimeError, ValueError) as error:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"Could not download/validate {target.name}: {error}") from error


def _download_audio_task(url: str, target: Path) -> None:
    with requests.Session() as session:
        session.headers.update({"User-Agent": "EchoMind-evaluation/0.1"})
        _download_audio(session, url, target)


def download_fleurs(
    root: Path,
    limit: int,
    split: str,
    languages: list[str],
    session: requests.Session | None = None,
) -> list[dict[str, str]]:
    api_split = "validation" if split == "dev" else split
    active_session = session or requests.Session()
    active_session.headers.update({"User-Agent": "EchoMind-evaluation/0.1"})
    rows_out: list[dict[str, str]] = []
    for config, language in FLEURS_LANGUAGES.items():
        if language not in languages:
            continue
        print(f"Lecture des métadonnées FLEURS {language}/{api_split}…", flush=True)
        if split == "test":
            print(
                f"  préparation du split test officiel {language} depuis l'archive en flux…",
                flush=True,
            )
            rows_out.extend(
                _download_archive_subset(
                    root, active_session, config, language, api_split, limit
                )
            )
            continue
        rows = _select_rows(_fetch_split_rows(active_session, config, api_split), limit)
        output_dir = root / "data" / "evaluation" / "corpus" / "fleurs" / language / api_split
        tasks = []
        for position, item in enumerate(rows, 1):
            item_id = f"fleurs_{language}_{api_split}_{item.get('id', position)}"
            target = output_dir / f"{item.get('id', position)}.wav"
            pair = (position, item_id, item, target)
            tasks.append((pair, _audio_source(item)))

        def download(pair: tuple[int, str, dict, Path], url: str) -> tuple[int, dict[str, str]]:
            position, item_id, item, target = pair
            _download_audio_task(url, target)
            row_manifest = {
                "id": item_id,
                "audio_path": target.relative_to(root).as_posix(),
                "reference_text": str(
                    item.get("raw_transcription") or item.get("transcription") or ""
                ).strip(),
                "language": language,
                "speaker_id": "unknown",
                "condition": "clean",
                "intent": "",
                "self_correction": "",
                "source_dataset": f"{FLEURS_REPO}:{config}",
                "source_split": api_split,
                "source_url": "https://huggingface.co/datasets/google/fleurs",
                "license": "CC-BY-4.0",
            }
            return position, row_manifest

        ordered_rows: dict[int, dict[str, str]] = {}
        with ThreadPoolExecutor(max_workers=min(4, len(rows))) as executor:
            pending = {
                executor.submit(download, pair, url): pair[0]
                for pair, url in tasks
            }
            for done, future in enumerate(as_completed(pending), 1):
                position, row_manifest = future.result()
                ordered_rows[position] = row_manifest
                print(f"  {language}: clip {done}/{len(rows)} validé", flush=True)
        rows_out.extend(ordered_rows[index] for index in sorted(ordered_rows))
        print(f"FLEURS {language}/{api_split}: {len(ordered_rows)} clips ready", flush=True)
    return rows_out


def write_manifest(root: Path, rows: list[dict[str, str]], output_path: str | None = None) -> Path:
    manifest = (
        (root / output_path).resolve()
        if output_path
        else root / "data" / "evaluation" / "manifests" / "benchmark_multilingual.csv"
    )
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download a compact, balanced FLEURS subset (one audio clip at a time)"
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--max-per-language", type=int, default=20)
    parser.add_argument(
        "--split",
        choices=["dev", "validation", "test"],
        default="dev",
        help="dev is an alias for FLEURS validation; test stays a separate official split",
    )
    parser.add_argument(
        "--languages",
        nargs="+",
        choices=sorted(FLEURS_LANGUAGES.values()),
        default=list(FLEURS_LANGUAGES.values()),
        help="languages to download; default: en fr ar",
    )
    parser.add_argument(
        "--output-manifest",
        help="write the manifest to this path instead of benchmark_multilingual.csv",
    )
    args = parser.parse_args()
    if args.max_per_language < 1:
        parser.error("--max-per-language must be at least 1")
    root = Path(args.root).resolve()
    try:
        rows = download_fleurs(root, args.max_per_language, args.split, args.languages)
        manifest = write_manifest(root, rows, args.output_manifest)
    except (OSError, RuntimeError, requests.RequestException, ValueError) as error:
        print(f"Erreur: {error}", file=sys.stderr)
        return 1
    print(f"Manifest: {manifest}")
    print(f"Total clips: {len(rows)}")
    print("Source FLEURS: CC BY 4.0; speaker_id absent, source split preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
