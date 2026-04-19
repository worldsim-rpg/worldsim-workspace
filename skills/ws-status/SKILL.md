---
name: ws-status
description: Show git status dashboard across all worldsim repos. Use this skill whenever the user says "статус", "ws-status", "что изменилось", "покажи статус репо", "status across repos", "git status all", or wants a quick overview of the state of all worldsim repositories.
---

# ws-status

Prints a compact git dashboard for all 7 worldsim repos at once.

## Repos

```
C:/Users/ZAKHAR/Documents/ПРОЕКТЫ/sandbox/repos/
  worldsim-workspace
  worldsim-orchestrator
  worldsim-world-builder
  worldsim-canon-keeper
  worldsim-scene-master
  worldsim-npc-mind
  worldsim-personal-progression
```

## Data to collect per repo

For each repo run these in parallel:

```bash
# branch + ahead/behind
git -C <repo> status --porcelain=v1 -b

# short name for dirty files
git -C <repo> status --short
```

Parse:
- **Branch**: first line `## <branch>...<remote>`
- **Ahead**: `ahead N` from the branch line
- **Behind**: `behind N` from the branch line
- **Dirty**: count of lines from `--short` (uncommitted changes)

## Output format

```
WORLDSIM WORKSPACE STATUS
──────────────────────────────────────────────────────────────
Repo                          Branch    Ahead  Behind  Dirty
──────────────────────────────────────────────────────────────
worldsim-workspace            dev         0       0      —
worldsim-orchestrator         dev         2       0      3 files
worldsim-world-builder        dev         0       1      —
worldsim-canon-keeper         dev         0       0      1 file
worldsim-scene-master         dev         0       0      —
worldsim-npc-mind             dev         0       0      —
worldsim-personal-progression dev         0       0      —
──────────────────────────────────────────────────────────────
```

Highlight rows that need attention:
- **ahead > 0** → `↑` marker (have local commits to push)
- **behind > 0** → `↓` marker (remote has commits to pull)
- **dirty > 0** → show file count

## After the table

If any repo is behind: suggest `/github-sync` (pull).
If any repo is ahead: suggest `/github-sync` (push).
If schema files in workspace are newer than `.synced` markers in agents: suggest `/schema-sync`.

Keep the summary to one line, not a wall of text.
