import pytest
from ui.server import provider_of

@pytest.mark.parametrize("ref, expected", [
    ("anthropic/claude-3-opus", "anthropic"),
    ("openai/gpt-4-turbo", "openai"),
    ("google/gemini-pro.1", "google"),
    ("openrouter/anthropic/claude-3-opus", "openrouter"),
    ("ollama/llama3:8b", "ollama"),
    ("provider", ""),
    ("", ""),
    ("no_slash", ""),
    ("multiple/slashes/in/ref", "multiple"),
])
def test_provider_of(ref, expected):
    assert provider_of(ref) == expected
