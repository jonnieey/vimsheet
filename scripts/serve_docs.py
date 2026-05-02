import http.server
import os
import re
import urllib.parse
from pathlib import Path

import markdown

# DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
DOCS_DIR = Path(__file__).parent.parent / "docs"

MD_EXTENSIONS = ["extra", "toc", "tables", "fenced_code", "codehilite"]

NAV_HTML = """
<nav style="background:#1a1a2e;padding:8px 16px;margin-bottom:16px;border-radius:6px;">
  <a href="/" style="color:#e94560;font-weight:bold;margin-right:16px;">Home</a>
  <span style="color:#888;">PySheet Docs</span>
</nav>
"""

FOOTER_HTML = """
<hr>
<footer style="color:#888;font-size:0.85em;padding:8px 0;">
  PySheet Documentation
</footer>
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        Helvetica, Arial, sans-serif;
      line-height: 1.6;
      color: #e0e0e0;
      background: #0f0f23;
      max-width: 900px;
      margin: 0 auto;
      padding: 20px;
    }}
    a {{ color: #64b5f6; }}
    a:visited {{ color: #ce93d8; }}
    h1, h2, h3, h4 {{ color: #e94560; }}
    code {{
      background: #1e1e3f;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.9em;
    }}
    pre {{
      background: #1e1e3f;
      padding: 16px;
      border-radius: 8px;
      overflow-x: auto;
    }}
    pre code {{ background: none; padding: 0; }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin: 16px 0;
    }}
    th, td {{
      border: 1px solid #333;
      padding: 8px 12px;
      text-align: left;
    }}
    th {{ background: #1a1a2e; color: #e94560; }}
    tr:nth-child(even) {{ background: #151530; }}
    blockquote {{
      border-left: 4px solid #e94560;
      margin-left: 0;
      padding-left: 16px;
      color: #aaa;
    }}
    img {{ max-width: 100%; }}
    hr {{ border: none; border-top: 1px solid #333; }}
  </style>
</head>
<body>
  {nav}
  {content}
  {footer}
</body>
</html>"""


def rewrite_md_links(html: str) -> str:
    def _rewrite(m):
        href = m.group(1)
        if href.endswith(".md") and not href.startswith(("http://", "https://", "#")):
            return f'href="{href}"'
        return m.group(0)

    return re.sub(r'href="([^"]+)"', _rewrite, html)


def render_md_to_html(md_path: str) -> str:
    with open(md_path, encoding="utf-8") as f:
        md_text = f.read()
    html_body = markdown.markdown(md_text, extensions=MD_EXTENSIONS)
    html_body = rewrite_md_links(html_body)
    title_match = re.search(r"<h1>(.+?)</h1>", html_body)
    title = title_match.group(1) if title_match else "PySheet Docs"
    return HTML_TEMPLATE.format(
        title=title,
        nav=NAV_HTML,
        content=html_body,
        footer=FOOTER_HTML,
    )


class DocHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DOCS_DIR, **kwargs)

    def guess_type(self, path):
        if path.endswith(".md"):
            return "text/html; charset=utf-8"
        return super().guess_type(path)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "":
            path = "/index.md"

        if path.endswith(".md"):
            fs_path = Path(DOCS_DIR, path.lstrip("/"))
            if not os.path.isfile(fs_path):
                self.send_error(404, "File not found")
                return
            try:
                html = render_md_to_html(fs_path)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html.encode())))
                self.end_headers()
                self.wfile.write(html.encode())
            except Exception as e:
                self.send_error(500, str(e))
            return

        super().do_GET()


if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8080
    print(f"Serving PySheet docs at http://localhost:{port}")
    print(f"  Directory: {DOCS_DIR}")
    httpd = http.server.HTTPServer((host, port), DocHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        httpd.server_close()
