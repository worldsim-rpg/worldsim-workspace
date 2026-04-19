# Модель канона

Канон мира — набор JSON-файлов в папке сейва. Это **единственный
источник правды** о мире. LLM его не помнит — он каждый раз читает
только нужные куски.

## Физическая структура сейва

```
repos/worldsim-orchestrator/saves/<world_id>/
├── world_meta.json         — title, genre, tone, themes, premise, tick
├── game_settings.json      — язык, сложность, темп, per-agent модели
├── locations.json          — список Location
├── characters.json         — список Character (и NPC, и игрок с is_player=true)
├── factions.json           — список Faction
├── secrets.json            — список Secret
├── arcs.json               — список Arc
├── plot_state.json         — main_tensions, active_arcs-ссылки, dramatic_pressure
├── player_progression.json — PlayerProgression
├── timeline.jsonl          — append-only TimelineEvent, по одному на строку
└── session_log.jsonl       — append-only лог: что игрок ввёл, что отрендерилось,
                               какие патчи применились, за какое время
```

## Четыре слоя истины

| Слой | Где живёт |
|---|---|
| **Ontological** — что есть | `Character`, `Location`, `Faction`, `Secret` (все поля) |
| **Epistemic** — кто что знает | `Character.knowledge`, `PlayerProgression.known_facts` |
| **Narrative** — что сейчас важно | `Arc.urgency`, `PlotState.dramatic_pressure`, `Arc.stage` |
| **Player-facing** — что видит игрок | не хранится отдельно; `scene-master` фильтрует на лету |

## Правила записи

1. **Никаких прямых перезаписей**. Любое изменение — `PatchOp` через
   `persistence.apply_patches`.
2. **Зоны ответственности по агентам:**
   - `world-builder` → locations, characters (кроме игрока), factions,
     secrets, arcs, plot_state, world_meta;
   - `personal-progression` → player_progression;
   - `orchestrator` → game_settings, session_log, timeline.
   Два агента никогда не пишут в один файл.
3. **Валидация пишется через pydantic** на этапе загрузки и сохранения.
   Если файл повреждён — игра падает сразу, а не на 20-м ходу.

## Ленивая детализация локаций

- `Location.short_description` заполняется при world-init (строка-две).
- `Location.full_description` — `null` до первого визита. При первом
  входе игрока в локацию `world-builder.run_location_detail` генерит
  детальное описание.
- Цель: мир из 10 локаций стоит в ~5 раз дешевле в токенах при создании.

## Timeline

Append-only лог в `.jsonl`. Каждая строка:

```json
{"tick": 12, "type": "conversation", "summary": "Игрок заговорил с Мирой о пропавшем грузе."}
```

Используется:
- для отладки (понять, что происходило);
- как краткая память в `context_builder` — последние 5-10 событий
  передаются в контекст каждого агентного вызова.

## Session log

Тоже append-only `.jsonl`. Каждый ход записывается:

```json
{
  "tick": 12,
  "timestamp": "2026-04-19T10:22:01",
  "player_input": "спросить Миру о грузе",
  "intent": {...},
  "rendered_scene": "...",
  "patches_applied": [...],
  "tokens": {"input": 2340, "output": 580}
}
```

Полезно для дебага, A/B-тестов промптов, и чтобы игрок мог откатить ход.
