from PyQt6.QtWebEngineWidgets import QWebEngineView


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
        <body contenteditable="true">
            {body_content}
        </body>
        </html>
        """

    def setHtmlContent(self, html_content):
        self.setHtml(self.generate_full_html(html_content))

    def export_to_pdf(self, file_path):
        self.page().printToPdf(file_path)
