# {{AGENT_NAME}}

{{ONE_LINE_DESCRIPTION}}

Часть мульти-репо системы [worldsim](https://github.com/b3axap/worldsim-workspace).

## Контракт

```python
from {{PKG_NAME}} import run

result = run(input, *, client)  # input — pydantic-модель, result — pydantic-модель
```

Точные типы вход/выход — см. `src/{{PKG_NAME}}/agent.py`.

## Установка

```bash
pip install -e .
```

Зависит от shared-пакетов из `worldsim-workspace`:

```bash
pip install -e ../worldsim-workspace/packages/schemas
pip install -e ../worldsim-workspace/packages/prompts
```

## Промпт

Живёт в `prompts/`. Редактируйте напрямую, это основной способ
изменить поведение агента.

## _schemas/ и _prompts/

Это снимки shared-пакетов из workspace. **Не редактируйте руками** —
их перезапишет `sync-all.sh`. Если нужно поменять схему — правьте в
`worldsim-workspace/packages/schemas/`.

## Тесты

```bash
python -m pytest -q
```
