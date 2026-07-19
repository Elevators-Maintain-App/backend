import uuid

from sqlalchemy import Column, ForeignKey, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class PdfReportGenerationEvent(Base):
    __tablename__ = "pdf_report_generation_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companias.id"), nullable=False, index=True)
    orden_id = Column(UUID(as_uuid=True), ForeignKey("ordenes_de_trabajo.id"), nullable=True, index=True)
    checklist_id = Column(
        UUID(as_uuid=True),
        ForeignKey("checklists.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    report_type = Column(String, nullable=False)
    storage_url = Column(String, nullable=True)
    status = Column(String, nullable=False, default="success", server_default="success", index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)

    checklist = relationship(
        "Checklist",
        back_populates="pdf_report_generation_events",
    )
