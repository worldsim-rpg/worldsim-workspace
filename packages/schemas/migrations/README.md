# Миграции канона

Каждый bump **MAJOR** версии (`SCHEMA_VERSION` в `../src/worldsim_schemas/version.py`)
требует миграцию — иначе сейвы старше текущего MAJOR не смогут загрузиться
(`SchemaVersionMismatch` из `worldsim_orchestrator.persistence`).

## Когда нужен MAJOR

- Удаление поля pydantic-модели.
- Переименование поля (без обратно-совместимого alias).
- Смена типа поля (int → str, optional → required).
- Инверсия инварианта (например, `attributes ∈ [0,1]` → `[-1,1]`).

MINOR (добавление опционального поля, новое enum-значение) миграции не требует.

## Структура файла миграции

```
migrations/
├── README.md                (этот файл)
├── v0_to_v1.py              (скелет — писать при первом MAJOR bump)
└── v1_to_v2.py              ...
```

Каждый файл экспортирует:

```python
FROM_MAJOR = 0
TO_MAJOR = 1

def migrate(meta: dict, locations: list[dict], characters: list[dict],
            factions: list[dict], secrets: list[dict], arcs: list[dict],
            plot_state: dict, player_progression: dict) -> dict:
    """
    Принимает dict'ы сейва (не pydantic — старые модели могут не парситься
    в новой версии). Возвращает dict со всеми переработанными кусками
    в той же форме, что ждёт новая версия схем.
    """
    ...
```

## Применение

Пока миграции не подключены автоматически — при MAJOR mismatch
`load_world` падает с `SchemaVersionMismatch`. Первый bump MAJOR
(0 → 1) должен:

1. Завести первый файл миграции под этим README.
2. Добавить в `worldsim_orchestrator.persistence.load_world` попытку
   применить подходящую миграцию до `WorldMeta.model_validate`.
3. Написать тест: сейв v0 → load → migrate → проверить инварианты новой версии.

Пока не было ни одного MAJOR bump → миграций нет, инфраструктура на стопе.
