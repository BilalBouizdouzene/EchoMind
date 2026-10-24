"""Create reproducible noisy variants without changing speaker identity."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from echomind.audio.augmentation import augment_audio
from echomind.audio.loader import load_audio, to_mono
from echomind.audio.preprocessing import resample_audio
from echomind.evaluation.benchmark import load_manifest
from echomind.evaluation.dataset import validate_manifest

VARIANTS = {
    "noise": {"noise_std": 0.025, "condition": "noise_low"},
    "noise_strong": {"noise_std": 0.060, "condition": "noise_strong"},
    "reverb": {"reverb_decay": 0.28, "condition": "reverb"},
    "speed": {"speed": 0.92, "condition": "speed_0.92"},
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--output", default="data/evaluation/manifests/benchmark_augmented.csv")
    parser.add_argument("--audio-root", default="data/evaluation/corpus/augmented")
    parser.add_argument("--variants", default="noise,noise_strong,reverb,speed")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    rows = load_manifest(manifest_path)
    errors = validate_manifest(rows, check_files=True, base_dir=manifest_path.parent)
    if errors:
        raise SystemExit("Invalid manifest:\n" + "\n".join(errors[:20]))
    selected = [name.strip() for name in args.variants.split(",") if name.strip()]
    unknown = sorted(set(selected) - set(VARIANTS))
    if unknown:
        raise SystemExit(f"Unknown variants: {', '.join(unknown)}")

    root = Path.cwd().resolve()
    audio_root = (root / args.audio_root).resolve()
    output_path = (root / args.output).resolve()
    output_rows = list(rows)
    for row_index, row in enumerate(rows):
        source_path = Path(row["audio_path"])
        if not source_path.is_absolute():
            source_path = next(
                candidate
                for candidate in (root / source_path, manifest_path.parent / source_path)
                if candidate.is_file()
            )
        audio, sample_rate, _ = load_audio(source_path)
        mono = resample_audio(to_mono(audio), sample_rate, 16000)
        for variant_index, variant_name in enumerate(selected):
            settings = VARIANTS[variant_name]
            augmented = augment_audio(
                mono,
                16000,
                seed=row_index * 100 + variant_index,
                **{key: value for key, value in settings.items() if key != "condition"},
            )
            filename = f"{row.get('id', row_index)}__{variant_name}.wav"
            target = audio_root / str(row.get("language") or "unknown") / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            sf.write(target, augmented, 16000, subtype="PCM_16")
            derived = dict(row)
            derived.update(
                {
                    "id": f"{row.get('id', row_index)}__{variant_name}",
                    "audio_path": target.relative_to(root).as_posix(),
                    "condition": settings["condition"],
                    "source_id": row.get("id", str(row_index)),
                    "augmentation": variant_name,
                }
            )
            output_rows.append(derived)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(field for row in output_rows for field in row))
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Manifest: {output_path}")
    print(f"Rows: {len(output_rows)} (original={len(rows)}, augmented={len(output_rows) - len(rows)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
