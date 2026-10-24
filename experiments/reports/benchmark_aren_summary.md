# EchoMind — ARen benchmark summary

Audit run: 2026-10-23. The runs used local faster-whisper models on CPU with
INT8 inference. No demo or simulator was used.

## Data and reproducibility

- Corpus: [TNSA AI, ARen](https://huggingface.co/datasets/TNSA/Aren), CC BY 4.0.
- Sample: 5 Arabic and 5 English source utterances, each paired across `clean`,
  `tel8k`, and `tel8k_noisy` (30 audio rows per run).
- English source selection is round-robin across the available source corpora.
- The noise condition is synthetically degraded. It is not a real recording in
  a noisy room or from a phone network.
- ARen supplies no speaker IDs, intent labels, or spontaneous self-correction
  labels. The manifest records `speaker_id=unknown`; no speaker-disjoint claim
  is valid.
- Base model file: 145,217,532 bytes; SHA-256
  `d01c3014881c9c6f3133c182f3d2887eb6ca1c789a7538c5c007196857a0a6a9`.
- Reproduce with:

```powershell
python scripts/download_aren.py --samples-per-language 5
python scripts/prepare_dataset.py data/evaluation/manifests/benchmark_aren.csv
python scripts/evaluate.py data/evaluation/manifests/benchmark_aren.csv --model base --output experiments/reports/benchmark_aren_base.json
python scripts/evaluate.py data/evaluation/manifests/benchmark_aren.csv --model base --ablation --output experiments/reports/benchmark_aren_base_e0_e3.json
python scripts/evaluate.py data/evaluation/manifests/benchmark_aren.csv --model tiny --output experiments/reports/benchmark_aren_tiny.json
```

## Model comparison

WER/CER without a `_macro` suffix are corpus micro-averages; `_macro` fields
are arithmetic means across utterances. Normalized values use EchoMind's
documented Unicode/text normalization.

| Model | Measured | Empty | WER micro / normalized | WER macro | CER micro / normalized | Mean latency | p95 | Mean RTF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `tiny` | 30/30 | 1 | 57.67% / 56.67% | 59.76% | 29.72% / 27.76% | 1,411 ms | 1,605 ms | 0.295 |
| `base` | 30/30 | 0 | 58.90% / 57.50% | 57.42% | 31.68% / 29.94% | 3,075 ms | 4,716 ms | 0.649 |

The base weights now load and produce actual transcripts. On this small sample,
base is slightly worse overall than tiny and is about 2.2× slower by mean
latency, but it produced no empty outputs (tiny produced one). This is not
enough data to rank the models reliably.

## Base model by language and condition

| Group | Clips | WER micro / normalized | CER micro / normalized | Mean latency | Mean RTF |
| --- | ---: | ---: | ---: | ---: | ---: |
| Arabic | 15 | 50.98% / 48.48% | 15.66% / 13.86% | 3,089 ms | 0.286 |
| English | 15 | 72.13% / 72.13% | 64.27% / 62.08% | 3,060 ms | 1.012 |
| Clean | 10 | 31.29% / 29.38% | 11.96% / 9.85% | 2,772 ms | 0.575 |
| Telephony-bandlimited | 10 | 44.17% / 42.50% | 17.72% / 15.46% | 2,866 ms | 0.604 |
| Telephony + synthetic noise | 10 | 101.23% / 100.63% | 65.35% / 64.49% | 3,586 ms | 0.767 |

Tiny scored better than base on the noisy subset (WER 71% vs. 101%); base
scored better on clean and telephony-bandlimited audio. The current English
WER and noisy-audio result are clear quality problems, not solved by merely
downloading the base weights.

## E0–E3 ablation with `base`

All four conditions measured the same final text metrics. No correction was
accepted, so useful and harmful corrections were both zero. E2 and E3 still
re-decoded an average 0.74% of audio, but did not change final hypotheses.

| Condition | WER micro / normalized | CER micro / normalized | Mean latency | p95 | Mean RTF | Re-decoded | Accepted corrections |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E0 — baseline ASR | 58.90% / 57.50% | 31.68% / 29.94% | 2,823 ms | 4,318 ms | 0.603 | 0.00% | 0 |
| E1 — contextual correction | 58.90% / 57.50% | 31.68% / 29.94% | 2,992 ms | 4,428 ms | 0.645 | 0.00% | 0 |
| E2 — selective re-decode | 58.90% / 57.50% | 31.68% / 29.94% | 2,941 ms | 4,574 ms | 0.625 | 0.74% | 0 |
| E3 — complete EchoMind | 58.90% / 57.50% | 31.68% / 29.94% | 2,827 ms | 4,409 ms | 0.600 | 0.74% | 0 |

## Dashboard and tests

- FastAPI `/dashboard/analyze`, real WAV and `model_name=base`: HTTP 200,
  backend `faster-whisper`, Arabic language detected, two ASR segments, and
  metrics/timeline HTML returned without warnings.
- `pytest`: 21 passed.
- The report does **not** validate uncertainty calibration, intent accuracy,
  speaker generalization, correction usefulness on annotated errors, French
  accuracy, or real-world noisy speech.

Full row-level outputs:

- `benchmark_aren_base.json`
- `benchmark_aren_base_e0_e3.json`
- `benchmark_aren_tiny.json`

## Follow-up: confidence gate and E0–E3 (2026-10-23)

This fresh run applies the revised selective-correction gate to the same 30 ARen
files. It is a robustness sanity check, not an independent held-out evaluation:
these ARen items were already used in prior project benchmarks, and the source
manifest has no speaker IDs. The full machine-readable report is
`benchmark_aren_base_confidence_gate_e0_e3.json`.

| Condition | Clips | Normalized WER | Normalized CER | Accepted / useful / harmful | Mean latency | p95 | RTF | Re-decoded |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E0 — baseline ASR | 30 | 57.50% | 29.94% | 0 / 0 / 0 | 1,900 ms | 2,755 ms | 0.404 | 0.00% |
| E1 — contextual | 30 | 57.50% | 29.94% | 0 / 0 / 0 | 1,881 ms | 2,510 ms | 0.403 | 0.00% |
| E2 — selective re-decode | 30 | 57.29% | 29.82% | 1 / 1 / 0 | 1,948 ms | 3,143 ms | 0.409 | 0.74% |
| E3 — complete EchoMind | 30 | 57.29% | 29.82% | 1 / 1 / 0 | 1,942 ms | 3,136 ms | 0.408 | 0.74% |

E3's single accepted correction was useful under reference WER/CER, but the
normalized WER reduction is only 0.21 percentage points (57.50% to 57.29%).
Language-level normalized WER was 48.48% Arabic and 71.58% English. By
condition it was 29.38% clean, 42.50% telephony-bandlimited, and 100.00% on the
synthetically noisy subset. This shows that the code path can make a
beneficial change, not that corrections are reliable. Full metrics and group
breakdowns are in the JSON report.

An independent official FLEURS `test` subset has now been streamed separately
from the validation data used for threshold selection. Its controlled base
E0–E3 results, correction provenance, selection limits and annotation template
are documented in `experiments/reports/benchmark_fleurs_dev_summary.md` and
`PROJECT_AUDIT.md`.
