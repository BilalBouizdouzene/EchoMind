"""Small local API surface that does not require a database or cloud service."""

from __future__ import annotations

import base64
import binascii
import io
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from echomind.api.dashboard import dashboard_page
from echomind.asr.demo_engine import DemoEngine, demo_audio
from echomind.nlp.contradiction_detection import detect_self_correction
from echomind.nlp.intent_extraction import extract_semantics
from echomind.pipeline.orchestrator import EchoMindPipeline, PipelineOptions
from echomind.ui.components import analysis_json, metrics_html, timeline_html


class TextAnalysisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    context: str = Field(default="", max_length=20000)


class AudioAnalysisRequest(BaseModel):
    audio_path: str = Field(min_length=1, max_length=4096)
    context: str = Field(default="", max_length=20000)
    model_name: str = Field(default="tiny", min_length=1, max_length=64)
    language_hint: str | None = None
    enable_selective_correction: bool = True


class BrowserAnalysisRequest(BaseModel):
    demo_mode: bool = True
    scenario: str = "selective_correction"
    audio_base64: str | None = None
    audio_filename: str | None = None
    context: str = Field(default="", max_length=20000)
    model_name: str = Field(default="tiny", min_length=1, max_length=64)
    language_hint: str | None = None
    enable_uncertainty: bool = True
    enable_selective_correction: bool = True
    enable_contextual_nlp: bool = True


def _raise_if_asr_unavailable(result) -> None:
    baseline = getattr(result, "baseline", None)
    if baseline is None:
        return
    failure = next(
        (
            warning
            for warning in baseline.warnings
            if warning.startswith("ASR failed:")
            or warning.startswith("faster-whisper is not installed.")
        ),
        None,
    )
    if failure is None:
        return

    model_name = baseline.model_name
    detail = f"Local ASR could not load model '{model_name}'."
    if "model is not installed locally" in failure.lower() or "cached snapshot" in failure.lower():
        if model_name in {"tiny", "base", "small"}:
            detail += (
                f" Its weights are not cached. To download them, run "
                f"`python scripts/download_models.py --model {model_name} --download` "
                "from the project directory, then restart EchoMind."
            )
        else:
            detail += " Its weights are not cached locally. Select a supported model and prepare its weights explicitly."
    elif "faster-whisper is not installed" in failure.lower():
        detail += " Install the ASR extra with `pip install -e \".[asr]\"`."
    detail += f" Details: {failure}"
    raise HTTPException(status_code=503, detail=detail)


def build_router(pipeline_factory=None) -> APIRouter:
    router = APIRouter()
    factory = pipeline_factory or (lambda request: EchoMindPipeline(PipelineOptions(model_name=request.model_name, language_hint=request.language_hint, enable_selective_correction=request.enable_selective_correction)))

    @router.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "echomind", "local_only": True}

    @router.get("/", include_in_schema=False)
    def root_dashboard():
        return dashboard_page()

    @router.get("/dashboard", include_in_schema=False)
    def dashboard():
        return dashboard_page()

    @router.post("/analyze/text")
    def analyze_text(request: TextAnalysisRequest) -> dict:
        semantics = extract_semantics(request.text)
        event = detect_self_correction(request.text)
        return {"text": request.text, "semantic_interpretation": semantics.model_copy(update={"self_correction": event}).model_dump(mode="json")}

    @router.post("/analyze/audio")
    def analyze_audio(request: AudioAnalysisRequest) -> dict:
        path = Path(request.audio_path).resolve()
        if not path.is_file():
            raise HTTPException(status_code=400, detail="audio_path must reference an existing local file")
        if path.suffix.lower() not in {".wav", ".flac", ".ogg", ".mp3"}:
            raise HTTPException(status_code=415, detail="unsupported audio extension")
        if path.stat().st_size > 16 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="audio file exceeds the 16 MB local limit")
        result = factory(request).process(path, context=request.context)
        _raise_if_asr_unavailable(result)
        return result.model_dump(mode="json")

    @router.post("/dashboard/analyze")
    def analyze_browser(request: BrowserAnalysisRequest) -> dict:
        options = PipelineOptions(
            model_name=request.model_name,
            language_hint=request.language_hint,
            enable_uncertainty=request.enable_uncertainty,
            enable_selective_correction=request.enable_selective_correction,
            enable_contextual_nlp=request.enable_contextual_nlp,
        )
        if request.demo_mode:
            result = EchoMindPipeline(options, engine=DemoEngine(request.scenario)).process(demo_audio(), context=request.context)
        else:
            if not request.audio_base64:
                raise HTTPException(status_code=400, detail="Select a local audio file in Local ASR mode")
            if request.audio_filename and Path(request.audio_filename).suffix.lower() not in {".wav", ".flac", ".ogg", ".mp3"}:
                raise HTTPException(status_code=415, detail="Unsupported audio extension")
            try:
                encoded = request.audio_base64.split(",", 1)[-1]
                if len(encoded) > 22_000_000:
                    raise HTTPException(status_code=413, detail="Audio upload exceeds the 16 MB dashboard limit")
                raw = base64.b64decode(encoded, validate=True)
            except (ValueError, binascii.Error) as error:
                raise HTTPException(status_code=400, detail="Invalid local audio payload") from error
            result = EchoMindPipeline(options).process(io.BytesIO(raw), context=request.context)
            _raise_if_asr_unavailable(result)
        data = analysis_json(result)
        data.update({"metrics_html": metrics_html(result), "timeline_html": timeline_html(result)})
        return data

    return router
