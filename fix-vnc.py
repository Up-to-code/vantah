"""Apply the local noVNC modifier fix, preserving the upstream source backups.

noVNC modifications remain covered by its MPL-2.0-or-later license.
"""
from pathlib import Path

root = Path('/usr/share/novnc')
keyboard = root / 'core/input/keyboard.js'
ui = root / 'app/ui.js'
for path in (keyboard, ui):
    backup = path.with_suffix(path.suffix + '.before-alpine-shell')
    if not backup.exists():
        backup.write_text(path.read_text())

text = keyboard.read_text()
if 'Alpine Shell modifier repair' not in text:
    anchor = '        // Is this key already pressed?'
    repair = '''        // Alpine Shell modifier repair: native macOS shortcuts can lose keyup
        // when the host intercepts them. Do not turn subsequent letters into
        // Linux Alt-menu accelerators when that modifier is no longer held.
        if (browser.isMac() || browser.isIOS()) {
            const modifiers = [
                ['MetaLeft', e.metaKey], ['MetaRight', e.metaKey],
                ['AltLeft', e.altKey], ['AltRight', e.altKey],
                ['ControlLeft', e.ctrlKey], ['ControlRight', e.ctrlKey],
                ['ShiftLeft', e.shiftKey], ['ShiftRight', e.shiftKey],
            ];
            for (const [modifier, held] of modifiers) {
                if (!held && modifier !== code && modifier in this._keyDownList) {
                    this._sendKeyEvent(this._keyDownList[modifier], modifier, false);
                }
            }
        }

'''
    if anchor not in text:
        raise SystemExit('Unexpected noVNC keyboard source; no patch applied.')
    text = text.replace(anchor, repair + anchor, 1)
    text = text.replace('case KeyTable.XK_Super_L:\n                    keysym = KeyTable.XK_Alt_L;',
                        'case KeyTable.XK_Super_L:\n                    keysym = KeyTable.XK_Super_L;', 1)
    keyboard.write_text(text)

text = ui.read_text()
if 'Alpine Shell connection modifier reset' not in text:
    anchor = '    connectFinished(e) {\n        UI.connected = true;'
    reset = '''    connectFinished(e) {
        UI.connected = true;
        // Alpine Shell connection modifier reset: a previous viewer may have
        // disconnected while Command/Alt was held. Clear remote state as well
        // as the current browser's tracked keyboard state.
        for (const [symbol, code] of [
            [KeyTable.XK_Alt_L, 'AltLeft'], [KeyTable.XK_Alt_R, 'AltRight'],
            [KeyTable.XK_Super_L, 'MetaLeft'], [KeyTable.XK_Super_R, 'MetaRight'],
            [KeyTable.XK_Control_L, 'ControlLeft'], [KeyTable.XK_Control_R, 'ControlRight'],
            [KeyTable.XK_Shift_L, 'ShiftLeft'], [KeyTable.XK_Shift_R, 'ShiftRight'],
        ]) {
            UI.rfb.sendKey(symbol, code, false);
        }'''
    if anchor not in text:
        raise SystemExit('Unexpected noVNC UI source; no UI patch applied.')
    ui.write_text(text.replace(anchor, reset, 1))
print('noVNC macOS modifier handling repaired.')
