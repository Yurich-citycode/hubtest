#!/usr/bin/env bash
# Обёртка над HyperFrames CLI: сама поднимает окружение песочницы.
#
#   bash bin/hf.sh lint    projects/yurichhub-intro
#   bash bin/hf.sh check   projects/yurichhub-intro
#   bash bin/hf.sh snapshot projects/yurichhub-intro --at 1,4,9
#   bash bin/hf.sh render  projects/yurichhub-intro -o renders/yurichhub-intro.mp4
#   bash bin/hf.sh preview projects/yurichhub-intro --port 3002
#
# Внутри самих проектов можно вызывать короче:
#   cd projects/yurichhub-intro && npx hyperframes render .
set -euo pipefail
VIDEO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=env.sh
source "$VIDEO_ROOT/bin/env.sh"

if [ ! -x "$VIDEO_ROOT/node_modules/.bin/hyperframes" ]; then
  echo "Нет HyperFrames CLI. Запусти: bash $VIDEO_ROOT/setup.sh" >&2
  exit 1
fi

exec "$VIDEO_ROOT/node_modules/.bin/hyperframes" "$@"
