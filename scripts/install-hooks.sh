#!/usr/bin/env bash
# Install project git hooks. Opt-in — run once per clone.
set -euo pipefail
REPO_ROOT=$(git rev-parse --show-toplevel)
SRC="$REPO_ROOT/scripts/git-hooks"
DEST="$REPO_ROOT/.git/hooks"

for hook in "$SRC"/*; do
  name=$(basename "$hook")
  chmod +x "$hook"
  ln -sf "$SRC/$name" "$DEST/$name"
  echo "[ok] installed $name → $DEST/$name"
done
