# Стратегия веток

На MVP-фазе — максимально просто.

## Ветки

- **`main`** — default, сюда идут все изменения. CI (когда появится)
  гоняет тесты.
- **`release`** — появится позже, когда будет публичный релиз. Пока не
  используем.

## Как вносить изменения

1. Клонируйте нужный репо (или работайте в `sandbox/repos/<agent>/`).
2. Создайте ветку от `main`: `git checkout -b feature/<короткое-имя>`.
3. Коммитьте атомарно, конвенциональными сообщениями:
   `feat:`, `fix:`, `docs:`, `refactor:`, `test:`.
4. Пушьте: `git push -u origin feature/<name>`.
5. Откройте PR в `main`. Опишите **что** и **зачем**.
6. Merge после ревью (или самоmerge на текущей фазе).

## Что считается "сломанным" main

- `pytest` в репо падает на чистом клоне после `pip install -e .`.
- Агент не валидирует свой output через pydantic — скипнулась
  валидация.
- Изменены поля в `worldsim_schemas`, но не запущен `sync-all.sh` —
  `_schemas/` в агентах рассогласованы.

## Workflow после изменений в схемах

```bash
# 1. Правите packages/schemas/src/worldsim_schemas/schemas.py в workspace
# 2. Бампните версию в packages/schemas/pyproject.toml (0.1.0 → 0.1.1)
# 3. Запустите sync
cd repos/worldsim-workspace
./repo-setup/sync-all.sh
# 4. Пройдитесь по агентам — там _schemas/ обновились, протестируйте
for r in ../worldsim-orchestrator ../worldsim-world-builder ../worldsim-canon-keeper \
         ../worldsim-scene-master ../worldsim-npc-mind ../worldsim-personal-progression; do
  (cd "$r" && python -m pytest -q)
done
# 5. Коммитьте изменения в workspace и агентах отдельными PR
```

## Разделение ответственности

- Менять схемы канона — **только в workspace**.
- Менять промпт агента — **только в его репо**.
- Менять `validators.py`, цикл хода, persistence — **только в
  orchestrator**.
- Общий prompt-framework (`packages/prompts`) — **только в workspace**.
