import sys
from PyQt6.QtWidgets import QApplication
from editor import MarkdownEditor
from welcome import ProjectSelectionWindow
import editablewebengineview
from pathlib import Path
import json
import os
from PyQt6.QtWidgets import QMessageBox



if __name__ == "__main__":
    app = QApplication(sys.argv)

    config_path = "config.json"
    config = {}

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        QMessageBox.warning(None, "Error", "Config corrupted")

    app.setStyleSheet(Path('Styles/Dark.qss').read_text(encoding='utf-8'))

    if not config.get("kartei"):
        selection_window = ProjectSelectionWindow()
        selection_window.show()
    else:
        editor_window = MarkdownEditor(config.get("kartei"))
        editor_window.show()

    sys.exit(app.exec())