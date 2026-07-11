"""add overtime requests and immutable events

Revision ID: 7b8d4f2c1a90
Revises: 2c9f7e3b4a1d
Create Date: 2026-07-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "7b8d4f2c1a90"
down_revision = "2c9f7e3b4a1d"
branch_labels = None
depends_on = None


request_status = postgresql.ENUM(
    "pending", "approved", "adjusted", "rejected", name="overtime_request_status", create_type=False
)
event_type = postgresql.ENUM(
    "submitted",
    "approved",
    "adjusted_and_approved",
    "rejected",
    name="overtime_request_event_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    request_status.create(bind, checkfirst=True)
    event_type.create(bind, checkfirst=True)

    op.create_table(
        "overtime_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("technician_id", sa.UUID(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("entry_time", sa.Time(), nullable=False),
        sa.Column("break_start_time", sa.Time(), nullable=True),
        sa.Column("break_end_time", sa.Time(), nullable=True),
        sa.Column("exit_time", sa.Time(), nullable=False),
        sa.Column("activity", sa.Text(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("authorizing_supervisor_id", sa.UUID(), nullable=False),
        sa.Column("worked_minutes", sa.Integer(), nullable=False),
        sa.Column("regular_minutes", sa.Integer(), nullable=False),
        sa.Column("overtime_minutes", sa.Integer(), nullable=False),
        sa.Column("status", request_status, server_default="pending", nullable=False),
        sa.Column("submitted_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", sa.UUID(), nullable=True),
        sa.Column("supervisor_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("exit_time > entry_time", name="ck_overtime_requests_time_order"),
        sa.CheckConstraint(
            "(break_start_time IS NULL AND break_end_time IS NULL) OR "
            "(break_start_time IS NOT NULL AND break_end_time IS NOT NULL)",
            name="ck_overtime_requests_break_pair",
        ),
        sa.CheckConstraint(
            "break_start_time IS NULL OR (break_start_time >= entry_time AND "
            "break_end_time > break_start_time AND break_end_time <= exit_time)",
            name="ck_overtime_requests_break_bounds",
        ),
        sa.CheckConstraint("worked_minutes > 0", name="ck_overtime_requests_worked_positive"),
        sa.CheckConstraint(
            "regular_minutes >= 0 AND regular_minutes <= 480",
            name="ck_overtime_requests_regular_range",
        ),
        sa.CheckConstraint("overtime_minutes >= 0", name="ck_overtime_requests_overtime_nonnegative"),
        sa.CheckConstraint(
            "worked_minutes = regular_minutes + overtime_minutes",
            name="ck_overtime_requests_minutes_total",
        ),
        sa.CheckConstraint(
            "regular_minutes = LEAST(worked_minutes, 480)",
            name="ck_overtime_requests_regular_formula",
        ),
        sa.CheckConstraint(
            "overtime_minutes = GREATEST(worked_minutes - 480, 0)",
            name="ck_overtime_requests_overtime_formula",
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companias.id"], name="fk_overtime_requests_company"),
        sa.ForeignKeyConstraint(["technician_id"], ["usuarios.id"], name="fk_overtime_requests_technician"),
        sa.ForeignKeyConstraint(["project_id"], ["proyectos.id"], name="fk_overtime_requests_project"),
        sa.ForeignKeyConstraint(
            ["authorizing_supervisor_id"], ["usuarios.id"], name="fk_overtime_requests_authorizing_supervisor"
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"], ["usuarios.id"], name="fk_overtime_requests_reviewed_by"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_overtime_requests"),
    )
    for name, columns in (
        ("ix_overtime_requests_company_id", ["company_id"]),
        ("ix_overtime_requests_technician_id", ["technician_id"]),
        ("ix_overtime_requests_authorizing_supervisor_id", ["authorizing_supervisor_id"]),
        ("ix_overtime_requests_work_date", ["work_date"]),
        ("ix_overtime_requests_status", ["status"]),
        ("ix_overtime_requests_submitted_at", ["submitted_at"]),
        ("ix_overtime_requests_company_status", ["company_id", "status"]),
        ("ix_overtime_requests_technician_work_date", ["technician_id", "work_date"]),
        ("ix_overtime_requests_supervisor_status", ["authorizing_supervisor_id", "status"]),
    ):
        op.create_index(name, "overtime_requests", columns, unique=False)

    op.create_table(
        "overtime_request_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("overtime_request_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("actor_user_id", sa.UUID(), nullable=False),
        sa.Column("event_type", event_type, nullable=False),
        sa.Column("previous_status", request_status, nullable=True),
        sa.Column("new_status", request_status, nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("snapshot_before", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("snapshot_after", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["overtime_request_id"], ["overtime_requests.id"], name="fk_overtime_request_events_request"
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companias.id"], name="fk_overtime_request_events_company"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["usuarios.id"], name="fk_overtime_request_events_actor"),
        sa.PrimaryKeyConstraint("id", name="pk_overtime_request_events"),
    )
    op.create_index("ix_overtime_request_events_overtime_request_id", "overtime_request_events", ["overtime_request_id"])
    op.create_index("ix_overtime_request_events_company_id", "overtime_request_events", ["company_id"])
    op.create_index("ix_overtime_request_events_actor_user_id", "overtime_request_events", ["actor_user_id"])
    op.create_index(
        "ix_overtime_request_events_request_created",
        "overtime_request_events",
        ["overtime_request_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("overtime_request_events")
    op.drop_table("overtime_requests")
    bind = op.get_bind()
    event_type.drop(bind, checkfirst=True)
    request_status.drop(bind, checkfirst=True)
