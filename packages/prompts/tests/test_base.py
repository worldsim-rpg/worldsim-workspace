"""Тесты утилит промптов: render, extract_json, call_json."""

import json
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from worldsim_prompts.base import call_json, extract_json, render


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------


def test_render_simple():
    assert render("Hello, {{name}}!", name="World") == "Hello, World!"


def test_render_multiple_vars():
    tpl = "{{greeting}}, {{subject}}. Tick: {{tick}}."
    result = render(tpl, greeting="Привет", subject="мир", tick=42)
    assert result == "Привет, мир. Tick: 42."


def test_render_dict_var():
    tpl = "Data: {{payload}}"
    result = render(tpl, payload={"key": "val"})
    parsed = json.loads(result.replace("Data: ", ""))
    assert parsed["key"] == "val"


def test_render_list_var():
    tpl = "Items: {{items}}"
    result = render(tpl, items=[1, 2, 3])
    assert "[" in result


def test_render_whitespace_in_key():
    assert render("{{ name }}", name="Alice") == "Alice"


def test_render_missing_key():
    with pytest.raises(KeyError, match="name"):
        render("{{name}}", age=5)


def test_render_no_placeholders():
    tpl = "Static text."
    assert render(tpl) == "Static text."


def test_render_repeated_placeholder():
    result = render("{{x}} and {{x}}", x="yes")
    assert result == "yes and yes"


def test_render_none_value():
    result = render("{{val}}", val=None)
    assert result == "None"


# ---------------------------------------------------------------------------
# extract_json
# ---------------------------------------------------------------------------


def test_extract_json_plain_object():
    raw = '{"key": "value", "num": 42}'
    result = extract_json(raw)
    assert result == {"key": "value", "num": 42}


def test_extract_json_plain_array():
    raw = '[1, 2, 3]'
    result = extract_json(raw)
    assert result == [1, 2, 3]


def test_extract_json_markdown_block():
    raw = '```json\n{"answer": true}\n```'
    result = extract_json(raw)
    assert result == {"answer": True}


def test_extract_json_markdown_block_no_lang():
    raw = '```\n{"x": 1}\n```'
    result = extract_json(raw)
    assert result == {"x": 1}


def test_extract_json_embedded_in_text():
    raw = 'Sure! Here is the result: {"status": "ok"} Hope that helps.'
    result = extract_json(raw)
    assert result == {"status": "ok"}


def test_extract_json_leading_trailing_whitespace():
    raw = '   \n{"a": 1}\n   '
    assert extract_json(raw) == {"a": 1}


def test_extract_json_nested():
    data = {"outer": {"inner": [1, 2, 3]}}
    raw = json.dumps(data)
    assert extract_json(raw) == data


def test_extract_json_invalid_raises():
    with pytest.raises(ValueError, match="Не удалось извлечь JSON"):
        extract_json("This is plain text with no JSON.")


def test_extract_json_empty_raises():
    with pytest.raises((ValueError, json.JSONDecodeError)):
        extract_json("")


def test_extract_json_unicode():
    raw = '{"текст": "Привет мир"}'
    result = extract_json(raw)
    assert result["текст"] == "Привет мир"


# ---------------------------------------------------------------------------
# call_json
# ---------------------------------------------------------------------------


class _SampleSchema(BaseModel):
    action: str
    value: int


def _make_mock_client(response_text: str) -> MagicMock:
    client = MagicMock()
    client.complete.return_value = response_text
    return client


def test_call_json_success():
    payload = {"action": "move", "value": 5}
    client = _make_mock_client(json.dumps(payload))
    result = call_json(
        client,
        system="sys",
        user="usr",
        model="claude-test",
        schema=_SampleSchema,
    )
    assert isinstance(result, _SampleSchema)
    assert result.action == "move"
    assert result.value == 5


def test_call_json_markdown_response():
    payload = {"action": "wait", "value": 0}
    raw = f"```json\n{json.dumps(payload)}\n```"
    client = _make_mock_client(raw)
    result = call_json(client, system="s", user="u", model="m", schema=_SampleSchema)
    assert result.action == "wait"


def test_call_json_passes_params_to_client():
    payload = {"action": "run", "value": 1}
    client = _make_mock_client(json.dumps(payload))
    call_json(
        client,
        system="system_prompt",
        user="user_prompt",
        model="claude-opus-4-7",
        schema=_SampleSchema,
        max_tokens=1024,
        temperature=0.3,
    )
    client.complete.assert_called_once_with(
        model="claude-opus-4-7",
        system="system_prompt",
        user="user_prompt",
        max_tokens=1024,
        temperature=0.3,
    )


def test_call_json_invalid_schema_raises():
    bad_payload = '{"wrong_field": "x"}'
    client = _make_mock_client(bad_payload)
    with pytest.raises(Exception):
        call_json(client, system="s", user="u", model="m", schema=_SampleSchema)


def test_call_json_invalid_json_raises():
    client = _make_mock_client("Not JSON at all.")
    with pytest.raises(ValueError):
        call_json(client, system="s", user="u", model="m", schema=_SampleSchema)
