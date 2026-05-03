"""Тонкая обёртка над anthropic.Anthropic для worldsim-агентов."""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

import anthropic
from dotenv import load_dotenv


@dataclass
class CallLog:
    model: str
    input_tokens: int
    output_tokens: int
    duration_s: float


# Сигнатура колбэка dev-лога: принимает dict-запись, ничего не возвращает.
DevLogCallback = Callable[[dict], None]


class AnthropicClient:
    """
    Единый клиент для всех агентов.

    - Читает ANTHROPIC_API_KEY из окружения (или .env рядом с вызовом).
    - Поддерживает WORLDSIM_DEBUG=1 — печатает system/user/response в stderr.
    - Делает простой retry на rate-limit / transient errors.
    - Принимает опциональный dev_log_callback: вызывается после каждого
      LLM-вызова с dict-записью для developer JSONL-лога.
    """

    def __init__(
        self,
        api_key: str | None = None,
        debug: bool | None = None,
        dev_log_callback: DevLogCallback | None = None,
    ):
        load_dotenv()
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY не задан. Скопируйте .env.example в .env и "
                "вставьте ключ."
            )
        self._client = anthropic.Anthropic(api_key=key)
        self._debug = debug if debug is not None else os.environ.get("WORLDSIM_DEBUG") == "1"
        self._dev_log_callback = dev_log_callback
        self.last_call: CallLog | None = None

        # Контекст для dev-лога, проставляется извне перед вызовом агента.
        self._log_turn: int | None = None
        self._log_agent: str | None = None

    def complete(
        self,
        *,
        model: str,
        system: str,
        user: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        max_retries: int = 3,
    ) -> str:
        """Возвращает текст ответа ассистента. Без структурных проверок."""

        if self._debug:
            _log(f"=== SYSTEM ({model}) ===\n{system}\n=== USER ===\n{user}\n")

        attempt = 0
        start = time.time()
        error_msg: str | None = None
        msg = None
        while True:
            try:
                msg = self._client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                break
            except (anthropic.RateLimitError, anthropic.APIStatusError) as e:
                attempt += 1
                if attempt > max_retries:
                    error_msg = str(e)
                    duration = time.time() - start
                    if self._dev_log_callback is not None:
                        self._dev_log_callback(
                            _make_dev_entry(
                                turn=self._log_turn,
                                agent=self._log_agent,
                                model=model,
                                prompt_tokens=0,
                                completion_tokens=0,
                                duration_ms=int(duration * 1000),
                                system_prompt_hash=_hash8(system),
                                error=error_msg,
                            )
                        )
                    raise
                delay = 2**attempt
                _log(f"[retry {attempt}] {type(e).__name__}, sleeping {delay}s")
                time.sleep(delay)

        duration = time.time() - start
        text = "".join(block.text for block in msg.content if block.type == "text")

        self.last_call = CallLog(
            model=model,
            input_tokens=msg.usage.input_tokens,
            output_tokens=msg.usage.output_tokens,
            duration_s=duration,
        )

        if self._dev_log_callback is not None:
            self._dev_log_callback(
                _make_dev_entry(
                    turn=self._log_turn,
                    agent=self._log_agent,
                    model=model,
                    prompt_tokens=msg.usage.input_tokens,
                    completion_tokens=msg.usage.output_tokens,
                    duration_ms=int(duration * 1000),
                    system_prompt_hash=_hash8(system),
                    error=None,
                )
            )

        if self._debug:
            _log(
                f"=== RESPONSE ({msg.usage.input_tokens}→{msg.usage.output_tokens} tok, "
                f"{duration:.1f}s) ===\n{text}\n"
            )

        return text


def _hash8(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:8]


def _make_dev_entry(
    *,
    turn: int | None,
    agent: str | None,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration_ms: int,
    system_prompt_hash: str,
    error: str | None,
) -> dict:
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
    return {
        "ts": ts,
        "turn": turn,
        "agent": agent,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "duration_ms": duration_ms,
        "system_prompt_hash": system_prompt_hash,
        "error": error,
    }


def _log(msg: str) -> None:
    import sys

    print(msg, file=sys.stderr, flush=True)
