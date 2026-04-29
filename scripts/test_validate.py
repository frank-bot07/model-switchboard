import pytest
from scripts.validate import validate_model_ref

@pytest.mark.parametrize("model, expected_valid", [
    ("anthropic/claude-3-opus", True),
    ("openrouter/anthropic/claude-3-opus", True),
    ("ollama/llama3:8b", True),
    ("google/gemini-pro.1", True),
    ("my-provider/model_id", True),
    ("openai/gpt-4-turbo", True),
    ("provider-123/model.name_v1", True),
])
def test_validate_model_ref_valid(model, expected_valid):
    valid, msg = validate_model_ref(model)
    assert valid is True
    assert msg == "Valid"

@pytest.mark.parametrize("model, expected_msg", [
    (None, "Model reference cannot be empty"),
    (123, "Model reference cannot be empty"),
    ("", "Model reference cannot be empty"),
    ("provider", "Must be provider/model-name"),
    ("/model", "Must be provider/model-name"),
    ("provider/", "Must be provider/model-name"),
])
def test_validate_model_ref_invalid_format(model, expected_msg):
    valid, msg = validate_model_ref(model)
    assert valid is False
    assert expected_msg in msg

@pytest.mark.parametrize("model, expected_msg", [
    ("Provider/model", "Invalid provider"),
    ("-provider/model", "Invalid provider"),
    ("provider /model", "Invalid provider"),
    ("prov_ider/model", "Invalid provider"),
])
def test_validate_model_ref_invalid_provider(model, expected_msg):
    valid, msg = validate_model_ref(model)
    assert valid is False
    assert expected_msg in msg

@pytest.mark.parametrize("model, expected_msg", [
    ("provider/ model", "Invalid model ID"),
    ("provider/!model", "Invalid model ID"),
    ("provider/@model", "Invalid model ID"),
    ("provider/#model", "Invalid model ID"),
])
def test_validate_model_ref_invalid_model_id(model, expected_msg):
    valid, msg = validate_model_ref(model)
    assert valid is False
    assert expected_msg in msg
