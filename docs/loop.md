# Цикл хода

## Универсальная схема

```
восприятие → осмысление → намерение → выбор средства → действие → последствия → новое восприятие
```

Работает **одинаково** для игрока и для мира-агента (world-builder).

## Ход игрока — по шагам

```
1. Orchestrator показывает сцену (scene-master от прошлого хода или стартовая)
2. Игрок вводит free-text
3. Orchestrator: intent parsing (LLM, внутри orchestrator)
     → Intent{intent, method, target, target_raw, tone, risk_level, raw_text}
4. Orchestrator: hard-constraint validation
     → нарушение? вернуть игроку человечную ошибку, ход НЕ идёт дальше
5. Orchestrator: context build (детерминированный)
     → слепок из:
        * player_progression (полный)
        * current_location (full)
        * connected_locations (short)
        * nearby NPCs (full для тех, что в локации игрока)
        * related factions, arcs, secrets (только известные игроку)
        * последние 5-10 timeline events
6. [ветка диалога] Если Intent касается конкретного NPC:
     npc-mind.respond(npc, intent, context) → NPCResponse
7. world-builder.run_turn_update(context, intent, npc_response)
     → TurnPatch (world-side)
8. personal-progression.update(progression, intent, outcome)
     → TurnPatch (player-side)
9. canon-keeper.validate(patches_world + patches_player)
     → ok → идём дальше; fail → чинит или отклоняет, возвращается на шаг 7
10. Orchestrator: persistence.apply(patches)
     → запись в файлы сейва
11. scene-master.render(new_context) → текст сцены
12. Orchestrator: печатает сцену, инкрементирует tick, пишет session_log
13. GOTO 2
```

## Ход мира-агента (world-builder) — тот же цикл внутри шага 7

Когда `world-builder.run_turn_update` вызывается, он у себя в голове
проходит тот же цикл за NPC/фракции:

```
1. восприятие   = актуальный срез канона + intent игрока + ответ NPC
2. осмысление   = напряжения, цели NPC, позиции фракций
3. намерение    = что бы NPC/фракции сделали в ответ на действие игрока
4. выбор сред-  = какие их ресурсы, связи, знания применимы
5. действие     = конкретные шаги (NPC идёт туда, фракция распускает слух)
6. последствия  = TurnPatch, который world-builder вернёт наверх
```

Поэтому один и тот же агент симулирует "что случилось" с точки зрения
мира, без привязки к игроку.

## Создание мира — одноразовый pipeline

```
1. CLI: orchestrator.new спрашивает у игрока вдохновение
   (genre, tone, themes, references, scale, harshness, free_notes)
   → WorldInspiration
2. world-builder.run_world_init(inspiration) → WorldSnapshot
   (все стартовые файлы канона, в памяти)
3. canon-keeper.validate(snapshot)
   → противоречия правятся в цикле max_retries=2
4. Orchestrator: persistence.save_initial(world_id, snapshot)
5. scene-master.render(initial_context) → первая сцена
6. Игрок попадает в шаг 2 ходового цикла
```

## Ленивая догенерация локации

Когда игрок впервые входит в локацию, у которой `full_description is
null`:

```
шаг 7 хода:
  world-builder.run_location_detail(location, context) → Location с полным
  описанием и active_elements
  → включается в TurnPatch как update PatchOp
```

Дешевле, чем генерить детали 10 локаций заранее.

## Token budget (ориентир)

Грубые оценки на один ход (Sonnet):

| Шаг | input tok | output tok |
|---|---|---|
| intent parsing | ~500 | ~150 |
| npc-mind (если есть) | ~1500 | ~300 |
| world-builder.turn_update | ~3000 | ~800 |
| personal-progression | ~800 | ~200 |
| canon-keeper.validate | ~1000 | ~150 |
| scene-master.render | ~2000 | ~400 |
| **всего за ход** | **~8800** | **~2000** |

С prompt caching на системных промптах — в разы дешевле. См.
[packages/prompts](../packages/prompts) — там предусмотрен caching.
