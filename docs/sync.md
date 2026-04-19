# Sync между workspace и агент-репо

Каноничный источник схем и промптов — `worldsim-workspace/packages/`.
Каждый агент-репо держит снимок в `_schemas/` и `_prompts/`. Снимки
пишутся автоматически — руками их править НЕЛЬЗЯ.

## Как устроено

```
workspace/packages/schemas/src/worldsim_schemas/   ← канон
workspace/packages/prompts/src/worldsim_prompts/   ← канон
        │
        │  ./repo-setup/sync-all.sh
        ▼
repos/<agent>/_schemas/       ← снимок + __header__.py + .sync-manifest
repos/<agent>/_prompts/       ← снимок + __header__.py + .sync-manifest
```

`.sync-manifest` — `sha256sum` по всем файлам снимка. Формат совместим
с `sha256sum -c`.

## Типичные сценарии

### 1. Ты добавил поле в pydantic-схему

```bash
cd repos/worldsim-workspace
# ... правка packages/schemas/src/worldsim_schemas/schemas.py
./repo-setup/sync-all.sh
./repo-setup/sync-check.sh   # должен вернуть OK
git commit   # коммит в workspace
# в каждом задетом агент-репо — отдельный PR с обновлённым _schemas/
```

### 2. CI в агент-репо упал на sync-check

Значит кто-то правил `_schemas/` или `_prompts/` руками, либо забыл
прогнать sync после изменений в workspace. Правильная реакция:

```bash
cd repos/worldsim-workspace
./repo-setup/sync-all.sh     # перекатываем канон поверх
cd ../worldsim-<agent>
git status                    # смотрим, что изменилось
git add _schemas _prompts && git commit
```

Если в workspace тоже есть незакоммиченные правки — сначала закоммить
workspace, потом гонять sync и коммитить в агент.

### 3. Сломался локальный sync-check

```bash
cd repos/worldsim-workspace
./repo-setup/sync-check.sh           # проверить все агенты
./repo-setup/sync-check.sh --local   # проверить только текущий CWD-агент
```

Вывод укажет, какие файлы разошлись или появились лишние.

## Что НЕЛЬЗЯ

- Редактировать `_schemas/*.py` или `_prompts/*.py` в агент-репо руками.
- Удалять `.sync-manifest` — без него sync-check не сработает.
- Коммитить частичный sync (например, только `_schemas/` без `_prompts/`) —
  нарушает целостность манифеста.

## Как работает CI

В каждом агент-репо лежит `.github/workflows/sync-check.yml` (скопирован из
`worldsim-workspace/repo-setup/templates/sync-check.yml`). На PR, который
трогает `_schemas/` или `_prompts/`:

1. Клонируется текущий ref workspace (по умолчанию `main`, настраивается
   через repo var `WORLDSIM_WORKSPACE_REF`).
2. Запускается `bash workspace/repo-setup/sync-check.sh --local`.
3. Мерж блокируется при drift.

В workspace CI проверяет, что `agents.toml` парсится и не содержит
дубликатов фаз.
