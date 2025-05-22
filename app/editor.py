import json
import os
import re
import sys

import markdown

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QMainWindow, QListWidget,
                             QTreeWidgetItem, QMenu, QInputDialog,
                             QMessageBox, QFileDialog)
from PyQt6.uic import loadUi
from pathlib import Path
from app.watcher import ProjectFolderWatcher
from app.editablewebengineview import EditableWebEngineView  # do not delete!

sys.path.append(os.path.abspath("app"))


class MarkdownEditor(QMainWindow):
    def __init__(self, path=None):
        super().__init__()
        loadUi("resources/ui/main.ui", self)
        self.setWindowTitle("Gestein")
        self.setWindowIcon(QIcon('resources/icons/icon.png'))
        self.current_dir_path = path
        self.recent_files = []

        config = self.load_config()
        self.theme = config["theme"]
        self.set_theme(self.theme)
        self.save_config(config)

        config = self.load_config()
        self.current_file_path = config.get("lastOpenFile")
        if self.current_file_path:
            self.load_markdown_file(self.current_file_path)
        else:
            self.reset_editor()

        self.build_kartei(self.current_dir_path)

        self.actionOpen.triggered.connect(self.load_dir)
        self.actionSave.triggered.connect(self.save_markdown_file)
        self.actionPDF.triggered.connect(self.export_to_pdf)
        self.actionBold.triggered.connect(self.make_bold)
        self.actionItalic.triggered.connect(self.make_italic)
        self.file_list = QListWidget()

        for i in range(1, 7):
            (getattr(self, f"actionHeader{i}").triggered.connect
             (lambda heading, level=i: self.insert_heading(level)))

        for theme_name in ["Dark", "Light", "Aqua", "Emerald",
                           "Amethyst", "Sunny", "Custom1", "Custom2"]:
            getattr(self, f"action{theme_name}").triggered.connect(
                lambda _, name=theme_name.lower(): self.set_theme(name)
            )

        self.textEdit.textChanged.connect(self.update_preview)
        self.textEdit.cursorPositionChanged.connect(self.update_preview)
        self.update_preview()

        self.treeWidget.itemClicked.connect(self.on_tree_item_clicked)

        self.treeWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.
                                             CustomContextMenu)
        (self.treeWidget.customContextMenuRequested
         .connect(self.open_context_menu))

    def set_theme(self, name):
        config_path = "app/config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        config["theme"] = name
        self.theme = name

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

        self.setStyleSheet(Path(f'resources/Styles/{name}.qss')
                           .read_text(encoding='utf-8'))

    def on_tree_item_clicked(self, item):
        file_path = item.toolTip(0)
        if file_path != self.current_file_path and file_path.endswith(".md"):
            if not self.textEdit.isReadOnly():
                self.save_markdown_file()
            self.load_markdown_file(file_path)

    def build_project_tree(self, root_path):
        self.treeWidget.clear()

        def add_items(parent_item, path):
            entries = sorted(os.listdir(path))

            for name in entries:
                abs_path = os.path.join(path, name)
                if os.path.isdir(abs_path):
                    folder_item = QTreeWidgetItem([name])
                    folder_item.setToolTip(0, abs_path)
                    parent_item.addChild(folder_item)
                    add_items(folder_item, abs_path)
                elif name.lower().endswith(".md"):
                    file_item = QTreeWidgetItem([name])
                    file_item.setToolTip(0, abs_path)
                    parent_item.addChild(file_item)

        root_item = QTreeWidgetItem([os.path.basename(root_path)])
        root_item.setToolTip(0, root_path)
        self.treeWidget.addTopLevelItem(root_item)
        add_items(root_item, root_path)
        self.treeWidget.expandAll()

    def open_context_menu(self, position):
        item = self.treeWidget.itemAt(position)
        if not item:
            return

        item_path = item.toolTip(0)

        menu = QMenu()
        if os.path.isdir(item_path):
            create_file_action = menu.addAction("Создать новый файл")
            create_folder_action = menu.addAction("Создать новую папку")
            delete_action = menu.addAction("Удалить папку")
        else:
            delete_action = menu.addAction("Удалить файл")

        action = menu.exec(self.treeWidget.viewport().mapToGlobal(position))

        if action == delete_action:
            self.delete_item(item_path)
        elif os.path.isdir(item_path):
            if action == create_file_action:
                self.create_new_file_in_folder(item_path)
            elif action == create_folder_action:
                self.create_new_folder(item_path)

    def create_new_folder(self, parent_folder_path):
        folder_name, ok = QInputDialog.getText(self,
                                               "Новая папка",
                                               "Введите имя папки:")
        if ok and folder_name:
            new_folder_path = os.path.join(parent_folder_path, folder_name)

            if os.path.exists(new_folder_path):
                QMessageBox.warning(self, "Папка существует",
                                    "Папка с таким именем уже существует.")
                return

            os.makedirs(new_folder_path)
            QMessageBox.information(self, "Папка создана",
                                    f"Папка {folder_name} создана.")
            self.build_project_tree(self.current_dir_path)  # Обновить дерево

    def create_new_file_in_folder(self, parent_folder_path):
        text, ok = QInputDialog.getText(self,
                                        "Новый файл",
                                        "Введите имя файла:")
        if ok and text:
            if not text.lower()[-3:] == ".md":
                text += ".md"
            new_file_path = os.path.join(parent_folder_path, text)
            if os.path.exists(new_file_path):
                QMessageBox.warning(self, "Ошибка",
                                    "Файл с таким именем уже существует.")
                return
            with open(new_file_path, "w", encoding="utf-8") as f:
                f.write(f"# Новый файл {text}\n")
            QMessageBox.information(self,
                                    "Файл создан",
                                    f"Файл {text} создан.")
            self.build_project_tree(self.current_dir_path)
            self.load_markdown_file(new_file_path)

    def delete_item(self, path):

        def remove_dir_recursive(dir_path):
            for entry in os.listdir(dir_path):
                full_path = os.path.join(dir_path, entry)
                if os.path.isdir(full_path):
                    remove_dir_recursive(full_path)
                else:
                    os.remove(full_path)
            os.rmdir(dir_path)

        confirm = QMessageBox.question(
            self,
            "Подтвердите удаление",
            f"Вы уверены, что хотите удалить «{os.path.basename(path)}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        if os.path.isdir(path):
            current_dir = os.path.dirname(self.current_file_path)
            if os.path.commonpath([current_dir, path]) == path:
                remove_dir_recursive(path)
            else:
                self.reset_editor()
                config = self.load_config()
                if config.get("lastOpenFile") == path:
                    config["lastOpenFile"] = ""
                    self.save_config(config)
                remove_dir_recursive(path)
        else:
            if self.current_file_path == path:
                self.reset_editor()

                config = self.load_config()
                if config.get("lastOpenFile") == path:
                    config["lastOpenFile"] = ""
                    self.save_config(config)

            os.remove(path)
        self.build_project_tree(self.current_dir_path)
        QMessageBox.information(self,
                                "Удаление",
                                "Удаление выполнено успешно.")

    def load_markdown_file(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Выберите Markdown файл", "", "Markdown Files (*.md)")
        if not file_path:
            return
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.textEdit.setPlainText(content)
            self.current_file_path = file_path
            self.update_preview()
            self.textEdit.setReadOnly(False)
            self.textEdit.setPlaceholderText("Введите текст здесь...")
            self.setWindowTitle(f"Gestein - {os.path.basename(file_path)}")
        config_path = "app/config.json"
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}
        config["lastOpenFile"] = file_path
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    def load_dir(self):
        self.save_markdown_file()

        config_path = "app/config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        folder_path = (QFileDialog.
                       getExistingDirectory(self,
                                            "Выберите папку проекта",
                                            desktop_path))
        if not folder_path:
            return
        config["kartei"] = folder_path
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

        self.reset_editor()
        self.build_kartei(folder_path)

    def save_markdown_file(self):
        if self.current_file_path:
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(self.textEdit.toPlainText())
            return

    def export_to_pdf(self):
        md_text = self.textEdit.toPlainText()
        lines = md_text.splitlines()
        html_lines = []
        for line in lines:
            html = (markdown.markdown(line)
                    .replace("<p>", "")
                    .replace("</p>", ""))
            html_lines.append(f"<div>{html}</div>")
        html_content = "\n".join(html_lines)

        self.webView.set_html_content(html_content, highlight=False)

        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как PDF",
            desktop_path,
            "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            self.webView.export_to_pdf(file_path)
            QMessageBox.information(self,
                                    "Успех",
                                    "PDF успешно сохранён.")

    def make_bold(self):
        cursor = self.textEdit.textCursor()
        if cursor.hasSelection():
            matches = re.findall(r"(^\*{2,3}([^*]+)\*{2,3}$)",
                                 cursor.selectedText())
            if not matches:
                cursor.insertText(f"**{cursor.selectedText()}**")
            else:
                cursor.insertText(cursor.selectedText()[2:-2])

    def make_italic(self):
        cursor = self.textEdit.textCursor()
        if cursor.hasSelection():
            matches = re.findall(r"(^\*|\*{3})([^*]+)(\*|\*{3}$)",
                                 cursor.selectedText())
            if not matches:
                cursor.insertText(f"*{cursor.selectedText()}*")
            else:
                cursor.insertText(cursor.selectedText()[1:-1])

    def insert_heading(self, index):
        cursor = self.textEdit.textCursor()
        level = index
        text = cursor.selectedText() or "Заголовок"
        cursor.insertText(f"{'#' * level} {text}\n")

    def update_preview(self):
        md_text = self.textEdit.toPlainText()
        lines = md_text.splitlines()
        cursor = self.textEdit.textCursor()
        current_line = cursor.blockNumber()
        html_lines = []
        for i, line in enumerate(lines):
            html = (markdown.markdown(line).replace("<p>", "")
                    .replace("</p>", ""))
            if i == current_line:
                cls = "active-line"
            else:
                cls = ""
            html_lines.append(f"<div class='{cls}'>{html}</div>")
        self.webView.set_html_content("\n".join(html_lines), highlight=True)

    def handle_folder_change(self):
        self.build_project_tree(self.current_dir_path)

    def load_config(self):
        config_path = "app/config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_config(self, config):
        config_path = "app/config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    def reset_editor(self):
        self.textEdit.clear()
        self.textEdit.setReadOnly(True)
        self.textEdit.setPlaceholderText("Выберите файл для редактирования")
        self.current_file_path = None
        self.setWindowTitle("Gestein")

    def build_kartei(self, path):
        self.build_project_tree(path)
        self.current_dir_path = path
        self.watcher = ProjectFolderWatcher(path)
        self.watcher.file_changed.connect(self.handle_folder_change)
        self.watcher.start()

    def closeEvent(self, event):
        if hasattr(self, 'watcher'):
            self.watcher.stop()

        reply = QMessageBox.question(
            self,
            "Подтвердите выход",
            "Вы уверены, что хотите выйти?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.save_markdown_file()
            event.accept()
        else:
            event.ignore()
