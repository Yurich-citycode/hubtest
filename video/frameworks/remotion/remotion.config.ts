import { Config } from '@remotion/cli/config';

// Рендер идёт через локальный Chromium из video/bin/provision.mjs:
// путь подставляется флагом --browser-executable в bin/remotion.sh.
Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
Config.setConcurrency(2);
