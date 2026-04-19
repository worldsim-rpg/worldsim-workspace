# Карта агентов

Каждый агент — это один pip-пакет в своём git-репо с **единым публичным
контрактом**: чистая функция `run(input) -> output`, где input/output —
pydantic-модели из `worldsim_schemas`.

## orchestrator

**Репо:** [`worldsim-orchestrator`](https://github.com/b3axap/worldsim-orchestrator)

**Роль:** единственный "голос" системы. Разговаривает с игроком,
оркестрирует всех остальных агентов, хранит settings, validators,
persistence.

**Содержит LLM внутри для одной операции — intent parsing** (free-text
игрока → `Intent`). Это было бы отдельным агентом, но так компактнее
(парсинг короткий, всегда зовётся перед всеми остальными).

**Пишет в канон:** `game_settings.json`, `session_log.jsonl`,
`timeline.jsonl`. Всё остальное — через патчи от агентов.

---

## world-builder

**Репо:** [`worldsim-world-builder`](https://github.com/b3axap/worldsim-world-builder)

**Роль:** мир-движок. Три подрежима:

1. `run_world_init(inspiration) -> WorldSnapshot` — генерация мира из
   вдохновения игрока. Один раз при `new`.
2. `run_location_detail(location) -> Location` — догенерация
   `full_description` и `active_elements` при первом посещении.
3. `run_turn_update(context, intent, npc_response) -> TurnPatch` — после
   хода игрока решает, что изменилось в мире: NPC, локации, факты, арки.

**Пишет в канон:** locations, characters (NPC), factions, secrets, arcs,
plot_state, world_meta. **Не трогает** `player_progression`.

---

## canon-keeper

**Репо:** [`worldsim-canon-keeper`](https://github.com/b3axap/worldsim-canon-keeper)

**Роль:** проверка консистентности. Вызывается дважды:

1. Сразу после `world-builder.run_world_init` — чистит противоречия в
   свежесгенерированном мире.
2. Перед коммитом патчей от `world-builder` и `personal-progression` —
   последний фильтр.

**Контракт:** `validate(snapshot_or_patches) -> ValidationResult` с
полями `ok: bool`, `issues: list[str]`, `fixed: PatchList`.

**Пишет в канон:** ничего напрямую. Отклоняет или предлагает
исправления, которые orchestrator применяет.

---

## scene-master

**Репо:** [`worldsim-scene-master`](https://github.com/b3axap/worldsim-scene-master)

**Роль:** финальный рендер сцены для игрока. Получает слепок канона,
фильтрует через `known_facts` и `discovered/visited` флаги, и рисует
атмосферную сцену. Никогда не раскрывает `hidden_traits`,
нераскрытые `secrets`, `hidden_agenda` фракций.

**Контракт:** `render(context) -> str` — готовый текст для терминала.

**Пишет в канон:** ничего. Чистый рендер.

---

## npc-mind

**Репо:** [`worldsim-npc-mind`](https://github.com/b3axap/worldsim-npc-mind)

**Роль:** когда игрок взаимодействует с конкретным NPC (диалог,
вопрос), этот агент думает от лица NPC. Строго в пределах
`knowledge`, `goals`, `public_traits`, `attitude_to_player`.

**Контракт:** `respond(npc, player_intent, context) -> NPCResponse` с
полями `speech: str`, `action_hint: str | None`, `attitude_delta: float`.

**Пишет в канон:** ничего напрямую. Его ответ становится входом для
`world-builder.run_turn_update`, который оформляет это патчами.

---

## personal-progression

**Репо:** [`worldsim-personal-progression`](https://github.com/b3axap/worldsim-personal-progression)

**Роль:** обновление прогрессии игрока после каждого хода. Решает:

- какие `skill_counters` инкрементнуть;
- как изменилась `reputation[faction_id]`;
- добавился ли новый факт в `known_facts`;
- изменилось ли `condition` (tired/wounded/…);
- дошёл ли какой-то `skill_counter` до порога, чтобы прокачать атрибут.

**Контракт:** `update(progression, intent, outcome) -> TurnPatch`.

**Пишет в канон:** только `player_progression.json`.

---

## Контракты между агентами

Все передают друг другу pydantic-модели из `worldsim_schemas`. Никакой
свободной формы. Формат запроса к LLM — всегда JSON. Каждый агент
валидирует вход и выход.
