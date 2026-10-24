# Local evaluation data

Place local audio and an accompanying CSV or JSONL manifest here. The project never invents labels or results.

Minimum CSV columns:

```csv
id,audio_path,reference_text,language,speaker_id,condition,intent,self_correction
sample-1,data/samples/sample.wav,"bonjour demain",fr,spk-1,clean,appointment_rescheduling,false
```

Keep recordings from the same speaker in the same split. Augmented copies must inherit the source speaker and recording identifiers.

For a compact, paired robustness benchmark in Arabic and English, download ARen:

```powershell
python scripts/download_aren.py --samples-per-language 5
python scripts/prepare_dataset.py data/evaluation/manifests/benchmark_aren.csv
python scripts/evaluate.py data/evaluation/manifests/benchmark_aren.csv --model base --output experiments/reports/benchmark_aren_base.json
python scripts/evaluate.py data/evaluation/manifests/benchmark_aren.csv --model base --ablation --output experiments/reports/benchmark_aren_base_e0_e3.json
```

The default selects five Arabic and five English utterances, balanced across
available English source corpora, in three paired conditions: clean,
telephony-bandlimited, and telephony-bandlimited with synthetic noise. This
creates 30 audio evaluations. The corpus is CC BY 4.0; preserve the row-level
source and license fields and cite TNSA AI / ARen plus upstream sources.

ARen does not provide speaker IDs, spontaneous self-correction labels, or intent
labels. Its `speaker_id` is therefore `unknown`; the generated split is not a
speaker holdout, and correction usefulness / intent accuracy remain unmeasured.
The noise condition is a published synthetic degradation, not a real noisy
recording. The small default subset is a smoke/diagnostic benchmark, not a
statistically conclusive model ranking.

For a broader clean-speech development benchmark including French, the FLEURS
downloader fetches only selected audio clips through the dataset viewer:

```powershell
python scripts/download_corpus.py --languages en fr ar --max-per-language 20 --split dev --output-manifest data/evaluation/manifests/benchmark_fleurs_dev.csv
```

`dev` maps to the official FLEURS `validation` split. The downloader samples
transcripts evenly and deterministically across each language split, preserves
the official split name in `source_split`, and validates each downloaded WAV.
FLEURS is CC BY 4.0. Individual speaker IDs are not exposed in the downloaded
metadata, so `speaker_id` remains `unknown`; do not create a random speaker split
from these rows. Keep the official validation and test splits separate.

For an independent test sample, the downloader streams the official test
archives and retains only the first requested number of unique transcripts per
language; this avoids extracting the full multi-hundred-MiB archives:

```powershell
python scripts/download_corpus.py --max-per-language 20 --split test --languages en fr ar --output-manifest data/evaluation/manifests/benchmark_fleurs_test_independent.csv
python scripts/evaluate.py data/evaluation/manifests/benchmark_fleurs_test_independent.csv --model base --ablation --output experiments/reports/benchmark_fleurs_test_base_e0_e3_warm.json
```

The public viewer cannot scan some test Parquet row groups, so test mode uses
the official archive/TSV route directly rather than substituting validation
rows. The resulting 60-clip test sample is held out from threshold tuning, but
is small and consists of clean read speech; it is not a full-split or
conversational-speech estimate. See the benchmark report for measured scores and
sampling limitations.

Validate the manifest and inspect a speaker-aware split with:

```powershell
python scripts/prepare_dataset.py data/evaluation/manifest.csv
```

The `echomind.audio.augmentation.augment_audio` helper supports seeded additive noise, speed perturbation, gain, and a limited echo-style reverberation experiment. It does not automatically create files or treat augmented copies as new speakers.
