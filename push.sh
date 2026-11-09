#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
message="${*:-Update KVAdapt}"

uv run pytest -q
git add -A

if git diff --cached --quiet; then
    echo 'No changes to commit.'
else
    git commit -m "$message"
fi

git push -u origin main
