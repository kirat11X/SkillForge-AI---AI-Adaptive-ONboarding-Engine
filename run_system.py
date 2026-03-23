#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
WEBSITE_DIR = PROJECT_ROOT / "Website"
FRONTEND_DIR = WEBSITE_DIR / "frontend"
BACKEND_APP_DIR = WEBSITE_DIR


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the SkillForge frontend and backend together."
    )
    parser.add_argument("--backend-host", default="127.0.0.1", help="Backend bind host.")
    parser.add_argument("--backend-port", default=8000, type=int, help="Backend port.")
    parser.add_argument("--frontend-host", default="127.0.0.1", help="Frontend bind host.")
    parser.add_argument("--frontend-port", default=5173, type=int, help="Frontend port.")
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="Run only the backend server.",
    )
    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="Run only the frontend dev server.",
    )
    return parser.parse_args()


def _require_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")


def _resolve_npm_command() -> str:
    npm_command = "npm.cmd" if os.name == "nt" else "npm"
    if shutil.which(npm_command) is None:
        raise RuntimeError(
            "npm is not available in PATH. Install Node.js dependencies before running the frontend."
        )
    return npm_command


def _require_python_module(module_name: str, install_hint: str) -> None:
    if importlib.util.find_spec(module_name) is None:
        raise RuntimeError(f"Missing Python dependency '{module_name}'. {install_hint}")


def _frontend_backend_target(host: str, port: int) -> str:
    proxy_host = host
    if host in {"0.0.0.0", "::"}:
        proxy_host = "127.0.0.1"
    return f"http://{proxy_host}:{port}"


def _display_host(host: str) -> str:
    if host in {"0.0.0.0", "::"}:
        return "127.0.0.1"
    return host


def _start_process(command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.Popen:
    if os.name == "nt":
        return subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    return subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        start_new_session=True,
    )


def _stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return

    try:
        if os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return

    try:
        process.wait(timeout=5)
        return
    except subprocess.TimeoutExpired:
        pass

    try:
        if os.name == "nt":
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return

    process.wait(timeout=5)


def main() -> int:
    args = _parse_args()
    try:
        if args.backend_only and args.frontend_only:
            print("Choose either --backend-only or --frontend-only, not both.", file=sys.stderr)
            return 2

        _require_exists(WEBSITE_DIR, "Website directory")
        if not args.frontend_only:
            _require_exists(BACKEND_APP_DIR / "backend" / "main.py", "Backend entrypoint")
            _require_python_module(
                "uvicorn",
                "Install backend requirements with: pip install -r Website/backend/requirements.txt",
            )
        if not args.backend_only:
            _require_exists(FRONTEND_DIR, "Frontend directory")
            _require_exists(FRONTEND_DIR / "package.json", "Frontend package.json")

        processes: list[subprocess.Popen] = []

        if not args.frontend_only:
            backend_env = os.environ.copy()
            backend_command = [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.main:app",
                "--app-dir",
                str(BACKEND_APP_DIR),
                "--host",
                args.backend_host,
                "--port",
                str(args.backend_port),
                "--reload",
            ]
            processes.append(_start_process(backend_command, PROJECT_ROOT, backend_env))
            print(
                f"Backend running on http://{_display_host(args.backend_host)}:{args.backend_port}"
            )

        if not args.backend_only:
            frontend_env = os.environ.copy()
            frontend_env["VITE_BACKEND_URL"] = _frontend_backend_target(
                args.backend_host, args.backend_port
            )
            npm_command = _resolve_npm_command()
            frontend_command = [
                npm_command,
                "run",
                "dev",
                "--",
                "--host",
                args.frontend_host,
                "--port",
                str(args.frontend_port),
            ]
            processes.append(_start_process(frontend_command, FRONTEND_DIR, frontend_env))
            print(
                f"Frontend running on http://{_display_host(args.frontend_host)}:{args.frontend_port}"
            )

        print("Press Ctrl+C to stop the whole system.")

        while processes:
            for process in processes:
                exit_code = process.poll()
                if exit_code is not None:
                    print(
                        f"One process exited with code {exit_code}. Stopping the remaining services.",
                        file=sys.stderr,
                    )
                    return exit_code
            time.sleep(1)

        return 0
    except KeyboardInterrupt:
        print("\nStopping SkillForge...")
        return 0
    except (FileNotFoundError, RuntimeError) as exc:
        print(exc, file=sys.stderr)
        return 1
    finally:
        for process in reversed(locals().get("processes", [])):
            _stop_process(process)


if __name__ == "__main__":
    raise SystemExit(main())
