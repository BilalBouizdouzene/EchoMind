from echomind.pipeline.schemas import PipelineResult


def test_pipeline_json_schema_roundtrip():
    result = PipelineResult(final_transcript="hello")
    data = result.model_dump(mode="json")
    restored = PipelineResult.model_validate(data)
    assert restored.final_transcript == "hello"
    assert restored.decision == "ACCEPT"
