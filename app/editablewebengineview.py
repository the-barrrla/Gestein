from PyQt6.QtWebEngineWidgets import QWebEngineView
from app.template import HTML_TEMPLATE


class EditableWebEngineView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)

    @staticmethod
    def generate_full_html(body_content):
        return HTML_TEMPLATE.format(body_content=body_content)

    def set_html_content(self, html_content, highlight=True):
        if not highlight:
            html_content = html_content.replace("class='active-line'", "")
        self.setHtml(self.generate_full_html(html_content))

    def export_to_pdf(self, file_path):
        self.page().printToPdf(file_path)
