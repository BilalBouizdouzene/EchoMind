# Data card

## Scope

The evaluation fixtures include 20 FLEURS validation clips and 20 separate
official test clips each for English, French and Arabic. CSV metadata preserves
the transcript, language, official source split, source and license. Audio is
downloaded locally and is not committed. The [FLEURS dataset card](https://huggingface.co/datasets/google/fleurs)
identifies CC BY 4.0; the [FLEURS paper](https://arxiv.org/abs/2205.12446)
describes speaker-disjoint source splits. Individual speaker IDs are not
included in this export.

## Intended use

- smoke-testing local audio loading and pipeline schemas;
- demonstrating multilingual text handling and speaker-aware splitting when verified speaker IDs are available;
- measuring a first ASR baseline/model comparison after local model installation.

## Not intended for

- production ASR claims;
- demographic or accent fairness conclusions;
- training a model from this small evaluation subset;
- mixing speakers across train and test splits;
- publishing raw audio without checking the upstream license and terms.

## Evaluation hygiene

The manifest preserves upstream provenance. Keep the source-provided validation
and test splits separate; do not infer speaker IDs or create random speaker
splits from `unknown`. Report the exact model, package versions, manifest hash
and command. EchoMind reports missing labels as `null` and does not invent scores
when a metric cannot be measured. Validation results are for development/model
selection; the small test subset is held out from the current threshold tuning,
but is not a full-split or conversational-speech estimate.
