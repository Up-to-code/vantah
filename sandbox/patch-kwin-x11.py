#!/usr/bin/env python3
"""Enable Mesa GLX in Alpine, where Qt's own GLX plugin is disabled.

The GTK desktop uses an independent GLX scene; KWin's QtQuick surfaces use
Qt's software backend. On Qt builds with GLX, keep upstream context sharing.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1])
cmake = root / 'CMakeLists.txt'
text = cmake.read_text()
text = text.replace('set(HAVE_GLX false)', 'set(HAVE_GLX ${epoxy_HAS_GLX})')
text = text.replace('Disable GLX because Qt6::Gui was built without xcb_glx_plugin',
                    'Use standalone Mesa GLX with software QtQuick surfaces')
cmake.write_text(text)
context = root / 'src/backends/x11/standalone/glxcontext.cpp'
text = context.read_text()
start = text.index('    QOpenGLContext *qtGlobalShareContext =')
end = text.index('    GLXContext handle = nullptr;', start)
block = text[start:end]
block = block.replace('    GLXContext globalShareContext = nullptr;\n', '')
text = text[:start] + '    GLXContext globalShareContext = nullptr;\n#if QT_CONFIG(xcb_glx_plugin)\n' + block + '#endif\n\n' + text[end:]
context.write_text(text)
options = root / 'src/options.cpp'
text = options.read_text()
text = text.replace('if (QOpenGLContext::openGLModuleType() == QOpenGLContext::LibGLES) {',
    'if (QOpenGLContext::openGLModuleType() == QOpenGLContext::LibGLES && qstrcmp(envOpenGLInterface, "glx") != 0) {')
options.write_text(text)
src_cmake = root / 'src/CMakeLists.txt'
text = src_cmake.read_text()
if 'target_precompile_headers(kwin' not in text:
    text += '\ntarget_precompile_headers(kwin PRIVATE window.h workspace.h)\n'
    text += 'set_source_files_properties(3rdparty/xcursor.c PROPERTIES SKIP_PRECOMPILE_HEADERS ON)\n'
src_cmake.write_text(text)
