import uuid

from sqlalchemy import Boolean, Column, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    code = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    max_admins = Column(Integer, nullable=True)
    max_supervisors = Column(Integer, nullable=True)
    max_technicians = Column(Integer, nullable=True)
    max_projects = Column(Integer, nullable=True)
    max_clients = Column(Integer, nullable=True)
    max_units = Column(Integer, nullable=True)
    max_work_orders_per_month = Column(Integer, nullable=True)
    max_pdf_reports_per_month = Column(Integer, nullable=True)
    storage_limit_mb = Column(Integer, nullable=True)
    allow_offline_mode = Column(Boolean, nullable=False, default=False, server_default="false")
    allow_custom_checklists = Column(Boolean, nullable=False, default=False, server_default="false")
    allow_advanced_dashboard = Column(Boolean, nullable=False, default=False, server_default="false")
    allow_evidence_editing = Column(Boolean, nullable=False, default=False, server_default="false")
    is_public = Column(Boolean, nullable=False, default=True, server_default="true")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    subscriptions = relationship("CompanySubscription", back_populates="plan")

