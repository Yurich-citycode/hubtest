#!/usr/bin/env bash
# YurichHub video — установка окружения. Идемпотентно: можно запускать сколько угодно раз.
#
# Что делает:
#   1. ставит npm-зависимости (HyperFrames CLI, GSAP, Chromium, FFmpeg, FFprobe)
#   2. распаковывает Chromium и системные библиотеки в /tmp (в песочнице нет apt и Google CDN)
#   3. вендорит gsap.min.js в video/vendor (композиции не ходят в интернет)
#   4. показывает отчёт doctor
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "== 1/4  npm install =="
npm install --no-audit --no-fund

echo
echo "== 2/4  Chromium + системные библиотеки =="
node bin/provision.mjs

echo
echo "== 3/4  проверка окружения =="
node bin/doctor.mjs

echo
echo "Готово. Дальше:"
echo "  bash bin/hf.sh lint    projects/yurichhub-intro"
echo "  bash bin/hf.sh preview projects/yurichhub-intro"
echo "  bash bin/hf.sh render  projects/yurichhub-intro -o renders/yurichhub-intro.mp4"
