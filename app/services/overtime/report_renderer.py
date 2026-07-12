from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML


class OvertimePdfRenderer:
    def __init__(self, template_dir: Path | None = None):
        self.template_dir = template_dir or Path(__file__).resolve().parents[2] / "templates"
        self.environment = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(("html", "xml")),
        )

    def render(self, context: dict) -> bytes:
        html = self.environment.get_template("overtime_requests_report.html").render(**context)
        return HTML(string=html, base_url=str(self.template_dir)).write_pdf()
