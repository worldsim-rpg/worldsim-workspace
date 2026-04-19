# Контракт агента

Каждый LLM-агент worldsim — Python-пакет, который orchestrator вызывает
через registry. Никаких прямых импортов из `loop.py` нет. Добавление
нового агента сводится к двум шагам: создать пакет по шаблону и добавить
секцию в `agents.toml`.

## Что такое агент

Агент — это один или несколько callable'ов, каждый из которых:

- принимает `dict` payload (вход, зависит от фазы — см. ниже),
- принимает `client: AnthropicClient` и `model: str` как kwargs,
- возвращает pydantic-объект или dict (зависит от фазы).

Агент НЕ:

- читает файлы канона напрямую (`saves/`, `session_log.jsonl`),
- импортирует другие агенты,
- правит `_schemas/` или `_prompts/` руками — они синкаются из workspace.

## Обязательные экспорты

В `__init__.py` агент-пакета:

```python
from worldsim_schemas import AgentManifest, AgentPhase
from .agent import run  # или run_turn_update, validate, etc.

MANIFEST = AgentManifest(
    name="my-agent",
    package="worldsim_my_agent",
    entrypoint="run",
    phase=AgentPhase.WORLD_UPDATE,
    model_tier="heavy",
    description="Одна строка: что делает.",
)

__all__ = ["run", "MANIFEST"]
```

Если агент обслуживает несколько фаз (как `world-builder`), экспортируется
`MANIFESTS: list[AgentManifest]` вместо одиночного `MANIFEST`.

`MANIFEST` — самодекларация агента. Каноничный реестр живёт в
`worldsim-workspace/agents.toml`. Тест `test_registry.py` в orchestrator
проверяет, что самодекларация и agents.toml согласованы.

## Фазы

См. `AgentPhase` в `worldsim_schemas.agent_contract`. Порядок вызова
детерминирован:

1. `world_init` — при создании нового мира (off-turn).
2. `location_detail` — при первом входе в локацию (off-turn).
3. `npc_respond` — опционально, если `intent == "converse"`.
4. `world_update` — основное обновление мира.
5. `progression_update` — апдейт прогрессии игрока.
6. `canon_validate` — валидация патчей до применения.
7. `scene_render` — финальный рендер сцены.

Одну фазу обслуживает ровно один агент. Попытка объявить две записи
с одной и той же фазой — ошибка загрузки реестра.

## Контракты payload/return по фазам

| Фаза | payload | return |
|---|---|---|
| `world_init` | `{inspiration, settings}` | `WorldSnapshot` (dict) |
| `location_detail` | `{location_id, context}` | `Location` (patch) |
| `npc_respond` | `{npc, intent, context}` | `str` (реплика) |
| `world_update` | `{intent, npc_response, context}` | `TurnPatch` |
| `progression_update` | `{intent, world_patch, progression, context}` | `TurnPatch` |
| `canon_validate` | `{patches, snapshot}` | `{ok: bool, issues: list[str]}` |
| `scene_render` | `{context, last_action_summary, opening?}` | `str` |

Точные формы входов/выходов — pydantic-модели в
`worldsim_schemas.schemas`. Payload сериализуется оркестратором через
`.model_dump()` — агент работает с dict'ами.

## Добавление нового агента

1. `cd repos/worldsim-workspace && ./repo-setup/generate-scaffold.sh <name> <pkg> "<desc>"`.
2. Реализовать `run()` в сгенерированном `src/<pkg>/agent.py`.
3. Добавить `MANIFEST` в `__init__.py` пакета (см. выше).
4. Добавить секцию `[[agents]]` в `worldsim-workspace/agents.toml`.
5. Добавить имя в `worldsim-workspace/repo-setup/agents.txt` (для sync).
6. `./repo-setup/sync-all.sh`.
7. В orchestrator: `pip install -e ../worldsim-<name>` (локально) либо
   добавить в `pyproject.toml` dependencies (когда опубликуется).
8. `cd ../worldsim-orchestrator && python -m pytest tests/test_registry.py`.

Важно: `loop.py` при этом НЕ трогается. Если правка `loop.py` требуется —
скорее всего вводится новая фаза, и это требует отдельного обсуждения (ADR).
