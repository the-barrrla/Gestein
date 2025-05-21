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
    QSplitter, QScrollArea, QColorDialog, QComboBox, QListWidget, QListWidgetItem, QTreeWidgetItem, QDialog
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.uic import loadUi
import re

# doesn't work without this on older machines. with qt6.9.0
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-gpu-compositing'

class ProjectFolderWatcher(QThread): # сигнал про обновление папок (а у меня нет папы)
    file_changed = pyqtSignal()

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.observer = Observer()
        self.event_handler = FileSystemEventHandler()
        self.event_handler.on_modified = self.on_file_modified
        self.event_handler.on_created = self.on_file_created
        self.event_handler.on_deleted = self.on_file_deleted

    def on_file_modified(self, event):
        self.file_changed.emit()

    def on_file_created(self, event):
        self.file_changed.emit()

    def on_file_deleted(self, event):
        self.file_changed.emit()

    def run(self):
        self.observer.schedule(self.event_handler, self.folder_path, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

    def stop(self):
        self.observer.stop()
        self.wait()


class EditableWebEngineView(QWebEngineView):  # html window
    def __init__(self, parent=None):
        super().__init__(parent)

    def generate_full_html(self, body_content):  # html template
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
        <body>
            {body_content}
        </body>
        </html>
        """

    def setHtmlContent(self, html_content):  # set html
        self.setHtml(self.generate_full_html(html_content))

    def export_to_pdf(self, file_path):  # export html to pdf
        self.page().printToPdf(file_path)


class ProjectSelectionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Выбор папки проекта")
        self.setGeometry(100, 100, 400, 200)

        # combining a layout (redo in ui later)
        self.widget = QWidget()
        self.setCentralWidget(self.widget)
        layout = QVBoxLayout()
        self.folder_label = QLabel("Папка проекта не выбрана.")
        layout.addWidget(self.folder_label)
        self.select_button = QPushButton("Выбрать папку проекта")
        layout.addWidget(self.select_button)
        self.widget.setLayout(layout)

        # сигнал
        self.select_button.clicked.connect(self.select_project_folder)


    def select_project_folder(self): # пока не особо (вообще) работает
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку проекта")
        if folder:
            config_path = "config.json"
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

            config["kartei"] = folder
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4) # запомнить проект открытый
            self.open_main_window() # ???????


class MarkdownEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("main.ui", self)
        self.setWindowTitle("Gestein")
        self.current_file_path = None
        self.recent_files = []

        # выбор картотеки
        self.project_folder = self.select_project_folder()

        # отмена если отмена
        if not self.project_folder:
            return

        # mapping signals to buttons
        self.actionNewFile.triggered.connect(self.create_new_file)
        self.actionOpen.triggered.connect(self.load_markdown_file)
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

        # tree clicks
        self.treeWidget.itemClicked.connect(self.on_tree_item_clicked)

        #
        self.build_project_tree(self.project_folder)

    def on_tree_item_clicked(self, item, column):
        file_path = item.toolTip(0)  # Получаем полный путь к файлу
        if file_path.endswith(".md") and os.path.exists(file_path):
            self.load_markdown_file(file_path)

    def select_project_folder(self): # а класс?
        config_path = "config.json"
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            QMessageBox.warning(self, "Error", "Config corrupted")
            return None

        if not config.get("kartei"):
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            folder = QFileDialog.getExistingDirectory(self, "Выберите папку проекта", desktop_path)
            if folder:
                config["kartei"] = folder
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
                return folder
            else:
                QMessageBox.warning(self, "Внимание", "Папка проекта не выбрана.")
                return None
        return config["kartei"]

    def build_project_tree(self, root_path):
        self.treeWidget.clear()

        def add_items(parent, path):
            for name in sorted(os.listdir(path)):
                abs_path = os.path.join(path, name)
                item = QTreeWidgetItem([name])
                item.setToolTip(0, abs_path)
                parent.addChild(item)
                if os.path.isdir(abs_path):
                    add_items(item, abs_path)

        root_item = QTreeWidgetItem([os.path.basename(root_path)])
        root_item.setToolTip(0, root_path)
        self.treeWidget.addTopLevelItem(root_item)
        add_items(root_item, root_path)
        self.treeWidget.expandAll()

    def add_to_recent_files(self, file_path):
        if file_path not in self.recent_files:
            self.recent_files.append(file_path)
            item = QListWidgetItem(os.path.basename(file_path))
            item.setToolTip(file_path)
            self.file_list.addItem(item)

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
                self.add_to_recent_files(file_path)
                self.update_preview()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")

    def create_new_file(self): # redo l8r
        self.current_file_path = None
        self.textEdit.clear()

    def save_markdown_file(self):
        if self.current_file_path:
            try:
                with open(self.current_file_path, "w", encoding="utf-8") as f:
                    f.write(self.textEdit.toPlainText())
                # QMessageBox.information(self, "Успешно", "Файл сохранён.")
                return
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении:\n{e}")
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как Markdown", "", "Markdown Files (*.md);;All Files (*)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.textEdit.toPlainText())
                self.current_file_path = file_path
                self.add_to_recent_files(file_path)
                QMessageBox.information(self, "Успех", "Файл сохранён.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{e}")

    def export_to_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как PDF", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            try:
                self.webView.export_to_pdf(file_path)
                QMessageBox.information(self, "Успешно", "PDF успешно сохранён.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать в PDF:\n{e}")

    def make_bold(self): # сделать обратно
        cursor = self.textEdit.textCursor()
        if cursor.hasSelection():
            matches = re.findall(r"(^\*{2,3}([^*]+)\*{2,3}$)",
                                 cursor.selectedText())
            if not matches:
                cursor.insertText(f"**{cursor.selectedText()}**") # blod if not

    def make_italic(self):
        cursor = self.textEdit.textCursor()
        if cursor.hasSelection():
            matches = re.findall(r"(^\*|\*{3})([^*]+)(\*|\*{3}$)",
                                 cursor.selectedText())
            if not matches:
                cursor.insertText(f"*{cursor.selectedText()}*") # italic if not

    def insert_heading(self, index):
        cursor = self.textEdit.textCursor()
        level = index
        text = cursor.selectedText() or "Заголовок"
        cursor.insertText(f"{'#' * level} {text}\n")

    def update_preview(self):
        md_text = self.textEdit.toPlainText()
        lines = md_text.splitlines()
        cursor = self.textEdit.textCursor()
        current_line = cursor.blockNumber()  # Получаем номер текущей строки
        html_lines = []
        for i, line in enumerate(lines):
            html = markdown.markdown(line).replace("<p>", "").replace("</p>", "")
            if i == current_line:
                cls = "active-line"
            else:
                cls = ""
            html_lines.append(f"<div class='{cls}'>{html}</div>")
        self.webView.setHtmlContent("\n".join(html_lines))

    def closeEvent(self, event):
        if hasattr(self, 'watcher'):
            self.watcher.stop()

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите выйти?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MarkdownEditor()
    window.show()
    sys.exit(app.exec())