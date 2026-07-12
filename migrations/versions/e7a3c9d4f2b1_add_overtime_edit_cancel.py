"""add overtime edit and cancellation states and events

Revision ID: e7a3c9d4f2b1
Revises: c4f8a1d2e6b9
Create Date: 2026-07-12 00:00:00.000000
"""

from alembic import op
from sqlalchemy import text


revision = "e7a3c9d4f2b1"
down_revision = "c4f8a1d2e6b9"
branch_labels = None
depends_on = None

OVERLAP_CONSTRAINT = "excl_overtime_requests_active_overlap"


def upgrade() -> None:
    op.execute("ALTER TYPE overtime_request_status ADD VALUE IF NOT EXISTS 'cancelled'")
    op.execute("ALTER TYPE overtime_request_event_type ADD VALUE IF NOT EXISTS 'edited'")
    op.execute("ALTER TYPE overtime_request_event_type ADD VALUE IF NOT EXISTS 'cancelled'")


def downgrade() -> None:
    bind = op.get_bind()
    blocked = bind.execute(
        text(
            """
            SELECT
                EXISTS (
                    SELECT 1 FROM overtime_requests WHERE status::text = 'cancelled'
                ) OR EXISTS (
                    SELECT 1 FROM overtime_request_events
                    WHERE event_type::text IN ('edited', 'cancelled')
                       OR previous_status::text = 'cancelled'
                       OR new_status::text = 'cancelled'
                )
            """
        )
    ).scalar_one()
    if blocked:
        raise RuntimeError(
            "No se puede revertir la migración de edición/cancelación: existen solicitudes "
            "o eventos con los nuevos valores de enum. Preserve la auditoría y resuelva "
            "los datos explícitamente antes de reintentar."
        )

    op.execute(f"ALTER TABLE overtime_requests DROP CONSTRAINT {OVERLAP_CONSTRAINT}")
    op.execute("ALTER TABLE overtime_requests ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TYPE overtime_request_status RENAME TO overtime_request_status_old")
    op.execute(
        "CREATE TYPE overtime_request_status AS ENUM "
        "('pending', 'approved', 'adjusted', 'rejected')"
    )
    op.execute(
        "ALTER TABLE overtime_requests ALTER COLUMN status TYPE overtime_request_status "
        "USING status::text::overtime_request_status"
    )
    op.execute(
        "ALTER TABLE overtime_request_events ALTER COLUMN previous_status "
        "TYPE overtime_request_status USING previous_status::text::overtime_request_status"
    )
    op.execute(
        "ALTER TABLE overtime_request_events ALTER COLUMN new_status "
        "TYPE overtime_request_status USING new_status::text::overtime_request_status"
    )
    op.execute("ALTER TABLE overtime_requests ALTER COLUMN status SET DEFAULT 'pending'")
    op.execute("DROP TYPE overtime_request_status_old")

    op.execute("ALTER TYPE overtime_request_event_type RENAME TO overtime_request_event_type_old")
    op.execute(
        "CREATE TYPE overtime_request_event_type AS ENUM "
        "('submitted', 'approved', 'adjusted_and_approved', 'rejected')"
    )
    op.execute(
        "ALTER TABLE overtime_request_events ALTER COLUMN event_type "
        "TYPE overtime_request_event_type USING event_type::text::overtime_request_event_type"
    )
    op.execute("DROP TYPE overtime_request_event_type_old")

    op.execute(
        f"""
        ALTER TABLE overtime_requests
        ADD CONSTRAINT {OVERLAP_CONSTRAINT}
        EXCLUDE USING gist (
            company_id WITH =,
            technician_id WITH =,
            tsrange(work_date + entry_time, work_date + exit_time, '[)') WITH &&
        )
        WHERE (status IN ('pending', 'approved', 'adjusted'))
        """
    )
