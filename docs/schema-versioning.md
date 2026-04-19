# Версионирование канона

Единственный номер, который решает совместимость — `SCHEMA_VERSION`
в `packages/schemas/src/worldsim_schemas/version.py`. SemVer:

| Часть | Когда bump | Эффект на сейвы |
|---|---|---|
| MAJOR (`1.x.x` → `2.0.0`) | Удаление/переименование поля, смена типа, инверсия инварианта | Старый сейв не грузится без миграции |
| MINOR (`1.1.x` → `1.2.0`) | Добавление опционального поля, новое enum-значение | Грузится с дефолтом, перештампуется |
| PATCH (`1.1.1` → `1.1.2`) | Docstring, comment, переименование константы без смысла | Ничего не меняется |

## Правила

1. **Любая правка `schemas.py` требует bump.** CI-скрипт
   `repo-setup/check-version-bump.sh` детектит случаи, когда `schemas.py`
   меняется в коммите, а `version.py` — нет.
2. **`schema_version` в `WorldMeta`** штампуется при каждом `save_world`
   в orchestrator. Сейв, сохранённый без версии (pre-versioning мир),
   получает `"0.0.0"` — он грузится молча, затем перештампуется.
3. **`pyproject.toml` версия schemas-пакета** движется вместе с
   `SCHEMA_VERSION`. Это не строго проверяется, но нужно для pip-разрешения
   версий когда пакет появится в индексе.

## Что делает load_world при mismatch

```python
from worldsim_orchestrator.persistence import load_world, SchemaVersionMismatch

try:
    snap = load_world("20260419-123456-abcdef")
except SchemaVersionMismatch as e:
    # Сейв несовместим. Нужна миграция.
    print(e)
```

Правило: **MAJOR несовпадает → падаем**. MINOR/PATCH — грузим, на save
перештампуется на текущий.

## Как делать bump

### MINOR (типичный случай)

```bash
cd repos/worldsim-workspace
# 1. Правка schemas.py (добавил поле)
# 2. Обновить version.py:
sed -i 's/SCHEMA_VERSION = "0.1.0"/SCHEMA_VERSION = "0.2.0"/' \
    packages/schemas/src/worldsim_schemas/version.py
# 3. Синхронизировать pyproject.toml
sed -i 's/version = "0.1.0"/version = "0.2.0"/' \
    packages/schemas/pyproject.toml
# 4. Sync + тесты
./repo-setup/sync-all.sh
./repo-setup/sync-check.sh
cd ../worldsim-orchestrator && python -m pytest -q
```

### MAJOR

Всё то же плюс:

5. Создать `packages/schemas/migrations/vN_to_vM.py` (см. `migrations/README.md`).
6. Подключить миграцию в `worldsim_orchestrator.persistence.load_world`.
7. Тест `test_schema_version.py`: старый сейв → load через миграцию → ok.

## Как проверить совместимость программно

```python
from worldsim_schemas import SCHEMA_VERSION, is_compatible, major

is_compatible("0.1.5")     # True (тот же MAJOR)
is_compatible("1.0.0")     # False (разный MAJOR)
major("0.3.7")             # 0
```
