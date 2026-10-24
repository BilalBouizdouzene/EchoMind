"""Professional Gradio dashboard, optional at install time."""

from __future__ import annotations

from pathlib import Path

from echomind.asr.demo_engine import DemoEngine, demo_audio
from echomind.pipeline.orchestrator import EchoMindPipeline, PipelineOptions
from echomind.ui.components import analysis_json, metrics_html, result_markdown, timeline_html


def create_dashboard():
    try:
        import gradio as gr
    except ImportError as error:
        raise RuntimeError("Gradio is optional. Install with: pip install 'echomind[ui]'") from error

    css = """
    body { background: #080b18; color: #f3f4ff; }
    .gradio-container { max-width: 1480px !important; background: radial-gradient(ellipse at 82% 4%,#342258 0,transparent 30%),radial-gradient(ellipse at 0 24%,#123c55 0,transparent 34%),#080b18; }
    .hero { min-height: 150px; border: 1px solid #3a4164; border-radius: 24px; padding: 24px; background: linear-gradient(112deg,#11182bea,#15152be8 58%,#211b39e8); box-shadow: 0 22px 60px #02040e77; }
    .hero h1 { color: #a5fff5; margin: 0 0 6px; letter-spacing: -0.05em; font-size: 2.2rem; }
    .hero p, .muted { color: #b5bdd6; }
    .gradio-container button.primary { background: linear-gradient(105deg,#21b8c3,#7367e8 68%,#a363ce); border: 0; }
    .gradio-container input:focus, .gradio-container textarea:focus { border-color: #78e9eb !important; box-shadow: 0 0 0 3px #78e9eb1b !important; }
    .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
    .metric-card { border: 1px solid #343953; border-radius: 15px; padding: 14px; background: #0c1121; }
    .metric-card span { display: block; color: #8da7bb; font-size: 10px; letter-spacing: .12em; }
    .metric-card strong { display: block; margin-top: 5px; font-size: 18px; color: #67e8f9; }
    .timeline-wrap { padding: 10px 0; }
    .timeline-axis { display: flex; justify-content: space-between; color: #8da7bb; font-size: 11px; }
    .timeline { position: relative; height: 22px; margin: 8px 0; border-radius: 999px; background: #132536; border: 1px solid #24455b; overflow: hidden; }
    .timeline-bar { position: absolute; top: 3px; height: 14px; border-radius: 99px; min-width: 7px; }
    .legend { display: flex; gap: 16px; color: #8da7bb; font-size: 11px; }
    .dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:5px; }
    .dot.cyan { background:#67e8f9; } .dot.amber { background:#fbbf24; } .dot.red { background:#fb7185; }
    @media(max-width:900px){ .metric-grid { grid-template-columns: repeat(2,1fr); } }
    """
    with gr.Blocks(title="EchoMind — Speech Intelligence", css=css, theme=gr.themes.Soft(primary_hue="cyan")) as demo:
        with gr.Row(equal_height=True):
            gr.HTML("<div class='hero'><p class='muted'>VOICE INTELLIGENCE / LOCAL</p><h1>EchoMind</h1><p>Multilingual speech analysis with transparent, experimental selective re-decoding.</p></div>", scale=4)
            gr.Image(
                value=str(Path(__file__).parents[1] / "api" / "static" / "echomind-anime-engineer.png"),
                show_label=False,
                container=False,
                interactive=False,
                height=170,
                scale=1,
            )
        with gr.Tab("Live Speech Demo"):
            with gr.Row():
                with gr.Column(scale=1):
                    mode = gr.Radio(["Demo / model-free", "Local ASR"], value="Demo / model-free", label="Execution mode")
                    scenario = gr.Dropdown(
                        ["selective_correction", "self_correction", "multilingual"],
                        value="selective_correction",
                        label="Demo scenario",
                    )
                    audio = gr.Audio(type="filepath", sources=["upload", "microphone"], label="Local audio (optional in Demo mode)")
                    model = gr.Dropdown(["tiny", "base", "small"], value="tiny", label="ASR model")
                    language = gr.Dropdown(["auto", "en", "fr", "ar"], value="auto", label="Language hint")
                    context = gr.Textbox(label="Verified context / vocabulary", lines=3)
                    with gr.Row():
                        uncertainty = gr.Checkbox(True, label="Uncertainty")
                        correction = gr.Checkbox(True, label="Selective correction")
                        nlp = gr.Checkbox(True, label="Contextual NLP")
                    run = gr.Button("Run local analysis", variant="primary")
                    gr.Markdown("Demo mode uses a synthetic tone and simulated hypotheses. It demonstrates the reasoning UX, not ASR accuracy.")
                with gr.Column(scale=2):
                    summary = gr.Markdown("### Ready\nChoose Demo mode for an immediate model-free demonstration.")
                    metrics = gr.HTML(label="Pipeline metrics")
                    with gr.Row():
                        original = gr.Textbox(label="Baseline ASR", lines=3)
                        final = gr.Textbox(label="Final grounded result", lines=3)
                    timeline = gr.HTML(label="Uncertainty timeline")
        with gr.Tab("Explainable Error Analysis"):
            gr.Markdown("Raw risk scores are interpretable heuristics unless a separately fitted calibrator is present. Missing Whisper statistics are never fabricated.")
            with gr.Row():
                uncertainty_table = gr.JSON(label="Segment assessments")
                corrections_table = gr.JSON(label="Correction provenance")
        with gr.Tab("Multilingual Intelligence"):
            multilingual = gr.JSON(label="Languages, intent, entities, and self-correction")
        with gr.Tab("Benchmark & Evaluation"):
            gr.Markdown("Measured results only. Run `python scripts/evaluate.py <manifest>` to produce a local report.")
            gr.JSON(value={"status": "Not evaluated yet."}, label="Measured results")
        with gr.Tab("System Settings"):
            gr.Markdown("All recordings stay local. Runtime options currently use code defaults; the YAML files in `config/` are not loaded by the application yet.")
            gr.Code(value="mode: LIGHT\nmax_redecode_regions: 2\nmax_redecode_fraction: 0.25\nmax_concurrent_inference: 1", language="yaml", label="Active safety defaults")
        raw = gr.JSON(label="Full structured result")

        def run_pipeline(mode_name, scenario_name, audio_path, model_name, language_hint, context_text, use_uncertainty, use_correction, use_nlp):
            is_demo = mode_name == "Demo / model-free"
            if not is_demo and not audio_path:
                empty = {"warnings": ["Provide a local recording in Local ASR mode."], "decision": "ACCEPT"}
                return "### Audio required", "", "", "", "<div class='empty-state'>No analysis yet.</div>", [], [], {}, empty
            options = PipelineOptions(
                model_name=model_name,
                language_hint=None if language_hint == "auto" else language_hint,
                enable_uncertainty=use_uncertainty,
                enable_selective_correction=use_correction,
                enable_contextual_nlp=use_nlp,
            )
            engine = DemoEngine(scenario_name) if is_demo else None
            source = demo_audio() if is_demo else audio_path
            result = EchoMindPipeline(options, engine=engine).process(source, context=context_text)
            data = analysis_json(result)
            return result_markdown(result), result.original_transcript, result.final_transcript, metrics_html(result), timeline_html(result), data["uncertain_segments"], data["corrections"], data["semantic_interpretation"], data

        run.click(
            run_pipeline,
            [mode, scenario, audio, model, language, context, uncertainty, correction, nlp],
            [summary, original, final, metrics, timeline, uncertainty_table, corrections_table, multilingual, raw],
        )
    return demo
