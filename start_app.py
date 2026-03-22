from __future__ import annotations

import argparse
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / 'backend'
FRONTEND_DIR = ROOT / 'frontend'
VENV_DIR = BACKEND_DIR / '.venv'
BACKEND_REQUIREMENTS = BACKEND_DIR / 'requirements.txt'
FRONTEND_DIST = FRONTEND_DIR / 'dist'
DEFAULT_URL = 'http://127.0.0.1:8000'


def is_windows() -> bool:
    return sys.platform.startswith('win')


def venv_python() -> Path:
    return VENV_DIR / ('Scripts/python.exe' if is_windows() else 'bin/python')


def npm_command() -> str:
    return 'npm.cmd' if is_windows() else 'npm'


def run_step(command: list[str], *, cwd: Path) -> None:
    print(f"\n[step] {' '.join(command)}")
    subprocess.run(command, cwd=cwd, check=True)


def ensure_backend_environment() -> None:
    if not venv_python().exists():
        run_step([sys.executable, '-m', 'venv', str(VENV_DIR)], cwd=ROOT)
    run_step([str(venv_python()), '-m', 'pip', 'install', '-r', str(BACKEND_REQUIREMENTS)], cwd=BACKEND_DIR)


def ensure_frontend_build() -> None:
    node_modules = FRONTEND_DIR / 'node_modules'
    if not node_modules.exists():
        run_step([npm_command(), 'install'], cwd=FRONTEND_DIR)
    run_step([npm_command(), 'run', 'build'], cwd=FRONTEND_DIR)


def wait_for_server(url: str, timeout_seconds: int = 30) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f'{url}/health', timeout=2) as response:
                return response.status == 200
        except (urllib.error.URLError, TimeoutError):
            time.sleep(1)
    return False


def start_backend(detach: bool) -> subprocess.Popen[str]:
    command = [
        str(venv_python()),
        '-m',
        'uvicorn',
        'app.main:app',
        '--host',
        '127.0.0.1',
        '--port',
        '8000',
    ]
    creationflags = subprocess.CREATE_NEW_CONSOLE if detach and is_windows() else 0
    print(f"\n[launch] {' '.join(command)}")
    return subprocess.Popen(command, cwd=BACKEND_DIR, creationflags=creationflags, text=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Prepare and launch the local Hunting with AI app.')
    parser.add_argument('--prepare-only', action='store_true', help='Install/build dependencies but do not start the server.')
    parser.add_argument('--no-browser', action='store_true', help='Do not open the browser after startup.')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print('Preparing local app…')
    ensure_backend_environment()
    ensure_frontend_build()

    if args.prepare_only:
        print('\nPreparation complete. You can now run start_app.bat on Windows.')
        return 0

    process = start_backend(detach=False)
    if wait_for_server(DEFAULT_URL):
        print(f'Local app is available at {DEFAULT_URL}')
        if not args.no_browser:
            webbrowser.open(DEFAULT_URL)
    else:
        print('The server did not become ready in time.', file=sys.stderr)
        process.terminate()
        return 1

    try:
        return process.wait()
    except KeyboardInterrupt:
        print('\nStopping local app…')
        process.terminate()
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
