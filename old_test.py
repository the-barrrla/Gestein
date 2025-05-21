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


class EditableWebEngineView(QWebEngineView):
    def __init__(self):
        super().__init__()

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
                    white-space: pre;
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


class MarkdownEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestein")
        self.setGeometry(100, 100, 1200, 800)

        self.current_file_path = None
        self.recent_files = []

        self.markdown_input = QTextEdit()
        self.markdown_input.setPlaceholderText("Введите Markdown текст здесь...")

        self.preview_browser = EditableWebEngineView()

        self.new_button = QPushButton("Новый файл")
        self.open_button = QPushButton("Открыть Markdown файл")
        self.save_button = QPushButton("Сохранить как Markdown")
        self.export_pdf_button = QPushButton("Экспорт в PDF")

        self.bold_button = QPushButton("B")
        self.bold_button.setStyleSheet("font-weight: bold; font-size: 18px;")

        self.italic_button = QPushButton("I")
        self.italic_button.setStyleSheet("font-style: italic; font-size: 18px;")

        self.underline_button = QPushButton("U")
        self.underline_button.setStyleSheet("text-decoration: underline; font-size: 18px;")

        self.color_button = QPushButton("A")
        self.color_button.setStyleSheet("font-size: 18px;")

        self.heading_combo = QComboBox()
        self.heading_combo.addItems([f"Заголовок {i}" for i in range(1, 7)])
        self.heading_combo.setCurrentIndex(-1)
        self.heading_combo.setPlaceholderText("Заголовок")

        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.load_file_from_list)

        self.new_button.clicked.connect(self.create_new_file)
        self.open_button.clicked.connect(self.load_markdown_file)
        self.save_button.clicked.connect(self.save_markdown_file)
        self.export_pdf_button.clicked.connect(self.export_to_pdf)

        self.markdown_input.textChanged.connect(self.update_preview)

        self.bold_button.clicked.connect(self.make_bold)
        self.italic_button.clicked.connect(self.make_italic)
        self.underline_button.clicked.connect(self.make_underline)
        self.color_button.clicked.connect(self.make_color)
        self.heading_combo.currentIndexChanged.connect(self.insert_heading)


        button_layout = QHBoxLayout()
        for btn in [self.new_button, self.open_button, self.save_button, self.export_pdf_button,
                    self.bold_button, self.italic_button, self.underline_button, self.color_button,
                    self.heading_combo]:
            button_layout.addWidget(btn)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.preview_browser)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.markdown_input)
        splitter.addWidget(scroll_area)
        splitter.setSizes([600, 600])

        editor_preview_layout = QVBoxLayout()
        editor_preview_layout.addLayout(button_layout)
        editor_preview_layout.addWidget(splitter)

        file_sidebar_layout = QVBoxLayout()
        file_sidebar_layout.addWidget(QLabel("Файлы"))
        file_sidebar_layout.addWidget(self.file_list)

        file_sidebar = QWidget()
        file_sidebar.setLayout(file_sidebar_layout)

        editor_preview_widget = QWidget()
        editor_preview_widget.setLayout(editor_preview_layout)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(file_sidebar)
        main_splitter.addWidget(editor_preview_widget)
        main_splitter.setSizes([200, 1000])

        central_layout = QVBoxLayout()
        central_layout.addWidget(main_splitter)
        central_widget = QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

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
                self.markdown_input.setPlainText(f.read())
                self.current_file_path = file_path
                self.update_preview()
        else:
            QMessageBox.warning(self, "Файл не найден", "Файл не существует или был удален.")
            self.file_list.takeItem(self.file_list.row(item))
            self.recent_files.remove(file_path)

    def create_new_file(self):
        self.current_file_path = None
        self.markdown_input.clear()

    def load_markdown_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите Markdown файл", "", "Markdown Files (*.md)")
        if not file_path:
            return
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.markdown_input.setPlainText(content)
            self.current_file_path = file_path
            self.add_to_recent_files(file_path)
            self.update_preview()

    def save_markdown_file(self):
        if self.current_file_path:
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(self.markdown_input.toPlainText())
            QMessageBox.information(self, "Успех", "Файл сохранён.")
            return


        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как Markdown", "", "Markdown Files (*.md);;All Files (*)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.markdown_input.toPlainText())
            self.current_file_path = file_path
            self.add_to_recent_files(file_path)
            QMessageBox.information(self, "Успех", "Файл сохранён.")

    def export_to_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как PDF", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            try:
                self.preview_browser.export_to_pdf(file_path)
                QMessageBox.information(self, "Успешно", "PDF успешно сохранён.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать в PDF:\n{e}")

    def make_bold(self):
        cursor = self.markdown_input.textCursor()
        if cursor.hasSelection():
            cursor.insertText(f"**{cursor.selectedText()}**")

    def make_italic(self):
        cursor = self.markdown_input.textCursor()
        if cursor.hasSelection():
            cursor.insertText(f"*{cursor.selectedText()}*")

    def make_underline(self):
        cursor = self.markdown_input.textCursor()
        if cursor.hasSelection():
            cursor.insertText(f"<u>{cursor.selectedText()}</u>")

    """def make_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            cursor = self.markdown_input.textCursor()
            if cursor.hasSelection():
                cursor.insertText(f"<span style='color:{color.name()}'>{cursor.selectedText()}</span>")"""

    def insert_heading(self, index):
        if index == -1:
            return
        cursor = self.markdown_input.textCursor()
        level = index + 1
        text = cursor.selectedText() or "Заголовок"
        cursor.insertText(f"{'#' * level} {text}\n")
        self.heading_combo.setCurrentIndex(-1)

    def update_preview(self):
        md_text = self.markdown_input.toPlainText()
        lines = md_text.splitlines()
        cursor = self.markdown_input.textCursor()
        current_line = cursor.blockNumber()
        html_lines = []
        for i, line in enumerate(lines):
            html = markdown.markdown(line).replace("<p>", "").replace("</p>", "")
            cls = "active-line" if i == current_line else ""
            html_lines.append(f"<div class='{cls}'>{html}</div>")
        self.preview_browser.setHtmlContent("\n".join(html_lines))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MarkdownEditor()
    window.show()
    sys.exit(app.exec())