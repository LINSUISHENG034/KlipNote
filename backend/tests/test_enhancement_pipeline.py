import pytest

from app.ai_services.enhancement.pipeline import EnhancementPipeline
from app.ai_services.enhancement import factory as pipeline_factory


class DummyComponent:
    def __init__(self, label: str):
        self.label = label
        self._calls = 0

    def process(self, segments, audio_path, **kwargs):
        self._calls += 1
        updated = []
        for segment in segments:
            clone = dict(segment)
            clone["text"] = f"{self.label}-{clone.get('text', '')}"
            enhancements = clone.setdefault("enhancements_applied", [])
            enhancements.append(self.label)
            updated.append(clone)
        return updated

    def get_metrics(self):
        return {"calls": self._calls}


def test_empty_pipeline_returns_input_unchanged():
    pipeline = EnhancementPipeline([])
    segments = [{"start": 0.0, "end": 1.0, "text": "hello"}]

    result, metrics = pipeline.process(segments, "/tmp/audio.wav")

    assert result == segments
    assert metrics["components_executed"] == 0
    assert metrics["component_metrics"] == []


def test_single_component_pipeline_applies_changes():
    component = DummyComponent("vad")
    pipeline = EnhancementPipeline([component])
    segments = [{"start": 0.0, "end": 1.0, "text": "hi"}]

    result, metrics = pipeline.process(segments, "/tmp/audio.wav")

    assert result[0]["text"].startswith("vad-")
    assert "vad" in result[0]["enhancements_applied"]
    assert metrics["components_executed"] == 1


def test_pipeline_preserves_execution_order():
    class ComponentA(DummyComponent):
        def process(self, segments, audio_path, **kwargs):
            result = super().process(segments, audio_path, **kwargs)
            for item in result:
                item["order"] = item.get("order", []) + ["A"]
            return result

    class ComponentB(DummyComponent):
        def process(self, segments, audio_path, **kwargs):
            result = super().process(segments, audio_path, **kwargs)
            for item in result:
                item["order"] = item.get("order", []) + ["B"]
            return result

    pipeline = EnhancementPipeline([ComponentA("a"), ComponentB("b")])
    segments = [{"start": 0.0, "end": 1.0, "text": "hi"}]

    result, _ = pipeline.process(segments, "/tmp/audio.wav")

    assert result[0]["order"] == ["A", "B"]


def test_pipeline_handles_component_exception(caplog):
    class FailingComponent(DummyComponent):
        def process(self, segments, audio_path, **kwargs):
            raise RuntimeError("boom")

    pipeline = EnhancementPipeline([FailingComponent("fail")])
    segments = [{"start": 0.0, "end": 1.0, "text": "hi"}]

    result, metrics = pipeline.process(segments, "/tmp/audio.wav")

    assert result == segments  # fallback to original segments
    assert metrics["component_metrics"][0]["error"] == "boom"


def test_factory_valid_configs(monkeypatch):
    builders = {
        "alpha": lambda: DummyComponent("alpha"),
        "beta": lambda: DummyComponent("beta"),
    }
    monkeypatch.setattr(pipeline_factory, "COMPONENT_BUILDERS", builders)

    pipeline = pipeline_factory.create_pipeline("alpha,beta")

    assert len(pipeline.components) == 2
    assert [c.label for c in pipeline.components] == ["alpha", "beta"]


def test_factory_invalid_config(monkeypatch):
    monkeypatch.setattr(pipeline_factory, "COMPONENT_BUILDERS", {"alpha": lambda: DummyComponent("alpha")})

    with pytest.raises(ValueError):
        pipeline_factory.create_pipeline("alpha,unknown")
