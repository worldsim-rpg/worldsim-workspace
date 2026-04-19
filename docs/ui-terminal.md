# Терминальный интерфейс worldsim

## Обзор

Единый, минималистичный интерфейс в терминале. Игрок видит **сцену, контекст
и строку ввода**. Всё остальное (инвентарь, карта, статус) доступно через
горячие клавиши.

**Принципы:**
- Не перегруженный, фокус на нарративе
- Свободный текстовый ввод (не choices)
- Контекст меняется в зависимости от локации и состояния мира
- Typewriter effect для атмосферы
- Готовность к расширениям (choices, карты — заглушки)

## Layout

```
┌─────────────────────────────────────────────────────────────┐
│ LOCATION: The Tavern · Day 3 · 14:30                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ You push open the wooden door. The tavern smells of ale    │
│ and woodsmoke. A warm glow emanates from the fireplace.    │
│ Several patrons sit at scattered tables. A bartender...    │
│                                                              │
│ [NPCs here] bartender, drunk sailor, hooded stranger       │
│ [Items] empty bottle on the floor, lost coin               │
│ [Exits] north → road, east → back alley                    │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ > _                                                          │
│                                                              │
│ [i]nventory [p]rogression [s]ave [?]help · choices[WIP]   │
└─────────────────────────────────────────────────────────────┘
```

### Зоны

| Зона | Высота | Назначение |
|------|--------|-----------|
| Header | 1 строка | Локация, день/время, статус |
| Scene | ~60-70% экрана | Нарратив (печатается с эффектом) |
| Context | ~15-20% экрана | NPCs, items, exits, status |
| Input | 1 строка | Ввод команды + приглашение `> ` |
| Footer | 1 строка | Горячие клавиши + статус features |

## Компоненты

### 1. Header

```
LOCATION: The Tavern · Day 3 · 14:30
```

**Формат:** `LOCATION: <location_name> · Day <day> · <time>`

**Обновляется:** каждый ход (изменение локации, времени)

**Источник:** `current_location.name`, `game_state.day`, `game_state.time`

---

### 2. Scene (Нарратив)

**Что это:**
- Основной текст от scene-master'а
- Печатается с typewriter effect (1-3 символа в ms, настраивается)
- Может быть 3-10+ предложений
- После окончания — игрок вводит команду

**Как выглядит:**
```
You push open the wooden door. The tavern smells of ale
and woodsmoke. A warm glow emanates from the fireplace.
Several patrons sit at scattered tables. A bartender
with a scarred face polishes glasses behind the bar.
```

**Typewriter effect:**
- Задержка между символами: 10-20 ms (настраивается через `ui.typewriter_delay`)
- Полная печать текста: ~1-3 секунды
- Можно ускорить: нажать Space/Enter → текст выводится сразу
- Если игрок вводит текст во время печати → оставить текущее состояние, не выводить дальше

**Источник:** `scene_response.narrative` (от scene-master'а)

---

### 3. Context Info

Выводится **после** сцены, всегда видна текущая информация о локации.

**[NPCs here]** — только в текущей локации игрока:
```
[NPCs here] bartender, drunk sailor, hooded stranger
```

**[Items]** — видимые предметы в локации:
```
[Items] empty bottle on the floor, lost coin
```

**[Exits]** — возможные направления:
```
[Exits] north → road, east → back alley, up → stairs
```

**Источник:** 
- `current_location.npcs` (фильтр: где игрок)
- `current_location.items` (видимые предметы)
- `current_location.connections` (выходы)

**[Status]** — статус игрока (опционально, если важно):
```
[Status] Health: 85/100 · Mana: 40/60 · Condition: healthy
```

---

### 4. Input Line

```
> talk to the bartender
```

**Формат:** `> ` + свободный текст от игрока

**Поведение:**
- Игрок пишет что угодно: "attack the goblin", "cast spell", "ask npc about quest"
- Мультистрочный ввод: если игрок нажимает Shift+Enter, добавить новую строку
- По Enter: отправить команду

**Обработка:**
1. Orchestrator получает `raw_text`
2. Intent parser: извлекает intent, метод, цель, тон, риск
3. Hard constraints: проверка валидности
4. Context build: контекст для LLM-агентов
5. Выполнение действия

---

### 5. Footer (Горячие клавиши)

```
[i]nventory [p]rogression [s]ave [?]help · choices[WIP] · map[WIP]
```

**Основные:**
- `i` — инвентарь (отдельный экран с item list)
- `p` — прогрессия (stats, skills, quests)
- `s` — сохранить игру
- `?` — справка

**Заглушки:**
- `c` — choices (Coming Soon)
- `m` — карта (Coming Soon)

**При нажатии:**
- Показать подсистему (инвентарь как отдельная таблица)
- Или вернуться в главное меню
- После выхода — вернуться в основное окно с той же сценой

---

## Typewriter Effect (Реализация)

```python
async def render_scene_with_typewriter(narrative: str, delay_ms: int = 15):
    """
    Печатает текст посимвольно.
    
    delay_ms: задержка в миллисекундах между символами
    
    Клавиши:
    - Space / Enter: завершить анимацию, вывести весь текст
    - Ctrl+C: отменить ввод
    """
    for char in narrative:
        print(char, end='', flush=True)
        await asyncio.sleep(delay_ms / 1000)
    print()  # новая строка в конце
```

**Настройка:**
- `settings.ui.typewriter_delay_ms` (по умолчанию 15)
- `settings.ui.typewriter_enabled` (можно отключить для быстрого тестирования)

---

## Context Rendering Rules

**Порядок вывода контекста (после сцены):**

```
[NPCs here] ...
[Items] ...
[Exits] ...
[Status] ...
```

**Условия видимости:**

| Элемент | Видимо если | Скрыто если |
|---------|-----------|-----------|
| NPC | В той же локации, что игрок | Скрыт/невидим (заглушка) |
| Item | В локации + Не скрыт | Находится в чьём-то инвентаре |
| Exit | Известен игроку или виден в описании | Скрыт квестом/ловушка |
| Status | Свежий (< 1 хода) | Старый (изменился, нужна подсвеженность) |

**Источник данных:**
- `current_location` (из канона)
- `player_progression` (видимые миру)
- `game_state.visibility` (скрытые элементы)

---

## Input Parsing Flow

```
User input: "attack the goblin"
    ↓
Orchestrator.parse_intent()
    ↓ (LLM внутри)
Intent {
    intent: "attack",
    method: "melee",  # or "spell", "ranged", "social"
    target: "goblin",
    target_raw: "the goblin",
    tone: "aggressive",
    risk_level: "medium",
    raw_text: "attack the goblin"
}
    ↓
Hard constraints validation
    ↓ (Может ли игрок выполнить это?)
    ├─ Есть ли "goblin" в локации? → Yes
    ├─ Есть ли у игрока оружие? → Check progression
    └─ Не в защищённой зоне? → Check location.flags
    ↓
Valid? → Continue
Invalid? → Show error, loop back to input
```

---

## Горячие клавиши (Keybindings)

| Клавиша | Действие | Реализация |
|---------|---------|-----------|
| `Enter` | Отправить команду | Input handler |
| `Space` | Ускорить typewriter (если печатает) | Scene renderer |
| `i` | Инвентарь | UI subsystem |
| `p` | Прогрессия | UI subsystem |
| `s` | Сохранить | Persistence |
| `?` | Справка | UI subsystem |
| `q` | Выход (с сохранением) | Orchestrator |
| `Ctrl+C` | Аварийный выход | Sighandler |

**Реализация:** `worldsim-orchestrator/src/ui/keybindings.ts`

---

## Заглушки (Coming Soon)

### 1. Choices System

**Планы:**
- Вместо/дополнительно к свободному вводу показывать numbered choices
- `[1] Attack the goblin [2] Talk to the goblin [3] Run away`
- Игрок вводит либо число, либо свободный текст

**Статус:** Зарезервирована архитектура, реализация позже

**Файл:**
```
worldsim-orchestrator/src/ui/choices-system.ts
→ export class ChoicesRenderer { /* заглушка */ }
```

---

### 2. Map System

**Планы:**
- Нажать `[m]` → открыть карту локально (PNG, SVG или текстовый файл)
- Карты сохраняются в `saves/<world-name>/maps/`
- Генерируются scene-master'ом или world-builder'ом
- При нажатии `m`: открыть в браузере или текстовом редакторе

**Статус:** Зарезервирована архитектура, реализация позже

**Файл:**
```
worldsim-orchestrator/src/ui/map-manager.ts
→ export class MapManager {
    async openMap(world_id: string): Promise<void> { /* заглушка */ }
  }
```

---

## Примеры экранов

### 1. Начало игры

```
┌──────────────────────────────────────────────┐
│ LOCATION: Crossroads · Day 1 · Morning       │
├──────────────────────────────────────────────┤
│                                              │
│ You wake up on a dusty road. The sun is     │
│ just rising over the horizon. To the north  │
│ lies the great city of Eldoria. To the      │
│ east, a dense forest stretches endlessly.   │
│ Behind you, the road winds back toward the  │
│ small village you grew up in.               │
│                                              │
│ [NPCs here] none                            │
│ [Items] weathered backpack (worn)           │
│ [Exits] north → Eldoria, east → forest,    │
│         south → village                     │
│                                              │
├──────────────────────────────────────────────┤
│ > _                                          │
│                                              │
│ [i] [p] [s] [?]                             │
└──────────────────────────────────────────────┘
```

---

### 2. В диалоге с NPC

```
┌──────────────────────────────────────────────┐
│ LOCATION: The Tavern · Day 3 · Evening      │
├──────────────────────────────────────────────┤
│                                              │
│ The bartender looks up from polishing a     │
│ glass. His weathered face breaks into a     │
│ knowing smile. "You look like you've got a  │
│ story to tell, friend. Drink?"              │
│                                              │
│ [NPCs here] bartender, sailor, hooded       │
│ [Items] empty bottle, lost coin             │
│ [Exits] north → road, east → back alley     │
│                                              │
├──────────────────────────────────────────────┤
│ > tell the bartender about the quest        │
│                                              │
│ [i] [p] [s] [?]                             │
└──────────────────────────────────────────────┘
```

---

### 3. Ошибка валидации

```
┌──────────────────────────────────────────────┐
│ LOCATION: The Tavern · Day 3 · Evening      │
├──────────────────────────────────────────────┤
│                                              │
│ [Error] There's no "merchant" in this      │
│ location. You see: bartender, sailor,      │
│ hooded stranger.                            │
│                                              │
│ Try again:                                  │
│                                              │
├──────────────────────────────────────────────┤
│ > _                                          │
│                                              │
│ [i] [p] [s] [?]                             │
└──────────────────────────────────────────────┘
```

---

## Data Flow (Архитектура)

```
┌──────────────────────────────────────┐
│  Orchestrator.run_turn()              │
└──────────┬──────────────────────────┘
           │
           ├─→ SceneRenderer.render_with_typewriter()
           │    └─→ scene_response.narrative
           │         (печать с эффектом)
           │
           ├─→ ContextRenderer.render_context()
           │    └─→ [NPCs] [Items] [Exits] [Status]
           │
           ├─→ InputHandler.get_user_input()
           │    └─→ raw_text от игрока
           │
           └─→ Intent Parser + Validators
                └─→ Выполнение действия
```

### Файловая структура (orchestrator)

```
worldsim-orchestrator/src/ui/
├── __init__.py
├── components.py           # SceneRenderer, ContextRenderer
├── input-handler.py        # InputHandler, keybinding logic
├── map-manager.py          # MapManager (заглушка)
├── choices-system.py       # ChoicesRenderer (заглушка)
├── constants.py            # Colors, delays, formats
└── types.ts                # UIState, ContextInfo types
```

---

## Конфигурация

**`settings.ui` в config-файле orchestrator'а:**

```yaml
ui:
  typewriter_enabled: true
  typewriter_delay_ms: 15
  max_scene_height: 20
  context_collapse: false  # Если true, контекст сворачивается в одну строку
  color_scheme: "default"  # или "dark", "light"
  input_prefix: "> "
```

---

## Тестирование

**Unit тесты:**
- `test_typewriter_effect()` — скорость и правильность печати
- `test_context_rendering()` — порядок и видимость элементов
- `test_input_parsing()` — обработка различных команд
- `test_keybindings()` — горячие клавиши

**Integration тесты:**
- Полный цикл: сцена → ввод → валидация → обновление → новая сцена

---

## Будущие расширения

1. **Choices** → нумерованные выборы, если нужны (заглушка уже есть)
2. **Карты** → локальные PNG/SVG, открываются в браузере (заглушка уже есть)
3. **Статус-бар** → в реальном времени обновляющийся прогресс
4. **Multi-window** → рядом инвентарь + сцена (не нужно, заглушка достаточна)
5. **Colors** → синтаксис вроде `[red]text[/red]` для цветного вывода

---
