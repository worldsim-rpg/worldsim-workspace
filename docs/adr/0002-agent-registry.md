# 0002. Диспатч агентов через agents.toml + AgentManifest

- **Статус:** accepted
- **Дата:** 2026-04-19
- **Связано с:** [0003](0003-no-inter-agent-bus.md)

## Context

До этого решения `worldsim-orchestrator/loop.py` хардкодил вызовы
агентов: `_import_agent("worldsim_world_builder", "run_turn_update")` +
if/elif по фазе хода. При 4 параллельно работающих разработчиках это
гарантированный merge-conflict: каждый, кто трогает цикл, правит один
и тот же файл.

Добавление нового агента (например, `combat-resolver`) требовало
изменения `loop.py` — чужого кода, с чужими тестами.

## Decision

Вводим декларативный реестр:

- `worldsim-workspace/agents.toml` — каноничный список агентов.
  Каждая запись — `AgentManifest` (pydantic): `name`, `package`,
  `entrypoint`, `phase`, `version`, `optional`, `model_tier`.
- `AgentPhase` (enum в `worldsim_schemas.agent_contract`) — закрытый
  перечень фаз хода. Одна фаза = один агент (см. Alternatives).
- `worldsim-orchestrator/src/worldsim_orchestrator/registry.py` —
  загружает TOML, валидирует манифесты, предоставляет
  `reg.call(phase, payload, ...)`.
- `loop.py` не импортирует агентов напрямую — только вызывает registry.
- Каждый агент-пакет экспортирует `MANIFEST` или `MANIFESTS` в
  `__init__.py` (самодекларация, проверяется тестом consistency с
  `agents.toml`).

## Alternatives considered

- **Оставить if/elif в `loop.py`.** Отвергнуто: merge-conflict hell
  при 4 разработчиках, плохая изоляция смены состава агентов.
- **Ручной реестр в коде** (`REGISTRY: dict[AgentPhase, Callable]` в
  orchestrator). Лучше, но всё ещё требует правки orchestrator-кода
  для добавления агента и не годится для non-coder редактирования.
- **Несколько агентов на одну фазу (fan-out).** Преждевременно:
  сейчас у каждой фазы один владелец, fan-out добавит вопрос порядка,
  мержа TurnPatch, тестов на порядок вызовов. Когда/если понадобится —
  новый ADR и расширение Registry.
- **Полноценный plugin discovery через entry points в `pyproject.toml`**
  (`[project.entry-points."worldsim.agents"]`). Более питонично, но
  добавляет установочный этап: агент должен быть pip-installed, иначе
  не виден. Не подходит для workflow "клонировал репо рядом — и
  работает".

## Consequences

**Плюсы:**
- Добавление агента = новый репо с `MANIFEST` + строка в `agents.toml`.
  `loop.py` не трогается.
- Конфликты на добавлении агентов физически разнесены (каждый трогает
  свой файл + отдельную строку в TOML).
- Тест `test_registry.py` валидирует полный реестр за 0.1 сек на CI.

**Минусы / trade-offs:**
- Два источника истины (agents.toml + MANIFEST в пакете).
  Митигация — тест consistency.
- Фиксированный перечень `AgentPhase`: новую фазу вводит тот, кто
  трогает `worldsim_schemas` и orchestrator. Это фича, не баг —
  новые фазы = архитектурное решение, требует обсуждения.

**Что теперь нельзя:**
- Два агента на одной фазе. Registry поднимает `RegistryError`.
- Вызывать агента в обход registry (напрямую `__import__`). Контракт
  только через `reg.call(phase, ...)`.

## Notes

- Реализация: `worldsim-workspace/agents.toml`,
  `packages/schemas/src/worldsim_schemas/agent_contract.py`,
  `worldsim-orchestrator/src/worldsim_orchestrator/registry.py`.
- Тесты: `worldsim-orchestrator/tests/test_registry.py`.
- Гайд для добавления агента: `docs/agent-contract.md`.
