import json
import os

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QDialog
from PyQt6.uic import loadUi
from app.editor import MarkdownEditor
from pathlib import Path


class ProjectSelectionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi(f"{Path(__file__).parent.parent}/resources/ui/select.ui", self)
        self.setWindowTitle("Добро пожаловать!")
        self.setWindowIcon(QIcon('/"resources"/"icons"/"icon.png"'))
        self.selectButton.clicked.connect(self.select_project_folder)

    def select_project_folder(self):
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        folder = (QFileDialog.getExistingDirectory(self,
                                                   "Выберите папку проекта",
                                                   desktop_path))
        if folder:
            theme_dialog = ThemeDialog(self)
            if theme_dialog.exec():
                theme = theme_dialog.chosen_theme

                config_path = "app/config.json"
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                config["kartei"] = folder
                config["theme"] = theme

                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)

                self.editor_window = MarkdownEditor(folder)
                self.editor_window.show()
                self.close()


class ThemeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(f'{Path(__file__).parent.parent}'
               f'/resources/ui/themeDialog.ui', self)
        self.setWindowTitle("Выбор темы")

        self.setStyleSheet(Path(f'{Path(__file__).parent.parent}'
                                f'/resources/Styles/Dark.qss')
                           .read_text(encoding='utf-8'))
        self.chosen_theme = None

        self.buttonLight.clicked.connect(self.choose_light)
        self.buttonDark.clicked.connect(self.choose_dark)

    def choose_light(self):
        self.chosen_theme = "Light"
        self.accept()

    def choose_dark(self):
        self.chosen_theme = "Dark"
        self.accept()
