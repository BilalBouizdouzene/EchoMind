"""Optional local Ollama adapter; never required by the baseline pipeline."""

from __future__ import annotations

import json
import urllib.request


class OllamaAdapter:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "phi3:mini") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def available(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=1) as response:
                return response.status == 200
        except Exception:
            return False

    def grounded_json(self, original_text: str, candidates: list[str], context: str = "") -> dict:
        prompt = {
            "instruction": "Select only among the supplied candidates. Do not invent spoken facts.",
            "original": original_text,
            "candidates": candidates,
            "context": context,
            "output": {"selected_candidate": "", "ambiguities": [], "reason": ""},
        }
        payload = json.dumps({"model": self.model, "prompt": json.dumps(prompt), "stream": False}).encode()
        request = urllib.request.Request(
            f"{self.base_url}/api/generate", data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = json.loads(response.read().decode("utf-8"))
        text = raw.get("response", "")
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Ollama did not return structured JSON")
        parsed = json.loads(text[start : end + 1])
        selected = parsed.get("selected_candidate", "")
        if selected and selected not in candidates:
            raise ValueError("Ollama selected text outside the grounded candidate set")
        return parsed
