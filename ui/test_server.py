import pytest
from ui.server import _get_path, _ensure_path, _set_path, provider_of, validate_model_ref

def test_get_path():
    config = {
        "a": {
            "b": {
                "c": 42
            }
        },
        "d": [1, 2, 3]
    }

    # Happy path
    assert _get_path(config, ["a", "b", "c"]) == 42
    assert _get_path(config, ["a", "b"]) == {"c": 42}
    assert _get_path(config, ["d"]) == [1, 2, 3]

    # Missing keys
    assert _get_path(config, ["a", "x"]) is None
    assert _get_path(config, ["x"]) is None

    # Custom default
    assert _get_path(config, ["a", "x"], default="missing") == "missing"

    # Non-dict intermediate
    assert _get_path(config, ["d", "0"]) is None

def test_ensure_path():
    config = {"a": {}}

    # Existing path
    res = _ensure_path(config, ["a"])
    assert res == {}
    assert config == {"a": {}}

    # New nested path
    res = _ensure_path(config, ["a", "b", "c"])
    assert res == {}
    assert config == {"a": {"b": {"c": {}}}}

    # Path with non-dict intermediate
    config2 = {"a": 1}
    res = _ensure_path(config2, ["a", "b"])
    assert res == {}
    assert config2 == {"a": {"b": {}}}

def test_set_path():
    config = {}

    # Root level
    _set_path(config, ["a"], 1)
    assert config == {"a": 1}

    # Nested level
    _set_path(config, ["b", "c"], 2)
    assert config == {"a": 1, "b": {"c": 2}}

    # Overwrite
    _set_path(config, ["a"], 3)
    assert config == {"a": 3, "b": {"c": 2}}

def test_provider_of():
    assert provider_of("openai/gpt-4") == "openai"
    assert provider_of("anthropic/claude-3") == "anthropic"
    assert provider_of("model-only") == ""
    assert provider_of("") == ""

def test_validate_model_ref():
    # Valid refs
    assert validate_model_ref("openai/gpt-4") is True
    assert validate_model_ref("anthropic/claude-3-opus") is True
    assert validate_model_ref("ollama/llama3:8b") is True

    # Invalid refs
    assert validate_model_ref("invalid-format") is False
    assert validate_model_ref("Upper/Case") is False # regex uses [a-z]
    assert validate_model_ref("") is False
    assert validate_model_ref(None) is False
    assert validate_model_ref(123) is False
    assert validate_model_ref("a" * 250 + "/b") is False # Too long
