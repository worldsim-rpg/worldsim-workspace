# Установка локально

## Требования

- Python 3.11+
- git
- Anthropic API ключ (получить: https://console.anthropic.com)

## Шаги

### 1. Клонировать все репо

```bash
mkdir sandbox && cd sandbox
mkdir repos && cd repos

for r in worldsim-workspace worldsim-orchestrator worldsim-world-builder \
         worldsim-canon-keeper worldsim-scene-master worldsim-npc-mind \
         worldsim-personal-progression; do
  git clone "https://github.com/b3axap/$r.git"
done
```

Структура после клонов должна быть:

```
sandbox/
  repos/
    worldsim-workspace/
    worldsim-orchestrator/
    worldsim-world-builder/
    ... (остальные 4 агента)
```

### 2. Создать виртуальное окружение

Одно общее окружение на все репо:

```bash
cd ..        # обратно в sandbox
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Установить все пакеты

```bash
cd repos

# shared пакеты из workspace (schemas + prompt-framework)
pip install -e ./worldsim-workspace/packages/schemas
pip install -e ./worldsim-workspace/packages/prompts

# все агенты
for r in worldsim-orchestrator worldsim-world-builder worldsim-canon-keeper \
         worldsim-scene-master worldsim-npc-mind worldsim-personal-progression; do
  pip install -e "./$r"
done
```

### 4. Прописать API ключ

```bash
cd worldsim-orchestrator
cp .env.example .env
# откройте .env в редакторе и вставьте ваш ANTHROPIC_API_KEY
```

### 5. Проверить установку

```bash
# из корня sandbox/
cd repos/worldsim-workspace
./repo-setup/sync-all.sh       # раскатать shared schemas в _schemas/ агентов

# запустить все тесты
for r in ../worldsim-orchestrator ../worldsim-world-builder ../worldsim-canon-keeper \
         ../worldsim-scene-master ../worldsim-npc-mind ../worldsim-personal-progression; do
  (cd "$r" && python -m pytest -q)
done
```

### 6. Первая игра

```bash
cd ../worldsim-orchestrator
python -m worldsim_orchestrator new        # создать новый мир
python -m worldsim_orchestrator play       # играть в последний
```

## Частые проблемы

### `ModuleNotFoundError: worldsim_schemas`

Не установлен shared пакет. Выполните:

```bash
pip install -e repos/worldsim-workspace/packages/schemas
```

### `ANTHROPIC_API_KEY не задан`

Либо нет `.env`, либо ключ пустой. `cd repos/worldsim-orchestrator &&
cp .env.example .env` и проставьте ключ.

### `_schemas/` в агент-репо пустой

Не запускали `sync-all.sh`. Запустите его из `worldsim-workspace/`.
