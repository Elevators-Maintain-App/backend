"""add pdf report generation events

Revision ID: 2c9f7e3b4a1d
Revises: 9f5ab90ded2a
Create Date: 2026-05-16 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "2c9f7e3b4a1d"
down_revision = "9f5ab90ded2a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pdf_report_generation_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("orden_id", sa.UUID(), nullable=True),
        sa.Column("checklist_id", sa.UUID(), nullable=True),
        sa.Column("report_type", sa.String(), nullable=False),
        sa.Column("storage_url", sa.String(), nullable=True),
        sa.Column("status", sa.String(), server_default="success", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["checklist_id"], ["checklists.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companias.id"]),
        sa.ForeignKeyConstraint(["orden_id"], ["ordenes_de_trabajo.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_pdf_report_generation_events_checklist_id"),
        "pdf_report_generation_events",
        ["checklist_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_pdf_report_generation_events_company_id"),
        "pdf_report_generation_events",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_pdf_report_generation_events_created_at"),
        "pdf_report_generation_events",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_pdf_report_generation_events_id"),
        "pdf_report_generation_events",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_pdf_report_generation_events_orden_id"),
        "pdf_report_generation_events",
        ["orden_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_pdf_report_generation_events_status"),
        "pdf_report_generation_events",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_pdf_report_generation_events_status"), table_name="pdf_report_generation_events")
    op.drop_index(op.f("ix_pdf_report_generation_events_orden_id"), table_name="pdf_report_generation_events")
    op.drop_index(op.f("ix_pdf_report_generation_events_id"), table_name="pdf_report_generation_events")
    op.drop_index(op.f("ix_pdf_report_generation_events_created_at"), table_name="pdf_report_generation_events")
    op.drop_index(op.f("ix_pdf_report_generation_events_company_id"), table_name="pdf_report_generation_events")
    op.drop_index(op.f("ix_pdf_report_generation_events_checklist_id"), table_name="pdf_report_generation_events")
    op.drop_table("pdf_report_generation_events")
