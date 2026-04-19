---
name: github-sync
description: Sync all worldsim repos with GitHub — pull (rebase) and/or push. Use this skill whenever the user says "sync with github", "pull all repos", "push all repos", "обновить репо", "синхронизировать с гитхабом", "запуллить все", "запушить", or anything implying a multi-repo git operation across the worldsim workspace.
---

# github-sync

Syncs all worldsim repos in `repos/` with their GitHub remotes.

## Repos

```
repos/worldsim-workspace
repos/worldsim-orchestrator
repos/worldsim-world-builder
repos/worldsim-canon-keeper
repos/worldsim-scene-master
repos/worldsim-npc-mind
repos/worldsim-personal-progression
```

Base path: `C:/Users/ZAKHAR/Documents/ПРОЕКТЫ/sandbox/repos`

## Workflow

### Step 1 — clarify direction (if not obvious from context)

If the user said "sync", "обновить", or didn't specify direction, ask:
> Pull only, push only, or both?

If they said "pull" → pull only. If "push" → push only. If "both" → pull then push.

### Step 2 — pull (if requested)

For each repo run:
```bash
git -C <repo-path> pull --rebase --autostash
```

`--autostash` prevents failure when there are uncommitted local changes — git stashes them, rebases, then pops. This is safe for a dev workspace.

Show results as a compact table:

```
Repo                          Status
──────────────────────────────────────
worldsim-workspace            ✓ up to date
worldsim-orchestrator         ✓ 3 commits pulled
worldsim-world-builder        ⚠ conflicts — needs manual fix
```

If any repo has conflicts or errors, describe them clearly and stop before pushing.

### Step 3 — push (if requested)

Only push repos that have local commits ahead of remote:
```bash
git -C <repo-path> status --porcelain=v1 -b
```
Check `ahead N` in the branch status line.

For repos with unpushed commits:
```bash
git -C <repo-path> push
```

Show the same compact table with results.

### Step 4 — summary

End with a one-line summary: how many repos were updated, and whether anything needs attention.

## Edge cases

- **Uncommitted changes (dirty worktree)**: `--autostash` handles this for pull. For push, note that dirty repos exist but don't block the push of committed changes.
- **Repo doesn't exist locally**: skip with a warning — user may not have cloned all repos yet.
- **No remote configured**: report as a warning, skip.
- **Branch context**: repos normally sit on `dev`. If a repo is on `staging` or `main`, note it — direct push to those is blocked by branch protection; only PRs can update them.
