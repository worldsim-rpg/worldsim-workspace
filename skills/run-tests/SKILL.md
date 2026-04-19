---
name: run-tests
description: Run pytest across all or selected worldsim agent repos and show aggregated results. Use this skill whenever the user says "запустить тесты", "run tests", "прогнать тесты", "проверить тесты", "test all agents", or after schema changes or refactoring that might break agent packages.
---

# run-tests

Runs the test suite across worldsim agent repos and shows a consolidated pass/fail summary.

## Repos with tests

```
worldsim-orchestrator
worldsim-world-builder
worldsim-canon-keeper
worldsim-scene-master
worldsim-npc-mind
worldsim-personal-progression
```

`worldsim-workspace` itself has package tests under `packages/schemas/` and `packages/prompts/` — include those too.

## Scope

If the user specified a repo or agent name, test only that one. Otherwise test all.

## Command per repo

```bash
cd <repo-path>
python -m pytest -q --tb=short 2>&1
```

Use the `.venv` python if present in sandbox root:
```bash
C:/Users/ZAKHAR/Documents/ПРОЕКТЫ/sandbox/.venv/Scripts/python -m pytest -q --tb=short
```

Run repos **in parallel** (spawn background processes), collect output, then show results together — don't wait for one to finish before starting the next.

## Output format

```
TEST RESULTS
──────────────────────────────────────────────────────────────
Repo                          Result      Tests   Time
──────────────────────────────────────────────────────────────
worldsim-workspace/schemas    ✓ passed    14       1.2s
worldsim-workspace/prompts    ✓ passed     6       0.4s
worldsim-orchestrator         ✓ passed    23       2.1s
worldsim-world-builder        ✗ FAILED     8/11    1.8s
worldsim-canon-keeper         ✓ passed    17       1.5s
worldsim-scene-master         ✓ passed    12       1.1s
worldsim-npc-mind             — no tests   —        —
worldsim-personal-progression ✓ passed     9       0.9s
──────────────────────────────────────────────────────────────
7/8 suites passed · 3 failures in worldsim-world-builder
```

For any `✗ FAILED` repo, show the `--tb=short` failure output below the table so the developer can see exactly what broke.

## Common failures

- **`ModuleNotFoundError: worldsim_schemas`** → schemas not installed. Fix: `pip install -e repos/worldsim-workspace/packages/schemas`
- **`_schemas/ is empty`** → sync not run. Suggest: `/schema-sync`
- **`ImportError` in agent package** → package not installed in .venv. Fix: `pip install -e repos/<agent>`
