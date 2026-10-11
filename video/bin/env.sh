#!/usr/bin/env bash
# Переменные окружения для рендера. Использование:  source bin/env.sh
#
# Почему так: в песочнице нет apt, Google CDN и релизов GitHub, поэтому Chromium
# и FFmpeg берутся из npm-пакетов, а библиотеки libnspr4/libnss3 распаковываются
# рядом с ним в /tmp. HyperFrames умеет уважать эти переменные.

VIDEO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -f "$VIDEO_ROOT/.runtime/env.json" ]; then
  ( cd "$VIDEO_ROOT" && node bin/provision.mjs >/dev/null )
fi

eval "$(node -e '
  const fs = require("fs");
  const env = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
  const quote = (v) => JSON.stringify(String(v));
  const lines = [
    ["HYPERFRAMES_BROWSER_PATH", env.browser],
    ["HYPERFRAMES_FFMPEG_PATH", env.ffmpeg],
    ["HYPERFRAMES_FFPROBE_PATH", env.ffprobe],
    ["LD_LIBRARY_PATH", env.libDir + ":" + (process.env.LD_LIBRARY_PATH || "")],
    ["HYPERFRAMES_NO_TELEMETRY", "1"],
  ];
  for (const [k, v] of lines) console.log(`export ${k}=${quote(v)};`);
' "$VIDEO_ROOT/.runtime/env.json")"

export PATH="$VIDEO_ROOT/node_modules/.bin:$PATH"
