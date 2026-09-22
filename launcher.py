"""Local startup only: environment setup, server lifecycle and browser opening.

No frontend rendering or workbook processing belongs in this module.
"""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent
ENV = ROOT / '.launcher-venv'


def prepare_environment():
    """Use a dedicated environment, leaving developer environments untouched."""
    python = ENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.exists():
        print('First-time setup: creating a private Python environment...', flush=True)
        subprocess.run([sys.executable, '-m', 'venv', str(ENV)], check=True)
    requirements = ROOT / 'requirements.txt'
    fingerprint = hashlib.sha256(requirements.read_bytes()).hexdigest()
    stamp = ENV / 'requirements.sha256'
    healthy = subprocess.run([str(python), '-c', 'import flask, openpyxl, waitress'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if not healthy or not stamp.exists() or stamp.read_text() != fingerprint:
        print('Installing required libraries. This step needs internet access and may take a few minutes.', flush=True)
        subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(requirements)], check=True)
        stamp.write_text(fingerprint)
    return python


def open_when_ready(url, stop, opener=webbrowser.open):
    """Open only after our bound server answers; avoid proxying localhost."""
    client = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    deadline = time.monotonic() + 30
    while not stop.is_set() and time.monotonic() < deadline:
        try:
            with client.open(url, timeout=1) as response:
                ready = response.status == 200
            if ready:
                if not stop.is_set():
                    try:
                        if not opener(url):
                            print(f'Please open this address in your browser: {url}', flush=True)
                    except Exception:
                        print(f'Please open this address in your browser: {url}', flush=True)
                return
        except OSError:
            pass
        stop.wait(0.2)
    if not stop.is_set():
        print(f'The browser could not open automatically. Try {url}', flush=True)


def serve(open_browser=True):
    # Import the web adapter only after dependency setup is complete.
    from waitress import create_server
    from app import app

    server = create_server(app, host='127.0.0.1', port=0)
    url = f'http://127.0.0.1:{server.effective_port}/'
    stop = threading.Event()
    print(f'Excel Consolidator is available at {url}', flush=True)
    print('Keep this window open while using the app.', flush=True)
    print('Close this window or press Ctrl+C to stop Excel Consolidator.', flush=True)
    if open_browser:
        threading.Thread(target=open_when_ready, args=(url, stop), daemon=True).start()
    try:
        server.run()
    finally:
        stop.set()
        server.close()


def main():
    parser = argparse.ArgumentParser(description='Start Excel Consolidator and open its web page.')
    parser.add_argument('--serve', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--no-browser', action='store_true', help='Start without opening a browser.')
    args = parser.parse_args()
    try:
        if args.serve:
            serve(not args.no_browser)
        else:
            if sys.version_info < (3, 12):
                raise RuntimeError('Install Python 3.12 or newer and try again.')
            python = prepare_environment()
            command = [str(python), str(Path(__file__).resolve()), '--serve']
            if args.no_browser:
                command.append('--no-browser')
            child = subprocess.Popen(command, cwd=ROOT)
            try:
                return child.wait()
            finally:
                if child.poll() is None:
                    child.terminate()
                    child.wait()
        return 0
    except KeyboardInterrupt:
        print('\nExcel Consolidator stopped.', flush=True)
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f'\nCould not start Excel Consolidator: {exc}', file=sys.stderr)
        print('Check your internet connection during setup and that this folder is writable.\n'
              'If setup was interrupted, run the launcher again.\n'
              'If the private environment is damaged, rename .launcher-venv and retry.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
