# worldsim-prompts

Общий prompt-фреймворк и Anthropic-клиент для всех агентов.

## Что внутри

- `client.py` — обёртка над `anthropic.Anthropic`, читает `.env`,
  поддерживает `WORLDSIM_DEBUG=1` для логирования сырых запросов/ответов,
  делает базовый retry/backoff.
- `base.py` — функции для сборки промптов: `load_prompt(path)`,
  `render(template, **vars)`, `call_json(client, system, user, model, schema)`
  с извлечением JSON из ответа и валидацией через pydantic.

## Почему оно общее

Все агенты делают одну и ту же базовую вещь: собрать system+user, дернуть
Claude, достать JSON, провалидировать через pydantic-модель. Не хочется
это копипастить в 6 местах.

## Использование в агенте

```python
from worldsim_prompts import AnthropicClient, call_json
from worldsim_schemas import TurnPatch

client = AnthropicClient()
patch = call_json(
    client,
    system=load_prompt("prompts/turn_update.md"),
    user=...,  # сериализованный контекст
    model="claude-sonnet-4-6",
    schema=TurnPatch,
)
```
