import json
import os

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QPushButton, QFileDialog, QWidget
from PyQt6.uic import loadUi
from editor import MarkdownEditor


class ProjectSelectionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("select.ui", self)
        self.setWindowTitle("Добро пожаловать!")
        self.setWindowIcon(QIcon('icon.png'))
        self.selectButton.clicked.connect(self.select_project_folder)

    def select_project_folder(self):
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку проекта", desktop_path)
        if folder:
            config_path = "config.json"
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            config["kartei"] = folder
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)

            print(folder)
            self.editor_window = MarkdownEditor(folder)
            self.editor_window.show()
            self.close()
