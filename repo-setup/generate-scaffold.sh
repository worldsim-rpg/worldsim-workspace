#!/usr/bin/env bash
# Создаёт скелет нового агент-репо по шаблонам.
#
# Usage:
#   ./repo-setup/generate-scaffold.sh worldsim-plot-weaver worldsim_plot_weaver \
#       "LLM-агент, продвигающий сюжетные арки."

set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <repo-name> <python_pkg_name> <one-line-description>"
  echo "Example: $0 worldsim-plot-weaver worldsim_plot_weaver \"LLM-агент для арок\""
  exit 1
fi

REPO_NAME="$1"
PKG_NAME="$2"
DESCRIPTION="$3"

WORKSPACE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPOS_DIR="$(cd "${WORKSPACE_DIR}/.." && pwd)"
TARGET="${REPOS_DIR}/${REPO_NAME}"
TEMPLATES="${WORKSPACE_DIR}/repo-setup/templates"

if [[ -d "${TARGET}" ]]; then
  echo "${TARGET} уже существует. Удалите его вручную, если хотите пересоздать."
  exit 1
fi

mkdir -p "${TARGET}"/{src/"${PKG_NAME}",prompts,_schemas,_prompts,tests}

render() {
  sed \
    -e "s|{{AGENT_NAME}}|${REPO_NAME}|g" \
    -e "s|{{PKG_NAME}}|${PKG_NAME}|g" \
    -e "s|{{PKG_NAME_HYPHEN}}|${PKG_NAME//_/-}|g" \
    -e "s|{{ONE_LINE_DESCRIPTION}}|${DESCRIPTION}|g" \
    -e "s|{{WRITES_TO_CANON}}|НЕ пишет в канон напрямую — возвращает pydantic-модель|g" \
    -e "s|{{NEVER_WRITES}}|ничего не пишет, только возвращает результат|g" \
    "$1"
}

render "${TEMPLATES}/agent-README.md"      > "${TARGET}/README.md"
render "${TEMPLATES}/agent-CLAUDE.md"      > "${TARGET}/CLAUDE.md"
render "${TEMPLATES}/agent-pyproject.toml" > "${TARGET}/pyproject.toml"

cat > "${TARGET}/.gitignore" <<EOF
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
dist/
build/
.venv/
.env
EOF

cat > "${TARGET}/src/${PKG_NAME}/__init__.py" <<EOF
from .agent import run

__all__ = ["run"]
EOF

cat > "${TARGET}/src/${PKG_NAME}/agent.py" <<EOF
"""${REPO_NAME} — ${DESCRIPTION}"""

from __future__ import annotations


def run(input, *, client):
    """TODO: реализовать."""
    raise NotImplementedError
EOF

cat > "${TARGET}/prompts/main.md" <<'EOF'
# System prompt

TODO: напиши промпт для агента.

## Формат ответа

Строгий JSON, соответствующий схеме.
EOF

cat > "${TARGET}/tests/__init__.py" <<'EOF'
EOF

cat > "${TARGET}/tests/test_smoke.py" <<EOF
"""Дымовой тест — импорт должен работать."""


def test_import():
    from ${PKG_NAME} import run

    assert callable(run)
EOF

echo "✓ Создан ${TARGET}"
echo ""
echo "Дальше:"
echo "  1. Добавить имя '${REPO_NAME}' в ${WORKSPACE_DIR}/repo-setup/agents.txt"
echo "  2. Создать репо на GitHub: gh repo create worldsim-rpg/${REPO_NAME} --public"
echo "  3. cd ${TARGET} && git init -b main && git add . && git commit -m 'feat: scaffold'"
echo "  4. git remote add origin https://github.com/worldsim-rpg/${REPO_NAME}.git && git push -u origin main"
echo "  5. Из ${WORKSPACE_DIR}: ./repo-setup/sync-all.sh"
