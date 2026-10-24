# Evaluation protocol

Use a CSV/JSONL manifest with `audio_path`, `reference_text`, `language`, `speaker_id`, `condition`, `intent`, and `self_correction` fields. Split by speaker where possible, fit a learned uncertainty estimator on training examples, calibrate on validation examples, and report held-out test results.

```powershell
python scripts/evaluate.py data/evaluation/manifest.csv
python scripts/evaluate.py data/evaluation/manifest.csv --ablation
```

Report WER, CER, sentence error rate, intent/entity accuracy, error detection precision/recall/F1/AUROC/AUPRC, calibration ECE/Brier, latency, real-time factor, fraction re-decoded, and harmful corrections. Break down results by language, noise, duration, code-switching, and self-correction status when labels exist.

The benchmark report stores both `baseline_hypothesis` and final `hypothesis`. A correction is classified as `improved`, `unchanged` or `harmful` only when a reference transcript is present. `harmful_correction_rate` uses applied corrections as its denominator; `harmful_correction_rate_all` uses all evaluated examples. When labels are absent, the corresponding values remain `null`.

The current multilingual comparison is documented in
`experiments/reports/benchmark_fleurs_dev_summary.md`. It uses the FLEURS
validation split only; its scores are development/model-selection evidence, not
a final held-out test estimate. No calibrated-uncertainty or beneficial
self-correction claim is supported by this run.
