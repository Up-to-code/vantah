"""Native Settings and Files. Files operates on real Gio files, including Trash."""
from pathlib import Path
import shutil
import math
import cairo
from gi.repository import Gtk, Gio, GLib, Gdk

AR = {'Resize window':'تغيير حجم النافذة','Close':'إغلاق','Minimize':'تصغير','Maximize':'تكبير','Applications':'التطبيقات','Terminal':'الطرفية','Text Editor':'محرر النصوص','Search applications':'البحث عن التطبيقات','All':'الكل','Accessories':'الملحقات','Development':'التطوير','No matching applications':'لا توجد تطبيقات مطابقة','applications  ·  Enter to open  ·  Esc to close':'تطبيقات · Enter للفتح · Esc للإغلاق','About vAntah':'حول vAntah','Home folder':'المجلد الرئيسي','System settings':'إعدادات النظام','Change wallpaper':'تغيير الخلفية','Dark appearance':'المظهر الداكن','Reduce motion':'تقليل الحركة','Settings':'الإعدادات','Files':'الملفات','Appearance':'المظهر','Language':'اللغة','About':'حول النظام',
      'Dark Mode':'الوضع الداكن','Reduce Motion':'تقليل الحركة','Liquid Glass':'الزجاج السائل',
      'English / Arabic':'الإنجليزية / العربية','Home':'المنزل','Desktop':'سطح المكتب',
      'Documents':'المستندات','Downloads':'التنزيلات','Trash':'سلة المهملات','Favorites':'المفضلة',
      'Search files':'البحث عن الملفات','New Folder':'مجلد جديد','Move to Trash':'نقل إلى سلة المهملات',
      'Restore':'استعادة','Name':'الاسم','Size':'الحجم','Back':'رجوع','Open':'فتح',
      'Storage':'التخزين','System':'النظام','Clear':'شفاف','Tinted':'ملون','items':'عناصر',
      'Trash is empty':'سلة المهملات فارغة','Choose a file':'اختر ملفًا','Folder name':'اسم المجلد',
      'Create':'إنشاء','Cancel':'إلغاء','Error':'خطأ','Interface language':'لغة الواجهة',
      'Arabic mirrors these native views. Other apps retain their own language settings.':'تعكس العربية اتجاه هذه الواجهات الأصلية. تحتفظ التطبيقات الأخرى بإعدادات لغتها.',
      'Real-time KWin blur and refraction':'تمويه وانكسار فوري عبر KWin',
      'Native Linux desktop':'سطح مكتب لينكس أصلي','Available':'متاح'}

def tr(shell, text):
    return AR.get(text, text) if shell.preferences.get('language') == 'ar' else text

def styled(widget, name):
    widget.get_style_context().add_class(name)
    return widget

class DesktopWindow(Gtk.Window):
    def __init__(self, shell, title, wmclass):
        super().__init__(title=tr(shell, title))
        self.shell, self.name = shell, title
        self.set_wmclass(wmclass, wmclass)
        self.set_decorated(False)
        self.set_default_size(830, 570)
        self.set_position(Gtk.WindowPosition.CENTER)
        visual = self.get_screen().get_rgba_visual()
        if visual: self.set_visual(visual)
        self.set_app_paintable(True)
        self.connect('draw', self.paint_client)
        styled(self, 'desktop-app')
        shell.style_appearance(self)
        self.connect('size-allocate', self.request_glass)
        self.connect('delete-event', self.hide_window)
        self.root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        overlay=Gtk.Overlay(); overlay.add(self.root)
        grip=Gtk.EventBox(); grip.set_visible_window(False); grip.set_size_request(16,16)
        grip.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        grip.set_halign(Gtk.Align.END); grip.set_valign(Gtk.Align.END)
        grip.set_tooltip_text(tr(shell,'Resize window'))
        grip.connect('button-press-event',lambda _,event:self.resize_drag(event))
        overlay.add_overlay(grip); self.add(overlay)
        self.connect('key-press-event', self.key)
    def resize_drag(self,event):
        if event.button == 1:
            self.begin_resize_drag(Gdk.WindowEdge.SOUTH_EAST,1,int(event.x_root),int(event.y_root),event.time)
            return True
        return False
    def request_glass(self,widget,allocation):
        radius=0 if self.is_maximized() else 16
        self.shell.glass_region(self,self.shell.rounded_region(0,0,allocation.width,allocation.height,radius))
    def paint_client(self, _, cr):
        # GTK children must also be clipped: transparent window CSS alone does
        # not round an opaque content pane. The full native surface is clipped.
        allocation = self.get_allocation()
        w, h = allocation.width, allocation.height
        radius = 0 if self.is_maximized() else 16
        cr.save()
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0); cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.move_to(radius, 0); cr.line_to(w-radius, 0)
        if radius:
            cr.arc(w-radius, radius, radius, -math.pi/2, 0)
            cr.line_to(w, h-radius); cr.arc(w-radius, h-radius, radius, 0, math.pi/2)
            cr.line_to(radius, h); cr.arc(radius, h-radius, radius, math.pi/2, math.pi)
            cr.line_to(0, radius); cr.arc(radius, radius, radius, math.pi, 3*math.pi/2)
        else: cr.line_to(w, 0); cr.line_to(w, h); cr.line_to(0, h); cr.line_to(0, 0)
        cr.close_path(); cr.clip()
        Gtk.Window.do_draw(self, cr)
        cr.restore()
        return True

    def build_header(self):
        area = Gtk.EventBox(); area.set_visible_window(True); area.set_size_request(-1,32)
        area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        area.connect('button-press-event', self.move_header)
        overlay = styled(Gtk.Overlay(), 'native-titlebar')
        title = Gtk.Label(label=tr(self.shell,self.name)); title.centered=True
        base=styled(Gtk.Box(), 'native-titlebar'); base.pack_start(title,True,True,0)
        overlay.add(base)
        controls=Gtk.Box(spacing=2); controls.set_halign(Gtk.Align.START)
        controls.set_valign(Gtk.Align.CENTER); controls.set_margin_start(12)
        for color, text, action in [('close','Close',self.hide),('minimize','Minimize',self.iconify),('maximize','Maximize',self.toggle_maximize)]:
            obj=styled(Gtk.Button(), 'traffic-'+color)
            obj.set_tooltip_text(tr(self.shell,text)); obj.get_accessible().set_name(tr(self.shell,text))
            obj.add(styled(Gtk.Box(), 'traffic-light'))
            obj.connect('clicked',lambda _, callback=action:callback())
            controls.pack_start(obj,False,False,0)
        overlay.add_overlay(controls); area.add(overlay)
        self.root.pack_start(area,False,False,0)
    def toggle_maximize(self):
        self.unmaximize() if self.is_maximized() else self.maximize()
    def move_header(self,area,event):
        if event.button != 1 or event.window != area.get_window(): return False
        if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS: self.toggle_maximize()
        else: self.begin_move_drag(1,int(event.x_root),int(event.y_root),event.time)
        return True

    def hide_window(self, *_):
        self.hide()
        return True
    def key(self, _, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide(); return True
        return False
    def refresh_language(self):
        self.set_title(tr(self.shell, self.name))
        self.set_direction(Gtk.TextDirection.RTL if self.shell.preferences.get('language') == 'ar' else Gtk.TextDirection.LTR)
        for child in self.root.get_children(): child.destroy()
        self.build_header()
        self.build()
        rtl = self.shell.preferences.get('language') == 'ar'
        def direction(widget):
            widget.set_direction(Gtk.TextDirection.RTL if rtl else Gtk.TextDirection.LTR)
            if isinstance(widget, Gtk.Label): widget.set_xalign(.5 if getattr(widget, 'centered', False) else 0)
            if isinstance(widget, Gtk.Container):
                for child in widget.get_children(): direction(child)
        direction(self.root)
        if hasattr(self, 'path_label'): self.path_label.set_direction(Gtk.TextDirection.LTR)
        self.show_all()
    def show_view(self):
        self.refresh_language()
        self.present()
    def label(self, text, heading=False):
        label = Gtk.Label(label=tr(self.shell, text), xalign=0)
        if heading: styled(label, 'app-heading')
        label.set_line_wrap(True)
        return label
    def action(self, text, callback):
        obj = Gtk.Button(label=tr(self.shell, text))
        obj.connect('clicked', lambda _: callback())
        return obj
    def error(self, error):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.CLOSE, text=tr(self.shell, 'Error'))
        dialog.format_secondary_text(str(error)); dialog.run(); dialog.destroy()

class SettingsWindow(DesktopWindow):
    def __init__(self, shell):
        super().__init__(shell, 'Settings', 'vantah-settings')
        self.section = 'Appearance'
    def build(self):
        split = Gtk.Box(spacing=0)
        self.root.pack_start(split, True, True, 0)
        sidebar = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6), 'app-sidebar')
        sidebar.set_size_request(210, -1)
        sidebar.pack_start(self.label('Settings', True), False, False, 12)
        for title, icon in [('Appearance','preferences-desktop-theme'),('Language','preferences-desktop-locale'),('About','help-about')]:
            row = self.action(title, lambda t=title: self.select(t))
            row.set_image(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON))
            row.set_always_show_image(True)
            styled(row, 'sidebar-row')
            if title == self.section: styled(row, 'selected')
            sidebar.pack_start(row, False, False, 0)
        split.pack_start(sidebar, False, False, 0)
        self.content = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18), 'app-content')
        split.pack_start(self.content, True, True, 0)
        self.content.pack_start(self.label(self.section, True), False, True, 0)
        self.render_section()
    def select(self, section):
        self.section = section; self.refresh_language()
    def row(self, title, control):
        row = styled(Gtk.Box(spacing=20), 'settings-row')
        row.pack_start(self.label(title), True, True, 0)
        row.pack_end(control, False, False, 0)
        self.card.pack_start(row, False, False, 0)
    def render_section(self):
        self.card = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1), 'settings-card')
        self.content.pack_start(self.card, False, False, 0)
        if self.section == 'Appearance':
            for title, key in [('Dark Mode','dark'),('Reduce Motion','reduced_motion')]:
                switch = Gtk.Switch(active=self.shell.preferences[key])
                switch.set_valign(Gtk.Align.CENTER)
                switch.get_accessible().set_name(tr(self.shell,title))
                switch.connect('notify::active', lambda obj, _, k=key: self.shell.change_mode(k,obj.get_active()))
                self.row(title,switch)
            slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.1, 0.65, .05)
            slider.set_size_request(180, -1); slider.set_draw_value(False)
            slider.set_value(self.shell.preferences.get('glass_tint', .28))
            slider.get_accessible().set_name(tr(self.shell,'Liquid Glass'))
            slider.connect('value-changed', lambda obj: self.shell.change_glass(obj.get_value()))
            self.row('Liquid Glass',slider)
            self.content.pack_start(self.label('Real-time KWin blur and refraction'),False,False,0)
            self.content.pack_start(self.label(tr(self.shell,'Clear') + '  ← →  ' + tr(self.shell,'Tinted')),False,False,0)
        elif self.section == 'Language':
            combo = Gtk.ComboBoxText()
            combo.append('en','English'); combo.append('ar','العربية')
            combo.set_active_id(self.shell.preferences.get('language','en'))
            combo.get_accessible().set_name(tr(self.shell,'Interface language'))
            combo.connect('changed',lambda obj: self.shell.change_language(obj.get_active_id()))
            self.row('Interface language',combo)
            self.content.pack_start(self.label('Arabic mirrors these native views. Other apps retain their own language settings.'),False,False,0)
        else:
            self.row('System',self.label('vAntah · Alpine Linux'))
            self.row('Liquid Glass',self.label('KWin / OpenGL'))
            total,used,free = shutil.disk_usage(Path.home())
            self.row('Storage',self.label(f'{used/2**30:.1f} / {total/2**30:.1f} GiB'))
            self.row('Available',self.label(f'{free/2**30:.1f} GiB'))
            self.content.pack_start(self.label('Native Linux desktop'),False,False,0)

class FilesWindow(DesktopWindow):
    def __init__(self, shell):
        super().__init__(shell, 'Files', 'vantah-files')
        for folder in ('Desktop', 'Documents', 'Downloads'):
            (Path.home() / folder).mkdir(exist_ok=True)
        self.location = Gio.File.new_for_path(str(Path.home()))
        self.history = []
        self.query = ''
        self.entries = []
        self.trash_refresh = GLib.timeout_add_seconds(1, self.refresh_trash)
        self.connect('destroy', lambda *_: GLib.source_remove(self.trash_refresh))
    def refresh_trash(self):
        if self.get_visible() and self.location.get_uri().startswith('trash:'):
            self.load()
        return True
    def build(self):
        toolbar = styled(Gtk.Box(spacing=8), 'files-toolbar')
        toolbar.pack_start(self.action('Back',self.back),False,False,0)
        self.path_label = Gtk.Label(xalign=0); self.path_label.set_ellipsize(3)
        toolbar.pack_start(self.path_label,True,True,0)
        search = Gtk.SearchEntry(); search.set_placeholder_text(tr(self.shell,'Search files'))
        search.set_text(self.query)
        search.connect('search-changed',lambda obj: self.search(obj.get_text()))
        toolbar.pack_end(search,False,False,0)
        self.root.pack_start(toolbar,False,False,0)
        split = Gtk.Box()
        self.root.pack_start(split,True,True,0)
        side = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5),'app-sidebar')
        side.set_size_request(180,-1)
        side.pack_start(self.label('Favorites'),False,False,8)
        for name, path in [('Home',Path.home()),('Desktop',Path.home()/'Desktop'),('Documents',Path.home()/'Documents'),('Downloads',Path.home()/'Downloads'),('Trash',None)]:
            obj = self.action(name,lambda p=path: self.navigate(Gio.File.new_for_path(str(p)) if p else Gio.File.new_for_uri('trash:///')))
            styled(obj,'sidebar-row'); side.pack_start(obj,False,False,0)
        split.pack_start(side,False,False,0)
        area = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10),'app-content')
        split.pack_start(area,True,True,0)
        self.model = Gtk.ListStore(Gio.Icon,str,str,object)
        self.tree = Gtk.TreeView(model=self.model)
        pix = Gtk.CellRendererPixbuf(); pix.set_property('stock-size',Gtk.IconSize.DIALOG)
        col = Gtk.TreeViewColumn(tr(self.shell,'Name'))
        col.pack_start(pix,False); col.add_attribute(pix,'gicon',0)
        text = Gtk.CellRendererText(); text.set_property('xalign', 0); col.pack_start(text,True); col.add_attribute(text,'text',1)
        col.set_alignment(0)
        col.set_expand(True); self.tree.append_column(col)
        self.tree.append_column(Gtk.TreeViewColumn(tr(self.shell,'Size'),Gtk.CellRendererText(),text=2))
        self.tree.connect('row-activated',self.open_row)
        self.tree.get_selection().connect('changed',lambda *_: self.selection_changed())
        scroll = Gtk.ScrolledWindow(); scroll.add(self.tree); area.pack_start(scroll,True,True,0)
        actions = Gtk.Box(spacing=8)
        self.new_button=self.action('New Folder',self.new_folder)
        self.trash_button=self.action('Move to Trash',self.trash_selected)
        self.restore_button=self.action('Restore',self.restore_selected)
        for obj in (self.new_button,self.trash_button,self.restore_button): actions.pack_start(obj,False,False,0)
        area.pack_start(actions,False,False,0)
        self.status = self.label(''); area.pack_start(self.status,False,False,0)
        self.load()
    def navigate(self, location):
        self.history.append(self.location); self.location=location; self.query=''; self.refresh_language()
    def back(self):
        if self.history: self.location=self.history.pop(); self.query=''; self.refresh_language()
    def search(self,text):
        self.query=text; self.load()
    def load(self):
        selected, _ = self.selected()
        selected_name = selected.get_basename() if selected else None
        self.model.clear(); self.entries=[]
        trash=self.location.get_uri().startswith('trash:')
        self.path_label.set_text(tr(self.shell,'Trash') if trash else self.location.get_parse_name())
        self.path_label.set_direction(Gtk.TextDirection.LTR)
        self.new_button.set_sensitive(not trash); self.trash_button.set_sensitive(not trash)
        self.restore_button.set_sensitive(trash)
        self.selection_changed()
        try:
            enum=self.location.enumerate_children('standard::*,trash::orig-path',Gio.FileQueryInfoFlags.NONE,None)
            while True:
                info=enum.next_file(None)
                if info is None: break
                if not info.get_is_hidden() and self.query.casefold() in info.get_display_name().casefold():
                    self.entries.append(info)
            enum.close(None)
            self.entries.sort(key=lambda info:(info.get_file_type()!=Gio.FileType.DIRECTORY,info.get_display_name().casefold()))
            for info in self.entries:
                size='—' if info.get_file_type()==Gio.FileType.DIRECTORY else GLib.format_size(info.get_size())
                itr = self.model.append([info.get_icon(),info.get_display_name(),size,info])
                if info.get_name() == selected_name: self.tree.get_selection().select_iter(itr)
            self.status.set_text(tr(self.shell,'Trash is empty') if trash and not self.entries else f'{len(self.entries)} '+tr(self.shell,'items'))
        except GLib.Error as error:
            self.status.set_text(error.message)
    def selection_changed(self):
        if not hasattr(self, "trash_button"): return
        _, itr = self.tree.get_selection().get_selected()
        trash = self.location.get_uri().startswith("trash:")
        self.trash_button.set_sensitive(itr is not None and not trash)
        self.restore_button.set_sensitive(itr is not None and trash)

    def selected(self):
        model,itr=self.tree.get_selection().get_selected()
        if itr is None: return None,None
        info=model[itr][3]
        return self.location.get_child(info.get_name()),info
    def open_row(self, *_):
        file,info=self.selected()
        if file is None:return
        if info.get_file_type()==Gio.FileType.DIRECTORY: self.navigate(file)
        else:
            try: Gio.AppInfo.launch_default_for_uri(file.get_uri(),None)
            except GLib.Error as error:self.error(error)
    def new_folder(self):
        dialog=Gtk.Dialog(title=tr(self.shell,'New Folder'),transient_for=self,modal=True)
        dialog.add_button(tr(self.shell,'Cancel'),Gtk.ResponseType.CANCEL)
        dialog.add_button(tr(self.shell,'Create'),Gtk.ResponseType.OK)
        entry=Gtk.Entry(); entry.set_placeholder_text(tr(self.shell,'Folder name'))
        dialog.get_content_area().pack_start(entry,True,True,12); dialog.show_all()
        response=dialog.run(); name=entry.get_text().strip(); dialog.destroy()
        if response==Gtk.ResponseType.OK and name:
            try:
                if '/' in name or name in ('.','..'):raise ValueError('Use a single folder name.')
                self.location.get_child(name).make_directory(None); self.load()
            except (GLib.Error,ValueError) as error:self.error(error)
    def trash_selected(self):
        file,_=self.selected()
        if file:
            try:file.trash(None); self.load()
            except GLib.Error as error:self.error(error)
    def restore_selected(self):
        file,info=self.selected()
        if file and info:
            try:
                original=info.get_attribute_byte_string('trash::orig-path')
                if not original:raise ValueError('Original location is unavailable.')
                file.move(Gio.File.new_for_path(original),Gio.FileCopyFlags.NONE,None,None,None);self.load()
            except (GLib.Error,ValueError) as error:self.error(error)
