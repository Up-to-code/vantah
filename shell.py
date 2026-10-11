#!/usr/bin/env python3
"""vAntah: a native GTK desktop shell on the X11 window manager."""
import datetime
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
    obj.set_tooltip_text(tooltip or label)
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
        self.launcher = None
        self.app_infos = self.installed_apps()
        self.pins = [
            ('thunar.desktop', 'Files', 'system-file-manager', ('thunar',)),
            ('xfce4-terminal.desktop', 'Terminal', 'utilities-terminal', ('xfce4-terminal',)),
            ('org.xfce.mousepad.desktop', 'Text Editor', 'accessories-text-editor', ('mousepad',)),
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

    def build_bar(self):
        box = style(Gtk.Box(spacing=4), 'menu-bar')
        self.bar.add(box)
        menu = Gtk.Menu()
        for text, callback in [
            ('About vAntah', self.about),
            ('Applications…', self.toggle_launcher),
            ('Open Home', lambda: self.launch_id('thunar.desktop')),
            ('System Settings…', lambda: self.launch_id('xfce-settings-manager.desktop')),
            ('Wallpaper…', lambda: self.launch_id('xfce-backdrop-settings.desktop')),
            ('Restore Xfce Panels', self.restore),
        ]:
            item = Gtk.MenuItem(label=text)
            item.connect('activate', lambda _, cb=callback: cb())
            menu.append(item)
        menu.show_all()
        for name, key, callback in [
            ('Dark Mode', 'dark', self.toggle_dark),
            ('Reduce Motion', 'reduced_motion', self.toggle_motion),
        ]:
            item = Gtk.CheckMenuItem(label=name)
            item.set_active(self.preferences[key])
            item.connect('toggled', lambda obj, k=key: self.change_mode(k, obj.get_active()))
            self.mode_items[key] = item
            menu.append(item)
        menu.show_all()
        brand = Gtk.MenuButton()
        self.brand_image = Gtk.Image()
        brand.add(self.brand_image)
        brand.set_popup(menu)
        brand.set_tooltip_text('vAntah menu')
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

    def icon(self, app_id, fallback, size):
        custom = {'thunar.desktop': 'files', 'xfce4-terminal.desktop': 'terminal',
                  'org.xfce.mousepad.desktop': 'editor', 'xfce-settings-manager.desktop': 'settings'}
        name = custom.get(app_id, 'applications' if fallback == 'view-app-grid-symbolic' else None)
        if name and (ROOT / 'icons' / f'{name}.svg').exists():
            return Gtk.Image.new_from_pixbuf(self.custom_pixbuf(name, size))
        app = Gio.DesktopAppInfo.new(app_id) if app_id else None
        if app and app.get_icon():
            image = Gtk.Image.new_from_gicon(app.get_icon(), Gtk.IconSize.DIALOG)
        else:
            image = Gtk.Image.new_from_icon_name(fallback, Gtk.IconSize.DIALOG)
        image.set_pixel_size(size)
        return image

    def build_dock(self):
        self.dock_box = style(Gtk.Box(spacing=3), 'dock')
        self.dock.add(self.dock_box)
        launcher = self.dock_item(None, 'Applications', 'view-app-grid-symbolic', self.toggle_launcher)
        self.dock_box.pack_start(launcher[0], False, False, 0)
        self.dock_box.pack_start(style(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), 'dock-separator'), False, False, 8)
        for app_id, name, fallback, classes in self.pins:
            item, dot = self.dock_item(app_id, name, fallback, lambda a=app_id, c=classes: self.activate_app(a, c))
            self.pin_widgets.append((classes, dot, item))
            self.dock_box.pack_start(item, False, False, 0)
        self.extras = Gtk.Box(spacing=3)
        self.dock_box.pack_start(self.extras, False, False, 0)

    def dock_item(self, app_id, name, icon_name, action, window=None):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        obj = style(Gtk.Button(), 'dock-button')
        obj.set_tooltip_text(name)
        obj.get_accessible().set_name(name)
        obj.connect('clicked', lambda _: action())
        if window and window.get_icon():
            pixbuf = window.get_icon().scale_simple(44, 44, 2)
            image = Gtk.Image.new_from_pixbuf(pixbuf)
        else:
            image = self.icon(app_id, icon_name, 44)
        obj.add(image)
        image.app_id, image.fallback = app_id, icon_name
        obj.set_size_request(54, 54)
        obj.connect('enter-notify-event', lambda *_: self.animate_icon(image, 49))
        obj.connect('leave-notify-event', lambda *_: self.animate_icon(image, 40))
        self.resize_icon(image, 40)
        obj.connect('button-press-event', lambda _, e: self.dock_context(e, app_id, window))
        dot = style(Gtk.Label(label=''), 'running-dot')
        outer.pack_start(obj, False, False, 0)
        outer.pack_start(dot, False, False, 0)
        return outer, dot

    def dock_context(self, event, app_id, window):
        if event.button != 3:
            return False
        menu = Gtk.Menu()
        if app_id:
            item = Gtk.MenuItem(label='New Window')
            item.connect('activate', lambda _: self.launch_id(app_id))
            menu.append(item)
        if window:
            item = Gtk.MenuItem(label='Close Window')
            item.connect('activate', lambda _: window.close(Gtk.get_current_event_time()))
            menu.append(item)
        menu.show_all()
        if menu.get_children():
            menu.popup_at_pointer(event)
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
            friendly = {'thunar': 'Files', 'xfce4-terminal': 'Terminal', 'mousepad': 'Text Editor',
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
        if self.launcher and self.launcher.get_visible():
            self.launcher.hide()
            return False
        if not self.launcher:
            self.build_launcher()
        self.entry.set_text('')
        self.filter_apps()
        width = min(620, self.geometry.width - 32)
        height = min(440, self.geometry.height - 120)
        self.launcher.set_size_request(width, height)
        self.launcher.show_all()
        self.launcher.resize(width, height)
        self.launcher.move(self.geometry.x + (self.geometry.width - width) // 2,
                           self.geometry.y + (self.geometry.height - height) // 2)
        self.launcher.present_with_time(Gtk.get_current_event_time())
        self.entry.grab_focus()
        return False

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
        win.connect('delete-event', lambda *_: win.hide() or True)
        win.connect('key-press-event', self.launcher_key)
        box = style(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12), 'launcher-card')
        win.add(box)
        heading = Gtk.Box()
        heading.pack_start(style(Gtk.Label(label='Applications'), 'launcher-heading'), False, False, 0)
        heading.pack_end(button('×', win.hide, 'Close application launcher'), False, False, 0)
        box.pack_start(heading, False, False, 0)
        self.entry = Gtk.SearchEntry()
        self.entry.set_placeholder_text('Search installed applications…')
        self.entry.get_accessible().set_name('Search installed applications')
        self.entry.connect('changed', lambda *_: self.filter_apps())
        self.entry.connect('activate', lambda *_: self.launch_first())
        box.pack_start(self.entry, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(270)
        self.results = Gtk.ListBox()
        self.results.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.results.connect('row-activated', lambda _, row: self.launch(row.app))
        scroll.add(self.results)
        box.pack_start(scroll, True, True, 0)
        box.pack_end(style(Gtk.Label(label='Enter to open  ·  ↑ ↓ to navigate  ·  Esc to close'), 'launcher-hint'), False, False, 0)
        self.launcher = win
        self.style_appearance(win)

    def style_appearance(self, window):
        ctx = window.get_style_context()
        ctx.remove_class('light') if self.preferences['dark'] else ctx.add_class('light')
        ctx.add_class('reduced-motion') if self.preferences['reduced_motion'] else ctx.remove_class('reduced-motion')

    def save_preferences(self):
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps(self.preferences, indent=2) + '\n')

    def apply_appearance(self):
        for win in (self.bar, self.dock, self.launcher):
            if win:
                self.style_appearance(win)
        dark = self.preferences['dark']
        logo = ROOT / 'assets' / ('logo-light.svg' if dark else 'logo.svg')
        self.brand_image.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_scale(str(logo), 22, 22, True))
        theme = 'WhiteSur-Dark' if dark else 'WhiteSur-Light'
        theme_roots = (Path.home() / '.themes', Path.home() / '.local/share/themes', Path('/usr/share/themes'))
        has_whitesur = any((root / theme / 'gtk-3.0').is_dir() for root in theme_roots)
        icon = 'WhiteSur-dark' if dark else 'WhiteSur-light'
        icon_roots = (Path.home() / '.icons', Path.home() / '.local/share/icons', Path('/usr/share/icons'))
        has_icons = any((root / icon).is_dir() for root in icon_roots)
        has_frames = any((root / theme / 'xfwm4').is_dir() for root in theme_roots)
        for channel, prop, value in [
            ('xsettings', '/Net/ThemeName', theme if has_whitesur else ('Adwaita-dark' if dark else 'Adwaita')),
            ('xsettings', '/Net/IconThemeName', icon if has_icons else 'Adwaita'),
            ('xfwm4', '/general/theme', theme if has_frames else 'Default'),
        ]:
            subprocess.run(['xfconf-query', '-c', channel, '-p', prop, '-s', value], check=False)
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
            self.resize_icon(image, 40)
            return False
        if getattr(image, 'animation_active', False):
            return False
        image.animation_active = True
        image.animation_size = float(getattr(image, 'current_size', 40))
        def frame():
            if self.preferences['reduced_motion']:
                self.resize_icon(image, 40)
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
        if name:
            image.set_from_pixbuf(self.custom_pixbuf(name, size))
        else:
            image.set_pixel_size(size)

    def custom_pixbuf(self, name, size):
        if name not in self.icon_pixbufs:
            self.icon_pixbufs[name] = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                str(ROOT / 'icons' / f'{name}.svg'), 64, 64, True)
        return self.icon_pixbufs[name].scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)

    def start_compositor(self):
        if self.compositor and self.compositor.poll() is None:
            self.compositor.terminate()
            self.compositor.wait(timeout=3)
        subprocess.run(['xfconf-query', '-c', 'xfwm4', '-p', '/general/use_compositing', '-s', 'false'], check=False)
        filename = 'picom-reduced.conf' if self.preferences['reduced_motion'] else 'picom.conf'
        self.compositor_log = open('/tmp/alpine-shell-compositor.log', 'w')
        self.compositor = subprocess.Popen(['picom', '--config', str(ROOT / filename)],
                                            stdout=self.compositor_log, stderr=self.compositor_log)

    def stop(self):
        if self.compositor and self.compositor.poll() is None:
            self.compositor.terminate()
            self.compositor.wait(timeout=3)
        subprocess.run(['xfconf-query', '-c', 'xfwm4', '-p', '/general/use_compositing', '-s', 'true'], check=False)

    def filter_apps(self):
        for child in self.results.get_children():
            child.destroy()
        query = self.entry.get_text().casefold().strip()
        filtered = [app for app in self.app_infos if query in
                    (app.get_display_name() + ' ' + (app.get_description() or '')).casefold()]
        for app in filtered:
            row = Gtk.ListBoxRow()
            row.app = app
            box = style(Gtk.Box(spacing=14), 'result-row')
            box.pack_start(self.icon(app.get_id(), 'application-x-executable', 32), False, False, 0)
            text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            label = Gtk.Label(label=app.get_display_name(), xalign=0)
            text.pack_start(style(label, 'result-title'), False, False, 0)
            detail = Gtk.Label(label=app.get_description() or 'Installed application', xalign=0)
            detail.set_ellipsize(Pango.EllipsizeMode.END)
            text.pack_start(style(detail, 'result-description'), False, False, 0)
            box.pack_start(text, True, True, 0)
            row.add(box)
            self.results.add(row)
        if not filtered:
            empty = style(Gtk.Label(label='No matching applications'), 'empty-result')
            self.results.add(empty)
        self.results.show_all()
        if filtered:
            self.results.select_row(self.results.get_row_at_index(0))

    def launch_first(self):
        row = self.results.get_selected_row()
        if row and hasattr(row, 'app'):
            self.launch(row.app)

    def launcher_key(self, _, event):
        if event.keyval == Gdk.KEY_Escape:
            self.launcher.hide()
            return True
        if event.keyval in (Gdk.KEY_Down, Gdk.KEY_Up):
            row = self.results.get_selected_row()
            index = row.get_index() if row else 0
            next_row = self.results.get_row_at_index(max(0, index + (1 if event.keyval == Gdk.KEY_Down else -1)))
            if next_row:
                self.results.select_row(next_row)
                next_row.grab_focus()
            return True
        return False

    def calendar(self):
        popover = Gtk.Popover.new(self.clock)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        content.set_border_width(16)
        content.add(Gtk.Label(label='Cairo · Africa/Cairo'))
        calendar = Gtk.Calendar()
        now = datetime.datetime.now(ZoneInfo('Africa/Cairo'))
        calendar.select_month(now.month - 1, now.year)
        calendar.select_day(now.day)
        content.add(calendar)
        popover.add(content)
        popover.show_all()
        popover.popup()

    def window_menu(self):
        menu = Gtk.Menu()
        for win in self.windows():
            item = Gtk.MenuItem(label=win.get_name())
            item.connect('activate', lambda _, w=win: self.activate(w))
            menu.append(item)
        menu.show_all()
        menu.popup_at_pointer(None)

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
