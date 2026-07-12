"""prevent active overtime request overlaps

Revision ID: c4f8a1d2e6b9
Revises: b3f4c6d8e9a1
Create Date: 2026-07-12 00:00:00.000000
"""

from alembic import op


revision = "c4f8a1d2e6b9"
down_revision = "b3f4c6d8e9a1"
branch_labels = None
depends_on = None

CONSTRAINT_NAME = "excl_overtime_requests_active_overlap"


def upgrade() -> None:
    bind = op.get_bind()
    overlap = bind.exec_driver_sql(
        """
        SELECT first_request.id, second_request.id
        FROM overtime_requests AS first_request
        JOIN overtime_requests AS second_request
          ON first_request.id < second_request.id
         AND first_request.company_id = second_request.company_id
         AND first_request.technician_id = second_request.technician_id
         AND first_request.work_date = second_request.work_date
         AND first_request.entry_time < second_request.exit_time
         AND first_request.exit_time > second_request.entry_time
        WHERE first_request.status IN ('pending', 'approved', 'adjusted')
          AND second_request.status IN ('pending', 'approved', 'adjusted')
        LIMIT 1
        """
    ).first()
    if overlap is not None:
        raise RuntimeError(
            "No se puede crear la restricción de solapamiento: existen solicitudes "
            "activas solapadas. Resuelva los datos manualmente antes de reintentar."
        )

    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        f"""
        ALTER TABLE overtime_requests
        ADD CONSTRAINT {CONSTRAINT_NAME}
        EXCLUDE USING gist (
            company_id WITH =,
            technician_id WITH =,
            tsrange(work_date + entry_time, work_date + exit_time, '[)') WITH &&
        )
        WHERE (status IN ('pending', 'approved', 'adjusted'))
        """
    )


def downgrade() -> None:
    op.execute(
        f"ALTER TABLE overtime_requests DROP CONSTRAINT {CONSTRAINT_NAME}"
    )
