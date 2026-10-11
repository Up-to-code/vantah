"""Add vAntah's GTK menu overlay while retaining existing user CSS."""
import os
from pathlib import Path
import re
import sys


def install(config, source):
    target = config / 'vantah'
    target.mkdir(parents=True, exist_ok=True)
    (target / 'gtk-menus.css').write_bytes(source.read_bytes())
    gtk = config / 'gtk-3.0'
    gtk.mkdir(parents=True, exist_ok=True)
    path = gtk / 'gtk.css'
    old = path.read_text() if path.exists() else ''
    marker = '/* vAntah application menus */\n@import url("../vantah/gtk-menus.css");\n/* end vAntah application menus */'
    pattern = r'/\* vAntah application menus \*/.*?/\* end vAntah application menus \*/'
    if re.search(pattern, old, re.S):
        new = re.sub(pattern, lambda _: marker, old, flags=re.S)
    else:
        new = old + ('\n' if old and not old.endswith('\n') else '') + marker + '\n'
    if new != old:
        path.write_text(new)


if __name__ == '__main__':
    config = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config')))
    install(config, Path(__file__).resolve().parents[1] / 'gtk-menus.css')
