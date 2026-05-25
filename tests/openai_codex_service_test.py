from AgentCrew.modules.openai_codex.service import OpenAICodexService


class TestOpenAICodexService:
    def test_codex_service_tier_defaults_to_default(self, monkeypatch):
        monkeypatch.delenv("AGENTCREW_FAST_CODEX", raising=False)

        assert OpenAICodexService._codex_service_tier() == "default"

    def test_codex_service_tier_uses_priority_when_fast_codex_enabled(
        self, monkeypatch
    ):
        monkeypatch.setenv("AGENTCREW_FAST_CODEX", "1")

        assert OpenAICodexService._codex_service_tier() == "priority"

    def test_codex_service_tier_ignores_other_values(self, monkeypatch):
        monkeypatch.setenv("AGENTCREW_FAST_CODEX", "true")

        assert OpenAICodexService._codex_service_tier() == "default"
