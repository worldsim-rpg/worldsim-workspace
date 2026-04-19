# CLAUDE.md — {{AGENT_NAME}}

Правила для Claude Code, работающего в этом репо.

## Что это

{{ONE_LINE_DESCRIPTION}}

Часть мульти-агентной системы [worldsim](https://github.com/worldsim-rpg/worldsim-workspace).
Общая архитектура — в `../worldsim-workspace/docs/architecture.md`.

## Границы этого агента

- ЭТОТ агент **{{WRITES_TO_CANON}}**.
- ЭТОТ агент НЕ трогает: {{NEVER_WRITES}}.
- За общие схемы отвечает `worldsim-workspace/packages/schemas/`. Если
  нужно поменять модель канона — пиши PR туда, НЕ сюда.
- За базовый клиент/фреймворк промптов — `worldsim-workspace/packages/prompts/`.
  Не дублируй его код тут.

## Как менять поведение

1. **Промпт** — `prompts/*.md`. Это 80% случаев.
2. **Pre/post-обработка** — `src/{{PKG_NAME}}/agent.py`.
3. **Схемы** — только в workspace, потом `sync-all.sh`.

## Тесты

Прогоняй `python -m pytest -q` после любого изменения. Если в тесте
есть реальный LLM-вызов, пропускай его без API-ключа — используй
`pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), ...)`.

## Никогда

- Не импортируй `worldsim_orchestrator` — это односторонняя зависимость
  (orchestrator импортирует агента, не наоборот).
- Не читай/не пиши файлы канона напрямую. Агент работает с входными
  pydantic-моделями и возвращает pydantic-модели. Запись в канон —
  задача оркестратора.
- Не редактируй `_schemas/` или `_prompts/` — их перезапишет sync.
