"""Exercise real X11 menu properties without mapping or displaying test windows."""
import ctypes
from pathlib import Path
import sys
import unittest
import cairo
import gi
gi.require_version('GdkX11', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gtk_menu_glass import GtkMenuGlass


class MenuGlassTests(unittest.TestCase):
    def setUp(self):
        self.x = ctypes.CDLL('libX11.so.6')
        self.x.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x.XOpenDisplay.restype = ctypes.c_void_p
        self.x.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        self.x.XInternAtom.restype = ctypes.c_ulong
        self.x.XChangeProperty.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
            ctypes.c_ulong, ctypes.c_ulong, ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int]
        self.connection = self.x.XOpenDisplay(None)
        self.assertTrue(self.connection)
        self.helper = GtkMenuGlass(Gdk.Display.get_default(), self.x, self.connection,
            lambda x, y, w, h, radius: cairo.Region(cairo.RectangleInt(x, y, w, h)))
        self.x.XCreateSimpleWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
            ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint,
            ctypes.c_uint, ctypes.c_ulong, ctypes.c_ulong]
        self.x.XCreateSimpleWindow.restype = ctypes.c_ulong
        self.x.XDestroyWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        self.x.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self.window = self.x.XCreateSimpleWindow(self.connection, self.helper.root,
                                                0, 0, 300, 200, 0, 0, 0)
        self.set_property('_NET_WM_WINDOW_TYPE',
                          [self.helper.atoms['_NET_WM_WINDOW_TYPE_POPUP_MENU']], 4)
        self.set_property('_GTK_FRAME_EXTENTS', [40, 40, 30, 50])

    def tearDown(self):
        if self.window: self.x.XDestroyWindow(self.connection, self.window)
        self.x.XCloseDisplay(self.connection)

    def set_property(self, name, values, kind=6):
        data = (ctypes.c_ulong * len(values))(*values)
        self.x.XChangeProperty(self.connection, self.window, self.helper.atoms[name],
            kind, 32, 0, ctypes.cast(data, ctypes.POINTER(ctypes.c_ubyte)), len(values))
        self.x.XSync(self.connection, False)

    def test_shadow_extents_are_excluded(self):
        self.helper.update()
        self.assertEqual(self.helper.property(self.window, '_KDE_NET_WM_BLUR_BEHIND_REGION'),
                         [40, 30, 220, 120])

    def test_application_blur_region_is_preserved(self):
        self.set_property('_KDE_NET_WM_BLUR_BEHIND_REGION', [50, 40, 100, 80])
        self.helper.update()
        self.assertEqual(self.helper.property(self.window, '_KDE_NET_WM_BLUR_BEHIND_REGION'),
                         [50, 40, 100, 80])

    def test_empty_application_region_is_preserved(self):
        self.set_property('_KDE_NET_WM_BLUR_BEHIND_REGION', [])
        self.helper.update()
        self.assertEqual(self.helper.property(self.window, '_KDE_NET_WM_BLUR_BEHIND_REGION'), [])

    def test_destroyed_menu_is_removed_without_badwindow_exit(self):
        self.helper.update()
        closed = self.window
        self.x.XDestroyWindow(self.connection, closed)
        self.window = None
        self.x.XSync(self.connection, False)
        self.helper.update()
        self.assertNotIn(closed, self.helper.cache)


if __name__ == '__main__': unittest.main()
