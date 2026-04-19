# Стратегия веток

Три постоянные ветки в каждом из 7 репо. Прямой push в `staging` и `main`
заблокирован branch protection rules на GitHub.

## Ветки

| Ветка     | Назначение           | Кто пишет               | Защита                        |
|-----------|----------------------|-------------------------|-------------------------------|
| `dev`     | активная разработка  | разработчик, прямой push | —                             |
| `staging` | синхронизация/ревью  | PR из `dev`             | 1 approve обязателен          |
| `main`    | деплой/продакшен     | PR из `staging`         | 1 approve обязателен          |

## Как вносить изменения

1. Убедитесь, что вы на `dev`: `git checkout dev && git pull`.
2. Коммитьте атомарно, конвенциональными сообщениями:
   `feat:`, `fix:`, `docs:`, `refactor:`, `test:`.
3. Пушьте: `git push` (или `git push -u origin dev` при первом пуше).
4. Откройте PR `dev → staging`. Опишите **что** и **зачем**.
5. Ревьюер апрувит и мержит в `staging`.
6. Ревьюер открывает PR `staging → main` и мержит для деплоя.

## Что считается "сломанным" main

- `pytest` в репо падает на чистом клоне после `pip install -e .`.
- Агент не валидирует свой output через pydantic — скипнулась
  валидация.
- Изменены поля в `worldsim_schemas`, но не запущен `sync-all.sh` —
  `_schemas/` в агентах рассогласованы.

## Workflow после изменений в схемах

```bash
# 1. Работаете в dev
git checkout dev

# 2. Правите packages/schemas/src/worldsim_schemas/schemas.py в workspace
# 3. Бампните версию в packages/schemas/pyproject.toml (0.1.0 → 0.1.1)
# 4. Запустите sync
cd repos/worldsim-workspace
./repo-setup/sync-all.sh

# 5. Пройдитесь по агентам — там _schemas/ обновились, протестируйте
for r in ../worldsim-orchestrator ../worldsim-world-builder ../worldsim-canon-keeper \
         ../worldsim-scene-master ../worldsim-npc-mind ../worldsim-personal-progression; do
  (cd "$r" && python -m pytest -q)
done

# 6. Коммитьте в dev и пушьте
# 7. PR dev → staging в каждом затронутом репо
# 8. После ревью — PR staging → main
```

## Разделение ответственности

- Менять схемы канона — **только в workspace**.
- Менять промпт агента — **только в его репо**.
- Менять `validators.py`, цикл хода, persistence — **только в
  orchestrator**.
- Общий prompt-framework (`packages/prompts`) — **только в workspace**.
