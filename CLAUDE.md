# CLAUDE.md — worldsim-workspace

Правила для Claude Code, работающего в этом репо.

## Что это

Source of truth для мульти-агентной системы worldsim. Здесь — общие
pydantic-схемы канона, prompt-framework, документация, sync-скрипты,
HTML-гайды.

## Границы этого репо

- ЭТО репо **не содержит агентов**. Логика агентов — в их
  собственных репо (см. `repo-setup/agents.txt`).
- ЭТО репо **не хранит данные игры**. Сейвы — в
  `repos/worldsim-orchestrator/saves/`.

## Что тут можно менять

| Путь | Зачем |
|---|---|
| `packages/schemas/src/worldsim_schemas/schemas.py` | Форма канона. После правок — `./repo-setup/sync-all.sh`. |
| `packages/prompts/src/worldsim_prompts/` | Базовый клиент и утилиты промптов. После правок — sync. |
| `docs/*.md` | Документация. Sync не нужен, но обновляй ссылки в README. |
| `GUIDES/*.html` | HTML-гайды для non-coder пользователей. |
| `repo-setup/agents.txt` | Список агентов, которым делается sync. |
| `test-fixtures/` | Примеры миров/ходов для интеграционных тестов. |

## Что делать после правок в `packages/`

1. Убедиться, что pydantic-модели импортируются:
   `python -c "import worldsim_schemas; print(dir(worldsim_schemas))"`.
2. Запустить sync: `./repo-setup/sync-all.sh`.
3. Пройтись по тестам каждого агента (см. `docs/setup.md`).
4. Отдельный PR сюда (изменение схем) + отдельный PR в каждый агент,
   где пришлось подправить логику под новые типы.

## Никогда

- Не коммить `.env`.
- Не добавляй агентам прямой доступ к файлам канона — только через
  orchestrator.
- Не реализуй новый агент прямо в workspace. Используй
  `repo-setup/generate-scaffold.sh` и создай отдельный репо.
