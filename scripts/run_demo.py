"""Run a text-only semantic demo without ASR model weights."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from echomind.nlp.contradiction_detection import detect_self_correction
from echomind.nlp.intent_extraction import extract_semantics


def main() -> int:
    text = "I want to cancel my booking Monday, no Tuesday."
    semantic = extract_semantics(text).model_copy(update={"self_correction": detect_self_correction(text)})
    print(json.dumps({"text": text, "semantic_interpretation": semantic.model_dump(mode="json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
