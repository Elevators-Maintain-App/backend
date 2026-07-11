import enum
import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Text,
    Time,
    TIMESTAMP,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class OvertimeRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ADJUSTED = "adjusted"
    REJECTED = "rejected"


class OvertimeRequestEventType(str, enum.Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    ADJUSTED_AND_APPROVED = "adjusted_and_approved"
    REJECTED = "rejected"


def _enum_values(enum_class: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_class]


class OvertimeRequest(Base):
    __tablename__ = "overtime_requests"
    __table_args__ = (
        CheckConstraint("exit_time > entry_time", name="ck_overtime_requests_time_order"),
        CheckConstraint(
            "(break_start_time IS NULL AND break_end_time IS NULL) OR "
            "(break_start_time IS NOT NULL AND break_end_time IS NOT NULL)",
            name="ck_overtime_requests_break_pair",
        ),
        CheckConstraint(
            "break_start_time IS NULL OR "
            "(break_start_time >= entry_time AND break_end_time > break_start_time "
            "AND break_end_time <= exit_time)",
            name="ck_overtime_requests_break_bounds",
        ),
        CheckConstraint("worked_minutes > 0", name="ck_overtime_requests_worked_positive"),
        CheckConstraint(
            "regular_minutes >= 0 AND regular_minutes <= 480",
            name="ck_overtime_requests_regular_range",
        ),
        CheckConstraint("overtime_minutes >= 0", name="ck_overtime_requests_overtime_nonnegative"),
        CheckConstraint(
            "worked_minutes = regular_minutes + overtime_minutes",
            name="ck_overtime_requests_minutes_total",
        ),
        CheckConstraint(
            "regular_minutes = LEAST(worked_minutes, 480)",
            name="ck_overtime_requests_regular_formula",
        ),
        CheckConstraint(
            "overtime_minutes = GREATEST(worked_minutes - 480, 0)",
            name="ck_overtime_requests_overtime_formula",
        ),
        Index("ix_overtime_requests_company_status", "company_id", "status"),
        Index("ix_overtime_requests_technician_work_date", "technician_id", "work_date"),
        Index(
            "ix_overtime_requests_supervisor_status",
            "authorizing_supervisor_id",
            "status",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companias.id"), nullable=False, index=True)
    technician_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True)
    work_date = Column(Date, nullable=False, index=True)
    entry_time = Column(Time, nullable=False)
    break_start_time = Column(Time, nullable=True)
    break_end_time = Column(Time, nullable=True)
    exit_time = Column(Time, nullable=False)
    activity = Column(Text, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=False)
    authorizing_supervisor_id = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True
    )
    worked_minutes = Column(Integer, nullable=False)
    regular_minutes = Column(Integer, nullable=False)
    overtime_minutes = Column(Integer, nullable=False)
    status = Column(
        Enum(
            OvertimeRequestStatus,
            name="overtime_request_status",
            values_callable=_enum_values,
        ),
        nullable=False,
        default=OvertimeRequestStatus.PENDING,
        server_default=OvertimeRequestStatus.PENDING.value,
        index=True,
    )
    submitted_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), index=True)
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    reviewed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    supervisor_note = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    company = relationship("Compania", foreign_keys=[company_id])
    technician = relationship("Usuario", foreign_keys=[technician_id])
    project = relationship("Proyecto", foreign_keys=[project_id])
    authorizing_supervisor = relationship("Usuario", foreign_keys=[authorizing_supervisor_id])
    reviewed_by_user = relationship("Usuario", foreign_keys=[reviewed_by_user_id])
    events = relationship(
        "OvertimeRequestEvent",
        back_populates="overtime_request",
        order_by="OvertimeRequestEvent.created_at",
    )


class OvertimeRequestEvent(Base):
    __tablename__ = "overtime_request_events"
    __table_args__ = (
        Index("ix_overtime_request_events_request_created", "overtime_request_id", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    overtime_request_id = Column(
        UUID(as_uuid=True), ForeignKey("overtime_requests.id"), nullable=False, index=True
    )
    company_id = Column(UUID(as_uuid=True), ForeignKey("companias.id"), nullable=False, index=True)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True)
    event_type = Column(
        Enum(
            OvertimeRequestEventType,
            name="overtime_request_event_type",
            values_callable=_enum_values,
        ),
        nullable=False,
    )
    previous_status = Column(
        Enum(
            OvertimeRequestStatus,
            name="overtime_request_status",
            values_callable=_enum_values,
            create_type=False,
        ),
        nullable=True,
    )
    new_status = Column(
        Enum(
            OvertimeRequestStatus,
            name="overtime_request_status",
            values_callable=_enum_values,
            create_type=False,
        ),
        nullable=False,
    )
    note = Column(Text, nullable=True)
    snapshot_before = Column(JSONB, nullable=True)
    snapshot_after = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    overtime_request = relationship("OvertimeRequest", back_populates="events")
    company = relationship("Compania", foreign_keys=[company_id])
    actor_user = relationship("Usuario", foreign_keys=[actor_user_id])
