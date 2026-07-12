from datetime import date, datetime, timezone
from types import SimpleNamespace

from app.db.models.overtime_requests import OvertimeRequestStatus
from app.services.overtime.report_renderer import OvertimePdfRenderer
from app.services.overtime.request_service import OvertimeRequestService


def test_renderer_autoescapes_user_content_and_creates_valid_pdf():
    row = SimpleNamespace(
        technician_id="tech-1",
        technician=SimpleNamespace(display_name="Técnico <Uno>"),
        project=SimpleNamespace(nombre="Proyecto & prueba"),
        work_date=date(2026, 7, 8),
        entry_time=datetime.strptime("08:00", "%H:%M").time(),
        exit_time=datetime.strptime("17:00", "%H:%M").time(),
        break_start_time=None,
        break_end_time=None,
        activity="<script>alert('x')</script>",
        worked_minutes=1500,
        regular_minutes=480,
        overtime_minutes=1020,
        status=OvertimeRequestStatus.CANCELLED,
    )
    supervisor = SimpleNamespace()
    context = OvertimeRequestService._build_pdf_context(
        rows=[row], supervisor=supervisor, status=None, technician_id=None,
        date_from=date(2026, 7, 1), date_to=date(2026, 7, 8),
        generated_at=datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc),
    )
    renderer = OvertimePdfRenderer()
    html = renderer.environment.get_template("overtime_requests_report.html").render(**context)
    assert "&lt;script&gt;" in html
    assert "<script>" not in html
    assert "25:00" in html
    assert "No aplica" in html
    pdf = renderer.render(context)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def test_empty_context_renders_message_and_zero_total_pdf():
    context = OvertimeRequestService._build_pdf_context(
        rows=[], supervisor=SimpleNamespace(), status=None, technician_id=None,
        date_from=date(2026, 7, 1), date_to=date(2026, 7, 8),
        generated_at=datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc),
    )
    renderer = OvertimePdfRenderer()
    html = renderer.environment.get_template("overtime_requests_report.html").render(**context)
    assert "No se encontraron solicitudes" in html
    assert context["grand_total"]["count"] == 0
    assert context["grand_total"]["overtime"] == "00:00"
    assert renderer.render(context).startswith(b"%PDF")
