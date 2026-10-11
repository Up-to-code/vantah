// Exercise the patched noVNC resize handler against saved viewer settings.
const fs = require('node:fs');
const assert = require('node:assert/strict');
const source = fs.readFileSync(process.argv[2], 'utf8');
const body = source.match(/applyResizeMode\(\) \{([\s\S]*?)\n    \},/);
assert.ok(body, 'noVNC resize handler must exist');
const apply = new Function('UI', body[1]);
for (const [mode, fit, remote] of [['remote', true, true], ['scale', true, false], ['off', false, false]]) {
  const UI = {rfb: {}, getSetting: () => mode};
  apply(UI);
  assert.equal(UI.rfb.scaleViewport, fit, `${mode}: fixed framebuffer must fit when requested`);
  assert.equal(UI.rfb.resizeSession, remote, `${mode}: preserve remote resize requests`);
}
apply({rfb: null});
console.log('PASS: saved remote links fit; scale fits; off preserves native size.');
