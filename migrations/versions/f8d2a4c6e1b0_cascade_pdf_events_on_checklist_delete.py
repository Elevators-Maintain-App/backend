"""cascade pdf events on checklist delete

Revision ID: f8d2a4c6e1b0
Revises: e7a3c9d4f2b1
Create Date: 2026-07-18 00:00:00.000000
"""

from alembic import op


revision = "f8d2a4c6e1b0"
down_revision = "e7a3c9d4f2b1"
branch_labels = None
depends_on = None


FK_NAME = "pdf_report_generation_events_checklist_id_fkey"


def upgrade() -> None:
    op.drop_constraint(FK_NAME, "pdf_report_generation_events", type_="foreignkey")
    op.create_foreign_key(
        FK_NAME,
        "pdf_report_generation_events",
        "checklists",
        ["checklist_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(FK_NAME, "pdf_report_generation_events", type_="foreignkey")
    op.create_foreign_key(
        FK_NAME,
        "pdf_report_generation_events",
        "checklists",
        ["checklist_id"],
        ["id"],
    )
