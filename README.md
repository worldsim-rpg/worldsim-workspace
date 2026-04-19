# worldsim-workspace

Source of truth для мульти-агентной системы worldsim. Здесь живут:

- общие pydantic-схемы канона (`packages/schemas/`);
- базовый prompt-фреймворк и Anthropic-клиент (`packages/prompts/`);
- документация системы (`docs/`);
- sync-скрипты, раскидывающие схемы/промпты по агент-репо (`repo-setup/`);
- тестовые фикстуры (`test-fixtures/`);
- HTML-гайды для non-coder пользователей (`GUIDES/`).

## Быстрый старт разработки

См. [`docs/setup.md`](docs/setup.md).

## Документы

| Документ | О чём |
|---|---|
| [architecture.md](docs/architecture.md) | Общая архитектура системы |
| [agent-map.md](docs/agent-map.md) | Карта агентов, их контракты и зоны ответственности |
| [canon-model.md](docs/canon-model.md) | Что такое канон, как он устроен, что куда пишется |
| [constraints.md](docs/constraints.md) | Hard и soft constraints — что проверяется и где |
| [loop.md](docs/loop.md) | Цикл хода, последовательность вызовов агентов |
| [branch-strategy.md](docs/branch-strategy.md) | Ветки, синк, релиз |
| [setup.md](docs/setup.md) | Как развернуть всё локально |

## Синхронизация

После правок в `packages/schemas/` или `packages/prompts/` нужно раскатать
изменения по всем агент-репо:

```bash
./repo-setup/sync-all.sh
```

Скрипт копирует:
- `packages/schemas/src/worldsim_schemas/` → `repos/<agent>/_schemas/`
- `packages/prompts/src/worldsim_prompts/` → `repos/<agent>/_prompts/`
- `GUIDES/` не синкается, он только тут.

Список агентов, которым раскатывается, — в `repo-setup/agents.txt`.

## GUIDES

- [dev-guide.html](GUIDES/dev-guide.html) — для тех, кто не кодит сам и работает
  через Claude Code. Как добавить фичу, как дебажить, как не сломать канон.
- [architecture-guide.html](GUIDES/architecture-guide.html) — описание того,
  что уже реализовано и как логика устроена под капотом.
