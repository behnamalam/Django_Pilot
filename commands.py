"""Process controller for Django Pilot.

This module is deliberately UI-agnostic: it can be used by the PyQt interface
or another frontend without changing Django command behavior.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable, Iterable


def find_project_root(start: str | Path | None = None) -> Path | None:
    start_path = Path(start or Path.cwd()).expanduser().resolve()
    for candidate in (start_path, *start_path.parents):
        if (candidate / "manage.py").is_file():
            return candidate
    return None


def venv_python(venv_path: str | Path) -> Path:
    venv = Path(venv_path).expanduser()
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


class DjangoCommands:
    """Run Django and shell processes without blocking the GUI thread."""

    def __init__(
        self,
        project_root: str | Path,
        output_callback: Callable[[str, str | None], None],
        status_callback: Callable[[str], None],
    ) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.output = output_callback
        self.status = status_callback
        self.python = sys.executable
        self.server_process: subprocess.Popen | None = None
        self.active_process: subprocess.Popen | None = None
        self._process_lock = threading.RLock()
        self._server_lock = threading.RLock()

    def set_python(self, interpreter: str | Path) -> None:
        self.python = str(Path(interpreter).expanduser().resolve())
        self.output(f"Python interpreter set: {self.python}", "success")

    def _process_environment(self) -> dict[str, str]:
        env = os.environ.copy()
        interpreter = Path(self.python)
        executable_dir = interpreter.parent
        if executable_dir.is_dir():
            env["PATH"] = str(executable_dir) + os.pathsep + env.get("PATH", "")
            # A selected venv normally has .../.venv/bin/python or Scripts/python.exe.
            if executable_dir.name.lower() in {"bin", "scripts"}:
                env["VIRTUAL_ENV"] = str(executable_dir.parent)
        return env

    def _spawn_reader(
        self,
        args: Iterable[str | Path],
        label: str,
        *,
        interactive: bool = False,
        on_started: Callable[[subprocess.Popen], None] | None = None,
        on_finished: Callable[[int], None] | None = None,
    ) -> None:
        command = [str(part) for part in args]

        def worker() -> None:
            process: subprocess.Popen | None = None
            self.status(f"Running · {label}")
            try:
                process = subprocess.Popen(
                    command,
                    cwd=str(self.project_root),
                    env=self._process_environment(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                )
                if interactive:
                    with self._process_lock:
                        self.active_process = process
                if on_started:
                    on_started(process)

                assert process.stdout is not None
                for line in iter(process.stdout.readline, ""):
                    self.output(line.rstrip("\r\n"), None)
                return_code = process.wait()
                self.status(f"Finished · exit code {return_code}")
                if on_finished:
                    on_finished(return_code)
            except Exception as exc:  # surfaced in the live console
                self.output(f"ERROR: {exc}", "error")
                self.status("Command failed")
            finally:
                if interactive and process is not None:
                    with self._process_lock:
                        if self.active_process is process:
                            self.active_process = None

        threading.Thread(target=worker, name="DjangoPilotProcess", daemon=True).start()

    def run_terminal_command(self, command: str) -> None:
        command = command.strip()
        if not command:
            return
        if os.name == "nt":
            args = ["cmd.exe", "/d", "/s", "/c", command]
        else:
            args = ["/bin/bash", "-c", command]
        self._spawn_reader(args, f"Terminal: {command}")

    def manage(self, *args: str, label: str | None = None) -> None:
        self._spawn_reader(
            [self.python, "manage.py", *args],
            label or " ".join(args),
        )

    def runserver(self, port: str = "8000") -> None:
        with self._server_lock:
            if self.server_process and self.server_process.poll() is None:
                self.output("Server is already running.", "warning")
                return

        def remember(process: subprocess.Popen) -> None:
            with self._server_lock:
                self.server_process = process
            with self._process_lock:
                self.active_process = process

        def finished(_code: int) -> None:
            with self._server_lock:
                old_process = self.server_process
                self.server_process = None
            with self._process_lock:
                if self.active_process is old_process:
                    self.active_process = None
            self.status("Server stopped")

        self._spawn_reader(
            [self.python, "manage.py", "runserver", f"127.0.0.1:{port}"],
            f"Django server · 127.0.0.1:{port}",
            interactive=True,
            on_started=remember,
            on_finished=finished,
        )

    def stop_server(self) -> None:
        with self._server_lock:
            process = self.server_process
        if process and process.poll() is None:
            process.terminate()
            self.output("Stop signal sent to server.", "warning")
        else:
            self.output("No running server process found.", "warning")

    def send_input(self, text: str) -> bool:
        with self._process_lock:
            process = self.active_process
            if not process or process.poll() is not None or process.stdin is None:
                return False
            try:
                process.stdin.write(text + "\n")
                process.stdin.flush()
                return True
            except (BrokenPipeError, OSError, ValueError) as exc:
                self.output(f"Input error: {exc}", "error")
                return False

    def create_venv(
        self,
        path: str | Path,
        callback: Callable[[str], None] | None = None,
    ) -> None:
        target = Path(path).expanduser().resolve()

        def worker() -> None:
            self.status("Creating virtual environment…")
            try:
                process = subprocess.Popen(
                    [sys.executable, "-m", "venv", str(target)],
                    cwd=str(self.project_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                assert process.stdout is not None
                for line in iter(process.stdout.readline, ""):
                    self.output(line.rstrip("\r\n"), None)
                code = process.wait()
                if code == 0:
                    interpreter = venv_python(target)
                    self.output(f"Virtual environment created: {target}", "success")
                    if callback:
                        callback(str(interpreter))
                    self.status("Virtual environment ready")
                else:
                    self.status(f"Venv creation failed · exit code {code}")
            except Exception as exc:
                self.output(f"VENV ERROR: {exc}", "error")
                self.status("Venv creation failed")

        threading.Thread(target=worker, name="DjangoPilotVenv", daemon=True).start()

    def create_app(self, app_name: str) -> None:
        self.manage("startapp", app_name, label=f"Create app: {app_name}")

    def make_migrations(self, app_name: str = "") -> None:
        args = ["makemigrations"]
        if app_name.strip():
            args.append(app_name.strip())
        self.manage(*args, label="Make migrations")

    def migrate(self) -> None:
        self.manage("migrate", label="Apply migrations")

    def collectstatic(self) -> None:
        self.manage("collectstatic", "--noinput", label="Collect static")

    def shell(self) -> None:
        self._spawn_reader(
            [self.python, "manage.py", "shell"],
            "Django shell",
            interactive=True,
        )
