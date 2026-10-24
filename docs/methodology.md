# Methodology

EchoMind's research unit is a segment, not an entire recording. A baseline decode is scored using available decoder statistics, audio quality heuristics, text instability, language-transition evidence, and optional context mismatch. High-risk segments receive at most one alternative decode within a configurable region and audio-fraction budget.

The semantic layer may select only among grounded candidates. It cannot invent a name, date, amount, medication, or phone number. Speaker self-correction is represented separately from acoustic ASR error, and unresolved critical ambiguity produces a clarification question instead of a confident rewrite.

The intended comparison is E0 baseline ASR, E1 contextual analysis, E2 selective acoustic re-decoding, and E3 the complete policy. Evaluation must use an annotated local manifest with speaker-aware splits; no benchmark result is shown until it has been measured.
