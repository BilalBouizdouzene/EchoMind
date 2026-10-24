"""Print a truthful local capability report without downloading anything."""

from __future__ import annotations

import importlib.util
import os
import platform
import sys


def main() -> int:
    modules = ["numpy", "soundfile", "pydantic", "fastapi", "gradio", "faster_whisper", "scipy", "sklearn", "jiwer"]
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    print(f"Platform: {platform.platform()}")
    print(f"CPU count: {os.cpu_count()}")
    print("Optional capabilities:")
    for module in modules:
        print(f"  {'OK' if importlib.util.find_spec(module) else 'missing':7} {module}")
    print("\nNo model weights are downloaded by this diagnostic.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
