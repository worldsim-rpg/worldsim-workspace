#!/usr/bin/env bash
# Устанавливает worldsim-скиллы в локальный Claude Code.
#
# Запуск: из корня worldsim-workspace
#   bash skills/install.sh
#
# Что делает:
#   1. Ищет папку skills в Claude AppData (Windows/macOS/Linux)
#   2. Копирует каждый скилл из skills/ в неё
#   3. Регистрирует скиллы в manifest.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── Найти папку Claude skills ───────────────────────────────────────────────

find_skills_dir() {
  # Windows (Git Bash / MSYS2)
  if [[ -n "${APPDATA:-}" ]]; then
    local base
    base=$(cygpath -u "$APPDATA" 2>/dev/null || echo "$APPDATA")
    local found
    found=$(find "$base/Claude/local-agent-mode-sessions/skills-plugin" \
      -maxdepth 3 -type d -name "skills" 2>/dev/null | head -1)
    [[ -n "$found" ]] && echo "$found" && return
  fi

  # macOS / Linux
  local xdg="${XDG_DATA_HOME:-$HOME/.local/share}"
  for base in \
    "$HOME/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin" \
    "$xdg/Claude/local-agent-mode-sessions/skills-plugin" \
    "$HOME/.config/Claude/local-agent-mode-sessions/skills-plugin"
  do
    local found
    found=$(find "$base" -maxdepth 3 -type d -name "skills" 2>/dev/null | head -1)
    [[ -n "$found" ]] && echo "$found" && return
  done

  echo ""
}

SKILLS_DIR=$(find_skills_dir)

if [[ -z "$SKILLS_DIR" ]]; then
  echo "Не удалось найти папку skills Claude Code."
  echo "Убедитесь что Claude Code установлен и хотя бы раз запущен."
  exit 1
fi

echo "Устанавливаю скиллы в: $SKILLS_DIR"
echo ""

# ── Копировать скиллы ────────────────────────────────────────────────────────

SKILLS=(github-sync schema-sync scaffold-agent check-setup ws-status run-tests)

for skill in "${SKILLS[@]}"; do
  src="$SCRIPT_DIR/$skill"
  dst="$SKILLS_DIR/$skill"

  if [[ ! -d "$src" ]]; then
    echo "! пропускаю $skill — папка $src не найдена"
    continue
  fi

  rm -rf "$dst"
  cp -r "$src" "$dst"
  echo "✓ $skill"
done

echo ""
echo "Готово. Перезапустите Claude Code чтобы скиллы подтянулись."
echo "Проверить сетап: /check-setup"
