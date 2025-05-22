import sys
from PyQt6.QtWidgets import QApplication
from app.editor import MarkdownEditor
from app.welcome import ProjectSelectionWindow
from pathlib import Path
import json
import os
from PyQt6.QtWidgets import QMessageBox


if __name__ == "__main__":
    app = QApplication(sys.argv)

    config = {}

    if os.path.exists("app/config.json"):
        with open("app/config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        QMessageBox.warning(None, "Error", "Config corrupted")

    app.setStyleSheet(Path('resources/Styles/Dark.qss').read_text(encoding='utf-8'))

    if not config.get("kartei"):
        selection_window = ProjectSelectionWindow()
        selection_window.show()
    else:
        editor_window = MarkdownEditor(config.get("kartei"))
        editor_window.show()

    sys.exit(app.exec())