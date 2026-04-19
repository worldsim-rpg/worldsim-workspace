---
name: schema-sync
description: Sync schemas and prompts from worldsim-workspace into all agent repos. Use this skill whenever the user says "синхронизировать схемы", "sync schemas", "sync prompts", "обновить _schemas", "обновить _prompts", "запустить sync-all", or mentions that schemas or prompts in agent repos might be stale after editing packages/ in workspace.
---

# schema-sync

Copies canonical schemas and prompts from `worldsim-workspace/packages/` into every agent repo's `_schemas/` and `_prompts/` directories.

## What the sync does

- Source: `repos/worldsim-workspace/packages/schemas/src/worldsim_schemas/` → `_schemas/`
- Source: `repos/worldsim-workspace/packages/prompts/src/worldsim_prompts/` → `_prompts/`
- Controlled by: `repos/worldsim-workspace/repo-setup/agents.txt`

The script clears old contents and replaces them, then writes a `.synced` timestamp marker.

## Workflow

### Step 1 — run sync-all.sh

```bash
cd C:/Users/ZAKHAR/Documents/ПРОЕКТЫ/sandbox/repos/worldsim-workspace
bash ./repo-setup/sync-all.sh
```

Capture stdout. The script prints `✓ <agent-name>` per repo, or a skip warning if the folder isn't found.

### Step 2 — show what changed

After the sync, for each repo that was updated check if git sees any diff:

```bash
git -C <repo-path> diff --stat -- _schemas/ _prompts/
```

Summarize in a table:

```
Repo                          Changes
──────────────────────────────────────
worldsim-orchestrator         _schemas/: 2 files changed
worldsim-world-builder        no changes
worldsim-canon-keeper         _prompts/: 1 file changed
```

### Step 3 — remind about next steps

If any files changed, remind the user:
> Run tests in changed repos: `python -m pytest -q` (or `uv run pytest -q` if using uv)
> Stage and commit `_schemas/` and `_prompts/` if your workflow tracks them in git.

## When to use this

Run after any edit to:
- `worldsim-workspace/packages/schemas/`
- `worldsim-workspace/packages/prompts/`

The agent repos must **not** have their `_schemas/` or `_prompts/` edited directly — those are managed by this sync.
