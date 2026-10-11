const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync(process.argv[2] || '/usr/share/novnc/core/input/keyboard.js', 'utf8')
  .replace(/^import .*;$/gm, '')
  .replace('export default class Keyboard', 'class Keyboard') + '\nthis.Keyboard = Keyboard;';
const KeyTable = {XK_Super_L:0xffeb, XK_Super_R:0xffec, XK_Alt_L:0xffe9,
  XK_Alt_R:0xffea, XK_Mode_switch:0xff7e, XK_ISO_Level3_Shift:0xfe03};
const context = {KeyTable, Log:{Debug(){}}, stopEvent(){},
  KeyboardUtil:{getKeycode:e=>e.code, getKeysym:e=>e.sym},
  browser:{isMac:()=>true, isIOS:()=>false, isWindows:()=>false},
  setTimeout, clearTimeout};
vm.createContext(context);
vm.runInContext(source, context);
const keyboard = new context.Keyboard(null);
const events = [];
keyboard.onkeyevent = (sym,code,down)=>events.push([sym,code,down]);
const event = (code,sym,metaKey=false)=>({code,sym,metaKey,altKey:false,
  ctrlKey:false,shiftKey:false,getModifierState:()=>false});
keyboard._handleKeyDown(event('MetaLeft',KeyTable.XK_Super_L,true));
keyboard._handleKeyDown(event('KeyE',101)); // Host swallowed Command keyup.
keyboard._handleKeyUp(event('KeyE',101));
assert.deepEqual(events, [[0xffeb,'MetaLeft',true],[0xffeb,'MetaLeft',false],
  [101,'KeyE',true],[101,'KeyE',false]]);
assert.equal(Object.keys(keyboard._keyDownList).length,0);
console.log('PASS: lost Command release repaired before e; no Alt sent; keys released.');
