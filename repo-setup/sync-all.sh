#!/usr/bin/env bash
# Раскатывает shared packages из workspace во все агент-репо.
#
# Запуск: из корня worldsim-workspace
#   ./repo-setup/sync-all.sh
#
# Что копируется:
#   packages/schemas/src/worldsim_schemas/   →  repos/<agent>/_schemas/
#   packages/prompts/src/worldsim_prompts/   →  repos/<agent>/_prompts/
#
# _schemas/ и _prompts/ в агентах — это снимки, не редактируйте вручную.

set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPOS_DIR="$(cd "${WORKSPACE_DIR}/.." && pwd)"
SCHEMAS_SRC="${WORKSPACE_DIR}/packages/schemas/src/worldsim_schemas"
PROMPTS_SRC="${WORKSPACE_DIR}/packages/prompts/src/worldsim_prompts"
AGENTS_FILE="${WORKSPACE_DIR}/repo-setup/agents.txt"

if [[ ! -d "${SCHEMAS_SRC}" ]]; then
  echo "Не найден ${SCHEMAS_SRC}" >&2
  exit 1
fi
if [[ ! -d "${PROMPTS_SRC}" ]]; then
  echo "Не найден ${PROMPTS_SRC}" >&2
  exit 1
fi

while IFS= read -r agent; do
  [[ -z "${agent}" ]] && continue
  [[ "${agent}" =~ ^# ]] && continue

  target="${REPOS_DIR}/${agent}"
  if [[ ! -d "${target}" ]]; then
    echo "! пропускаю ${agent} — папка ${target} не найдена"
    continue
  fi

  mkdir -p "${target}/_schemas" "${target}/_prompts"

  # Чистим старое содержимое (но не саму папку — она может быть в git)
  find "${target}/_schemas" -mindepth 1 -delete
  find "${target}/_prompts" -mindepth 1 -delete

  cp -R "${SCHEMAS_SRC}/." "${target}/_schemas/"
  cp -R "${PROMPTS_SRC}/." "${target}/_prompts/"

  # SYNCED маркер с таймштампом
  date -u +"%Y-%m-%dT%H:%M:%SZ" > "${target}/_schemas/.synced"
  date -u +"%Y-%m-%dT%H:%M:%SZ" > "${target}/_prompts/.synced"

  echo "✓ ${agent}"
done < "${AGENTS_FILE}"

echo ""
echo "Готово. Агент-репо теперь имеют свежие _schemas/ и _prompts/."
echo "Не забудьте запустить тесты в каждом: python -m pytest -q"
