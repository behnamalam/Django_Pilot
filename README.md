# Error Lover · Django Pilot (PyQt6 Edition)

A branded desktop command center for local Django projects, powered by **PyQt6**.
The interface carries the Error Lover identity with the Django Pilot aviation emblem.
The process controller remains independent from the UI.

## Features

- Error Lover / Django Pilot logo in the application header and window icon
- Native Qt icons on the toolbox actions (no extra icon package required)
- Persistent **Dark mode / Light mode** switch (theme selection is remembered)
- Independently scrollable toolbox sidebar (mouse wheel, touchpad and scrollbar)
- Load a Django project by selecting the folder containing `manage.py`
- Launch and stop the Django development server
- Run `makemigrations`, `migrate` and `collectstatic`
- Create Django apps and create a superuser
- Open an interactive Django shell
- Create a `.venv` or choose an existing virtual environment
- Use the selected venv interpreter for Django management commands
- Add the selected venv's `bin` / `Scripts` folder to terminal `PATH`, so `python` and `pip` resolve to the active environment
- Live process output and separate **Run command** / **Send input** actions
- Open the project folder from the app

## Requirements

- Python 3.10 or newer
- PyQt6

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run:

```bash
python main.py
```

On Windows, `run_windows.bat` is provided. On Linux/macOS-compatible shells, use `./run_linux.sh`.

## Themes

Use the top-right theme control to switch between Dark and Light mode. The selection is stored in the operating system's application settings and restored on the next launch.

## Terminal behavior

- **Run command** starts a new shell command in the selected project directory.
- **Send input** forwards text to the active interactive process, such as the Django development server or `manage.py shell`.
- When a virtual environment is selected, its executable directory is prepended to the child process `PATH`, allowing `python` and `pip` in terminal commands to use it.

## Project structure

```text
Django_Pilot/
├── assets/
│   └── error_lover_django_pilot.png
├── main.py
├── ui.py
├── commands.py
├── requirements.txt
├── run_windows.bat
├── run_linux.sh
├── README.md
└── test.py
```
