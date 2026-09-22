"""Startup tests are independent of workbook-processing tests."""
from io import StringIO
from pathlib import Path
import queue
import re
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
from unittest.mock import Mock, patch

import launcher


class SetupTests(unittest.TestCase):
    def test_setup_installs_once_and_reinstalls_after_requirement_change(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'requirements.txt').write_text('Flask>=3.1\n')
            env = root / 'environment'
            python = env / ('Scripts/python.exe' if launcher.os.name == 'nt' else 'bin/python')
            python.parent.mkdir(parents=True)
            python.touch()
            with patch.object(launcher, 'ROOT', root), patch.object(launcher, 'ENV', env), \
                    patch.object(launcher.subprocess, 'run', return_value=Mock(returncode=0)) as run:
                launcher.prepare_environment()
                self.assertEqual(run.call_count, 2)  # Import check plus initial install.
                run.reset_mock()
                launcher.prepare_environment()
                self.assertEqual(run.call_count, 1)  # Offline reuse, import check only.
                (root / 'requirements.txt').write_text('Flask>=3.1\nwaitress\n')
                run.reset_mock()
                launcher.prepare_environment()
                self.assertEqual(run.call_count, 2)

    def test_failed_install_does_not_record_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'requirements.txt').write_text('Flask\n')
            env = root / 'environment'
            python = env / ('Scripts/python.exe' if launcher.os.name == 'nt' else 'bin/python')
            python.parent.mkdir(parents=True)
            python.touch()
            with patch.object(launcher, 'ROOT', root), patch.object(launcher, 'ENV', env), \
                    patch.object(launcher.subprocess, 'run', side_effect=[Mock(returncode=1), subprocess.CalledProcessError(1, 'pip')]):
                with self.assertRaises(subprocess.CalledProcessError):
                    launcher.prepare_environment()
                self.assertFalse((env / 'requirements.sha256').exists())

    def test_stopped_launch_does_not_open_browser(self):
        stopped = threading.Event()
        stopped.set()
        opener = Mock()
        launcher.open_when_ready('http://127.0.0.1:1/', stopped, opener)
        opener.assert_not_called()

    def test_real_server_start_readiness_and_browser_fallback(self):
        process = subprocess.Popen([sys.executable, str(launcher.ROOT / 'launcher.py'), '--serve', '--no-browser'],
                                   cwd=tempfile.gettempdir(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True)
        lines = queue.Queue()
        def collect():
            for line in process.stdout:
                lines.put(line)
        reader = threading.Thread(target=collect, daemon=True)
        reader.start()
        try:
            line = lines.get(timeout=15)
            self.assertIn('http://127.0.0.1:', line)
            url = line.split(' at ', 1)[1].strip()
            opener = Mock(return_value=False)
            with patch('sys.stdout', new_callable=StringIO) as output:
                launcher.open_when_ready(url, threading.Event(), opener)
                self.assertIn(url, output.getvalue())
            opener.assert_called_once_with(url)
            client = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with client.open(url, timeout=5) as response:
                page = response.read().decode()
                self.assertIn('Excel Consolidator', page)
            token = re.search(r'name="local-stop-token" content="([^"]+)"', page).group(1)
            request = urllib.request.Request(url + 'stop', data=b'', method='POST',
                headers={'Origin': url.rstrip('/'), 'X-Stop-Token': token})
            with client.open(request, timeout=5) as response:
                self.assertIn(b'shutting down', response.read())
            self.assertEqual(process.wait(timeout=10), 0)
            with self.assertRaises(OSError):
                client.open(url, timeout=1)
        finally:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=10)
            reader.join(timeout=5)
            process.stdout.close()


if __name__ == '__main__':
    unittest.main()
