import sys
from PyQt6.QtWidgets import QApplication
from editor import MarkdownEditor
from welcome import ProjectSelectionWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from pathlib import Path
import json
import os
from PyQt6.QtWidgets import QMessageBox



if __name__ == "__main__":
    os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-gpu-compositing'
    app = QApplication(sys.argv)


    config_path = "config.json"
    config = {}

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        QMessageBox.warning(None, "Error", "Config corrupted")

    app.setStyleSheet(Path('Dark.qss').read_text(encoding='utf-8'))

    if not config.get("kartei"):
        selection_window = ProjectSelectionWindow()
        selection_window.show()
    else:
        editor_window = MarkdownEditor(config.get("kartei"))
        editor_window.show()

    sys.exit(app.exec())