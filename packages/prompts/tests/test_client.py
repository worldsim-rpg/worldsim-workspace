"""Тесты AnthropicClient — с мок-SDK, без реальных API-вызовов."""

import os
import time
from unittest.mock import MagicMock, patch, call as mock_call

import pytest

from worldsim_prompts.client import AnthropicClient, CallLog


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _make_client(api_key: str = "sk-test") -> AnthropicClient:
    with patch("worldsim_prompts.client.anthropic.Anthropic"):
        return AnthropicClient(api_key=api_key)


def _make_message(text: str = "response", input_tokens: int = 10, output_tokens: int = 20) -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = text
    msg = MagicMock()
    msg.content = [block]
    msg.usage.input_tokens = input_tokens
    msg.usage.output_tokens = output_tokens
    return msg


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------


def test_init_with_explicit_key():
    with patch("worldsim_prompts.client.anthropic.Anthropic") as mock_ant:
        AnthropicClient(api_key="sk-explicit")
        mock_ant.assert_called_once_with(api_key="sk-explicit")


def test_init_from_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-from-env")
    with patch("worldsim_prompts.client.anthropic.Anthropic"):
        client = AnthropicClient()
    assert client is not None


def test_init_no_key_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with patch("worldsim_prompts.client.load_dotenv"):
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            AnthropicClient()


def test_debug_from_env(monkeypatch):
    monkeypatch.setenv("WORLDSIM_DEBUG", "1")
    with patch("worldsim_prompts.client.anthropic.Anthropic"):
        client = AnthropicClient(api_key="sk-test")
    assert client._debug is True


def test_debug_override():
    with patch("worldsim_prompts.client.anthropic.Anthropic"):
        client = AnthropicClient(api_key="sk-test", debug=False)
    assert client._debug is False


# ---------------------------------------------------------------------------
# complete — happy path
# ---------------------------------------------------------------------------


def test_complete_returns_text():
    with patch("worldsim_prompts.client.anthropic.Anthropic") as mock_ant:
        mock_sdk = mock_ant.return_value
        mock_sdk.messages.create.return_value = _make_message("hello")
        client = AnthropicClient(api_key="sk-test")
        result = client.complete(model="m", system="sys", user="usr")
    assert result == "hello"


def test_complete_logs_call():
    with patch("worldsim_prompts.client.anthropic.Anthropic") as mock_ant:
        mock_sdk = mock_ant.return_value
        mock_sdk.messages.create.return_value = _make_message("hi", input_tokens=5, output_tokens=15)
        client = AnthropicClient(api_key="sk-test")
        client.complete(model="claude-test", system="s", user="u")
    log = client.last_call
    assert isinstance(log, CallLog)
    assert log.model == "claude-test"
    assert log.input_tokens == 5
    assert log.output_tokens == 15
    assert log.duration_s >= 0


def test_complete_passes_params():
    with patch("worldsim_prompts.client.anthropic.Anthropic") as mock_ant:
        mock_sdk = mock_ant.return_value
        mock_sdk.messages.create.return_value = _make_message()
        client = AnthropicClient(api_key="sk-test")
        client.complete(model="m", system="sys", user="usr", max_tokens=512, temperature=0.2)
        mock_sdk.messages.create.assert_called_once_with(
            model="m",
            max_tokens=512,
            temperature=0.2,
            system="sys",
            messages=[{"role": "user", "content": "usr"}],
        )


def test_complete_concatenates_multiple_blocks():
    with patch("worldsim_prompts.client.anthropic.Anthropic") as mock_ant:
        mock_sdk = mock_ant.return_value
        b1 = MagicMock(); b1.type = "text"; b1.text = "foo"
        b2 = MagicMock(); b2.type = "text"; b2.text = "bar"
        b3 = MagicMock(); b3.type = "tool_use"  # non-text block, should be skipped
        msg = MagicMock()
        msg.content = [b1, b2, b3]
        msg.usage.input_tokens = 1
        msg.usage.output_tokens = 1
        mock_sdk.messages.create.return_value = msg
        client = AnthropicClient(api_key="sk-test")
        result = client.complete(model="m", system="s", user="u")
    assert result == "foobar"


# ---------------------------------------------------------------------------
# complete — retry logic
# ---------------------------------------------------------------------------


def test_complete_retries_on_rate_limit():
    import anthropic as ant

    with patch("worldsim_prompts.client.anthropic.Anthropic") as mock_ant:
        with patch("worldsim_prompts.client.time.sleep"):
            mock_sdk = mock_ant.return_value
            mock_sdk.messages.create.side_effect = [
                ant.RateLimitError("rate limit", response=MagicMock(), body={}),
                _make_message("ok"),
            ]
            client = AnthropicClient(api_key="sk-test")
            result = client.complete(model="m", system="s", user="u", max_retries=3)
    assert result == "ok"
    assert mock_sdk.messages.create.call_count == 2


def test_complete_exhausts_retries():
    import anthropic as ant

    with patch("worldsim_prompts.client.anthropic.Anthropic") as mock_ant:
        with patch("worldsim_prompts.client.time.sleep"):
            mock_sdk = mock_ant.return_value
            mock_sdk.messages.create.side_effect = ant.RateLimitError(
                "rate limit", response=MagicMock(), body={}
            )
            client = AnthropicClient(api_key="sk-test")
            with pytest.raises(ant.RateLimitError):
                client.complete(model="m", system="s", user="u", max_retries=2)
    assert mock_sdk.messages.create.call_count == 3  # 1 initial + 2 retries


def test_complete_exponential_backoff():
    import anthropic as ant

    with patch("worldsim_prompts.client.anthropic.Anthropic") as mock_ant:
        with patch("worldsim_prompts.client.time.sleep") as mock_sleep:
            mock_sdk = mock_ant.return_value
            mock_sdk.messages.create.side_effect = [
                ant.RateLimitError("rl", response=MagicMock(), body={}),
                ant.RateLimitError("rl", response=MagicMock(), body={}),
                _make_message("ok"),
            ]
            client = AnthropicClient(api_key="sk-test")
            client.complete(model="m", system="s", user="u", max_retries=3)
    sleeps = [c.args[0] for c in mock_sleep.call_args_list]
    assert sleeps == [2, 4]  # 2^1, 2^2
