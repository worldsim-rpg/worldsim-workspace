# worldsim-schemas

Общие pydantic-модели канона мира. Этот пакет — **единственный источник
правды** о форме данных. Все агент-репо получают копию через `sync-all.sh`.

## Установка (в orchestrator или тестах)

```bash
pip install -e ../../worldsim-workspace/packages/schemas
```

## Состав

- `schemas.py` — все модели: `WorldMeta`, `Location`, `Character`, `Faction`,
  `Secret`, `Arc`, `PlayerProgression`, `Intent`, `PatchOp`, `TurnPatch` и т.п.

## Как вносить изменения

1. Отредактируй `src/worldsim_schemas/schemas.py`.
2. Из корня `worldsim-workspace/` запусти `./repo-setup/sync-all.sh` — это
   раскатает обновлённые схемы во все агент-репо (в `_schemas/`).
3. Не редактируй `_schemas/` в агент-репо руками — скрипт перезапишет.
