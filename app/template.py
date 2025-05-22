HTML_TEMPLATE = """
<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Optima, "Segoe UI", Arial, sans-serif;
                    margin: 20px;
                    background-color: #f9f9f9;
                    overflow: auto;
                }}
                h1 {{ font-size: 2.0em; }}
                h2 {{ font-size: 1.8em; }}
                h3 {{ font-size: 1.6em; }}
                h4 {{ font-size: 1.4em; }}
                h5 {{ font-size: 1.2em; }}
                h6 {{ font-size: 1.0em; }}

                p {{ font-size: 1.0em; line-height: 1.0; }}
                ul {{ padding-left: 20px; }}
                a {{ color: #0066cc; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                table {{ border-collapse: collapse; width: 100%; }}
                table, th, td {{ border: 1px solid #ddd; padding: 8px; }}
                th {{ background-color: #f2f2f2; }}
                .active-line {{ background-color: #ffffcc;
                 border-left: 4px solid orange; padding-left: 4px; }}
            </style>
        </head>
            {body_content}
        </body>
        </html>
"""
