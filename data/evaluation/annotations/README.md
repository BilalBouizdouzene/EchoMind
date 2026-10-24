# Segment error annotations

`error_annotations.jsonl` is generated from an evaluation manifest but is
intentionally empty at the segment-label level. It must be reviewed by a human
or an auditable annotation process before it is used to calibrate uncertainty.
No labels are inferred from the model output.

The current FLEURS development template is
`error_annotations_fleurs_dev.jsonl` (60 records, all `unreviewed`). It is a
review queue, not an error-labelled dataset; do not fit or claim calibration from
it until segments have verified timestamps and labels.

Each record has this shape:

```json
{
  "id": "example-id",
  "audio_path": "data/example.wav",
  "speaker_id": "speaker-1",
  "language": "ar",
  "reference_text": "...",
  "status": "reviewed",
  "segments": [
    {
      "segment_id": 0,
      "start": 0.0,
      "end": 1.2,
      "label": 1,
      "error_type": "substitution",
      "reference_text": "...",
      "notes": "..."
    }
  ],
  "reviewer": "initials",
  "notes": "..."
}
```

Use `label=1` for a verified ASR error and `label=0` for a verified correct
segment. Keep complete speakers in one split. Calibration must be fit on the
training speakers and evaluated on held-out speakers; utterance-level WER must
not be copied into every segment as a substitute for annotation.
