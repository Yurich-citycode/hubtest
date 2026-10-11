#!/usr/bin/env bash
# Обёртка над Remotion CLI: подставляет браузер из окружения песочницы.
#
#   bash bin/remotion.sh render src/index.ts TitleOutro out/title-outro.mp4
#   bash bin/remotion.sh studio
#   bash bin/remotion.sh lint
#
# Remotion не умеет читать HYPERFRAMES_BROWSER_PATH, поэтому передаём путь явно
# через --browser-executable (и он нужен только для render/studio/still).
set -euo pipefail
RM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VIDEO_ROOT="$(cd "$RM_ROOT/../.." && pwd)"
# shellcheck source=../../../bin/env.sh
source "$VIDEO_ROOT/bin/env.sh"

cd "$RM_ROOT"
exec npx remotion "$@" --browser-executable="$HYPERFRAMES_BROWSER_PATH"
