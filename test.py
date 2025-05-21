import sys
import os
import markdown
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QFileDialog, QPushButton, QMessageBox, QTextEdit, QLabel,
    QSplitter, QScrollArea, QColorDialog, QComboBox, QListWidget, QListWidgetItem
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.uic import loadUi
import re

# doesn't work without this on older machines. with qt6.9.0
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-gpu-compositing'


class EditableWebEngineView(QWebEngineView):  # html window
    def __init__(self, parent=None):
        super().__init__(parent)

    # так у нас контентэдитбл или как???
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
        <body contenteditable="true">
            {body_content}
        </body>
        </html>
        """

    def setHtmlContent(self, html_content):  # set html
        self.setHtml(self.generate_full_html(html_content))

    def export_to_pdf(self, file_path):  # export html to pdf
        self.page().printToPdf(file_path)

class MarkdownEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("main.ui", self) # loading ui from designer
        self.setWindowTitle("Gestein")
        self.current_file_path = None  # initiating empty file path
        self.recent_files = []  # initiating empty recent files
        # mapping signals to buttons
        self.actionNewFile.triggered.connect(self.create_new_file)
        self.actionOpen.triggered.connect(self.load_markdown_file)
        self.actionSave.triggered.connect(self.save_markdown_file)
        self.actionPDF.triggered.connect(self.export_to_pdf)
        self.actionBold.triggered.connect(self.make_bold)
        self.actionItalic.triggered.connect(self.make_italic)
        self.actionUnderline.triggered.connect(self.make_underline)
        # self.actionSetColor.triggered.connect(self.make_color)
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.load_file_from_list)
        self.actionHeader1.triggered.connect(lambda: self.insert_heading(1))
        self.actionHeader2.triggered.connect(lambda: self.insert_heading(2))
        self.actionHeader3.triggered.connect(lambda: self.insert_heading(3))
        self.actionHeader4.triggered.connect(lambda: self.insert_heading(4))
        self.actionHeader5.triggered.connect(lambda: self.insert_heading(5))
        self.actionHeader6.triggered.connect(lambda: self.insert_heading(6))
        # automatically update preview on ALL text edits (even only with cursor!!!)
        self.textEdit.textChanged.connect(self.update_preview)
        self.textEdit.cursorPositionChanged.connect(self.update_preview)
        self.update_preview()
    def add_to_recent_files(self, file_path):
        if file_path not in self.recent_files:
            self.recent_files.append(file_path)
            item = QListWidgetItem(os.path.basename(file_path))
            item.setToolTip(file_path)
            self.file_list.addItem(item)
    def load_file_from_list(self, item):
        file_path = item.toolTip()
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                self.textEdit.setPlainText(f.read())
                self.current_file_path = file_path
                self.update_preview()
        else:
            QMessageBox.warning(self, "Ошибка", "Файл не существует или был удалён.")
            self.file_list.takeItem(self.file_list.row(item))
            self.recent_files.remove(file_path)
    def create_new_file(self):
        self.current_file_path = None
        self.textEdit.clear()
    def load_markdown_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите Markdown файл", "", "Markdown Files (*.md)")
        if not file_path: # if cancel
            return
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.textEdit.setPlainText(content)
            self.current_file_path = file_path
            self.add_to_recent_files(file_path)
            self.update_preview()
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
            self.webView.export_to_pdf(file_path)
            QMessageBox.information(self, "Успешно", "PDF экспорт успешно сохранён.")
    def make_bold(self):
        cursor = self.textEdit.textCursor()
        if cursor.hasSelection():
            matches = re.findall(r"(^\*{2,3}([^*]+)\*{2,3}$)", # you can't bold the bold
                                 cursor.selectedText())
            if not matches:
                cursor.insertText(f"**{cursor.selectedText()}**")
    def make_italic(self):
        cursor = self.textEdit.textCursor()
        if cursor.hasSelection():
            matches = re.findall(r"(^\*|\*{3})([^*]+)(\*|\*{3}$)", # you can't italic the italic
                                 cursor.selectedText())
            if not matches:
                cursor.insertText(f"*{cursor.selectedText()}*")
    def make_underline(self): # deprecated
        cursor = self.textEdit.textCursor()
        if cursor.hasSelection():
            cursor.insertText(f"<u>{cursor.selectedText()}</u>")
    """def make_color(self): also deprecated!!!!!!!
        color = QColorDialog.getColor()
        if color.isValid():
            cursor = self.textEdit.textCursor()
            if cursor.hasSelection():
                cursor.insertText(f"<span style='color:{color.name()}'>{cursor.selectedText()}</span>")"""
    def insert_heading(self, index): # оно разве так работает?
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
    def closeEvent(self, event):
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