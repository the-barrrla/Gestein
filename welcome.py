import json
import os

from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QPushButton, QFileDialog, QWidget

from editor import MarkdownEditor


class ProjectSelectionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Выбор папки проекта")
        self.setGeometry(100, 100, 400, 200)
        self.widget = QWidget()
        self.setCentralWidget(self.widget)
        layout = QVBoxLayout()
        self.folder_label = QLabel("Папка проекта не выбрана.")
        layout.addWidget(self.folder_label)
        self.select_button = QPushButton("Выбрать папку проекта")
        layout.addWidget(self.select_button)
        self.select_button.clicked.connect(self.select_project_folder)
        self.widget.setLayout(layout)

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
