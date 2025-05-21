import sys
import os
import json
import markdown
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyQt6.QtCore import QThread, pyqtSignal
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QFileDialog, QPushButton, QMessageBox, QTextEdit, QLabel,
    QSplitter, QScrollArea, QColorDialog, QComboBox, QListWidget, QListWidgetItem, QTreeWidgetItem, QDialog,
    QInputDialog, QMenu
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.uic import loadUi
import re

os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-gpu-compositing'

class ProjectFolderWatcher(QThread):
    file_changed = pyqtSignal()

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.event_handler = FileSystemEventHandler()
        self.event_handler.on_any_event = self.on_any_event
        self.observer = Observer()

    def on_any_event(self, event):
        self.file_changed.emit()

    def run(self):
        self.observer.schedule(self.event_handler, self.folder_path, recursive=True)
        self.observer.start()
        try:
            while not self.isInterruptionRequested():
                time.sleep(1)
        finally:
            self.observer.stop()
            self.observer.join()

    def stop(self):
        self.requestInterruption()
        self.wait()

class EditableWebEngineView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)

    def generate_full_html(self, body_content):
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f9f9f9;
                    overflow: auto;
                }}
                h1, h2, h3 {{ color: #333; }}
                p {{ font-size: 16px; line-height: 0; }}
                ul {{ padding-left: 20px; }}
                a {{ color: #0066cc; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                table {{ border-collapse: collapse; width: 100%; }}
                table, th, td {{ border: 1px solid #ddd; padding: 8px; }}
                th {{ background-color: #f2f2f2; }}
                .active-line {{ background-color: #ffffcc; border-left: 4px solid orange; padding-left: 4px; }}
            </style>
        </head>
        <body contenteditable="true">
            {body_content}
        </body>
        </html>
        """

    def setHtmlContent(self, html_content):
        self.setHtml(self.generate_full_html(html_content))

    def export_to_pdf(self, file_path):
        self.page().printToPdf(file_path)

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

class MarkdownEditor(QMainWindow):
    def __init__(self, path=None):
        super().__init__()
        loadUi("main.ui", self)
        self.setWindowTitle("Gestein")
        self.current_dir_path = path
        self.recent_files = []

        config_path = "config.json"
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.current_file_path = config.get("lastOpenFile")
            if self.current_file_path:
                self.load_markdown_file(self.current_file_path)
            else:
                self.current_file_path = None
                self.textEdit.setReadOnly(True)
                self.textEdit.setPlaceholderText("Выберите файл для редактирования")


        self.build_project_tree(self.current_dir_path)

        self.watcher = ProjectFolderWatcher(self.current_dir_path)
        self.watcher.file_changed.connect(self.handle_folder_change)
        self.watcher.start()


        # self.actionNewFile.triggered.connect(self.create_new_file)
        self.actionOpen.triggered.connect(self.load_dir)
        self.actionSave.triggered.connect(self.save_markdown_file)
        self.actionPDF.triggered.connect(self.export_to_pdf)
        self.actionBold.triggered.connect(self.make_bold)
        self.actionItalic.triggered.connect(self.make_italic)
        self.file_list = QListWidget()
        self.actionHeader1.triggered.connect(lambda: self.insert_heading(1))
        self.actionHeader2.triggered.connect(lambda: self.insert_heading(2))
        self.actionHeader3.triggered.connect(lambda: self.insert_heading(3))
        self.actionHeader4.triggered.connect(lambda: self.insert_heading(4))
        self.actionHeader5.triggered.connect(lambda: self.insert_heading(5))
        self.actionHeader6.triggered.connect(lambda: self.insert_heading(6))


        self.textEdit.textChanged.connect(self.update_preview)
        self.textEdit.cursorPositionChanged.connect(self.update_preview)
        self.update_preview()

        self.treeWidget.itemClicked.connect(self.on_tree_item_clicked)

        self.treeWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.open_context_menu)



    def on_tree_item_clicked(self, item):
        file_path = item.toolTip(0)
        if file_path != self.current_file_path and file_path.endswith(".md"):
            if not self.textEdit.isReadOnly():
                self.save_markdown_file()
            self.load_markdown_file(file_path)

    def build_project_tree(self, root_path):
        self.treeWidget.clear()

        def add_items(parent_item, path):
            try:
                entries = sorted(os.listdir(path))
            except NotADirectoryError:
                return

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
        if not os.path.isdir(item_path):
            return

        menu = QMenu()
        create_file_action = menu.addAction("Создать новый файл")
        create_folder_action = menu.addAction("Создать новую папку")

        action = menu.exec(self.treeWidget.viewport().mapToGlobal(position))

        if action == create_file_action:
            self.create_new_file_in_folder(item_path)
        elif action == create_folder_action:
            self.create_new_folder(item_path)

    def create_new_folder(self, parent_folder_path):
        folder_name, ok = QInputDialog.getText(self, "Новая папка", "Введите имя папки:")
        if ok and folder_name:
            new_folder_path = os.path.join(parent_folder_path, folder_name)

            if os.path.exists(new_folder_path):
                QMessageBox.warning(self, "Папка существует", "Папка с таким именем уже существует.")
                return

            try:
                os.makedirs(new_folder_path)
                QMessageBox.information(self, "Папка создана", f"Папка {folder_name} создана.")
                self.build_project_tree(self.current_dir_path)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать папку:\n{e}")
    def create_new_file_in_folder(self, parent_folder_path):
        text, ok = QInputDialog.getText(self, "Новый файл", "Введите имя файла:")
        if ok and text:
            if not text.lower()[-3:] == ".md":
                text += ".md"
            new_file_path = os.path.join(parent_folder_path, text)
            if os.path.exists(new_file_path):
                QMessageBox.warning(self, "Файл существует", "Файл с таким именем уже существует.")
                return
            try:
                with open(new_file_path, "w", encoding="utf-8") as f:
                    f.write("# Новый файл\n")
                QMessageBox.information(self, "Файл создан", f"Файл {text} создан.")
                self.build_project_tree(self.current_dir_path)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать файл:\n{e}")
    def load_markdown_file(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Выберите Markdown файл", "", "Markdown Files (*.md)")
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.textEdit.setPlainText(content)
                self.current_file_path = file_path
                self.update_preview()
                self.textEdit.setReadOnly(False)
                self.textEdit.setPlaceholderText("Введите текст здесь...")
                self.setWindowTitle(f"Gestein - {os.path.basename(file_path)}")
            config_path = "config.json"
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            else:
                config = {}

            config["lastOpenFile"] = file_path

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")

    def load_dir(self):
        config_path = "config.json"
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            QMessageBox.warning(self, "Ошибка", "Файл конфигурации не найден.")
            return

        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку проекта")
        if not folder_path:
            return
        config["kartei"] = folder_path
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)


        self.textEdit.clear()
        print('dir', folder_path)
        self.build_project_tree(folder_path)
        self.setWindowTitle("Gestein")
        self.current_file_path = None
        self.textEdit.setPlaceholderText("Выберите файл для редактирования")
        self.textEdit.setReadOnly(True)
        self.watcher = ProjectFolderWatcher(folder_path)
        self.watcher.file_changed.connect(self.handle_folder_change)
        self.watcher.start()



    def save_markdown_file(self):
        if self.current_file_path:
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(self.textEdit.toPlainText())
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как Markdown", "", "Markdown Files (*.md);;All Files (*)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.textEdit.toPlainText())
            self.current_file_path = file_path
            QMessageBox.information(self, "Успех", "Файл сохранён.")
    def export_to_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как PDF", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            self.webView.export_to_pdf(file_path)
            QMessageBox.information(self, "Успех", "PDF успешно сохранён.")
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
            html = markdown.markdown(line).replace("<p>", "").replace("</p>", "")
            if i == current_line:
                cls = "active-line"
            else:
                cls = ""
            html_lines.append(f"<div class='{cls}'>{html}</div>")
        self.webView.setHtmlContent("\n".join(html_lines))

    def handle_folder_change(self):
        self.build_project_tree(self.current_dir_path)

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
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    config_path = "config.json"
    config = {}

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        QMessageBox.warning(None, "Error", "Config corrupted")

    if not config.get("kartei"):
        # print('kartei is empty')
        selection_window = ProjectSelectionWindow()
        selection_window.show()
    else:
        # print('kartei is filled')
        editor_window = MarkdownEditor(config.get("kartei"))
        editor_window.show()

    sys.exit(app.exec())