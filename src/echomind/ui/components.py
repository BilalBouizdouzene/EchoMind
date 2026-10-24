"""Dashboard formatting helpers."""

from __future__ import annotations

import html

from echomind.pipeline.schemas import PipelineResult


def result_markdown(result: PipelineResult) -> str:
    semantic = result.semantic_interpretation
    lines = [
        f"### Decision: `{result.decision}`",
        f"**Language:** `{result.language or 'unknown'}`",
        f"**Original:** {html.escape(result.original_transcript or '(empty)')}",
        f"**Final:** {html.escape(result.final_transcript or '(empty)')}",
        f"**Intent:** `{semantic.intent}` ({semantic.intent_confidence:.2f})",
        f"**Code switching:** `{semantic.code_switching}`",
    ]
    if result.clarification_question:
        lines.append(f"**Clarification:** {html.escape(result.clarification_question)}")
    if result.warnings:
        lines.append("\n**Warnings:**\n" + "\n".join(f"- {html.escape(item)}" for item in result.warnings))
    return "\n\n".join(lines)


def analysis_json(result: PipelineResult) -> dict:
    return result.model_dump(mode="json")


def metrics_html(result: PipelineResult) -> str:
    metrics = result.metrics
    cards = [
        ("DECISION", result.decision, "cyan"),
        ("LANGUAGE", result.language or "unknown", "blue"),
        ("TOTAL LATENCY", f"{metrics.total_latency_ms:.0f} ms", "violet"),
        ("RE-DECODED", f"{metrics.fraction_audio_redecoded * 100:.1f}%", "amber"),
    ]
    return "<div class='metric-grid'>" + "".join(
        f"<div class='metric-card {color}'><span>{label}</span><strong>{html.escape(str(value))}</strong></div>"
        for label, value, color in cards
    ) + "</div>"


def timeline_html(result: PipelineResult) -> str:
    """Render a compact, consistent timestamp timeline for the dashboard."""
    duration = result.audio.duration_seconds if result.audio else 0.0
    if duration <= 0:
        return "<div class='empty-state'>No timestamped audio analysis available.</div>"
    assessments = {item.segment_id: item for item in result.uncertain_segments}
    segments = result.baseline.segments if result.baseline else []
    if not segments:
        return "<div class='empty-state'>No ASR segments available. Install faster-whisper for live audio analysis.</div>"
    bars = []
    colors = {"low": "#22d3ee", "medium": "#fbbf24", "high": "#fb7185"}
    for segment in segments:
        assessment = assessments.get(segment.id)
        score = assessment.raw_score if assessment else 0.0
        band = assessment.band if assessment else "low"
        color = colors[band]
        left = max(0.0, min(100.0, segment.start / duration * 100))
        width = max(2.0, min(100.0 - left, (segment.end - segment.start) / duration * 100))
        title = html.escape(f"{segment.start:.2f}s–{segment.end:.2f}s · {band} · raw risk {score:.2f}")
        bars.append(f"<div class='timeline-bar' title='{title}' style='left:{left:.2f}%;width:{width:.2f}%;background:{color}'></div>")
    return (
        "<div class='timeline-wrap'><div class='timeline-axis'><span>0.00s</span>"
        f"<span>{duration:.2f}s</span></div><div class='timeline'>{''.join(bars)}</div>"
        "<div class='legend'><span><i class='dot cyan'></i>low</span><span><i class='dot amber'></i>medium</span>"
        "<span><i class='dot red'></i>high</span></div></div>"
    )
