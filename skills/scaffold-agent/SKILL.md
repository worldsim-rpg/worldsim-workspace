---
name: scaffold-agent
description: Scaffold a new worldsim agent repo from workspace templates. Use this skill whenever the user says "создать нового агента", "scaffold agent", "новый агент", "добавить агент", "generate scaffold", or describes wanting to add a new LLM agent to the worldsim system.
---

# scaffold-agent

Creates a new agent repo in `repos/` using the workspace's `generate-scaffold.sh` template system, then registers it in `agents.txt` and optionally creates a GitHub repo.

## Workflow

### Step 1 — gather info (ask if not provided)

You need three things:
1. **Repo name** — kebab-case, must start with `worldsim-`. Example: `worldsim-plot-weaver`
2. **Python package name** — snake_case version. Example: `worldsim_plot_weaver`
3. **One-line description** — what the agent does. Example: `"LLM-агент, продвигающий сюжетные арки"`

If the user gave a short name like "plot-weaver", prepend `worldsim-` automatically and confirm.
Derive the Python package name automatically (replace `-` with `_`) and confirm with the user.

### Step 2 — run generate-scaffold.sh

```bash
cd C:/Users/ZAKHAR/Documents/ПРОЕКТЫ/sandbox/repos/worldsim-workspace
bash ./repo-setup/generate-scaffold.sh "<repo-name>" "<pkg-name>" "<description>"
```

The script creates `repos/<repo-name>/` with:
- `README.md`, `CLAUDE.md`, `pyproject.toml`, `.gitignore`
- `src/<pkg-name>/__init__.py` (exports `run`)
- `src/<pkg-name>/agent.py` (stub)
- `prompts/`, `_schemas/`, `_prompts/`, `tests/`

### Step 3 — register in agents.txt

Add the new repo name to `repos/worldsim-workspace/repo-setup/agents.txt`:

```bash
echo "<repo-name>" >> C:/Users/ZAKHAR/Documents/ПРОЕКТЫ/sandbox/repos/worldsim-workspace/repo-setup/agents.txt
```

This ensures future `sync-all.sh` runs include the new agent.

### Step 4 — run schema-sync

Immediately populate the new agent's `_schemas/` and `_prompts/`:

```bash
cd C:/Users/ZAKHAR/Documents/ПРОЕКТЫ/sandbox/repos/worldsim-workspace
bash ./repo-setup/sync-all.sh
```

### Step 5 — git init + first commit

```bash
cd C:/Users/ZAKHAR/Documents/ПРОЕКТЫ/sandbox/repos/<repo-name>
git init -b main
git add .
git commit -m "chore: initial scaffold"
```

### Step 6 — ask about GitHub

Ask the user:
> Create a GitHub repo under `worldsim-rpg/<repo-name>` and push?

If yes:
```bash
gh repo create worldsim-rpg/<repo-name> --private --source=. --remote=origin --push
```

If no — skip, remind them to do it later with:
```bash
gh repo create worldsim-rpg/<repo-name> --private --source=. --remote=origin --push
```

### Step 7 — summary

Show what was created:
- Path to new repo
- Files scaffolded
- Whether GitHub repo was created
- Next steps: open `src/<pkg-name>/agent.py` and implement `run(...)`

## Important constraints

- Never overwrite an existing directory — the script will error; report it clearly.
- The repo name MUST start with `worldsim-` — this is a workspace convention.
- Don't edit `_schemas/` or `_prompts/` in the new repo — they are managed by sync.
