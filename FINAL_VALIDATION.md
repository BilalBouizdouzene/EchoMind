# EchoMind — final validation and frozen baseline

Date: 2026-10-24  
Decision: keep the project as a local multilingual ASR portfolio/research prototype; withdraw the claim that it is a reliably self-correcting product.

## Frozen evaluation design

- FLEURS validation: 60 clean clips, 20 each in Arabic, English and French. Used for model comparison only.
- FLEURS test: a distinct 60-clip sample, 20 per language. No clip IDs overlap with validation; official `validation` and `test` source splits are preserved. The FLEURS paper describes speaker-disjoint source splits, but this export does not provide individual speaker IDs, so separation cannot be audited per person. See the [FLEURS paper](https://arxiv.org/abs/2205.12446) and [dataset card](https://huggingface.co/datasets/google/fleurs).
- ARen: 30 real local audio files from 10 source utterances, repeated as clean, telephony-bandlimited and telephony-plus-synthetic-noise conditions. It has no speaker IDs; it is a diagnostic sample, not a speaker holdout. See the [ARen dataset card](https://huggingface.co/datasets/TNSA/Aren/blob/main/aren/README.md).
- Inference used local `faster-whisper`, CPU/INT8. No demo or simulator was used for the reported ASR metrics.

The FLEURS test manifest remains unchanged and is not used for model or threshold selection. SHA-256: `ba1c7cee70a583b2ec051685a59cb1a93911dd21636b7db3a1a736df822e9e35`.

## Base versus small: fresh paired Arabic validation

I ran both models on the same 20 Arabic WAVs from the FLEURS **validation** split. Both produced 20 non-empty transcriptions; no correction was accepted. `small` materially reduced error, at a higher but still sub-real-time mean RTF on this Arabic subset.

| Model | Raw WER | Normalized WER | Raw CER | Normalized CER | Mean / p95 latency | RTF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `base` | 53.87% | 51.19% | 19.91% | 17.61% | 1,925 / 2,182 ms | 0.179 |
| `small` | 31.19% | 27.59% | 10.24% | 7.20% | 6,013 / 6,565 ms | 0.563 |

These are development results, not a new test-set estimate. On the previously measured full 60-clip validation sample, `small` also scored better overall (`14.08%` normalized WER, RTF `1.552`) than `base` (`28.07%`, RTF `0.314`). Thus `small` is the accuracy choice in this sample; `base` is the faster all-language compromise. Neither result validates conversational or spontaneous speech.

## Selective re-decoding: held-out FLEURS test

Controlled E0–E3 run with `base`, one shared model instance, and model-load time reported separately:

| Condition | Raw WER / CER | Normalized WER / CER | Applied / useful / harmful | Mean / p95 latency | RTF | Audio re-decoded |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E0 baseline ASR | 29.45% / 12.22% | 28.20% / 10.67% | 0 / 0 / 0 | 1,833 / 2,304 ms | 0.185 | 0% |
| E1 contextual NLP | 29.45% / 12.22% | 28.20% / 10.67% | 0 / 0 / 0 | 1,880 / 2,484 ms | 0.189 | 0% |
| E2 selective re-decode | 29.12% / 12.06% | 27.86% / 10.49% | 1 / 1 / 0 | 1,959 / 2,877 ms | 0.193 | 0.91% |
| E3 complete pipeline | 29.12% / 12.06% | 27.86% / 10.49% | 1 / 1 / 0 | 1,975 / 2,888 ms | 0.195 | 0.91% |

The single candidate is French clip `fleurs_fr_test_10603531439273760949`, audio at `data/evaluation/corpus/fleurs/fr/test/10603531439273760949.wav`, 10.08–12.84 s. The baseline phrase `Alivellontant.` was replaced by `elle, il y a longtemps.`; the supplied reference supports that text, and the row's normalized WER changes from 19.35% to 3.23%. This is automatic reference scoring, **not completed human listening**. All 60 annotation records remain `unreviewed`; do not count this as a human-verified correction.

The overall normalized WER gain is only 0.34 percentage points and comes from one clip. It is not evidence of a reliable correction rate. Test normalized WER by language was Arabic 44.28%, English 11.82%, French 28.36%; Arabic remains a substantial quality gap.

## Representative-audio check and limits

A fresh E0–E3 run was completed on all 30 local ARen files:

| Condition | Normalized WER / CER | Applied / useful / harmful | Mean / p95 latency | RTF | Audio re-decoded |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E0 baseline ASR | 57.50% / 29.94% | 0 / 0 / 0 | 1,910 / 2,422 ms | 0.411 | 0% |
| E1 contextual NLP | 57.50% / 29.94% | 0 / 0 / 0 | 1,906 / 2,450 ms | 0.409 | 0% |
| E2 selective re-decode | 57.50% / 29.94% | 0 / 0 / 0 | 1,972 / 3,251 ms | 0.416 | 0.74% |
| E3 complete pipeline | 57.29% / 29.82% | 1 / 1 / 0 | 1,980 / 3,242 ms | 0.418 | 0.74% |

On the synthetic-noise condition, normalized WER remained 100.63%→100.00%; clean and telephony-bandlimited conditions were 29.38% and 42.50% respectively. The result demonstrates that the pipeline executes on degraded audio, not that it is robust to real-world noise.

No suitable spontaneous-speech or genuine within-utterance Arabic–English code-switch recordings with verified references and usable speaker IDs are present in the local corpus. FLEURS is clean read speech; ARen's English and Arabic examples are separate language rows and its noisy audio is synthetically degraded. Therefore:

- spontaneous self-correction: **not tested**;
- real code-switching: **not tested**;
- real-world environmental noise: **not tested**;
- human-reviewed correction usefulness: **not completed**;
- uncertainty calibration: **not validated**.

The test annotation queue is `data/evaluation/annotations/error_annotations_fleurs_test.jsonl`; it still contains 60 unreviewed records and zero segment labels. No labels were invented or filled from the model's own decisions.

## Frozen artifact hashes

These hashes identify the manifests and reports used for this decision. Preserve the referenced files; write future runs to new filenames.

| Artifact | SHA-256 |
| --- | --- |
| FLEURS validation manifest | `f1cfa94a9e08956761873fb7177da90c4ecf4e7b095936b2799d5d6bcfc1c154` |
| FLEURS independent test manifest | `ba1c7cee70a583b2ec051685a59cb1a93911dd21636b7db3a1a736df822e9e35` |
| FLEURS Arabic validation manifest | `709673824ebe3081de7e770f1b72dc9bf05cce39f39040640c7c4f9f82058342` |
| FLEURS all-language validation `base` report | `a468cb4051e499c7a9ae1dc06bf30a9400d4079279835ddbb8c7670c51bde2ef` |
| FLEURS all-language validation `small` report | `c6f6b361e096564db4ec60e9c329277837010c887e8afd3a24989ea491b8c235` |
| Fresh FLEURS Arabic `base` report | `2f1d8947129b6dec9dbcd65872cecf4bc8acda519f6872fc7654d43e8b1821ac` |
| Fresh FLEURS Arabic `small` report | `00bef645d58658f9e3af279a7754251247eb770a153f0c4e2b56005bd606770f` |
| FLEURS test E0–E3 report | `d96f92053da6e42f3fa58cde016675c15e6a789f80d37702ce184efb08bc8d1c` |
| FLEURS test row-level report | `ce5f10ef3c1588375db86c3e676aa5090371285a6c94f3cf3cd3edab355bcee3` |
| FLEURS test human-review template | `b3bf638f7639f98063d2a4345d2c35cc9230303a0dc0b008120a3ca181fe670a` |
| Fresh ARen E0–E3 report | `5020c6a0f06f5608ac1a6ced5850b0ecbdcc594dd76eeefb9778e98f17f5c52f` |
| Runtime ASR adapter | `a9d1ad999bf10253aaf6acfae63e9972243651224dcdb6f1db10d0be09e8bc11` |
| Runtime pipeline options | `015c0f5c0d800b7ae4b230b345c8fd593c9c58ca74de9411a5b53637943134e5` |
| Runtime uncertainty defaults | `109f238e7da5a6484849e86e752b270cbb499b5ae701f8448388d14acf4f280d` |
| Runtime correction gate | `5e77888ccbeca8b09027c72830625a01d49533e7d72570cf1c2b5fd10352ac49` |
| Static model YAML (not loaded) | `4988381001afc65d1fac7d7fb7f25f8340982cd7d418eabdb3b1507e31999bd2` |
| Static settings YAML (not loaded) | `640262cd70e5146239d7df803c60919176d0f85d3e9aa2a1673dab1e93dc3090` |
| Static thresholds YAML (not loaded; stale) | `67b9321c152d3fb3104602a12b51e09a0497f15854f15796e25250e61fd0b72f` |

Effective inference settings were faster-whisper CPU/INT8, beam size 1, temperature 0, automatic language detection, 4 CPU threads, max 2 re-decode regions, and a 25% re-decode budget. The runtime heuristic thresholds are medium `0.20` / high `0.30`; an acoustic alternative requires agreement from two bounded decode configurations and at least `+0.05` target-region mean word confidence unless verified context supports it.

Configuration caveat: runtime settings are currently code defaults/options; YAML files in `config/` are not loaded. In particular, `config/thresholds.yaml` says medium `0.40` / high `0.65`, so it does **not** describe the run above. This is recorded as incomplete rather than silently treated as the effective configuration.

## Go / no-go decision

**GO** for a recruiter-facing demonstration under the narrower description “local multilingual ASR with explainable, experimental selective re-decoding.” **NO-GO** for claiming reliable self-correction, calibrated uncertainty, code-switch robustness, or production readiness. Keep the existing feature as experimental; do not tune thresholds on the frozen test sample. The only remaining evidence step for the correction candidate is human listening and review of its annotation record.
