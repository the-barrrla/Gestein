from PyQt6.QtWebEngineWidgets import QWebEngineView

from template import HTML_TEMPLATE


class EditableWebEngineView(QWebEngineView):  # html window
    def __init__(self, parent=None):
        super().__init__(parent)

    def generate_full_html(self, body_content):
        return HTML_TEMPLATE.format(body_content=body_content)

    def setHtmlContent(self, html_content):
        self.setHtml(self.generate_full_html(html_content))

    def export_to_pdf(self, file_path):
        self.page().printToPdf(file_path)
