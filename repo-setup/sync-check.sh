#!/usr/bin/env bash
# Проверяет, что _schemas/ и _prompts/ в каждом агент-репо не разошлись
# с каноном в workspace.
#
# Запуск:
#   ./repo-setup/sync-check.sh               # проверить все агент-репо рядом
#   ./repo-setup/sync-check.sh --local       # проверить только текущий репо
#                                              (ожидает _schemas и _prompts в CWD)
#
# Для каждого агента:
#   1. sha256sum -c .sync-manifest → детектит изменённые/пропавшие файлы.
#   2. Сверяет список файлов с манифестом → детектит ЛИШНИЕ файлы.
#
# Exit 1 при любом расхождении.

set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPOS_DIR="$(cd "${WORKSPACE_DIR}/.." && pwd)"
AGENTS_FILE="${WORKSPACE_DIR}/repo-setup/agents.txt"

FAIL=0

# Проверка одной синкнутой папки (_schemas или _prompts).
check_dir() {
  local dir="$1"
  local label="$2"

  if [[ ! -d "${dir}" ]]; then
    echo "  ! ${label}: папка отсутствует — ${dir}"
    FAIL=1
    return
  fi
  if [[ ! -f "${dir}/.sync-manifest" ]]; then
    echo "  ! ${label}: нет .sync-manifest (прогоняли ли sync-all.sh?)"
    FAIL=1
    return
  fi

  # 1. Проверяем хэши того, что в манифесте.
  local check_out
  if ! check_out=$( (cd "${dir}" && sha256sum -c .sync-manifest --strict --quiet) 2>&1); then
    echo "  ✗ ${label}: файлы изменены относительно манифеста:"
    printf '%s\n' "${check_out}" | sed 's/^/      /'
    FAIL=1
  fi

  # 2. Ищем ЛИШНИЕ файлы: присутствуют на диске, но не упомянуты в манифесте.
  # __pycache__ игнорим — это локальный мусор рантайма, не drift.
  local actual expected extras
  actual=$( (cd "${dir}" && find . -type f \
    -not -name .sync-manifest \
    -not -path '*/__pycache__/*' \
    | LC_ALL=C sort) )
  # sha256sum в binary-режиме пишет "HASH *path" — убираем ведущую '*'.
  expected=$(awk '{path=$2; sub(/^\*/, "", path); print path}' "${dir}/.sync-manifest" | LC_ALL=C sort)
  extras=$(comm -23 <(printf '%s\n' "${actual}") <(printf '%s\n' "${expected}") || true)
  if [[ -n "${extras}" ]]; then
    echo "  ✗ ${label}: лишние файлы (добавлены руками, не из workspace):"
    printf '%s\n' "${extras}" | sed 's/^/      /'
    FAIL=1
  fi
}

check_agent() {
  local agent_dir="$1"
  local agent_name="$2"
  echo "→ ${agent_name}"
  check_dir "${agent_dir}/_schemas" "_schemas"
  check_dir "${agent_dir}/_prompts" "_prompts"
}

if [[ "${1:-}" == "--local" ]]; then
  check_agent "$(pwd)" "$(basename "$(pwd)")"
else
  while IFS= read -r agent; do
    [[ -z "${agent}" ]] && continue
    [[ "${agent}" =~ ^# ]] && continue
    target="${REPOS_DIR}/${agent}"
    if [[ ! -d "${target}" ]]; then
      echo "! пропускаю ${agent} — папка ${target} не найдена"
      continue
    fi
    check_agent "${target}" "${agent}"
  done < "${AGENTS_FILE}"
fi

echo ""
if [[ "${FAIL}" -ne 0 ]]; then
  echo "FAIL: обнаружен drift. Почини workspace и запусти ./repo-setup/sync-all.sh"
  echo "      Подробности: worldsim-workspace/docs/sync.md"
  exit 1
fi
echo "OK: все агенты синхронизированы с каноном."
