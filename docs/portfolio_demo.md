# Portfolio demo: EchoMind in 90 seconds

This script is designed for a recruiter, technical interviewer or project review. It shows product behavior and engineering evidence without presenting simulated output as measured ASR quality.

## 1. Start the local service

```powershell
python app.py --api --port 8000
```

Open `http://127.0.0.1:8000/dashboard` and select `Demo / model-free`.

## 2. Show the three decisions

Run these scenarios in order:

1. `Selective correction`: the system keeps the baseline, flags a suspicious region, and accepts a bounded alternative only when the correction policy allows it.
2. `Speaker self-correction`: a deterministic, model-free scenario illustrates the rule-based text path on “Monday, no, Tuesday.” It is not evidence that real spoken repairs are detected reliably.
3. `Multilingual`: a deterministic scenario illustrates the French/English/Arabic UI signals; it does not validate real within-utterance code-switching.

Say explicitly that these are deterministic demo transcripts used to inspect the decision flow; they are not WER measurements or validation of self-correction.

## 3. Show the engineering evidence

Use the tabs to point out:

- baseline transcript versus final transcript;
- uncertainty reasons and the ACCEPT/REDECODE/CLARIFY decision;
- correction records, latency and re-decoded audio fraction;
- provenance and raw JSON for reproducibility.

## 4. Run the measured path when model weights are installed

```powershell
python scripts/evaluate.py data/evaluation/manifests/benchmark_multilingual.csv --output experiments/reports/benchmark.json
```

The generated report separates baseline WER/CER from final WER/CER and reports harmful corrections, latency percentiles, real-time factor and grouped metrics. If weights are not installed, the command still produces an honest report with ASR warnings; it must not be presented as a quality benchmark.
