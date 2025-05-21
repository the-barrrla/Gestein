import sys
from PyQt6.QtWidgets import QApplication
from editor import MarkdownEditor
from welcome import ProjectSelectionWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from pathlib import Path
import winreg
import json
import os
from PyQt6.QtWidgets import QMessageBox

def is_dark_mode_enabled():
    try:
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key = winreg.OpenKey(registry,
                             r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize')
        value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
        winreg.CloseKey(key)
        return value == 0
    except Exception:
        return False

if __name__ == "__main__":
    os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-gpu-compositing'
    app = QApplication(sys.argv)

    dark_mode = is_dark_mode_enabled()

    if dark_mode:
        app.setStyleSheet(Path('dark.qss').read_text(encoding='utf-8'))
    else:
        app.setStyleSheet(Path('light.qss').read_text(encoding='utf-8'))

    config_path = "config.json"
    config = {}

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        QMessageBox.warning(None, "Error", "Config corrupted")

    if not config.get("kartei"):
        selection_window = ProjectSelectionWindow()
        selection_window.show()
    else:
        editor_window = MarkdownEditor(config.get("kartei"))
        editor_window.show()

    sys.exit(app.exec())