from echomind.evaluation import ablation
from echomind.pipeline.orchestrator import PipelineOptions


def test_ablation_reuses_one_preloaded_engine_for_all_conditions(monkeypatch):
    engine_ids = []

    monkeypatch.setattr(ablation.WhisperEngine, "load", lambda _self: object())

    def fake_run_benchmark(_manifest_path, pipeline):
        engine_ids.append(id(pipeline.engine))
        return {
            "metrics": {"evaluated_examples": 1},
            "rows": [{"id": "clip-1", "correction_applied": True}],
        }

    monkeypatch.setattr(ablation, "run_benchmark", fake_run_benchmark)

    result = ablation.run_ablation("not-read-by-mock.csv", PipelineOptions(model_name="base"))

    assert len(engine_ids) == 4
    assert len(set(engine_ids)) == 1
    assert all(item["model_loaded_before_conditions"] for item in result.values())
    assert all(item["model_load_ms_excluded_from_condition_latency"] >= 0 for item in result.values())
    assert all(item["correction_examples"][0]["id"] == "clip-1" for item in result.values())
