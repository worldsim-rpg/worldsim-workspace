# Hard / soft constraints

## Hard constraints — детерминированные правила

Проверяются Python-кодом в `orchestrator/validators.py` **до** того, как
любой LLM-агент что-то напишет. Если hard-правило нарушено — действие
игрока либо отклоняется с объяснением, либо переформулируется.

### Список hard-правил

| Код | Правило | Когда срабатывает |
|---|---|---|
| `NO_ITEM` | У игрока нет этого предмета в inventory | intent = `use_item`, `give`, `combine`, ... |
| `WRONG_LOCATION` | Игрок не в той локации, где находится объект/NPC | интеракция с любой сущностью у которой есть `location_id` |
| `NOT_CONNECTED` | Локация не соединена с текущей | intent = `move` |
| `DEAD` | Целевой NPC мёртв | любая интеракция с `alive=false` |
| `UNKNOWN_TO_NPC` | NPC не может обсуждать факт, которого нет в его knowledge | npc-mind: agent пытается упомянуть factId которого нет в `npc.knowledge` |
| `UNKNOWN_TO_PLAYER` | Игрок ссылается на сущность, которой нет в его `known_facts` и `discovered_locations` | целью Intent указан id, о котором игрок не слышал |
| `CONDITION_BLOCKED` | Игрок слишком устал/ранен для действия | intent требует усилия, `condition=exhausted` |

### Почему именно Python, а не LLM

Все эти правила формальны. LLM их периодически нарушает (галлюцинация
предмета, телепорт персонажа). Детерминированная проверка дешевле, быстрее
и надёжнее.

## Soft constraints — числовые поля канона

Меняются через `PatchOp` от LLM-агентов. LLM решает "на сколько
изменить", но:

- все soft-поля имеют **жёсткий диапазон** (pydantic validator): например
  `attitude_to_player ∈ [-1.0, 1.0]`, `dramatic_pressure ∈ [0.0, 1.0]`;
- любые изменения вне диапазона отклоняются `canon-keeper`.

### Список soft-полей

| Поле | Диапазон | Кто меняет |
|---|---|---|
| `Character.attitude_to_player` | [-1, 1] | world-builder, подсказывает npc-mind через `attitude_delta` |
| `Faction.relations[id]` | [-1, 1] | world-builder |
| `PlayerProgression.reputation[faction_id]` | [-1, 1] | personal-progression |
| `Arc.urgency` | [0, 1] | world-builder |
| `Arc.progress` | [0, 1] | world-builder, монотонно вверх |
| `Arc.clarity_to_player` | [0, 1] | world-builder, монотонно вверх |
| `PlotState.dramatic_pressure` | [0, 1] | world-builder |
| `Secret.discoverability` | [0, 1] | world-builder |

## Инварианты канона

Эти проверки — в `canon-keeper` (LLM) + дубликат в `validators.py`
(Python) для самых критичных.

1. **Reference integrity** — все `faction_id`, `location_id`, `character_id`,
   `arc.involved_entities[*]` должны указывать на существующие сущности.
2. **Location graph connectivity** — граф `connected_to` двунаправленный:
   если `A in B.connected_to`, то `B in A.connected_to`.
3. **Knowledge monotonicity** — факт, который NPC знал, не может
   "забыться" сам по себе (без явного события потери памяти).
4. **Death finality** — `alive: false → true` требует явного
   TimelineEvent типа `resurrection` или `mistaken_death`.
5. **Secret discoverability** — `Secret.status` меняется только по
   цепочке `hidden → hinted → revealed`, не в обратную сторону.
6. **Arc stage monotonicity** — `Arc.stage` не откатывается назад, кроме
   явного `reversal` события.

## Что НЕ считается hard constraint

- Отношения NPC к игроку ("Мира точно не согласится") — это soft.
- Готовность фракции пойти на конфликт — soft.
- Доступность тайны (`discoverability`) — soft.

Всё это — предмет убеждения, обстоятельств, давления. Жёстких правил
тут нет.
