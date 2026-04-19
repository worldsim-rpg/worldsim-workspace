# 0003. Нет прямых вызовов агент↔агент, всё через orchestrator

- **Статус:** accepted
- **Дата:** 2026-04-19
- **Связано с:** [0002](0002-agent-registry.md)

## Context

5 LLM-агентов внутри одного хода хода должны использовать результаты друг
друга: `world_update` читает итог `npc_respond`, `canon_validate` смотрит
результат `world_update`, `scene_render` берёт финальный state. Нужен
способ передавать данные между ними.

Искушение — дать агентам знать друг о друге: `world_builder` импортирует
клиента `canon_keeper` и вызывает напрямую, либо подписывается на события
через message bus. Это выглядит "как у взрослых" (event-driven), но
ломает ключевое свойство системы — единую точку правды о состоянии
мира.

## Decision

Агенты **не знают о существовании других агентов**. Коммуникация строго
через orchestrator:

- Агент получает `AgentContext` (срез WorldState, turn context, intent)
  и возвращает `TurnPatch` (декларативный список изменений).
- Orchestrator применяет patches последовательно по фазам (см. [0002](0002-agent-registry.md)),
  накапливая их в `WorldState`.
- Следующий агент получает уже обновлённый `WorldState` — но через
  orchestrator, не от предыдущего агента напрямую.
- Нет shared memory, нет message bus, нет прямых импортов между
  агент-пакетами.

## Alternatives considered

- **Прямые вызовы агент→агент.** `world_builder` вызывает
  `canon_keeper.validate(patch)` внутри своего turn_update. Отвергнуто:
  каждая пара агентов становится coupling-парой, граф зависимостей
  растёт квадратично, порядок вызовов размазан по кодовой базе.
- **In-process event bus** (pub/sub). Элегантно, но:
  1) усложняет отладку (что на что подписано — видно только в рантайме);
  2) события теряют порядок → non-determinism в игре;
  3) state оказывается в двух местах (WorldState + bus history).
- **Shared mutable WorldState.** Каждый агент мутирует объект напрямую.
  Отвергнуто: теряется возможность откатить turn, невозможно воспроизвести
  баг по сейву, race-условия на параллельных агентах (когда/если
  появятся).
- **Actor model** (каждый агент — actor с mailbox). Overkill для 5
  агентов в однопоточном CLI. Когда/если будет multi-player сервер —
  пересмотрим.

## Consequences

**Плюсы:**
- Один источник правды о state: `WorldState` в orchestrator.
- Отладка тривиальна: падение на фазе X → смотрим входной payload и
  выход, без трассировки через event history.
- Сейв полностью восстанавливает состояние — никакого скрытого state
  в inflight-событиях.
- Агенты можно тестировать изолированно: `MANIFEST.entrypoint(payload)`
  без поднятия остальной инфраструктуры.

**Минусы / trade-offs:**
- Все данные между агентами проходят через TurnPatch/WorldState — это
  диктует форму схем и иногда заставляет протаскивать поля ради одного
  агента.
- Orchestrator становится "толстым" — знает порядок фаз, момент применения
  patch, условную логику (skip `npc_respond` если intent != converse).
  Это осознанный trade-off: лучше толстый orchestrator, чем размазанная
  логика.

**Что теперь нельзя:**
- `worldsim_world_builder` не может `import worldsim_canon_keeper`
  (и симметрично). Это ловится lint-проверкой импортов (планируется).
- Агент не может "дождаться" результата другого агента — он работает
  только с тем, что orchestrator передал в payload.
- Нельзя добавить "sidechannel" коммуникацию (файлы, sqlite,
  environment) в обход orchestrator — это равнозначно event bus.

## Notes

- Реализация контракта: `packages/schemas/src/worldsim_schemas/agent_contract.py`
  (`TurnPatch`, `AgentContext`).
- Оркестрация: `worldsim-orchestrator/src/worldsim_orchestrator/loop.py`.
- Если появится потребность в прямом обмене — пишем новый ADR с
  конкретным use-case и предложением (bus / actor / прямые вызовы).
