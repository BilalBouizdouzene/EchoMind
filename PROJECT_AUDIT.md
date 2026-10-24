# EchoMind — Project Audit

Audit date: 2026-10-24

## Final disposition

EchoMind is a working local ASR research/portfolio prototype, not a reliable
self-correcting product. The independent FLEURS test sample shows one
reference-improving automatic correction in 60 clips and no harmful correction,
but this is too little evidence for a reliability claim; the correction has not
received human audio review. Present the feature as experimental selective
re-decoding. Frozen artifacts and final evidence are in
[FINAL_VALIDATION.md](FINAL_VALIDATION.md).

## Scope

The project scope is now English, French and standard Arabic. Dialect-specific
datasets, script-specific transliteration, lexical rules and UI options were removed.
The compact ARen subset remains available (10 Arabic/English utterances × 3
conditions = 30 WAVs). A separate FLEURS development manifest contains 60 real
clips: 20 each for English, French and Arabic, from the official validation
split. A separate 60-clip FLEURS test manifest has now been downloaded and
evaluated with `base`; FLEURS individual speaker IDs are unavailable, and the
source split is preserved. The viewer API hit a Parquet scan limit/time-out, so
the test subset was streamed from official files.

## Runtime snapshot

Windows; Python 3.12.14; faster-whisper 1.2.1; CTranslate2 4.8.3; inference on
CPU with INT8. At the time of inspection, the machine reported 15.64 GiB RAM
total and 5.67 GiB available (available memory is a transient snapshot).

## Current status

| Feature | Status | Evidence |
| --- | --- | --- |
| Local audio loading and preprocessing | Implemented and tested | WAV loading, mono conversion, resampling, quality checks and VAD are covered by tests |
| Faster-whisper CPU INT8 adapter | Tested on 30 ARen files, 60 FLEURS validation clips per model, and 60 FLEURS test clips with `base`; all test outputs were non-empty | Backend is `faster-whisper`; no demo engine used; row-level JSON records hypotheses, metrics and correction evidence |
| tiny/base/small models | Compared on the same 60 FLEURS clips; `small` had best WER but RTF 1.552, `base` RTF 0.314, and `tiny` was markedly less accurate | See `experiments/reports/benchmark_fleurs_dev_summary.md`; validation/model-selection data only, not a final held-out score |
| Base model | Downloaded and loaded locally in CPU/INT8 mode; SHA-256 verified against Hugging Face metadata | `scripts/download_models.py --model base --download` reports “Model is ready”; measured on ARen and FLEURS |
| English/French/Arabic language hints | Implemented | Dashboard and Gradio options expose `auto`, `en`, `fr`, `ar` |
| Language detection heuristics | Implemented and unit-tested | Lexicons are limited to English, French and standard Arabic |
| Uncertainty scoring | Heuristic and conservative gate tested on a separate FLEURS test sample; still uncalibrated | The high band starts at 0.30; acoustic acceptance requires two alternative configurations plus at least +0.05 target-region mean word confidence, or a material verified-context margin. E3 accepted 1/60 test corrections: reference-based useful 1, harmful 0; this is too few to establish reliability |
| Runtime configuration loading | Incomplete | Runtime options use code defaults. YAML files under `config/` are not loaded; `config/thresholds.yaml` is stale (`medium=0.40`, `high=0.65`) versus the effective heuristic defaults (`medium=0.20`, `high=0.30`) |
| Selective re-decoding | Implemented and tested | Region and compute budgets are enforced |
| Contextual reranking and provenance | Implemented | Candidate decisions preserve reasons and evidence |
| Error annotation workflow | Implemented; 120 FLEURS dev/test records generated, pending human review | Dev template remains unreviewed; test template includes baseline/final hypotheses and system correction provenance, while segment labels remain empty |
| Calibration | Utility available, not validated | No calibration was fit: annotation templates are unreviewed and only 60 held-out clips are available; raw scores are heuristic, not probabilities |
| FastAPI dashboard | Real-audio route and browser dashboard tested with `base` | FLEURS test WAV: `/dashboard/analyze` returned HTTP 200, `faster-whisper`, French, 3 segments, 1 correction, metrics/timeline HTML, no warnings |
| Rule-based self-correction markers | Implemented and unit-tested; not validated on real conversational audio | Recognizes text markers including `pardon`, `plutôt`, and `je voulais dire`; do not claim reliable spoken self-correction |
| ARen robustness subset | Downloaded and tested | 10 source utterances × 3 paired conditions; [CC BY 4.0 dataset card](https://huggingface.co/datasets/TNSA/Aren/blob/main/aren/README.md); Arabic and English only |
| FLEURS corpus downloader | Implemented and used for dev and test | Test split streams official audio and extracts only requested clips when the viewer is unavailable; all 60 test WAVs passed validation at 16 kHz mono |
| Noise/reverb/speed augmentation | Implemented | Augmented copies retain source IDs and references |
| Speaker-aware splitting | Implemented with a guard against unknown IDs | Unknown IDs now produce an explicit warning instead of a fake split; FLEURS official validation/test boundary is preserved |
| E0–E3 ablation runner | Implemented and benchmarked with real `base` inference on ARen and a separate FLEURS test sample | The runner now preloads and shares one model across conditions; model load time is reported separately, preventing the previous cold-start/condition timing confound |
| Native WebSocket streaming | Incomplete | Current endpoint remains a chunked placeholder |
| Optional Gradio UI | Implemented, environment-dependent | Requires the optional Gradio extra |

## Data policy

The Git repository does not track downloaded audio or generated JSON results.
The local ARen subset and reports are retained in the workspace; manifest rows
preserve the source URL and license. Evaluation records language, speaker,
condition and split, and marks unavailable speaker IDs as unknown.

## Reproduction

```powershell
python scripts/download_aren.py --samples-per-language 5
python scripts/prepare_dataset.py data/evaluation/manifests/benchmark_aren.csv
python scripts/evaluate.py data/evaluation/manifests/benchmark_aren.csv --model base --output experiments/reports/benchmark_aren_base.json
python scripts/evaluate.py data/evaluation/manifests/benchmark_aren.csv --model base --ablation --output experiments/reports/benchmark_aren_base_e0_e3.json
python scripts/evaluate.py data/evaluation/manifests/benchmark_aren.csv --model tiny --output experiments/reports/benchmark_aren_tiny.json
python scripts/download_corpus.py --max-per-language 20 --split test --languages en fr ar --output-manifest data/evaluation/manifests/benchmark_fleurs_test_independent.csv
python scripts/evaluate.py data/evaluation/manifests/benchmark_fleurs_test_independent.csv --model base --ablation --output experiments/reports/benchmark_fleurs_test_base_e0_e3_warm.json
python scripts/evaluate.py data/evaluation/manifests/benchmark_fleurs_test_independent.csv --model base --output experiments/reports/benchmark_fleurs_test_base_e3_rows.json
python scripts/create_error_annotation_template.py data/evaluation/manifests/benchmark_fleurs_test_independent.csv --report experiments/reports/benchmark_fleurs_test_base_e3_rows.json --output data/evaluation/annotations/error_annotations_fleurs_test.jsonl
python app.py --api --port 8000
```

## Measured base benchmark (ARen subset)

See `experiments/reports/benchmark_aren_base_recheck.json` for row-level hypotheses and
the complete output. WER/CER without the `_macro` suffix are corpus micro
averages; `_macro` fields are arithmetic means over individual clips.

| Measure | Result |
| --- | ---: |
| Evaluated / measured / empty outputs | 30 / 30 / 0 |
| Corpus WER / normalized WER | 58.9% / 57.5% |
| Corpus CER / normalized CER | 31.7% / 29.9% |
| Mean latency / p95 latency | 2,858 ms / 4,597 ms |
| Mean RTF | 0.605 |
| Mean audio fraction re-decoded | 0.74% |
| Accepted / useful / harmful corrections | 0 / 0 / 0 |

The cached `model.bin` is 145,217,532 bytes and its SHA-256 is
`d01c3014881c9c6f3133c182f3d2887eb6ca1c789a7538c5c007196857a0a6a9`.

Historical verification for that ARen run: 26 tests passed. Current full-suite
verification after the test-split downloader, annotation evidence and shared
ablation runner updates: 36 tests passed; Ruff passed for project source, scripts
and tests. A real WAV sent to FastAPI `/dashboard/analyze` with `model_name=base`
returned HTTP 200, two ASR segments, and metrics/timeline HTML.

The noisy condition is deliberately difficult: corpus micro normalized WER is
101.0% on this ten-clip subset, versus 29.0% clean and 42.0% telephony-bandlimited.
By language, normalized micro WER is 48% Arabic and 72% English (15 audio
conditions per language).

## E0–E3 and model comparison

The initial ARen runs and tiny/base/small FLEURS validation comparison remain
documented above and in `experiments/reports/benchmark_aren_summary.md` and
`experiments/reports/benchmark_fleurs_dev_summary.md`. The latest ARen
confidence-gate rerun accepted one reference-improving correction in 30 files;
normalized WER moved 57.50% → 57.29%. This is a small diagnostic set, not an
independent holdout.

On the separate FLEURS test sample, the `base` E0/E1 baseline normalized WER/CER
was 28.20% / 10.67%. E2/E3 ended at 27.86% / 10.49%, with 1 useful and 0
harmful accepted corrections. The model was loaded once and shared across all
four conditions; the 1,162 ms weight-load time is reported separately. E3 mean
latency was 1.98 s, p95 2.89 s, RTF 0.195, and mean re-decoded audio fraction
0.91%. Full controlled output is
`experiments/reports/benchmark_fleurs_test_base_e0_e3_warm.json`; per-example
hypotheses and correction provenance are in
`experiments/reports/benchmark_fleurs_test_base_e3_rows.json`.

E3 normalized WER by language on this small sample: Arabic 44.28%, English
11.82%, French 28.36%. One French correction changed a bad segment into the
reference-aligned phrase; it reduced that clip's normalized WER 19.35% → 3.23%.
This demonstrates a real beneficial example, not reliable generalization.

## FLEURS development model comparison

On 60 official FLEURS validation clips (20 per language), all three models
produced measured, non-empty outputs through the real faster-whisper backend.
`tiny` WER / normalized WER was 56.60% / 56.15%; `base` 29.06% / 28.07%; and
`small` 15.34% / 14.08%. Mean latency / RTF was 1.50 s / 0.159, 3.03 s / 0.314,
and 14.78 s / 1.552 respectively. Normalized WER for `small` was 27.59% Arabic,
6.38% English and 10.48% French. Details are in
`experiments/reports/benchmark_fleurs_dev_summary.md` and its three row-level
JSON reports.

A fresh paired Arabic-only validation run on the same 20 validation WAVs scored
`base` at 51.19% normalized WER / 17.61% normalized CER and `small` at 27.59% /
7.20%. Mean RTF was 0.179 for `base` and 0.563 for `small`; both had 20 measured
outputs and no accepted corrections. Reports are
`experiments/reports/benchmark_fleurs_dev_ar_base.json` and
`experiments/reports/benchmark_fleurs_dev_ar_small.json`. This remains
development/model-selection evidence.

In the initial pre-revision FLEURS validation runs, no clip triggered re-decoding.
For `small`, 45/60 clips had non-zero normalized WER, while the maximum raw score
was 0.32 against the former 0.65 high threshold. The raw-score diagnostic had
AUROC 0.339, ECE 0.613 and Brier 0.580 (raw heuristic, not probability). The
0.05 word-confidence margin was selected after inspecting that validation set;
the independent test sample is held out from that threshold selection. The
annotation templates still need human segment review before calibration claims.

## Important evaluation limits

ARen supplies no speaker IDs, intent labels or spontaneous self-correction
labels. Its `speaker_id=unknown` is not a speaker-disjoint holdout; the splitter
now explicitly refuses such a split. FLEURS provides a separate official test
split, but these 60 sampled files do not expose individual speaker IDs. The
sample uses the first 20 unique archive entries in each locale, selected
deterministically by the same streaming method. FLEURS is clean, read speech and does not validate
conversational, spontaneous self-correction, code-switching or real-world noisy
audio. The single useful correction on test is not enough to establish a
reliable improvement rate. Calibration still requires reviewed segment-level
labels; the 0.30 threshold remains an empirical heuristic, not a calibrated
production confidence threshold.

The only FLEURS test correction candidate is
`fleurs_fr_test_10603531439273760949` at
`data/evaluation/corpus/fleurs/fr/test/10603531439273760949.wav`. Against the
supplied transcript, the baseline `Alivellontant.` becomes `elle, il y a
longtemps.` and the row's normalized WER falls from 19.35% to 3.23%. This is
reference-based automatic scoring only. No human audio review was completed;
the annotation record remains `unreviewed`.
