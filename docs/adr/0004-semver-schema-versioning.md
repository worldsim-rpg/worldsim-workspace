# 0004. SemVer для канона, стемпинг в WorldMeta.schema_version

- **Статус:** accepted
- **Дата:** 2026-04-19
- **Связано с:** [0001](0001-one-way-schema-sync.md)

## Context

Pydantic-схемы канона (`Character`, `Location`, `WorldState`, ...) — живой
продукт. В ходе PoC они точно будут меняться: добавятся поля, переименуются
связи, поменяется shape. Одновременно у игроков на диске лежат сейвы в
старом формате.

Без явного версионирования:
- Старый сейв тихо грузится в новую модель → pydantic молча дропает
  неизвестные поля или падает с validation error в неожиданном месте.
- Агент, работающий с `_schemas/` версии N, может быть вызван orchestrator'ом
  с схемами версии N+1 — и никто этого не заметит, пока не упадёт тест.

Нужна инфраструктура версионирования, доступная людям и машинам.

## Decision

- Каноническая версия схем — константа `SCHEMA_VERSION` в
  `packages/schemas/src/worldsim_schemas/version.py`. SemVer:
  `MAJOR.MINOR.PATCH`.
- `WorldMeta` имеет обязательное поле `schema_version: str`. Orchestrator
  штампует его при сохранении; при загрузке сверяет MAJOR.
- Политика SemVer:
  - **MAJOR** bump — ломающее изменение (удаление поля, смена типа,
    переименование, ужесточение валидации). Старые сейвы требуют миграции.
  - **MINOR** bump — совместимое расширение (новое optional поле,
    новое значение в enum). Старый сейв грузится без проблем.
  - **PATCH** bump — правки валидаторов, опечатки в docstrings, ничего
    не меняющее в shape.
- `load_world()` при MAJOR mismatch → `SchemaVersionMismatch`, отказ грузить.
  При MINOR mismatch — warning + загрузка.
- Сейв без `schema_version` (pre-versioning artifact) → трактуется как
  `0.0.0`, грузится с warning, writeback при следующем save проставит
  текущую.
- `check-version-bump.sh` — pre-commit/CI скрипт: если `schemas.py`
  изменён, но `version.py` не bumped — падает.

## Alternatives considered

- **Монотонный integer** (`SCHEMA_VERSION = 7`). Проще, но теряется
  различие "сломал vs расширил". Каждое изменение требует миграции сейвов,
  даже если добавил optional поле.
- **Хэш структуры** (sha256 от dump schema). Детерминистично, но
  нечитаемо для человека и непригодно для политики "MAJOR — ломающее".
- **Версия через pydantic model discriminator** (`__version__` в каждой
  модели). Гранулярнее, но усложняет чтение сейвов — каждая подмодель
  несёт свой version, legacy load становится матрёшкой.
- **Без версионирования, полагаемся на тесты.** Отвергнуто: тест не
  защитит игрока с сейвом на диске от тихого data loss.

## Consequences

**Плюсы:**
- Игрок с сейвом видит внятную ошибку "schema 0.1.0, game 1.0.0,
  migration required" вместо pydantic traceback.
- Агенты при sync получают `SCHEMA_VERSION` вместе со схемами → могут
  проверить compat на старте (пока не требуется, но инфраструктура готова).
- Discipline: PR, меняющий schema без bump, валится на CI.

**Минусы / trade-offs:**
- SemVer субъективен — "это breaking или нет" требует суждения. Гайд
  в `docs/schema-versioning.md` даёт примеры, но edge-cases будут.
- Нужна дисциплина bump при каждом изменении. Проверяется скриптом,
  но человеческий фактор всё равно есть (можно bump'нуть неправильный
  сегмент).
- Миграций пока нет (только заглушка `migrations/README.md`). Первый
  MAJOR bump поднимет вопрос "как мигрировать старые сейвы" — тогда
  и пишется инфраструктура миграций.

**Что теперь нельзя:**
- Менять shape `schemas.py` без правки `version.py`. CI падает.
- Грузить сейв с `schema_version` иной MAJOR без миграции. Orchestrator
  отказывает, чтобы не было тихого data loss.

## Notes

- Реализация: `packages/schemas/src/worldsim_schemas/version.py`,
  `WorldMeta.schema_version`, `worldsim-orchestrator/src/worldsim_orchestrator/persistence.py`.
- Тесты: `worldsim-orchestrator/tests/test_schema_version.py`.
- Гайд: `docs/schema-versioning.md`.
- Check-bump скрипт: `repo-setup/check-version-bump.sh`.
