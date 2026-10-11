"""Exercise the release installer without network access or real Docker writes."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        fixtures = self.base / 'fixtures'
        fixtures.mkdir()
        source = self.base / 'source' / 'vantah-v0.1.0'
        (source / 'sandbox').mkdir(parents=True)
        (source / 'sandbox/run.sh').write_text((ROOT / 'sandbox/run.sh').read_text())
        archive = fixtures / 'vantah-v0.1.0.tar.gz'
        with tarfile.open(archive, 'w:gz') as handle:
            handle.add(source, arcname=source.name)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        (fixtures / 'SHA256SUMS').write_text(f'{digest}  {archive.name}\n')
        scripts = self.base / 'bin'
        scripts.mkdir()
        self.write_command(scripts / 'docker', '''
import json, os, sys
a = sys.argv[1:]
with open(os.environ['CALLS'], 'a') as f: f.write(json.dumps(a)+'\\n')
if a[:2] == ['container','inspect']: sys.exit(0 if os.environ['STATE'] != 'missing' else 1)
if a[0] == 'inspect': print('v0.1.0' if os.environ['STATE'] == 'owned' else 'other')
if a[0] == 'port': print('127.0.0.1:6099')
''')
        self.write_command(scripts / 'curl', '''
import os, pathlib, shutil, sys
a=sys.argv[1:]; url=next(x for x in a if x.startswith('https://'))
name=url.rsplit('/',1)[1]; dest=pathlib.Path(a[a.index('-o')+1])
shutil.copyfile(pathlib.Path(os.environ['FIXTURES'])/name,dest)
if os.environ.get('CORRUPT') and name.endswith('.tar.gz'): dest.write_bytes(b'corrupt')
''')
        self.env = dict(os.environ, PATH=str(scripts)+os.pathsep+os.environ['PATH'],
                        FIXTURES=str(fixtures), CALLS=str(self.base/'calls'),
                        STATE='missing', VANTAH_INSTALL_DIR=str(self.base/'install'))

    def write_command(self, path, body):
        path.write_text(f'#!{sys.executable}\n'+body)
        path.chmod(0o755)

    def run_installer(self, **overrides):
        return subprocess.run(['sh', str(ROOT/'try.sh')], env=dict(self.env, **overrides),
                              capture_output=True, text=True)

    def test_fresh_verified_download_builds_and_runs(self):
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.base/'install/sandbox/run.sh').exists())
        self.assertIn('org.qentrah.vantah=v0.1.0', (self.base/'calls').read_text())
        self.assertIn('127.0.0.1:6081', result.stdout)

    def test_corrupt_archive_is_rejected_before_build(self):
        result = self.run_installer(CORRUPT='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('checksum mismatch', result.stderr)
        self.assertNotIn('build', (self.base/'calls').read_text())

    def test_existing_owned_container_restarts_at_actual_port(self):
        result = self.run_installer(STATE='owned')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('127.0.0.1:6099', result.stdout)
        self.assertNotIn('build', (self.base/'calls').read_text())

    def test_unrelated_container_is_preserved(self):
        result = self.run_installer(STATE='unrelated')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('already exists', result.stderr)
        self.assertNotIn('start', (self.base/'calls').read_text())

    def test_invalid_port_stops_before_download(self):
        result = self.run_installer(VANTAH_PORT='70000')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.base/'install').exists())


if __name__ == '__main__':
    unittest.main()
