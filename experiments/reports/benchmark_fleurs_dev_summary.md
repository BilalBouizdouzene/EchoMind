# FLEURS multilingual development benchmark

Run date: 2026-10-23  
Manifest: `data/evaluation/manifests/benchmark_fleurs_dev.csv`  
Source: [Google FLEURS](https://huggingface.co/datasets/google/fleurs), CC BY 4.0. The [FLEURS paper](https://arxiv.org/abs/2205.12446) describes speaker-disjoint source splits.  
Split: official `validation` (the downloader's `--split dev` alias).  
Selection: 20 distinct transcripts per language, sampled evenly and deterministically.  
Audio: 60/60 valid WAV files, mono, 16 kHz; 20 each for English, French and Arabic.  
Inference: local faster-whisper, CPU/INT8; no demo/simulation backend.

## Model comparison

All three models used the same 60 rows and the complete EchoMind pipeline (E3).
The pipeline accepted every baseline transcript, so the final WER/CER equals
the ASR baseline for all three models.

| Model | Measured | WER | Normalized WER | CER | Normalized CER | Mean latency | p95 latency | RTF | Empty outputs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| tiny | 60/60 | 56.60% | 56.15% | 31.65% | 30.59% | 1,504 ms | 1,740 ms | 0.159 | 0 |
| base | 60/60 | 29.06% | 28.07% | 12.20% | 10.73% | 3,029 ms | 4,891 ms | 0.314 | 0 |
| small | 60/60 | 15.34% | 14.08% | 6.42% | 4.56% | 14,783 ms | 16,702 ms | 1.552 | 0 |

### Normalized WER by language

| Model | Arabic | English | French |
| --- | ---: | ---: | ---: |
| tiny | 64.46% | 15.49% | 87.00% |
| base | 51.19% | 10.02% | 26.42% |
| small | 27.59% | 6.38% | 10.48% |

`small` is the accuracy choice on this clean, read-speech development subset,
but its mean RTF is 1.552, so it is slower than real time on this CPU. `base`
is the practical interactive compromise here (RTF 0.314), with materially
higher error, especially in Arabic. `tiny` is too inaccurate for serious use
on this sample, particularly French. These results do not establish performance
on conversational speech or unseen speakers.

## Initial corrections and uncertainty run (before gate revision)

| Model | Accepted corrections | Useful | Harmful | Audio re-decoded | Decisions |
| --- | ---: | ---: | ---: | ---: | --- |
| tiny | 0 | 0 | 0 | 0.00% | ACCEPT 60/60 |
| base | 0 | 0 | 0 | 0.00% | ACCEPT 60/60 |
| small | 0 | 0 | 0 | 0.00% | ACCEPT 60/60 |

On `small`, normalized WER is nonzero for 45/60 clips, yet the largest raw
uncertainty score is only 0.32. The original 0.65 high threshold therefore
triggered no re-decodes. Its raw-score diagnostic reported AUROC 0.339, ECE
0.613 and Brier 0.580 for utterance-level raw-WER labels; these are not
calibrated probabilities or segment-level error labels.

## Selective-correction follow-up (base, after gate revision)

The high-band gate was lowered to 0.30 to match the observed heuristic score
range. An alternative is now accepted only when two bounded decoding
configurations agree and target-region mean word confidence improves by at
least 0.05, or when verified context provides a material reranking margin.
The original transcript remains the fallback. This is a conservative heuristic,
not a calibrated probability.

Real CPU/INT8 faster-whisper E3 evaluation on the same 60 FLEURS validation
clips (`experiments/reports/benchmark_fleurs_dev_base_confidence_gate.json`):

| Measure | Result |
| --- | ---: |
| Clips measured | 60/60 |
| Accepted / useful / harmful corrections | 1 / 1 / 0 |
| Normalized WER, baseline → final | 28.07% → 27.92% |
| Normalized CER, baseline → final | 10.73% → 10.73% |
| Mean latency / p95 latency | 2,076 ms / 3,548 ms |
| Mean RTF | 0.216 |
| Mean audio re-decoded | 0.71% |

The one accepted correction was on French clip `fleurs_fr_validation_1538`:
normalized WER changed from 30.00% to 23.33%; CER stayed 13.40%. The earlier
consensus-only pass had accepted two corrections, one harmful. The confidence
gate rejected that harmful alternative on this validation set. One successful
example does not establish general correction quality. The 0.05 confidence
margin was selected after inspecting outcomes on this same validation subset,
so these follow-up metrics are exploratory and potentially optimistic, not an
unbiased held-out estimate. Reviewed segment labels and an independent test
split are required before claiming general correction quality.

The 60-row annotation template is
`data/evaluation/annotations/error_annotations_fleurs_dev.jsonl`; all records
remain `unreviewed`. It does not invent segment labels. The references can
support a future auditable alignment, but a segment-level calibration target
still needs reviewed alignment and a separate evaluation split.

## Split and evidence limits

FLEURS' source splits are speaker-disjoint according to its dataset paper, but
this export does not expose individual speaker IDs; the manifest correctly
keeps `speaker_id=unknown` and retains `source_split=validation`. The public
viewer failed to extract `test` because scanning its Parquet row group exceeded
the 300 MB limit. No test clips were substituted, and these validation scores
must be treated as development/model-selection evidence, not final held-out
performance. The test archives are hundreds of MiB each and a bounded 1 MiB
transfer probe was slow, so they were not downloaded in this run.

Per-model row-level reports:

- `benchmark_fleurs_dev_tiny.json`
- `benchmark_fleurs_dev_base.json`
- `benchmark_fleurs_dev_small.json`

## Independent FLEURS test subset — base CPU/INT8 (2026-10-24)

The official `test` split was downloaded separately from the `validation` data
used to adjust the uncertainty threshold. The test manifest contains 60 valid
16 kHz mono WAV files, 20 per language, all marked `source_split=test` and
`CC-BY-4.0`; the public export provides no individual speaker IDs. The small
sample is not a full-split estimate. Selection is deterministic and uniform in
method: the first 20 unique transcripts in each official test archive are
streamed and retained. These are clean, read sentences—not spontaneous, noisy,
or code-switched speech. Manifest SHA-256:
`BA1C7CEE70A583B2EC051685A59CB1A93911DD21636B7DB3A1A736DF822E9E35`.

Controlled E0–E3 benchmark: the `base` model was loaded once (1,162.04 ms, reported
separately and excluded from per-condition latency) and shared across all four
conditions. All conditions produced the same baseline ASR scores, confirming
the ablation changes did not alter the source hypotheses.

| Condition | Normalized WER, final | Normalized CER, final | Corrections applied / useful / harmful | Mean latency | p95 | RTF | Audio re-decoded |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E0 — baseline ASR | 28.20% | 10.67% | 0 / 0 / 0 | 1,833 ms | 2,304 ms | 0.185 | 0.00% |
| E1 — contextual NLP | 28.20% | 10.67% | 0 / 0 / 0 | 1,880 ms | 2,484 ms | 0.189 | 0.00% |
| E2 — selective re-decode | 27.86% | 10.49% | 1 / 1 / 0 | 1,959 ms | 2,877 ms | 0.193 | 0.91% |
| E3 — complete EchoMind | 27.86% | 10.49% | 1 / 1 / 0 | 1,975 ms | 2,888 ms | 0.195 | 0.91% |

Corpus micro WER/CER (unnormalized) changed from 29.45% / 12.22% at baseline
to 29.12% / 12.06% for E3. The single accepted correction was French clip
`fleurs_fr_test_10603531439273760949`, at 10.08–12.84 s. It replaced the
misheard `Alivellontant.` with `elle, il y a longtemps.` Two bounded local
decoding configurations agreed; target-region mean word confidence increased
by about 0.65. Under the transcript reference, that clip's normalized WER fell
from 19.35% to 3.23%; the correction added about 1.96 s. This is one useful example,
not evidence of reliable correction rates. Machine-evaluated “useful” means
only that the final text scored better against the supplied reference; the
human annotation template remains unreviewed.

E3 normalized WER by language: Arabic 44.28%, English 11.82%, French 28.36%.
The high Arabic score and the small sample remain important limitations. The
full controlled report is `benchmark_fleurs_test_base_e0_e3_warm.json`; row-level
ASR outputs, correction rationale, and the decision trace are in
`benchmark_fleurs_test_base_e3_rows.json`. The earlier cold-run report
`benchmark_fleurs_test_base_e0_e3.json` is retained for traceability but is
superseded: it disagreed with the repeated row-level Arabic baseline, so its
metrics are not the headline results.

The reviewed-label template is
`data/evaluation/annotations/error_annotations_fleurs_test.jsonl`. It contains
baseline/final hypotheses and system correction evidence but leaves all 60
records `unreviewed` and all segment labels empty. FLEURS provides no labels for
spontaneous self-corrections or code-switching, so those capabilities remain
untested.

## Reproduction

```powershell
python scripts/download_corpus.py --max-per-language 20 --split dev --languages en fr ar --output-manifest data/evaluation/manifests/benchmark_fleurs_dev.csv
python scripts/evaluate.py data/evaluation/manifests/benchmark_fleurs_dev.csv --model tiny --output experiments/reports/benchmark_fleurs_dev_tiny.json
python scripts/evaluate.py data/evaluation/manifests/benchmark_fleurs_dev.csv --model base --output experiments/reports/benchmark_fleurs_dev_base.json
python scripts/evaluate.py data/evaluation/manifests/benchmark_fleurs_dev.csv --model small --output experiments/reports/benchmark_fleurs_dev_small.json
```

Independent test split reproduction (20 unique archive entries per language):

```powershell
python scripts/download_corpus.py --max-per-language 20 --split test --languages en fr ar --output-manifest data/evaluation/manifests/benchmark_fleurs_test_independent.csv
python scripts/evaluate.py data/evaluation/manifests/benchmark_fleurs_test_independent.csv --model base --ablation --output experiments/reports/benchmark_fleurs_test_base_e0_e3_warm.json
python scripts/evaluate.py data/evaluation/manifests/benchmark_fleurs_test_independent.csv --model base --output experiments/reports/benchmark_fleurs_test_base_e3_rows.json
python scripts/create_error_annotation_template.py data/evaluation/manifests/benchmark_fleurs_test_independent.csv --report experiments/reports/benchmark_fleurs_test_base_e3_rows.json --output data/evaluation/annotations/error_annotations_fleurs_test.jsonl
```
