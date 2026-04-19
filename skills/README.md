# Worldsim Skills

Claude Code скиллы для работы с worldsim workspace.

## Установка

```bash
cd repos/worldsim-workspace
bash skills/install.sh
```

Перезапусти Claude Code. Готово.

## Скиллы

| Скилл | Что делает |
|---|---|
| `/check-setup` | Проверяет локальный сетап разработчика |
| `/ws-status` | Git-дашборд по всем 7 репо |
| `/github-sync` | Pull/push всех репо с GitHub |
| `/schema-sync` | Раскатывает schemas+prompts из workspace в агент-репо |
| `/run-tests` | Запускает pytest по всем агент-репо |
| `/scaffold-agent` | Создаёт скелет нового агент-репо |

## Обновление скиллов

Если скилл изменился в `skills/<name>/SKILL.md`, повторно запусти `install.sh`.
