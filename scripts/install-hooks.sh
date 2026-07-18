#!/bin/sh
# Install the repo's git hooks by pointing core.hooksPath at .githooks.
set -eu

cd "$(git rev-parse --show-toplevel)"
git config core.hooksPath .githooks

echo "Git hooks installed: core.hooksPath -> .githooks"
