---
name: check-setup
description: Verify or perform the worldsim local developer setup. Use this skill whenever the user says "check setup", "проверить сетап", "setup", "настроить окружение", "onboarding", "всё ли установлено", "установить проект", "первый запуск", "новый разработчик", "check environment", "verify install", or when someone is setting up worldsim for the first time.
---

# check-setup

Works in two modes depending on how much is already installed:

- **Setup mode** — если ключевых вещей нет (репо не склонированы, venv отсутствует): проходит по шагам установки, спрашивает подтверждение перед каждым.
- **Audit mode** — если окружение в основном готово: проверяет всё и выводит отчёт с предложением починить найденные проблемы.

## Как определить режим

Сначала выполни быструю проверку:
```bash
test -d <sandbox>/repos/worldsim-workspace/.git   # репо клонированы?
test -d <sandbox>/.venv                            # venv есть?
```

Если **оба отсутствуют** → Setup mode.  
Если хотя бы одно есть → Audit mode (возможно, частичная установка).

Sandbox root на этой машине: `C:/Users/ZAKHAR/Documents/ПРОЕКТЫ/sandbox`.  
Если запускается на другой машине — спроси путь у пользователя.

---

## Setup mode — пошаговая установка

Проходи шаги по порядку. Перед каждым шагом коротко объясни что будет сделано и спроси "Продолжить?" (можно пропустить шаг если пользователь скажет).

### Шаг 1 — Структура папок

```bash
mkdir -p <sandbox>/repos
```

Проверь что `<sandbox>` сам по себе не git-репо. Если вдруг `.git` есть — предупреди, не удаляй.

Создай `<sandbox>/CLAUDE.md` если отсутствует, скопировав из workspace после клонирования.

### Шаг 2 — Клонировать репо

```bash
cd <sandbox>/repos
for r in worldsim-workspace worldsim-orchestrator worldsim-world-builder \
          worldsim-canon-keeper worldsim-scene-master worldsim-npc-mind \
          worldsim-personal-progression; do
  git clone "https://github.com/worldsim-rpg/$r.git"
done
```

Если какое-то репо уже есть — пропустить его (не перезаписывать).

### Шаг 3 — Python venv

```bash
cd <sandbox>
python -m venv .venv
```

На Windows активация: `.venv\Scripts\activate`  
На macOS/Linux: `source .venv/bin/activate`

### Шаг 4 — Установить пакеты

```bash
# shared пакеты
pip install -e repos/worldsim-workspace/packages/schemas
pip install -e repos/worldsim-workspace/packages/prompts

# все агенты
for r in worldsim-orchestrator worldsim-world-builder worldsim-canon-keeper \
          worldsim-scene-master worldsim-npc-mind worldsim-personal-progression; do
  pip install -e repos/$r
done
```

### Шаг 5 — Синхронизировать схемы

```bash
cd repos/worldsim-workspace
bash ./repo-setup/sync-all.sh
```

### Шаг 6 — Установить скиллы

```bash
cd repos/worldsim-workspace
bash skills/install.sh
```

### Шаг 7 — API ключ

Проверь `ANTHROPIC_API_KEY`:
```bash
[[ -n "${ANTHROPIC_API_KEY:-}" ]] && echo "set" || echo "missing"
```

Если не задан — подскажи:
```bash
cp repos/worldsim-orchestrator/.env.example repos/worldsim-orchestrator/.env
# затем открыть .env и вставить ключ
```

### Финал setup mode

После всех шагов автоматически переходи в Audit mode и покажи итоговый отчёт.

---

## Audit mode — проверка окружения

Собери все результаты, затем покажи единую таблицу.

### Чеклист

**Структура папок**
- `sandbox/` не является git-репо
- `sandbox/CLAUDE.md` существует
- Все 7 репо склонированы (каждый с `.git`)

**Git remotes**  
Для каждого репо: `git -C <repo> remote get-url origin`  
Ожидается `https://github.com/worldsim-rpg/<name>.git`

**Python окружение**  
- `.venv` существует в sandbox
- `worldsim_schemas` импортируется
- `worldsim_prompts` импортируется
- Каждый агент-пакет импортируется

```bash
<venv>/Scripts/python -c "import worldsim_schemas"   # Windows
<venv>/bin/python     -c "import worldsim_schemas"   # macOS/Linux
```

**API ключ**  
- `ANTHROPIC_API_KEY` задан в env, или в `repos/worldsim-orchestrator/.env`

**Freshness схем**  
Для каждого агент-репо: `cat repos/<agent>/_schemas/.synced`  
⚠ если старше 7 дней или файл отсутствует

**Скиллы**  
Найти папку skills Claude Code и проверить наличие:
`github-sync`, `schema-sync`, `scaffold-agent`, `check-setup`, `ws-status`, `run-tests`

**CLI инструменты**  
`git --version`, `python --version`, `gh --version`

### Формат вывода

```
WORLDSIM SETUP CHECK
════════════════════════════════════════════════

 Структура папок
  ✓ sandbox/ не является git-репо
  ✓ CLAUDE.md есть
  ✓ Все 7 репо склонированы

 Git remotes
  ✓ worldsim-workspace → github.com/worldsim-rpg/...
  ✗ worldsim-npc-mind → remote не настроен

 Python окружение
  ✓ .venv есть
  ✓ worldsim_schemas, worldsim_prompts
  ✗ worldsim_orchestrator — не установлен

 API ключ
  ✓ ANTHROPIC_API_KEY задан

 Схемы
  ✓ worldsim-orchestrator — 2026-04-17
  ⚠ worldsim-npc-mind — устарело (2026-03-01)

 Скиллы
  ✓ все 6 установлены

 CLI
  ✓ git 2.44  ✓ python 3.12  ✗ gh не найден

════════════════════════════════════════════════
 3 проблемы. См. ✗ выше.
```

### После отчёта

Предложи починить автоматически то, что можно:
- pip install для незагруженных пакетов
- schema-sync для устаревших схем
- skills/install.sh если скиллы не найдены

Не трогай без подтверждения: git remotes, отсутствующие репо, API ключ.
