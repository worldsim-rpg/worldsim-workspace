#!/usr/bin/env bash
# CI-гуард: не дать закоммитить правку schemas.py без bump'а SCHEMA_VERSION.
#
# Режимы:
#   check-version-bump.sh                 # локально: staged + unstaged + untracked
#   check-version-bump.sh <base-ref>      # для PR против базы (origin/main и т.п.)
#
# Выход:
#   0 — либо schemas.py не менялся, либо version.py тоже меняется.
#   1 — schemas.py меняется, а version.py — нет → напомнить про bump.
#
# Запускать из корня worldsim-workspace.

set -euo pipefail

BASE_REF="${1:-}"

SCHEMAS_FILE="packages/schemas/src/worldsim_schemas/schemas.py"
VERSION_FILE="packages/schemas/src/worldsim_schemas/version.py"

# Возвращает непустой вывод, если файл имеет изменения в соответствующем режиме.
changed_in_working_tree() {
  local path="$1"
  # staged, unstaged, untracked — всё вместе.
  git status --porcelain -- "${path}" | awk 'NF'
}

changed_vs_ref() {
  local path="$1"
  local base="$2"
  git diff --name-only "${base}"...HEAD -- "${path}"
}

if [[ -z "${BASE_REF}" ]]; then
  schemas_changed=$(changed_in_working_tree "${SCHEMAS_FILE}")
  version_changed=$(changed_in_working_tree "${VERSION_FILE}")
else
  schemas_changed=$(changed_vs_ref "${SCHEMAS_FILE}" "${BASE_REF}")
  version_changed=$(changed_vs_ref "${VERSION_FILE}" "${BASE_REF}")
fi

if [[ -n "${schemas_changed}" && -z "${version_changed}" ]]; then
  cat >&2 <<EOF
✗ schemas.py изменился, но version.py — нет.

Любая правка pydantic-моделей канона требует bump SCHEMA_VERSION
(см. docs/schema-versioning.md).

Что делать:
  - Добавил опциональное поле → MINOR bump (0.1.0 → 0.2.0).
  - Сломал форму поля → MAJOR bump + миграция (migrations/README.md).
  - Только docstring/комментарий → PATCH bump (0.1.0 → 0.1.1).

Файл: ${VERSION_FILE}
EOF
  exit 1
fi

target="${BASE_REF:-working tree}"
echo "ok: schemas.py / version.py согласованы (${target})."
