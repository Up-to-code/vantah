"""Integration checks use a disposable folder and Gio's real Trash service."""
import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,Gio,GLib
from desktop_apps import FilesWindow,SettingsWindow
class FakeShell:
    preferences={'dark':True,'reduced_motion':False,'language':'en','glass_tint':.28}
    def style_appearance(self,win):pass
    def full_glass_region(self,*args):pass
    def glass_region(self,*args):pass
    def rounded_region(self,*args):return None
    def change_mode(self,*args):pass
    def change_language(self,*args):pass
    def change_glass(self,*args):pass
class Tests(unittest.TestCase):
    def test_files_navigation_filter_trash_restore(self):
        with tempfile.TemporaryDirectory(prefix='vantah-files-check-') as folder:
            file=Path(folder)/('مرحبا-'+Path(folder).name+'.txt');file.write_text('vAntah integration test')
            window=FilesWindow(FakeShell());window.build()
            window.navigate(Gio.File.new_for_path(folder))
            self.assertEqual(len(window.model),1)
            window.search(file.name);self.assertEqual(len(window.model),1)
            window.tree.get_selection().select_path(Gtk.TreePath.new_from_indices([0]))
            window.trash_selected();self.assertFalse(file.exists())
            window.navigate(Gio.File.new_for_uri('trash:///'));window.search(file.name)
            # GVfs discovers newly trashed files asynchronously, especially cold.
            loop=GLib.MainLoop(); attempts=[0]
            def refreshed():
                window.load(); attempts[0]+=1
                if len(window.model)==1 or attempts[0]>=30:
                    loop.quit(); return False
                return True
            GLib.timeout_add(100,refreshed);loop.run()
            self.assertEqual(len(window.model),1)
            window.tree.get_selection().select_path(Gtk.TreePath.new_from_indices([0]))
            window.restore_selected();self.assertTrue(file.exists())
            self.assertEqual(file.read_text(),'vAntah integration test');window.destroy()
    def test_arabic_layout_and_settings_sections(self):
        shell=FakeShell();shell.preferences=dict(shell.preferences,language='ar')
        window=SettingsWindow(shell)
        for section in ('Appearance','Language','About'):
            window.section=section;window.refresh_language()
            self.assertEqual(window.get_direction(),Gtk.TextDirection.RTL)
            self.assertEqual(window.get_title(),'الإعدادات')
        window.destroy()
if __name__=='__main__':unittest.main()
