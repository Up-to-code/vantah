#!/usr/bin/env python3
"""vAntah: a native GTK desktop shell on the X11 window manager."""
import datetime
import ctypes
import fcntl
import json
import math
import os
from pathlib import Path
import signal
import subprocess
from zoneinfo import ZoneInfo

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkX11', '3.0')
gi.require_version('Wnck', '3.0')
from gi.repository import Gdk, GdkPixbuf, GdkX11, Gio, GLib, Gtk, Pango, Wnck
import cairo

ROOT = Path(__file__).resolve().parent
PID_FILE = Path(f'/tmp/alpine-shell-{os.getuid()}.pid')
LOCK = open(f'/tmp/alpine-shell-{os.getuid()}.lock', 'w')
try:
    fcntl.flock(LOCK, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    raise SystemExit('vAntah is already running.')
PID_FILE.write_text(str(os.getpid()))


def style(widget, name):
    widget.get_style_context().add_class(name)
    return widget


def button(label, action, tooltip=None):
    obj = Gtk.Button(label=label)
    obj.connect('clicked', lambda _: action())
    if tooltip:
        obj.set_tooltip_text(tooltip)
    obj.get_accessible().set_name(tooltip or label)
    return obj


class Shell:
    def __init__(self):
        provider = Gtk.CssProvider()
        provider.load_from_path(str(ROOT / 'shell.css'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        Wnck.set_client_type(Wnck.ClientType.PAGER)
        self.screen = Wnck.Screen.get_default()
        self.screen.force_update()
        self.display = Gdk.Display.get_default()
        self.glass_xlib = None
        if os.environ.get('VANTAH_COMPOSITOR') == 'kwin':
            self.glass_xlib = ctypes.CDLL('libX11.so.6')
            self.glass_xlib.XOpenDisplay.argtypes = [ctypes.c_char_p]
            self.glass_xlib.XOpenDisplay.restype = ctypes.c_void_p
            self.glass_xlib.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
            self.glass_xlib.XInternAtom.restype = ctypes.c_ulong
            self.glass_xlib.XChangeProperty.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
                ctypes.c_ulong, ctypes.c_ulong, ctypes.c_int, ctypes.c_int,
                ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int]
            self.glass_xlib.XFlush.argtypes = [ctypes.c_void_p]
            self.glass_connection = self.glass_xlib.XOpenDisplay(None)
        self.launcher = None
        self.panels = {}
        self.category = 'All'
        self.app_infos = self.installed_apps()
        self.pins = [
            ('thunar.desktop', 'Files', 'system-file-manager', ('thunar',)),
            ('xfce4-terminal.desktop', 'Terminal', 'utilities-terminal', ('xfce4-terminal',)),
            ('org.xfce.mousepad.desktop', 'Text Editor', 'accessories-text-editor', ('mousepad', 'org.xfce.mousepad')),
            ('xfce-settings-manager.desktop', 'Settings', 'preferences-system', ('xfce4-settings-manager',)),
        ]
        self.pin_widgets = []
        self.icon_pixbufs = {}
        self.mode_items = {}
        self.settings_path = Path.home() / '.config/alpine-shell/settings.json'
        self.preferences = {'dark': True, 'reduced_motion': False}
        if self.settings_path.exists():
            try:
                self.preferences.update(json.loads(self.settings_path.read_text()))
            except (ValueError, OSError):
                pass
        self.compositor = None
        self.start_compositor()
        self.extra_signature = None
        self.bar = self.surface('vAntah — Menu Bar')
        self.dock = self.surface('vAntah — Dock')
        self.build_bar()
        self.build_dock()
        self.dock.connect('size-allocate', self.shape_dock)
        self.apply_appearance()
        self.save_preferences()
        self.bar.show_all()
        self.dock.show_all()
        self.layout()
        self.screen.connect('active-window-changed', lambda *_: self.update())
        self.screen.connect('window-opened', lambda *_: self.update())
        self.screen.connect('window-closed', lambda *_: self.update())
        Gdk.Screen.get_default().connect('size-changed', lambda *_: self.layout())
        GLib.timeout_add(1000, self.tick)
        signal.signal(signal.SIGUSR1, lambda *_: GLib.idle_add(self.toggle_launcher))
        signal.signal(signal.SIGTERM, lambda *_: GLib.idle_add(Gtk.main_quit))
        self.tick()

    def installed_apps(self):
        apps = {}
        for app in Gio.AppInfo.get_all():
            if not app.should_show() or (app.get_id() or '').startswith('panel-'):
                continue
            apps.setdefault(app.get_display_name().casefold(), app)
        return sorted(apps.values(), key=lambda app: app.get_display_name().casefold())

    def surface(self, title):
        win = Gtk.Window(title=title)
        win.set_name('shell-surface')
        win.set_decorated(False)
        win.set_app_paintable(True)
        visual = win.get_screen().get_rgba_visual()
        if visual:
            win.set_visual(visual)
        win.connect('draw', self.clear_surface)
        win.connect('size-allocate', self.full_glass_region)
        win.set_resizable(False)
        win.set_accept_focus(False)
        win.set_type_hint(Gdk.WindowTypeHint.DOCK)
        win.set_keep_above(True)
        win.stick()
        win.set_skip_taskbar_hint(True)
        win.set_skip_pager_hint(True)
        return win

    def clear_surface(self, _, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        return False

    def shape_dock(self, widget, allocation):
        if not widget.get_realized():
            return
        width, height = allocation.width, allocation.height
        radius = min(24, height // 2)
        region = cairo.Region()
        for row in range(height):
            distance = max(0, radius - row - 0.5, row - (height - radius) + 0.5)
            inset = math.ceil(radius - math.sqrt(max(0, radius * radius - distance * distance))) if distance else 0
            region.union(cairo.RectangleInt(inset, row, max(1, width - inset * 2), 1))
        widget.get_window().shape_combine_region(region, 0, 0)
        self.glass_region(widget, region)

    def full_glass_region(self, widget, allocation):
        self.glass_region(widget, cairo.Region(cairo.RectangleInt(
            0, 0, allocation.width, allocation.height)))

    def glass_region(self, widget, region):
        if not self.glass_xlib or not self.glass_connection or not widget.get_realized():
            return
        values = []
        for index in range(region.num_rectangles()):
            rect = region.get_rectangle(index)
            values.extend((rect.x, rect.y, rect.width, rect.height))
        signature = tuple(values)
        if getattr(widget, 'glass_region_signature', None) == signature:
            return
        widget.glass_region_signature = signature
        # KWin's real backdrop effect follows the visible GTK shape, including
        # the transparent gap between the launcher pill and its app grid.
        data = (ctypes.c_ulong * len(values))(*values)
        prop = self.glass_xlib.XInternAtom(self.glass_connection,
            b'_KDE_NET_WM_BLUR_BEHIND_REGION', False)
        cardinal = self.glass_xlib.XInternAtom(self.glass_connection, b'CARDINAL', False)
        self.glass_xlib.XChangeProperty(self.glass_connection,
            widget.get_window().get_xid(), prop, cardinal, 32, 0,
            ctypes.cast(data, ctypes.POINTER(ctypes.c_ubyte)), len(values))
        self.glass_xlib.XFlush(self.glass_connection)

    def rounded_region(self, x, y, width, height, radius):
        region = cairo.Region()
        radius = min(radius, width // 2, height // 2)
        for row in range(height):
            distance = max(0, radius - row - 0.5, row - (height - radius) + 0.5)
            inset = math.ceil(radius - math.sqrt(max(0, radius * radius - distance * distance))) if distance else 0
            region.union(cairo.RectangleInt(x + inset, y + row, max(1, width - inset * 2), 1))
        return region

    def shape_panel(self, widget, allocation):
        if widget.get_realized():
            region = self.rounded_region(0, 0, allocation.width, allocation.height, 18)
            widget.get_window().shape_combine_region(region, 0, 0)
            self.glass_region(widget, region)

    def close_panels(self):
        for panel in self.panels.values():
            panel.hide()

    def show_panel(self, key, title, content, width=260, anchor=None):
        old = self.panels.get(key)
        visible = old and old.get_visible()
        self.close_panels()
        if visible:
            return
        if old:
            old.destroy()
        if self.launcher:
            self.launcher.hide()
        win = Gtk.Window(title=title)
        win.set_name('panel-window')
        win.set_decorated(False)
        win.set_resizable(False)
        win.set_app_paintable(True)
        visual = win.get_screen().get_rgba_visual()
        if visual:
            win.set_visual(visual)
        win.connect('draw', self.clear_surface)
        win.connect('size-allocate', self.shape_panel)
        win.set_type_hint(Gdk.WindowTypeHint.POPUP_MENU)
        win.set_keep_above(True)
        win.set_skip_taskbar_hint(True)
        win.set_skip_pager_hint(True)
        win.connect('focus-out-event', lambda *_: win.hide() or False)
        win.connect('key-press-event', lambda _, event: (win.hide() or True) if event.keyval == Gdk.KEY_Escape else False)
        card = style(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2), 'menu-card')
        card.add(content)
        win.add(card)
        self.panels[key] = win
        self.style_appearance(win)
        win.set_size_request(min(width, self.geometry.width - 24), -1)
        win.show_all()
        w, h = win.get_preferred_size()[1].width, win.get_preferred_size()[1].height
        if anchor:
            owner = anchor.get_toplevel()
            _, ox, oy = owner.get_window().get_origin()
            translated = anchor.translate_coordinates(owner, 0, 0)
            ax, ay = translated if translated else (0, 0)
            x, y = ox + ax, oy + ay + anchor.get_allocated_height() + 6
        else:
            _, x, y = self.display.get_default_seat().get_pointer().get_position()
        g = self.geometry
        win.move(max(g.x + 6, min(x, g.x + g.width - w - 6)),
                 max(g.y + 40, min(y, g.y + g.height - h - 10)))
        win.present_with_time(Gtk.get_current_event_time())

    def panel_action(self, box, label, callback):
        def activate():
            self.close_panels()
            callback()
        obj = style(button(label, activate), 'menu-action')
        obj.set_halign(Gtk.Align.FILL)
        obj.get_child().set_halign(Gtk.Align.START)
        box.pack_start(obj, False, False, 0)

    def main_menu(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        for text, callback in [
            ('About vAntah', self.about),
            ('Applications', self.toggle_launcher),
            ('Home folder', lambda: self.launch_id('thunar.desktop')),
            ('System settings', lambda: self.launch_id('xfce-settings-manager.desktop')),
            ('Change wallpaper', lambda: self.launch_id('xfce-backdrop-settings.desktop')),
        ]:
            self.panel_action(box, text, callback)
        box.pack_start(Gtk.Separator(), False, False, 7)
        self.mode_items = {}
        for name, key in [('Dark appearance', 'dark'), ('Reduce motion', 'reduced_motion')]:
            item = style(Gtk.CheckButton(label=name), 'menu-toggle')
            item.set_active(self.preferences[key])
            item.connect('toggled', lambda obj, k=key: self.change_mode(k, obj.get_active()))
            self.mode_items[key] = item
            box.pack_start(item, False, False, 0)
        if os.environ.get('VANTAH_COMPOSITOR') != 'kwin':
            box.pack_start(Gtk.Separator(), False, False, 7)
            self.panel_action(box, 'Restore Xfce panels', self.restore)
        self.show_panel('main', 'vAntah — Menu', box, anchor=self.brand_button)

    def build_bar(self):
        box = style(Gtk.Box(spacing=4), 'menu-bar')
        self.bar.add(box)
        brand = Gtk.Button()
        brand.connect('clicked', lambda *_: self.main_menu())
        self.brand_button = brand
        self.brand_image = Gtk.Image()
        brand.add(self.brand_image)
        brand.get_accessible().set_name('vAntah menu')
        style(brand, 'brand-button')
        box.pack_start(brand, False, False, 0)
        self.active_label = style(Gtk.Label(label='Desktop'), 'active-app')
        self.active_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.active_label.set_max_width_chars(24)
        box.pack_start(self.active_label, False, False, 9)
        self.apps_button = button('Applications', self.toggle_launcher)
        box.pack_start(self.apps_button, False, False, 0)
        box.pack_start(Gtk.Box(), True, True, 0)
        self.session_button = button('sandbox', self.session_menu, 'Session information')
        box.pack_end(self.session_button, False, False, 0)
        self.clock = button('', self.calendar, 'Date and calendar — Cairo time')
        box.pack_end(self.clock, False, False, 0)
        self.appearance_button = button('☾', self.toggle_dark, 'Toggle dark or light appearance')
        box.pack_end(self.appearance_button, False, False, 0)
        search = button('⌕', self.toggle_launcher, 'Search applications — Super+Space')
        style(search, 'search-button')
        box.pack_end(search, False, False, 0)

    def has_tahoe_icons(self):
        return any((root / 'MacTahoe').is_dir() for root in
                   (Path.home() / '.local/share/icons', Path('/usr/share/icons')))

    def icon(self, app_id, fallback, size):
        if self.has_tahoe_icons():
            themed = {'thunar.desktop': 'system-file-manager',
                      'xfce4-terminal.desktop': 'utilities-terminal',
                      'org.xfce.mousepad.desktop': 'accessories-text-editor',
                      'xfce-settings-manager.desktop': 'preferences-system',
                      'xfce4-appfinder.desktop': 'view-app-grid'}
            name = themed.get(app_id, 'view-app-grid' if fallback == 'view-app-grid-symbolic' else None)
            if name:
                image = Gtk.Image.new_from_icon_name(name, Gtk.IconSize.DIALOG)
                image.set_pixel_size(size)
                return image
        custom = {'thunar.desktop': 'files', 'xfce4-terminal.desktop': 'terminal',
                  'org.xfce.mousepad.desktop': 'editor', 'xfce-settings-manager.desktop': 'settings'}
        name = custom.get(app_id, 'applications' if fallback == 'view-app-grid-symbolic' else None)
        if not self.has_tahoe_icons() and name and (ROOT / 'icons' / f'{name}.svg').exists():
            return Gtk.Image.new_from_pixbuf(self.custom_pixbuf(name, size))
        app = Gio.DesktopAppInfo.new(app_id) if app_id else None
        if app and app.get_icon():
            image = Gtk.Image.new_from_gicon(app.get_icon(), Gtk.IconSize.DIALOG)
        else:
            image = Gtk.Image.new_from_icon_name(fallback, Gtk.IconSize.DIALOG)
        image.set_pixel_size(size)
        return image

    def build_dock(self):
        self.dock_box = style(Gtk.Box(spacing=2), 'dock')
        self.dock.add(self.dock_box)
        launcher = self.dock_item(None, 'Applications', 'view-app-grid-symbolic', self.toggle_launcher)
        self.dock_box.pack_start(launcher[0], False, False, 0)
        self.dock_box.pack_start(style(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), 'dock-separator'), False, False, 4)
        for app_id, name, fallback, classes in self.pins:
            item, dot = self.dock_item(app_id, name, fallback, lambda a=app_id, c=classes: self.activate_app(a, c))
            self.pin_widgets.append((classes, dot, item))
            self.dock_box.pack_start(item, False, False, 0)
        self.extras = Gtk.Box(spacing=2)
        self.dock_box.pack_start(self.extras, False, False, 0)

    def dock_item(self, app_id, name, icon_name, action, window=None):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        obj = style(Gtk.Button(), 'dock-button')
        obj.set_tooltip_text(name)
        obj.get_accessible().set_name(name)
        obj.connect('clicked', lambda _: action())
        if window and self.has_tahoe_icons():
            icon_name = (window.get_class_group_name() or 'application-x-executable').casefold()
            if not Gtk.IconTheme.get_default().has_icon(icon_name):
                icon_name = 'application-x-executable'
            image = self.icon(None, icon_name, 44)
        elif window and window.get_icon():
            pixbuf = window.get_icon().scale_simple(44, 44, 2)
            image = Gtk.Image.new_from_pixbuf(pixbuf)
        else:
            image = self.icon(app_id, icon_name, 44)
        obj.add(image)
        image.app_id, image.fallback = app_id, icon_name
        obj.set_size_request(56, 56)
        obj.connect('enter-notify-event', lambda *_: self.animate_icon(image, 54))
        obj.connect('leave-notify-event', lambda *_: self.animate_icon(image, 48))
        self.resize_icon(image, 48)
        obj.connect('button-press-event', lambda _, e: self.dock_context(e, app_id, window))
        dot = style(Gtk.Label(label=''), 'running-dot')
        outer.pack_start(obj, False, False, 0)
        outer.pack_start(dot, False, False, 0)
        return outer, dot

    def dock_context(self, event, app_id, window):
        if event.button != 3:
            return False
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        if app_id:
            self.panel_action(box, 'New window', lambda: self.launch_id(app_id))
        if window:
            self.panel_action(box, 'Close window', lambda: window.close(Gtk.get_current_event_time()))
        if box.get_children():
            self.show_panel('dock', 'vAntah — Dock Menu', box, width=210)
        return True

    def windows(self):
        return [w for w in self.screen.get_windows() if not w.is_skip_tasklist()
                and w.get_window_type() in (Wnck.WindowType.NORMAL, Wnck.WindowType.DIALOG)]

    def activate_app(self, app_id, classes):
        print(f'Dock activation: {app_id}', flush=True)
        matches = [w for w in self.windows() if (w.get_class_group_name() or '').casefold() in classes]
        if matches:
            active = self.screen.get_active_window()
            index = (matches.index(active) + 1) % len(matches) if active in matches else 0
            self.activate(matches[index])
        else:
            self.launch_id(app_id)

    def activate(self, window):
        time = Gtk.get_current_event_time()
        workspace = window.get_workspace()
        if workspace:
            workspace.activate(time)
        window.activate(time)

    def launch_id(self, app_id):
        app = Gio.DesktopAppInfo.new(app_id)
        if app:
            self.launch(app)

    def launch(self, app):
        print(f'Launch application: {app.get_id()}', flush=True)
        if self.launcher:
            self.launcher.hide()
        try:
            app.launch([], self.display.get_app_launch_context())
        except GLib.Error as error:
            self.message('Could not open application', str(error))

    def layout(self):
        monitor = self.display.get_primary_monitor() or self.display.get_monitor(0)
        self.geometry = monitor.get_geometry()
        g = self.geometry
        self.apps_button.set_visible(g.width >= 600)
        self.session_button.set_visible(g.width >= 700)
        self.active_label.set_max_width_chars(24 if g.width >= 700 else 14)
        self.bar.set_size_request(g.width, 34)
        self.bar.resize(g.width, 34)
        self.bar.move(g.x, g.y)
        width = min(self.dock_box.get_preferred_width()[1], g.width - 16)
        height = self.dock_box.get_preferred_height()[1]
        self.dock.resize(width, height)
        self.dock.move(g.x + (g.width - width) // 2, g.y + g.height - height - 12)
        self.reserve(self.bar, top=34)
        self.reserve(self.dock, bottom=98)
        return False

    def reserve(self, window, top=0, bottom=0):
        xid = window.get_window().get_xid()
        width = self.geometry.width
        values = [0, 0, top, bottom, 0, 0, 0, 0, 0, width - 1, 0, width - 1]
        subprocess.run(['xprop', '-id', str(xid), '-f', '_NET_WM_STRUT_PARTIAL', '32c',
                        '-set', '_NET_WM_STRUT_PARTIAL', ','.join(map(str, values))], check=False)

    def update(self):
        active = self.screen.get_active_window()
        if active and not active.is_skip_tasklist():
            name = active.get_class_group_name() or 'Desktop'
            friendly = {'thunar': 'Files', 'xfce4-terminal': 'Terminal', 'mousepad': 'Text Editor', 'org.xfce.mousepad': 'Text Editor',
                        'xfce4-settings-manager': 'Settings'}
            self.active_label.set_text(friendly.get(name.casefold(), name))
        elif not active or active.get_window_type() == Wnck.WindowType.DESKTOP:
            self.active_label.set_text('Desktop')
        windows = self.windows()
        for classes, dot, item in self.pin_widgets:
            matched = [w for w in windows if (w.get_class_group_name() or '').casefold() in classes]
            dot.set_text('•' if matched else '')
            ctx = item.get_style_context()
            ctx.add_class('active-dock-item') if active in matched else ctx.remove_class('active-dock-item')
        pinned = {name for _, _, _, classes in self.pins for name in classes}
        extra = [w for w in windows if (w.get_class_group_name() or '').casefold() not in pinned]
        capacity = max(0, (self.geometry.width - 390) // 58)
        signature = (capacity, tuple(w.get_xid() for w in extra))
        if signature != self.extra_signature:
            self.extra_signature = signature
            for child in self.extras.get_children():
                child.destroy()
            for win in extra[:capacity]:
                item, dot = self.dock_item(None, win.get_name(), 'application-x-executable',
                                           lambda w=win: self.activate(w), window=win)
                dot.set_text('•')
                self.extras.pack_start(item, False, False, 0)
            if len(extra) > capacity:
                item, dot = self.dock_item(None, 'All open windows', 'view-list-symbolic', self.window_menu)
                dot.set_text('•')
                self.extras.pack_start(item, False, False, 0)
            self.extras.show_all()
            GLib.idle_add(self.layout)

    def tick(self):
        pattern = '%a %d %b  %H:%M' if self.geometry.width >= 600 else '%a  %H:%M'
        self.clock.set_label(datetime.datetime.now(ZoneInfo('Africa/Cairo')).strftime(pattern))
        self.update()
        return True

    def toggle_launcher(self):
        self.close_panels()
        if self.launcher and self.launcher.get_visible():
            self.launcher.hide()
            return False
        if not self.launcher:
            self.build_launcher()
        self.entry.set_text('')
        width = min(760, self.geometry.width - 32)
        columns = max(1, (width - 40) // 110)
        rows = math.ceil(len(self.app_infos) / columns)
        height = min(520, self.geometry.height - 130, max(360, rows * 104 + 145))
        self.results.set_max_children_per_line(max(1, (width - 40) // 100))
        self.launcher.set_size_request(width, height)
        self.launcher.show_all()
        self.filter_apps()
        self.launcher.resize(width, height)
        self.launcher.move(self.geometry.x + (self.geometry.width - width) // 2,
                           self.geometry.y + max(48, (self.geometry.height - height) // 2))
        self.launcher.present_with_time(Gtk.get_current_event_time())
        self.entry.grab_focus()
        return False

    def shape_launcher(self, widget, allocation):
        if not widget.get_realized():
            return
        head = self.search_surface.get_allocation()
        card = self.grid_surface.get_allocation()
        region = self.rounded_region(head.x, head.y, head.width, head.height, head.height // 2)
        region.union(self.rounded_region(card.x, card.y, card.width, card.height, 24))
        widget.get_window().shape_combine_region(region, 0, 0)
        self.glass_region(widget, region)

    def build_launcher(self):
        win = Gtk.Window(title='vAntah — Applications')
        win.set_name('launcher-window')
        win.set_decorated(False)
        win.set_app_paintable(True)
        visual = win.get_screen().get_rgba_visual()
        if visual:
            win.set_visual(visual)
        win.connect('draw', self.clear_surface)
        win.set_resizable(False)
        win.set_keep_above(True)
        win.set_skip_taskbar_hint(True)
        win.set_skip_pager_hint(True)
        win.connect('delete-event', lambda *_: win.hide() or True)
        win.connect('focus-out-event', lambda *_: win.hide() or False)
        win.connect('key-press-event', self.launcher_key)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        win.add(root)
        head = style(Gtk.Box(spacing=8), 'launcher-search')
        self.search_surface = head
        self.entry = Gtk.SearchEntry()
        self.entry.set_placeholder_text('Search applications')
        self.entry.get_accessible().set_name('Search installed applications')
        self.entry.connect('changed', lambda *_: self.filter_apps())
        self.entry.connect('activate', lambda *_: self.launch_first())
        search_overlay = Gtk.Overlay()
        search_overlay.add(self.entry)
        self.search_hint = style(Gtk.Label(label='Search applications'), 'search-placeholder')
        self.search_hint.set_halign(Gtk.Align.START)
        self.search_hint.set_valign(Gtk.Align.CENTER)
        self.search_hint.set_margin_start(36)
        self.search_hint.set_no_show_all(True)
        search_overlay.add_overlay(self.search_hint)
        search_overlay.set_overlay_pass_through(self.search_hint, True)
        head.pack_start(search_overlay, True, True, 0)
        head.pack_end(style(button('×', win.hide, 'Close application launcher'), 'launcher-close'), False, False, 0)
        root.pack_start(head, False, False, 0)
        card = style(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10), 'app-grid-card')
        self.grid_surface = card
        root.pack_start(card, True, True, 0)
        categories = Gtk.Box(spacing=5)
        self.category_buttons = {}
        for name in ['All', 'Accessories', 'Development', 'System']:
            tab = style(Gtk.ToggleButton(label=name), 'category-tab')
            tab.set_active(name == self.category)
            tab.connect('clicked', lambda _, value=name: self.choose_category(value))
            self.category_buttons[name] = tab
            categories.pack_start(tab, False, False, 0)
        card.pack_start(categories, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(200)
        self.results = Gtk.FlowBox()
        self.results.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.results.set_homogeneous(True)
        self.results.set_valign(Gtk.Align.START)
        self.results.set_min_children_per_line(1)
        self.results.set_column_spacing(8)
        self.results.set_row_spacing(10)
        self.results.set_activate_on_single_click(True)
        self.results.connect('child-activated', lambda _, child: self.launch(child.app))
        scroll.add(self.results)
        card.pack_start(scroll, True, True, 0)
        self.empty_result = style(Gtk.Label(label='No matching applications'), 'empty-result')
        self.empty_result.set_no_show_all(True)
        card.pack_start(self.empty_result, False, False, 0)
        self.result_status = style(Gtk.Label(label=''), 'launcher-hint')
        card.pack_end(self.result_status, False, False, 0)
        self.launcher = win
        win.connect('size-allocate', self.shape_launcher)
        self.style_appearance(win)

    def choose_category(self, category):
        self.category = category
        for name, tab in self.category_buttons.items():
            tab.set_active(name == category)
        self.filter_apps()

    def style_appearance(self, window):
        ctx = window.get_style_context()
        if os.environ.get('VANTAH_COMPOSITOR') == 'kwin':
            ctx.add_class('kwin')
        ctx.remove_class('light') if self.preferences['dark'] else ctx.add_class('light')
        ctx.add_class('reduced-motion') if self.preferences['reduced_motion'] else ctx.remove_class('reduced-motion')

    def save_preferences(self):
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps(self.preferences, indent=2) + '\n')

    def apply_appearance(self):
        for win in (self.bar, self.dock, self.launcher, *self.panels.values()):
            if win:
                self.style_appearance(win)
        dark = self.preferences['dark']
        logo = ROOT / 'assets' / ('logo-light.svg' if dark else 'logo.svg')
        self.brand_image.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_scale(str(logo), 22, 22, True))
        theme = 'MacTahoe-Dark' if dark else 'MacTahoe-Light'
        theme_roots = (Path.home() / '.themes', Path.home() / '.local/share/themes', Path('/usr/share/themes'))
        has_theme = any((root / theme / 'gtk-3.0').is_dir() for root in theme_roots)
        if not has_theme:
            theme = 'WhiteSur-Dark' if dark else 'WhiteSur-Light'
            has_theme = any((root / theme / 'gtk-3.0').is_dir() for root in theme_roots)
        icon = ('MacTahoe-dark' if dark else 'MacTahoe-light') if self.has_tahoe_icons() else ('WhiteSur-dark' if dark else 'WhiteSur-light')
        icon_roots = (Path.home() / '.icons', Path.home() / '.local/share/icons', Path('/usr/share/icons'))
        has_icons = any((root / icon).is_dir() for root in icon_roots)
        has_frames = any((root / theme / 'xfwm4').is_dir() for root in theme_roots)
        for channel, prop, value in [
            ('xsettings', '/Net/ThemeName', theme if has_theme else ('Adwaita-dark' if dark else 'Adwaita')),
            ('xsettings', '/Net/IconThemeName', icon if has_icons else 'Adwaita'),
            ('xfwm4', '/general/theme', theme if has_frames else 'Default'),
        ]:
            subprocess.run(['xfconf-query', '-c', channel, '-p', prop, '-s', value], check=False)
        cursor = 'MacTahoe-dark-cursors' if dark else 'MacTahoe-cursors'
        if Path('/usr/share/icons', cursor).is_dir():
            subprocess.run(['xfconf-query', '-c', 'xsettings', '-p', '/Gtk/CursorThemeName',
                            '-n', '-t', 'string', '-s', cursor], check=False)
        subprocess.run(['xfconf-query', '-c', 'xsettings', '-p', '/Gtk/FontName',
                        '-n', '-t', 'string', '-s', 'Inter 10'], check=False)
        Gtk.Settings.get_default().set_property('gtk-icon-theme-name', icon if has_icons else 'Adwaita')
        if os.environ.get('VANTAH_COMPOSITOR') == 'kwin' and Path('/usr/share/aurorae/themes/MacTahoe-Dark').is_dir():
            decoration = 'MacTahoe-Dark' if dark else 'MacTahoe-Light'
            for key, value in [('library', 'org.kde.kwin.aurorae'), ('theme', '__aurorae__svg__' + decoration)]:
                subprocess.run(['kwriteconfig6', '--file', 'kwinrc', '--group', 'org.kde.kdecoration2',
                                '--key', key, value], check=False)
            subprocess.run(['gdbus', 'call', '--session', '--dest', 'org.kde.KWin', '--object-path', '/KWin',
                            '--method', 'org.kde.KWin.reconfigure'], stdout=subprocess.DEVNULL, check=False)
        self.appearance_button.set_label('☀' if dark else '☾')
        self.appearance_button.set_tooltip_text('Switch to light mode' if dark else 'Switch to dark mode')
        for key, item in self.mode_items.items():
            item.set_active(self.preferences[key])

    def toggle_dark(self):
        self.change_mode('dark', not self.preferences['dark'])

    def toggle_motion(self):
        self.change_mode('reduced_motion', not self.preferences['reduced_motion'])

    def change_mode(self, key, value):
        if self.preferences[key] == value:
            return
        self.preferences[key] = value
        self.apply_appearance()
        self.save_preferences()
        if key == 'reduced_motion':
            self.start_compositor()

    def animate_icon(self, image, target):
        image.animation_target = target
        if self.preferences['reduced_motion']:
            self.resize_icon(image, 48)
            return False
        if getattr(image, 'animation_active', False):
            return False
        image.animation_active = True
        image.animation_size = float(getattr(image, 'current_size', 48))
        def frame():
            if self.preferences['reduced_motion']:
                self.resize_icon(image, 48)
                image.animation_active = False
                return False
            image.animation_size += (image.animation_target - image.animation_size) * 0.25
            self.resize_icon(image, round(image.animation_size))
            if abs(image.animation_target - image.animation_size) < 0.3:
                self.resize_icon(image, image.animation_target)
                image.animation_active = False
                return False
            return True
        GLib.timeout_add(16, frame)
        return False

    def resize_icon(self, image, size):
        if getattr(image, 'current_size', None) == size:
            return
        image.current_size = size
        custom = {'thunar.desktop': 'files', 'xfce4-terminal.desktop': 'terminal',
                  'org.xfce.mousepad.desktop': 'editor', 'xfce-settings-manager.desktop': 'settings'}
        name = custom.get(getattr(image, 'app_id', None),
                          'applications' if getattr(image, 'fallback', '') == 'view-app-grid-symbolic' else None)
        if name and not self.has_tahoe_icons():
            image.set_from_pixbuf(self.custom_pixbuf(name, size))
        else:
            image.set_pixel_size(size)

    def custom_pixbuf(self, name, size):
        if name not in self.icon_pixbufs:
            self.icon_pixbufs[name] = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                str(ROOT / 'icons' / f'{name}.svg'), 64, 64, True)
        return self.icon_pixbufs[name].scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)

    def start_compositor(self):
        if os.environ.get('VANTAH_COMPOSITOR') == 'kwin':
            # KWin owns the Wayland scene and Xwayland clients. Starting Picom
            # here would compete with it and prevent compositor refraction.
            subprocess.run(['kwriteconfig6', '--file', 'kwinrc', '--group', 'KDE',
                            '--key', 'AnimationDurationFactor',
                            '0' if self.preferences['reduced_motion'] else '1'], check=False)
            subprocess.run(['gdbus', 'call', '--session', '--dest', 'org.kde.KWin',
                            '--object-path', '/KWin', '--method', 'org.kde.KWin.reconfigure'],
                           check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        if self.compositor and self.compositor.poll() is None:
            self.compositor.terminate()
            self.compositor.wait(timeout=3)
        subprocess.run(['xfconf-query', '-c', 'xfwm4', '-p', '/general/use_compositing', '-s', 'false'], check=False)
        filename = 'picom-reduced.conf' if self.preferences['reduced_motion'] else 'picom.conf'
        self.compositor_log = open('/tmp/alpine-shell-compositor.log', 'w')
        self.compositor = subprocess.Popen(['picom', '--config', str(ROOT / filename)],
                                            stdout=self.compositor_log, stderr=self.compositor_log)

    def stop(self):
        if os.environ.get('VANTAH_COMPOSITOR') == 'kwin':
            return
        if self.compositor and self.compositor.poll() is None:
            self.compositor.terminate()
            self.compositor.wait(timeout=3)
        subprocess.run(['xfconf-query', '-c', 'xfwm4', '-p', '/general/use_compositing', '-s', 'true'], check=False)

    def filter_apps(self):
        if not self.launcher:
            return
        for child in self.results.get_children():
            child.destroy()
        query = self.entry.get_text().casefold().strip()
        self.search_hint.set_visible(not self.entry.get_text())
        category_tags = {'Accessories': {'utility', 'office', 'audiovideo', 'graphics'},
                         'Development': {'development'}, 'System': {'system', 'settings'}}
        filtered = []
        for app in self.app_infos:
            tags = set((app.get_categories() or '').casefold().split(';'))
            if self.category != 'All' and not tags.intersection(category_tags[self.category]):
                continue
            if query not in (app.get_display_name() + ' ' + (app.get_description() or '')).casefold():
                continue
            filtered.append(app)
        for app in filtered:
            child = style(Gtk.FlowBoxChild(), 'app-tile')
            child.app = app
            child.set_tooltip_text(app.get_display_name())
            child.get_accessible().set_name(app.get_display_name())
            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
            content.pack_start(self.icon(app.get_id(), 'application-x-executable', 48), False, False, 0)
            label = style(Gtk.Label(label=app.get_display_name()), 'app-name')
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_max_width_chars(11)
            content.pack_start(label, False, False, 0)
            child.add(content)
            self.results.add(child)
        self.results.show_all()
        self.empty_result.set_visible(not filtered)
        self.result_status.set_text(f'{len(filtered)} applications  ·  Enter to open  ·  Esc to close')
        if filtered:
            self.results.select_child(self.results.get_child_at_index(0))

    def launch_first(self):
        selected = self.results.get_selected_children()
        if selected:
            self.launch(selected[0].app)

    def launcher_key(self, _, event):
        if event.keyval == Gdk.KEY_Escape:
            self.launcher.hide()
            return True
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self.launch_first()
            return True
        arrows = (Gdk.KEY_Down, Gdk.KEY_Up, Gdk.KEY_Left, Gdk.KEY_Right)
        if event.keyval not in arrows or (self.entry.has_focus() and event.keyval in (Gdk.KEY_Left, Gdk.KEY_Right)):
            return False
        children = self.results.get_children()
        selected = self.results.get_selected_children()
        if not children:
            return True
        current = selected[0] if selected else children[0]
        index = children.index(current)
        target = current
        if event.keyval in (Gdk.KEY_Left, Gdk.KEY_Right):
            step = -1 if event.keyval == Gdk.KEY_Left else 1
            target = children[max(0, min(len(children)-1, index+step))]
        else:
            allocation = current.get_allocation()
            candidates = [child for child in children if
                          (child.get_allocation().y > allocation.y if event.keyval == Gdk.KEY_Down
                           else child.get_allocation().y < allocation.y)]
            if candidates:
                target = min(candidates, key=lambda child: (abs(child.get_allocation().y-allocation.y),
                                                           abs(child.get_allocation().x-allocation.x)))
        self.results.select_child(target)
        target.grab_focus()
        return True

    def calendar(self):
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        content.add(Gtk.Label(label='Cairo · Africa/Cairo'))
        calendar = Gtk.Calendar()
        now = datetime.datetime.now(ZoneInfo('Africa/Cairo'))
        calendar.select_month(now.month - 1, now.year)
        calendar.select_day(now.day)
        content.add(calendar)
        self.show_panel('calendar', 'vAntah — Calendar', content, width=300, anchor=self.clock)

    def window_menu(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        for win in self.windows():
            self.panel_action(box, win.get_name(), lambda w=win: self.activate(w))
        if not box.get_children():
            box.add(Gtk.Label(label='No open windows'))
        self.show_panel('windows', 'vAntah — Window Menu', box, width=300)

    def session_menu(self):
        self.message('Alpine Linux', 'vAntah · native GTK desktop\nUser: sandbox\nSuper+Space opens application search.\nRight-click a dock app for window actions.')

    def about(self):
        self.message('vAntah', 'A custom native desktop shell for Alpine Linux.\nBuilt with GTK 3, PyGObject, and libwnck.\nSource: ~/.local/share/alpine-shell\nShell code: MIT license\nWhiteSur artwork remains under its upstream licenses.')

    def message(self, title, text):
        dialog = Gtk.MessageDialog(message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.CLOSE, text=title)
        dialog.format_secondary_text(text)
        dialog.connect('response', lambda obj, _: obj.destroy())
        dialog.show_all()

    def restore(self):
        subprocess.Popen(['xfce4-panel'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Gtk.main_quit()


if __name__ == '__main__':
    shell = Shell()
    try:
        Gtk.main()
    finally:
        shell.stop()
        PID_FILE.unlink(missing_ok=True)
