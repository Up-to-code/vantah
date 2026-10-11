"""Request KWin blur for GTK menu content, excluding client shadow extents."""
import ctypes
from gi.repository import GdkX11


class GtkMenuGlass:
    def __init__(self, display, xlib, connection, rounded_region):
        self.display, self.xlib, self.connection = display, xlib, connection
        self.rounded_region, self.cache = rounded_region, {}
        ulp = ctypes.POINTER(ctypes.c_ulong)
        xlib.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        xlib.XDefaultRootWindow.restype = ctypes.c_ulong
        self.root = xlib.XDefaultRootWindow(connection)
        xlib.XQueryTree.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ulp, ulp,
                                   ctypes.POINTER(ulp), ctypes.POINTER(ctypes.c_uint)]
        xlib.XGetWindowProperty.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong,
            ctypes.c_long, ctypes.c_long, ctypes.c_int, ctypes.c_ulong, ulp,
            ctypes.POINTER(ctypes.c_int), ulp, ulp, ctypes.POINTER(ctypes.c_void_p)]
        xlib.XFree.argtypes = [ctypes.c_void_p]
        xlib.XSetErrorHandler.argtypes = [ctypes.c_void_p]
        xlib.XSetErrorHandler.restype = ctypes.c_void_p
        xlib.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.error_handler = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p,
                                              ctypes.c_void_p)(lambda *_: 0)
        self.atoms = {name: xlib.XInternAtom(connection, name.encode(), False) for name in (
            '_NET_WM_WINDOW_TYPE', '_NET_WM_WINDOW_TYPE_POPUP_MENU',
            '_NET_WM_WINDOW_TYPE_DROPDOWN_MENU', '_GTK_FRAME_EXTENTS',
            '_KDE_NET_WM_BLUR_BEHIND_REGION')}

    def property(self, xid, name):
        actual, count, remaining = ctypes.c_ulong(), ctypes.c_ulong(), ctypes.c_ulong()
        fmt, data = ctypes.c_int(), ctypes.c_void_p()
        status = self.xlib.XGetWindowProperty(self.connection, xid, self.atoms[name],
            0, 4096, False, 0, ctypes.byref(actual), ctypes.byref(fmt), ctypes.byref(count),
            ctypes.byref(remaining), ctypes.byref(data))
        try:
            if status or not actual.value or fmt.value != 32:
                return None
            if not count.value:
                return []
            values = ctypes.cast(data, ctypes.POINTER(ctypes.c_ulong))
            return [values[i] for i in range(count.value)]
        finally:
            if data: self.xlib.XFree(data)

    def update(self):
        previous = self.xlib.XSetErrorHandler(self.error_handler)
        children = ctypes.POINTER(ctypes.c_ulong)()
        root, parent, count = ctypes.c_ulong(), ctypes.c_ulong(), ctypes.c_uint()
        alive = set()
        try:
            self.xlib.XQueryTree(self.connection, self.root, ctypes.byref(root),
                ctypes.byref(parent), ctypes.byref(children), ctypes.byref(count))
            for i in range(count.value):
                xid = children[i]
                kinds = self.property(xid, '_NET_WM_WINDOW_TYPE') or []
                if not any(self.atoms[k] in kinds for k in (
                        '_NET_WM_WINDOW_TYPE_POPUP_MENU', '_NET_WM_WINDOW_TYPE_DROPDOWN_MENU')):
                    continue
                extents = self.property(xid, '_GTK_FRAME_EXTENTS') or []
                if len(extents) != 4: continue
                window = GdkX11.X11Window.foreign_new_for_display(self.display, xid)
                if not window or window.is_destroyed(): continue
                _, _, width, height = window.get_geometry()
                left, right, top, bottom = extents
                if width <= left + right or height <= top + bottom: continue
                alive.add(xid)
                signature = (width, height, *extents)
                if self.cache.get(xid) == signature: continue
                # Respect a blur region supplied by the application itself.
                if xid not in self.cache and self.property(xid, '_KDE_NET_WM_BLUR_BEHIND_REGION') is not None:
                    continue
                region = self.rounded_region(left, top, width-left-right, height-top-bottom, 10)
                values = []
                for j in range(region.num_rectangles()):
                    r = region.get_rectangle(j)
                    values.extend((r.x, r.y, r.width, r.height))
                data = (ctypes.c_ulong * len(values))(*values)
                self.xlib.XChangeProperty(self.connection, xid,
                    self.atoms['_KDE_NET_WM_BLUR_BEHIND_REGION'], 6, 32, 0,
                    ctypes.cast(data, ctypes.POINTER(ctypes.c_ubyte)), len(values))
                self.cache[xid] = signature
            self.cache = {key: value for key, value in self.cache.items() if key in alive}
        finally:
            if children: self.xlib.XFree(children)
            self.xlib.XSync(self.connection, False)
            self.xlib.XSetErrorHandler(previous)
        return True
