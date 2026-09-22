'use strict';
const fs = require('fs');
const path = require('path');
const { render } = require('./render');

const dir = path.join(__dirname, 'examples');
const outDir = path.join(__dirname, '..', 'samples');
fs.mkdirSync(outDir, { recursive: true });

for (const name of fs.readdirSync(dir).filter(f => f.endsWith('.json'))) {
  const spec = JSON.parse(fs.readFileSync(path.join(dir, name), 'utf8'));
  const png = render(spec);
  const out = path.join(outDir, name.replace(/\.json$/, '.png'));
  fs.writeFileSync(out, png);
  console.log(out, png.length);
}
