from __future__ import annotations

import os
import queue
import re
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon, QPixmap, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QVBoxLayout,
    QWidget,

)

from PyQt6.QtCore import QSettings

from commands import DjangoCommands, find_project_root, venv_python


# Error Lover / Django Pilot visual system.
THEMES = {
    "dark": {
        "bg": "#0A1020", "surface": "#111B2E", "surface2": "#16233A",
        "surface3": "#1C2C47", "border": "#293B59", "text": "#F0F5FF",
        "muted": "#A5B5CF", "faint": "#7587A5", "field": "#0B1629",
        "field_focus": "#12233C", "button": "#1A2B46", "button_hover": "#263D5D",
        "scroll": "#0B1527", "scroll_handle": "#3A5277", "terminal": "#070D18",
        "terminal_chrome": "#101B2D", "terminal_text": "#D2E1F5",
        "command": "#14223A", "command_border": "#2B4162",
        "accent": "#65DCD5", "blue": "#8AAEFF", "green": "#63E3A7",
        "red": "#FF829A", "amber": "#F7C775", "pill_bg": "#123034",
        "pill_border": "#24595A", "section_bg": "#1B3454", "section_text": "#7BD8E4",
        "section_row": "#14243B", "section_border": "#263D5B",
        "section_title": "#C0D1E8", "section_hint": "#8FA5C3",
        "project_icon_bg": "#1A3452", "dialog": "#111B2E",
    },
    "light": {
        "bg": "#F2F5FB", "surface": "#FFFFFF", "surface2": "#F7F9FD",
        "surface3": "#EDF2FA", "border": "#DCE4F0", "text": "#17243B",
        "muted": "#5D6D87", "faint": "#8492A8", "field": "#F7F9FD",
        "field_focus": "#FFFFFF", "button": "#EEF3FA", "button_hover": "#E1EAF6",
        "scroll": "#E8EDF5", "scroll_handle": "#B8C6DA", "terminal": "#101827",
        "terminal_chrome": "#19263A", "terminal_text": "#D2E1F5",
        "command": "#F8FAFE", "command_border": "#D8E1EF",
        "accent": "#087F87", "blue": "#3867C8", "green": "#14865E",
        "red": "#C83E61", "amber": "#94610B", "pill_bg": "#E5F5EF",
        "pill_border": "#B9E4D4", "section_bg": "#DCEAF9", "section_text": "#245B91",
        "section_row": "#EAF1FA", "section_border": "#D7E3F1",
        "section_title": "#29496F", "section_hint": "#607A99",
        "project_icon_bg": "#E5F3F4", "dialog": "#FFFFFF",
    },
}


def build_stylesheet(theme_name: str) -> str:
    p = THEMES[theme_name]
    return f"""
    * {{ font-family: 'Inter', 'Segoe UI', sans-serif; color: {p['text']}; }}
    QMainWindow, QWidget#Root {{ background: {p['bg']}; }}
    QFrame#Header {{ background: transparent; border: 0; }}
    QFrame#ProjectCard, QFrame#SideCard, QFrame#ConsoleCard {{
        background: {p['surface']}; border: 1px solid {p['border']}; border-radius: 18px;
    }}
    QFrame#Sidebar {{ background: {p['surface2']}; border: 1px solid {p['border']}; border-radius: 18px; }}
    QWidget#SidebarContent, QScrollArea#ToolboxScroll,
    QScrollArea#ToolboxScroll QWidget#qt_scrollarea_viewport {{
        background: {p['surface2']}; border: 0;
    }}
    QFrame#ToolSection {{
        background: {p['section_row']}; border: 1px solid {p['section_border']};
        border-radius: 9px;
    }}
    QFrame#ToolSection QLabel#SectionTitle {{ color: {p['section_title']}; }}
    QFrame#ToolSection QLabel#SectionBadge {{ color: {p['section_hint']}; }}
    QFrame#BrandMark {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #1B3658, stop:1 #102E3B); border: 1px solid #315878; border-radius: 17px; }}
    QLabel#BrandTitle {{ font-size: 22px; font-weight: 950; letter-spacing: 2px; color: {p['text']}; }}
    QLabel#ToolboxTitle {{ color: {p['text']}; font-size: 12px; font-weight: 900; letter-spacing: 1.2px; }}
    QLabel#BrandSubtitle {{ color: {p['accent']}; font-size: 9px; font-weight: 900; letter-spacing: 1.6px; }}
    QLabel#Eyebrow {{ color: {p['faint']}; font-size: 9px; font-weight: 800; letter-spacing: 1.2px; }}
    QLabel#SectionTitle {{ color: {p['muted']}; font-size: 10px; font-weight: 900; letter-spacing: 1.1px; }}
    QLabel#Muted {{ color: {p['muted']}; }}
    QLabel#Faint {{ color: {p['faint']}; }}
    QLabel#Accent {{ color: {p['accent']}; font-weight: 750; }}
    QLabel#StatusPill {{ background: {p['pill_bg']}; color: {p['green']}; border: 1px solid {p['pill_border']}; border-radius: 10px; padding: 8px 12px; font-size: 9px; font-weight: 900; letter-spacing: 1px; }}
    QLabel#SectionNumber {{ background: {p['section_bg']}; color: {p['section_text']}; border-radius: 7px; font-size: 9px; font-weight: 900; }}
    QLabel#SectionBadge, QLabel#ToolboxHint {{ color: {p['faint']}; font-size: 8px; font-weight: 800; letter-spacing: 1px; }}
    QLabel#ProjectIcon {{ background: {p['project_icon_bg']}; color: {p['accent']}; border-radius: 12px; font-size: 22px; font-weight: 900; }}
    QLabel#FieldLabel {{ color: {p['muted']}; font-size: 8px; font-weight: 900; letter-spacing: 1px; }}
    QLabel#ActivePython {{ color: {p['accent']}; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 9px; }}
    QLabel#PanelTitle {{ color: {p['text']}; font-size: 14px; font-weight: 900; letter-spacing: 1.1px; }}
    QLabel#TerminalName {{ color: #91A5C4; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 9px; }}
    QLabel#TerminalDot[tone="red"] {{ color: #FF718F; font-size: 10px; }}
    QLabel#TerminalDot[tone="amber"] {{ color: #FFC978; font-size: 10px; }}
    QLabel#TerminalDot[tone="green"] {{ color: #61E7AC; font-size: 10px; }}
    QLabel#LiveDot {{ color: {p['green']}; font-size: 10px; }}
    QLabel#BrandLogo, QLabel#BrandLogoFallback {{ background: transparent; }}
    QLabel#BrandLogoFallback {{ color: #B8FFF4; font-size: 27px; font-weight: 900; }}
    QLabel#CommandTitle {{ color: {p['muted']}; font-size: 9px; font-weight: 900; letter-spacing: 1.2px; }}
    QLabel#KeyboardHint {{ color: {p['faint']}; font-size: 8px; font-weight: 800; }}
    QLabel#Prompt {{ color: #64DCD4; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 16px; font-weight: 900; }}
    QLabel#CommandNote {{ color: {p['faint']}; font-size: 9px; }}
    QFrame#TerminalFrame {{ background: {p['terminal']}; border: 1px solid {p['border']}; border-radius: 13px; }}
    QWidget#TerminalChrome {{ background: {p['terminal_chrome']}; border-top-left-radius: 13px; border-top-right-radius: 13px; }}
    QFrame#CommandArea {{ background: {p['command']}; border: 1px solid {p['command_border']}; border-radius: 13px; }}
    QLineEdit {{ background: {p['field']}; border: 1px solid {p['border']}; border-radius: 10px; padding: 11px 13px; color: {p['text']}; selection-background-color: #31568C; font-size: 11px; }}
    QLineEdit:focus {{ border: 1px solid {p['blue']}; background: {p['field_focus']}; }}
    QLineEdit#PathInput {{ font-family: 'Cascadia Code', 'Consolas', monospace; }}
    QPushButton {{ background: {p['button']}; border: 1px solid {p['border']}; border-radius: 10px; padding: 10px 13px; color: {p['text']}; font-size: 10px; font-weight: 750; text-align: left; }}
    QPushButton:hover {{ background: {p['button_hover']}; border-color: {p['blue']}; }}
    QPushButton:pressed {{ background: {p['surface3']}; }}
    QPushButton:disabled {{ color: {p['faint']}; background: {p['surface2']}; border-color: {p['border']}; }}
    QPushButton[variant="primary"] {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #668FF0, stop:1 #58C6C6); color: #071526; border: 0; font-weight: 900; }}
    QPushButton[variant="primary"]:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #87A9FF, stop:1 #76E6DD); }}
    QPushButton[variant="danger"] {{ background: {'#321C2A' if theme_name == 'dark' else '#FFF0F3'}; border-color: {'#613044' if theme_name == 'dark' else '#F2CBD5'}; color: {p['red']}; }}
    QPushButton[variant="danger"]:hover {{ background: {'#472234' if theme_name == 'dark' else '#FFE3EA'}; }}
    QPushButton[variant="ghost"] {{ background: transparent; border-color: transparent; color: {p['muted']}; }}
    QPushButton[variant="ghost"]:hover {{ background: {p['surface3']}; border-color: {p['border']}; color: {p['text']}; }}
    QScrollArea {{ border: 0; background: transparent; }}
    QScrollBar:vertical {{ background: {p['scroll']}; width: 9px; margin: 2px 1px; border-radius: 4px; }}
    QScrollBar::handle:vertical {{ background: {p['scroll_handle']}; min-height: 36px; border-radius: 4px; }}
    QScrollBar::handle:vertical:hover {{ background: {p['blue']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
    QPlainTextEdit {{ background: {p['terminal']}; border: 0; color: {p['terminal_text']}; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 10px; selection-background-color: #274A79; }}
    QPlainTextEdit#ConsoleOutput {{ padding: 16px; }}
    QDialog {{ background: {p['dialog']}; }}
    QDialog QLabel {{ color: {p['muted']}; }}
    QDialog QLineEdit {{ background: {p['field']}; }}
    """


class ActionButton(QPushButton):
    def __init__(self, text: str, callback=None, variant: str = "normal", parent=None):
        super().__init__(text, parent)
        self.setProperty("variant", variant)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(41)
        self.setIconSize(QSize(17, 17))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if callback:
            self.clicked.connect(callback)


class DjangoPilotApp(QMainWindow):
    """PyQt6 frontend for the existing Django Pilot process controller."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Django Pilot")
        self.setMinimumSize(1120, 760)
        self.resize(1510, 960)
        self.settings = QSettings("ErrorLover", "DjangoPilot")
        saved_theme = str(self.settings.value("theme", "dark")).lower()
        self.theme = saved_theme if saved_theme in THEMES else "dark"
        self.logo_path = Path(__file__).resolve().parent / "assets" / "error_lover_django_pilot.png"
        if self.logo_path.is_file():
            self.setWindowIcon(QIcon(str(self.logo_path)))

        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.project_path = str(find_project_root() or Path.cwd())
        self.port = "8000"
        self.venv_path = ""
        self.interpreter_path = sys.executable
        self.status_text = "Workspace ready"
        self.commands = DjangoCommands(self.project_path, self._queue_log, self._queue_status)

        self._build_ui()
        self._apply_theme(self.theme, clear_local_styles=True)
        self._attach_project(self.project_path)
        self._write("DJANGO PILOT / SESSION INITIALIZED", "success")
        self._write("Choose a Django workspace, select its Python environment, then launch a workflow.", "dim")

        self.event_timer = QTimer(self)
        self.event_timer.timeout.connect(self._drain_events)
        self.event_timer.start(45)

    def _apply_theme(self, theme_name: str, clear_local_styles: bool = False):
        """Apply a complete application-wide theme and persist the user's choice."""
        if theme_name not in THEMES:
            theme_name = "dark"
        if clear_local_styles:
            # Old inline widget styles contained hard-coded dark colors. Clear them once
            # so the application stylesheet can consistently control both themes.
            for child in self.findChildren(QWidget):
                child.setStyleSheet("")
        self.theme = theme_name
        self.setStyleSheet(build_stylesheet(theme_name))
        if hasattr(self, "theme_button"):
            if theme_name == "dark":
                self.theme_button.setText("◐  Light mode")
            else:
                self.theme_button.setText("◑  Dark mode")
        self.settings.setValue("theme", theme_name)
        self.settings.sync()
        if hasattr(self, "output_text"):
            self.output_text.viewport().update()

    def _toggle_theme(self):
        self._apply_theme("light" if self.theme == "dark" else "dark")

    # ----- Main composition -----
    def _build_ui(self):
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(26, 22, 26, 14)
        outer.setSpacing(15)

        outer.addWidget(self._build_header())
        outer.addWidget(self._build_project_bar())

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self._build_sidebar())
        body.addWidget(self._build_console(), 1)
        outer.addLayout(body, 1)
        outer.addWidget(self._build_footer())

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("Header")
        row = QHBoxLayout(header)
        row.setContentsMargins(2, 0, 2, 0)
        row.setSpacing(15)

        mark = QFrame()
        mark.setObjectName("BrandMark")
        mark.setFixedSize(76, 76)
        mark_layout = QVBoxLayout(mark)
        mark_layout.setContentsMargins(4, 4, 4, 4)
        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setObjectName("BrandLogo")
        if self.logo_path.is_file():
            pixmap = QPixmap(str(self.logo_path))
            logo.setPixmap(pixmap.scaled(66, 66, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            logo.setText("D✈")
            logo.setObjectName("BrandLogoFallback")
        mark_layout.addWidget(logo)
        row.addWidget(mark)

        brand = QVBoxLayout()
        brand.setSpacing(3)
        title = QLabel("DJANGO PILOT")
        title.setObjectName("BrandTitle")
        eyebrow = QLabel("DJANGO COMMAND CENTER")
        eyebrow.setObjectName("BrandSubtitle")
        brand.addWidget(title)
        brand.addWidget(eyebrow)
        row.addLayout(brand)
        row.addStretch(1)

        self.theme_button = ActionButton("◐  Light mode", self._toggle_theme, "ghost")
        self.theme_button.setMinimumWidth(132)
        self.theme_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon))
        self.theme_button.setToolTip("Switch between dark and light appearance")
        row.addWidget(self.theme_button, alignment=Qt.AlignmentFlag.AlignVCenter)

        meta = QVBoxLayout()
        meta.setSpacing(6)
        pill = QLabel("●  LOCAL WORKSPACE")
        pill.setObjectName("StatusPill")
        pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caption = QLabel("PLAN  /  BUILD  /  DEPLOY")
        caption.setObjectName("Eyebrow")
        caption.setAlignment(Qt.AlignmentFlag.AlignRight)
        meta.addWidget(pill, alignment=Qt.AlignmentFlag.AlignRight)
        meta.addWidget(caption)
        row.addLayout(meta)
        return header

    def _build_project_bar(self) -> QWidget:
        card = QFrame()
        card.setObjectName("ProjectCard")
        row = QHBoxLayout(card)
        row.setContentsMargins(16, 13, 16, 13)
        row.setSpacing(12)

        icon = QLabel("⌂")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(43, 43)
        icon.setObjectName("ProjectIcon")
        row.addWidget(icon)

        labels = QVBoxLayout()
        labels.setSpacing(3)
        active = QLabel("ACTIVE PROJECT")
        active.setObjectName("Eyebrow")
        subtitle = QLabel("Select the folder that contains manage.py")
        subtitle.setObjectName("Muted")
        subtitle.setStyleSheet("font-size:10px;")
        labels.addWidget(active)
        labels.addWidget(subtitle)
        row.addLayout(labels)

        self.project_input = QLineEdit(self.project_path)
        self.project_input.setObjectName("PathInput")
        self.project_input.setPlaceholderText("/path/to/your/django/project")
        row.addWidget(self.project_input, 1)
        row.addWidget(self._make_action_button("Browse", self._browse_project, icon=QStyle.StandardPixmap.SP_DirOpenIcon))
        row.addWidget(self._make_action_button("Open workspace", self._load_project, "primary", QStyle.StandardPixmap.SP_DialogOpenButton))
        return card

    def _build_sidebar(self) -> QWidget:
        shell = QFrame()
        shell.setObjectName("Sidebar")
        shell.setFixedWidth(350)
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        heading = QWidget()
        h = QVBoxLayout(heading)
        h.setContentsMargins(18, 18, 18, 14)
        h.setSpacing(4)
        title = QLabel("PILOT TOOLBOX")
        title.setObjectName("ToolboxTitle")
        sub = QLabel("Your Django workflow, all in one place")
        sub.setObjectName("Faint")
        sub.setStyleSheet("font-size:10px;")
        h.addWidget(title)
        h.addWidget(sub)
        layout.addWidget(heading)

        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setObjectName("ToolboxScroll")
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sidebar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.sidebar_scroll.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        content = QWidget()
        content.setObjectName("SidebarContent")
        self.toolbox_layout = QVBoxLayout(content)
        self.toolbox_layout.setContentsMargins(12, 0, 10, 12)
        self.toolbox_layout.setSpacing(0)
        self._populate_toolbox()
        self.toolbox_layout.addStretch(1)
        self.sidebar_scroll.setWidget(content)
        layout.addWidget(self.sidebar_scroll, 1)

        hint = QLabel("SCROLL TO EXPLORE ALL TOOLS  ↓")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setObjectName("ToolboxHint")
        layout.addWidget(hint)
        return shell

    def _populate_toolbox(self):
        # 01 — Run & control
        self._section("01", "RUN & CONTROL", "SERVER")
        server = self._side_card()
        port_row = QHBoxLayout()
        port_label = QLabel("Development port")
        port_label.setObjectName("Muted")
        self.port_input = QLineEdit("8000")
        self.port_input.setFixedWidth(88)
        self.port_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.port_input.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        port_row.addWidget(port_label)
        port_row.addStretch(1)
        port_row.addWidget(self.port_input)
        server.layout().addLayout(port_row)
        server.layout().addSpacing(9)
        self._button(server, "Launch Django server", self._run_server, "primary", QStyle.StandardPixmap.SP_MediaPlay)
        self._button(server, "Stop server", self._stop_server, "danger", QStyle.StandardPixmap.SP_MediaStop)

        # 02 — Database
        self._section("02", "DATABASE", "MIGRATIONS")
        database = self._side_card()
        self._button(database, "Make migrations", self._make_migrations, icon=QStyle.StandardPixmap.SP_BrowserReload)
        self._button(database, "Apply migrations", self._migrate, icon=QStyle.StandardPixmap.SP_DialogApplyButton)
        self._button(database, "Collect static files", self._collectstatic, icon=QStyle.StandardPixmap.SP_DirIcon)

        # 03 — Project tools
        self._section("03", "PROJECT TOOLS", "DJANGO")
        tools = self._side_card()
        tools.layout().addWidget(self._field_label("NEW DJANGO APP"))
        self.app_name_input = QLineEdit()
        self.app_name_input.setPlaceholderText("e.g. accounts, blog, shop")
        tools.layout().addWidget(self.app_name_input)
        self._button(tools, "Create Django app", self._create_app, "primary", QStyle.StandardPixmap.SP_FileIcon)
        self._button(tools, "Create superuser", self._superuser_dialog, icon=QStyle.StandardPixmap.SP_DirHomeIcon)
        self._button(tools, "Open Django shell", self._shell, icon=QStyle.StandardPixmap.SP_ComputerIcon)

        # 04 — Python environment
        self._section("04", "PYTHON ENVIRONMENT", "VENV")
        env = self._side_card()
        env.layout().addWidget(self._field_label("VIRTUAL ENVIRONMENT FOLDER"))
        venv_row = QHBoxLayout()
        self.venv_input = QLineEdit()
        self.venv_input.setPlaceholderText("Project .venv or existing environment")
        self.venv_input.setFont(QFont("Consolas", 8))
        browse = ActionButton("Browse", self._browse_venv)
        browse.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        browse.setFixedWidth(82)
        venv_row.addWidget(self.venv_input, 1)
        venv_row.addWidget(browse)
        env.layout().addLayout(venv_row)
        self._button(env, "Create virtual environment", self._create_venv, "primary", QStyle.StandardPixmap.SP_DriveHDIcon)
        self._button(env, "Use selected environment", self._use_venv, icon=QStyle.StandardPixmap.SP_DialogOkButton)
        env.layout().addSpacing(5)
        env.layout().addWidget(self._field_label("ACTIVE PYTHON"))
        self.active_python_label = QLabel(self.interpreter_path)
        self.active_python_label.setWordWrap(True)
        self.active_python_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.active_python_label.setObjectName("ActivePython")
        env.layout().addWidget(self.active_python_label)

        # 05 — Workspace
        self._section("05", "WORKSPACE", "FILES")
        workspace = self._side_card()
        self._button(workspace, "Open project folder", self._open_project_folder, icon=QStyle.StandardPixmap.SP_DirOpenIcon)
        self._button(workspace, "Clear live console", self._clear_output, icon=QStyle.StandardPixmap.SP_TrashIcon)

    def _build_console(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("ConsoleCard")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 17, 18, 15)
        layout.setSpacing(12)

        top = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("LIVE CONSOLE")
        title.setObjectName("PanelTitle")
        desc = QLabel("Real-time process output  ·  shell commands  ·  interactive input")
        desc.setObjectName("Muted")
        desc.setStyleSheet("font-size:10px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        top.addLayout(title_box)
        top.addStretch(1)
        live = QLabel("●  LIVE STREAM")
        live.setObjectName("StatusPill")
        top.addWidget(live, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top)

        terminal_frame = QFrame()
        terminal_frame.setObjectName("TerminalFrame")
        terminal_layout = QVBoxLayout(terminal_frame)
        terminal_layout.setContentsMargins(0, 0, 0, 0)
        terminal_layout.setSpacing(0)
        chrome = QWidget()
        chrome.setObjectName("TerminalChrome")
        chrome_row = QHBoxLayout(chrome)
        chrome_row.setContentsMargins(14, 9, 14, 9)
        chrome_row.setSpacing(6)
        for tone in ("red", "amber", "green"):
            dot = QLabel("●")
            dot.setObjectName("TerminalDot")
            dot.setProperty("tone", tone)
            chrome_row.addWidget(dot)
        chrome_row.addSpacing(7)
        terminal_name = QLabel("pilot-terminal  —  bash / powershell")
        terminal_name.setObjectName("TerminalName")
        chrome_row.addWidget(terminal_name)
        chrome_row.addStretch(1)
        terminal_layout.addWidget(chrome)

        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.output_text.setFrameShape(QFrame.Shape.NoFrame)
        self.output_text.setPlaceholderText("Your Django process output will appear here…")
        self.output_text.setFont(QFont("Cascadia Code" if sys.platform == "win32" else "DejaVu Sans Mono", 10))
        self.output_text.setObjectName("ConsoleOutput")
        terminal_layout.addWidget(self.output_text, 1)
        layout.addWidget(terminal_frame, 1)

        command_area = QFrame()
        command_area.setObjectName("CommandArea")
        ca = QVBoxLayout(command_area)
        ca.setContentsMargins(13, 11, 13, 10)
        ca.setSpacing(8)
        command_header = QHBoxLayout()
        command_title = QLabel("COMMAND INPUT")
        command_title.setObjectName("CommandTitle")
        command_header.addWidget(command_title)
        command_header.addStretch(1)
        keyboard_hint = QLabel("ENTER ↵")
        keyboard_hint.setObjectName("KeyboardHint")
        command_header.addWidget(keyboard_hint)
        ca.addLayout(command_header)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        prompt = QLabel("❯")
        prompt.setObjectName("Prompt")
        input_row.addWidget(prompt)
        self.terminal_input = QLineEdit()
        self.terminal_input.setPlaceholderText("Type a command…  e.g. pip install django, python manage.py check")
        self.terminal_input.returnPressed.connect(self._terminal_submit)
        input_row.addWidget(self.terminal_input, 1)
        input_row.addWidget(self._make_action_button("Run command", self._terminal_submit, "primary", QStyle.StandardPixmap.SP_MediaPlay))
        input_row.addWidget(self._make_action_button("Send input", self._send_process_input, icon=QStyle.StandardPixmap.SP_ArrowRight))
        ca.addLayout(input_row)
        note = QLabel("Run command starts a new shell process in the workspace. Send input forwards text to the active Django server or interactive shell.")
        note.setWordWrap(True)
        note.setObjectName("CommandNote")
        ca.addWidget(note)
        layout.addWidget(command_area)

        status_row = QHBoxLayout()
        self.status_label = QLabel(self.status_text)
        self.status_label.setObjectName("Muted")
        self.status_label.setStyleSheet("font-size:9px;")
        status_row.addWidget(QLabel("●"))
        status_row.itemAt(0).widget().setObjectName("LiveDot")
        status_row.addWidget(self.status_label)
        status_row.addStretch(1)
        status_row.addWidget(self._make_action_button("Clear output", self._clear_output, "ghost", QStyle.StandardPixmap.SP_TrashIcon))
        layout.addLayout(status_row)
        return panel

    def _build_footer(self) -> QWidget:
        footer = QWidget()
        row = QHBoxLayout(footer)
        row.setContentsMargins(2, 0, 2, 0)
        left = QLabel("Make with ❤️ by Error Lover")
        left.setObjectName("Eyebrow")

        right = QLabel("DJANGO PILOT  ·  YOUR DJANGO COMMAND CENTER")
        right.setObjectName("Eyebrow")
        row.addWidget(left)
        row.addStretch(1)
        row.addWidget(right)
        return footer

    # ----- Toolbox widgets -----
    def _section(self, number: str, title: str, hint: str):
        row = QHBoxLayout()
        row.setContentsMargins(8, 5, 8, 5)
        row.setSpacing(8)
        num = QLabel(number)
        num.setFixedSize(23, 23)
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num.setObjectName("SectionNumber")
        text = QLabel(title)
        text.setObjectName("SectionTitle")
        row.addWidget(num)
        row.addWidget(text)
        row.addStretch(1)
        badge = QLabel(hint)
        badge.setObjectName("SectionBadge")
        row.addWidget(badge)
        # Use a styled QFrame rather than a plain QWidget. On some Windows
        # styles a plain QWidget falls back to the system's near-black palette,
        # which left these bars dark even while Light Mode was active.
        wrapper = QFrame()
        wrapper.setObjectName("ToolSection")
        wrapper.setFrameShape(QFrame.Shape.NoFrame)
        wrapper.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        wrapper.setLayout(row)
        self.toolbox_layout.addWidget(wrapper)

    def _side_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("SideCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(11, 11, 11, 11)
        layout.setSpacing(7)
        self.toolbox_layout.addWidget(card)
        return card

    @staticmethod
    def _field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    def _make_action_button(self, text: str, callback, variant: str = "normal", icon=None) -> ActionButton:
        button = ActionButton(text, callback, variant)
        if icon is not None:
            button.setIcon(self.style().standardIcon(icon))
        return button

    def _button(self, parent: QFrame, text: str, callback, variant: str = "normal", icon=None) -> ActionButton:
        button = self._make_action_button(text, callback, variant, icon)
        parent.layout().addWidget(button)
        return button

    # ----- Project and action logic -----
    def _browse_project(self):
        selected = QFileDialog.getExistingDirectory(self, "Select Django project folder", self.project_input.text())
        if selected:
            self.project_input.setText(selected)

    def _browse_venv(self):
        selected = QFileDialog.getExistingDirectory(self, "Select virtual environment folder", self.venv_input.text() or self.project_input.text())
        if selected:
            self.venv_input.setText(selected)

    def _load_project(self):
        path = Path(self.project_input.text().strip()).expanduser().resolve()
        if not (path / "manage.py").is_file():
            QMessageBox.critical(self, "Not a Django project", "No manage.py was found in this folder.")
            return
        if self.commands.server_process and self.commands.server_process.poll() is None:
            QMessageBox.warning(self, "Server is running", "Stop the current Django server before switching projects.")
            return
        self._attach_project(str(path))
        self._write(f"Workspace loaded · {path}", "success")
        candidate = path / ".venv"
        if candidate.exists() and not self.venv_input.text().strip():
            self.venv_input.setText(str(candidate))
            self._use_venv(show_message=False)

    def _attach_project(self, path: str):
        self.project_path = str(Path(path).expanduser().resolve())
        self.commands = DjangoCommands(self.project_path, self._queue_log, self._queue_status)
        self.commands.set_python(self.interpreter_path)
        self.project_input.setText(self.project_path)

    def _valid_project(self) -> bool:
        path = Path(self.project_input.text().strip()).expanduser().resolve()
        if not (path / "manage.py").is_file():
            QMessageBox.critical(self, "Project not found", "Choose the folder containing manage.py, then click Open workspace.")
            return False
        if Path(self.commands.project_root) != path:
            self._attach_project(str(path))
        else:
            self.commands.set_python(self.interpreter_path)
        return True

    def _run_server(self):
        if not self._valid_project():
            return
        port = self.port_input.text().strip() or "8000"
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            QMessageBox.warning(self, "Invalid port", "Enter a port number between 1 and 65535.")
            return
        self.commands.runserver(port)

    def _stop_server(self):
        self.commands.stop_server()

    def _make_migrations(self):
        if self._valid_project():
            self.commands.make_migrations()

    def _migrate(self):
        if self._valid_project():
            self.commands.migrate()

    def _collectstatic(self):
        if self._valid_project():
            self.commands.collectstatic()

    def _create_app(self):
        name = self.app_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "App name", "Enter an app name first.")
            return
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            QMessageBox.warning(self, "Invalid app name", "Use a valid Python name: letters, numbers and underscores only.")
            return
        if self._valid_project():
            self.commands.create_app(name)
            self.app_name_input.clear()

    def _shell(self):
        if self._valid_project():
            self.commands.shell()

    def _create_venv(self):
        if not self._valid_project():
            return
        path_text = self.venv_input.text().strip()
        if not path_text:
            path_text = str(Path(self.project_path) / ".venv")
            self.venv_input.setText(path_text)
        target = Path(path_text).expanduser()
        if target.exists() and any(target.iterdir()):
            QMessageBox.information(self, "Environment already exists", "This folder is not empty. Choose it and press 'Use selected environment'.")
            return
        self.commands.create_venv(path_text, callback=self._queue_venv_ready)

    def _queue_venv_ready(self, interpreter: str):
        self.events.put(("venv", interpreter))

    def _apply_venv(self, interpreter: str):
        self.venv_path = str(Path(interpreter).parent.parent)
        self.venv_input.setText(self.venv_path)
        self.interpreter_path = interpreter
        self.active_python_label.setText(interpreter)
        self.commands.set_python(interpreter)
        self._write("Virtual environment activated for Django Pilot commands.", "success")

    def _use_venv(self, show_message: bool = True):
        path = self.venv_input.text().strip()
        if not path:
            QMessageBox.warning(self, "Venv path", "Select or enter your virtual environment folder.")
            return
        interpreter = venv_python(path)
        if not interpreter.is_file():
            QMessageBox.critical(self, "Python not found", f"Could not find the environment interpreter at:\n{interpreter}")
            return
        self._apply_venv(str(interpreter))
        if show_message:
            self._write(f"Virtual environment selected · {interpreter}", "success")

    def _superuser_dialog(self):
        if not self._valid_project():
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Django superuser")
        dialog.setMinimumWidth(430)
        dialog.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 22, 24, 20)
        title = QLabel("CREATE SUPERUSER")
        title.setStyleSheet("font-size:14px; font-weight:900; letter-spacing:1px;")
        desc = QLabel("Create an administrator account for this Django project.")
        desc.setObjectName("Muted")
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addSpacing(10)

        form = QFormLayout()
        form.setSpacing(10)
        username = QLineEdit()
        email = QLineEdit()
        password = QLineEdit()
        password.setEchoMode(QLineEdit.EchoMode.Password)
        username.setPlaceholderText("admin")
        email.setPlaceholderText("admin@example.com")
        password.setPlaceholderText("Password")
        form.addRow("Username", username)
        form.addRow("Email", email)
        form.addRow("Password", password)
        layout.addLayout(form)
        layout.addSpacing(12)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Create superuser")
        buttons.button(QDialogButtonBox.StandardButton.Ok).setProperty("variant", "primary")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        username_value = username.text().strip()
        email_value = email.text().strip()
        password_value = password.text()
        if not username_value or not password_value:
            QMessageBox.warning(self, "Required fields", "Username and password are required.")
            return
        script = (
            "from django.contrib.auth import get_user_model; "
            "U=get_user_model(); "
            f"U.objects.create_superuser({username_value!r}, {email_value!r}, {password_value!r}); "
            "print('Superuser created successfully')"
        )
        self.commands._spawn_reader(
            [self.commands.python, "manage.py", "shell", "-c", script],
            "Create superuser",
        )

    def _terminal_submit(self):
        command = self.terminal_input.text().strip()
        if not command:
            return
        self.terminal_input.clear()
        self._write(f"❯ {command}", "command")
        if self._valid_project():
            self.commands.run_terminal_command(command)

    def _send_process_input(self):
        text = self.terminal_input.text()
        if not text:
            return
        self.terminal_input.clear()
        self._write(f"↳ stdin: {text}", "dim")
        if self.commands.send_input(text):
            self._write("Input sent to active process", "success")
        else:
            self._write("No active interactive process is waiting for input", "warning")

    def _open_project_folder(self):
        path = Path(self.project_input.text().strip()).expanduser().resolve()
        if not path.is_dir():
            QMessageBox.critical(self, "Folder not found", "The selected project folder does not exist.")
            return
        try:
            if os.name == "nt":
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            self._write(f"Could not open folder: {exc}", "error")

    # ----- Console event bridge -----
    def _queue_log(self, text: str, tag: str | None = None):
        self.events.put(("log", (str(text), tag)))

    def _queue_status(self, text: str):
        self.events.put(("status", text))

    def _write(self, text: str, tag: str | None = None):
        palette = THEMES[self.theme]
        color_map = {
            "error": palette["red"],
            "success": palette["green"],
            "command": palette["accent"],
            "dim": palette["faint"],
            "warning": palette["amber"],
        }
        color = color_map.get(tag, palette["terminal_text"])
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if tag == "command":
            fmt.setFontWeight(QFont.Weight.Bold)
        cursor.insertText(str(text) + "\n", fmt)
        self.output_text.setTextCursor(cursor)
        self.output_text.ensureCursorVisible()

    def _drain_events(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "log":
                    text, tag = payload  # type: ignore[misc]
                    self._write(text, tag)
                elif kind == "status":
                    self.status_label.setText(str(payload))
                elif kind == "venv":
                    self._apply_venv(str(payload))
        except queue.Empty:
            pass

    def _clear_output(self):
        self.output_text.clear()
        self.status_label.setText("Console cleared")

    def closeEvent(self, event):
        server = getattr(self.commands, "server_process", None)
        if server and server.poll() is None:
            answer = QMessageBox.question(
                self,
                "Django server is running",
                "Stop the development server before closing Django Pilot?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self.commands.stop_server()
        event.accept()


# Compatibility alias for code that imported the previous class name.
DjangoManagerApp = DjangoPilotApp
