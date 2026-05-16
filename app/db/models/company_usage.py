import uuid

from sqlalchemy import Column, ForeignKey, Integer, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class CompanyUsage(Base):
    __tablename__ = "company_usage"
    __table_args__ = (
        UniqueConstraint("company_id", "period_year", "period_month", name="uq_company_usage_company_period"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companias.id"), nullable=False, index=True)
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=False)
    users_count = Column(Integer, nullable=False, default=0, server_default="0")
    admins_count = Column(Integer, nullable=False, default=0, server_default="0")
    supervisors_count = Column(Integer, nullable=False, default=0, server_default="0")
    technicians_count = Column(Integer, nullable=False, default=0, server_default="0")
    projects_count = Column(Integer, nullable=False, default=0, server_default="0")
    clients_count = Column(Integer, nullable=False, default=0, server_default="0")
    units_count = Column(Integer, nullable=False, default=0, server_default="0")
    work_orders_created = Column(Integer, nullable=False, default=0, server_default="0")
    pdf_reports_generated = Column(Integer, nullable=False, default=0, server_default="0")
    storage_used_mb = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    company = relationship("Compania", back_populates="usage_periods")

