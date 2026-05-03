# Plan: Phased World Generation

**Problem:** `run_world_init` генерирует весь мир в одном LLM-вызове (~20k символов JSON,
8 типов сущностей, ~40 объектов). Вероятность schema-compliance всех объектов одновременно
математически мала: при p=0.97 на объект → `0.97^40 ≈ 29%` успеха за прогон.

**Эффект:** постоянные pydantic ValidationError на разных полях при каждом запуске.
Coerce-слой в `_assemble_snapshot` только маскирует симптомы.

---

## Решение: поэтапная генерация

Разбить один вызов на **5 последовательных вызовов**, каждый — один тип сущностей,
малый JSON, схема инлайн в промпте.

### Этапы

| # | Вызов | Выход | Макс. токены |
|---|---|---|---|
| 1 | `_gen_meta_locations` | `WorldMeta` + `list[Location]` | 3 000 |
| 2 | `_gen_factions` | `list[Faction]` | 2 000 |
| 3 | `_gen_characters` | `list[Character]` (incl. pc) | 4 000 |
| 4 | `_gen_secrets_arcs` | `list[Secret]` + `list[Arc]` | 3 000 |
| 5 | `_gen_plot_player` | `PlotState` + `PlayerProgression` | 2 000 |

Каждый вызов получает в контексте результаты предыдущих (только ID + имена, не полные объекты).

---

## Промпты

Каждый этап — отдельный `.md` файл в `worldsim-world-builder/prompts/`:

```
prompts/
  world_init_meta_locations.md   # этап 1
  world_init_factions.md         # этап 2
  world_init_characters.md       # этап 3
  world_init_secrets_arcs.md     # этап 4
  world_init_plot_player.md      # этап 5
  world_init.md                  # (сохранить как legacy, удалить после перехода)
```

Каждый промпт обязан содержать:
1. Точные имена полей и типы для выдаваемых сущностей (копия из pydantic-схемы)
2. Пример минимального корректного объекта
3. Список обязательных vs опциональных полей
4. Ограничение: `Только JSON-массив [...]. Никакого текста вне JSON.`

---

## Изменения в коде

### `worldsim-world-builder/src/worldsim_world_builder/agent.py`

Заменить:
```python
def run_world_init(input, *, client, model) -> WorldSnapshotDict:
    system = load_prompt(_PROMPTS / "world_init.md")
    raw = client.complete(model=model, ..., max_tokens=16000)
    parsed = extract_json(raw)
    return _assemble_snapshot(parsed)
```

На:
```python
def run_world_init(input, *, client, model) -> WorldSnapshotDict:
    inspiration = input["inspiration"]
    world_id = input["world_id"]
    settings = input["settings"]

    meta, locations = _gen_meta_locations(inspiration, world_id, settings, client, model)
    loc_ctx = [{"id": l["id"], "name": l["name"]} for l in locations]

    factions = _gen_factions(inspiration, loc_ctx, client, model)
    fac_ctx = [{"id": f["id"], "name": f["name"]} for f in factions]

    characters = _gen_characters(inspiration, loc_ctx, fac_ctx, client, model)
    char_ctx = [{"id": c["id"], "name": c["name"], "location_id": c["location_id"]} for c in characters]

    secrets, arcs = _gen_secrets_arcs(inspiration, loc_ctx, fac_ctx, char_ctx, client, model)

    plot_state, player_progression = _gen_plot_player(
        arcs, loc_ctx, fac_ctx, char_ctx, settings, client, model
    )

    return _assemble_snapshot({
        "meta": meta, "settings": settings,
        "locations": locations, "characters": characters,
        "factions": factions, "secrets": secrets,
        "arcs": arcs, "plot_state": plot_state,
        "player_progression": player_progression,
    })
```

### Retry-логика на каждом этапе

```python
def _call_with_retry(client, *, system, user, model, max_tokens, schema_cls, max_retries=2):
    for attempt in range(max_retries + 1):
        raw = client.complete(model=model, system=system, user=user, max_tokens=max_tokens)
        try:
            data = extract_json(raw)
            # validate
            if isinstance(data, list):
                return [schema_cls.model_validate(it) for it in data]
            return schema_cls.model_validate(data)
        except (ValueError, ValidationError) as e:
            if attempt == max_retries:
                raise
            # Добавить hint об ошибке в следующий вызов
            user = user + f"\n\n[VALIDATION ERROR на попытке {attempt+1}]: {e}\nИсправь и верни только валидный JSON."
```

---

## Схемы в промптах — пример (этап 1)

```markdown
## Обязательные поля Location

```json
{
  "id": "loc_snake_case",          // string, латиница
  "name": "Имя на русском",        // string
  "short_description": "...",      // string, 1-2 предложения
  "full_description": null,        // всегда null на init
  "atmosphere": "...",             // string
  "connected_to": ["loc_other"],   // list[string] — ID других локаций
  "faction_control": null          // string | null — faction_id или null
}
```
```

---

## Изменения в workspace

После рефакторинга agent.py:
1. `./repo-setup/sync-all.sh` — синхронизировать новые промпты в `_prompts/`
2. Обновить `docs/loop.md` — секция "World Init"
3. Добавить тест `tests/test_agent_phased.py` — интеграционный, проверяет что каждый этап
   возвращает корректно валидированный список

---

## Ожидаемый эффект

| Метрика | До | После |
|---|---|---|
| Размер одного LLM-ответа | ~20 000 символов | ~2 000–4 000 символов |
| max_tokens на вызов | 16 000 | 2 000–4 000 |
| Вероятность ValidationError при init | ~70% | <5% |
| Отлаживаемость | «что-то сломалось где-то в 40 объектах» | «сломался этап 3, вот конкретный объект» |
| Retry при ошибке | нет (restart всего) | retry только сломанного этапа |

---

## Приоритет

**Высокий.** Без этого каждый запуск мира — лотерея. Все остальные улучшения (новые агенты,
расширение механик) упираются в то что мир не генерируется стабильно.

## Зависимости

- Нет зависимостей от других репо, всё в `worldsim-world-builder`
- После завершения: обновить тесты в `tests/test_agent.py`
- Старый `world_init.md` промпт удалить после прохождения smoke-теста

## Оценка работы

3–4 часа разработки:
- 2 часа: написать 5 промптов с инлайн-схемами
- 1 час: рефакторинг `agent.py` + retry-логика
- 1 час: тесты + smoke run
