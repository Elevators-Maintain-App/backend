"""add plans subscriptions and usage

Revision ID: 9f5ab90ded2a
Revises: d6a237fcfa36, ded70a953766
Create Date: 2026-05-15 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9f5ab90ded2a"
down_revision = ("d6a237fcfa36", "ded70a953766")
branch_labels = None
depends_on = None


PLAN_ROWS = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "code": "free",
        "name": "Free",
        "description": "Plan gratuito/controlado para pruebas iniciales",
        "max_admins": 1,
        "max_supervisors": 1,
        "max_technicians": 2,
        "max_projects": 1,
        "max_clients": 3,
        "max_units": 10,
        "max_work_orders_per_month": 30,
        "max_pdf_reports_per_month": 30,
        "storage_limit_mb": 500,
        "allow_offline_mode": True,
        "allow_custom_checklists": False,
        "allow_advanced_dashboard": False,
        "allow_evidence_editing": False,
        "is_public": True,
        "is_active": True,
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "code": "pilot_partner",
        "name": "Pilot Partner",
        "description": "Plan piloto colaborativo con límites ampliados y acompañamiento personalizado",
        "max_admins": 2,
        "max_supervisors": 3,
        "max_technicians": 10,
        "max_projects": 10,
        "max_clients": 20,
        "max_units": 100,
        "max_work_orders_per_month": 500,
        "max_pdf_reports_per_month": 500,
        "storage_limit_mb": 5000,
        "allow_offline_mode": True,
        "allow_custom_checklists": True,
        "allow_advanced_dashboard": True,
        "allow_evidence_editing": True,
        "is_public": True,
        "is_active": True,
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "code": "starter",
        "name": "Starter",
        "description": "Plan inicial para empresas pequeñas de mantenimiento",
        "max_admins": 2,
        "max_supervisors": 3,
        "max_technicians": 8,
        "max_projects": 10,
        "max_clients": 30,
        "max_units": 150,
        "max_work_orders_per_month": 400,
        "max_pdf_reports_per_month": 400,
        "storage_limit_mb": 3000,
        "allow_offline_mode": True,
        "allow_custom_checklists": False,
        "allow_advanced_dashboard": False,
        "allow_evidence_editing": False,
        "is_public": True,
        "is_active": True,
    },
    {
        "id": "44444444-4444-4444-4444-444444444444",
        "code": "professional",
        "name": "Professional",
        "description": "Plan profesional para operación técnica en crecimiento",
        "max_admins": 5,
        "max_supervisors": 10,
        "max_technicians": 50,
        "max_projects": 50,
        "max_clients": 150,
        "max_units": 1000,
        "max_work_orders_per_month": 3000,
        "max_pdf_reports_per_month": 3000,
        "storage_limit_mb": 25000,
        "allow_offline_mode": True,
        "allow_custom_checklists": True,
        "allow_advanced_dashboard": True,
        "allow_evidence_editing": True,
        "is_public": True,
        "is_active": True,
    },
    {
        "id": "55555555-5555-5555-5555-555555555555",
        "code": "enterprise",
        "name": "Enterprise",
        "description": "Plan empresarial con límites personalizados",
        "max_admins": None,
        "max_supervisors": None,
        "max_technicians": None,
        "max_projects": None,
        "max_clients": None,
        "max_units": None,
        "max_work_orders_per_month": None,
        "max_pdf_reports_per_month": None,
        "storage_limit_mb": None,
        "allow_offline_mode": True,
        "allow_custom_checklists": True,
        "allow_advanced_dashboard": True,
        "allow_evidence_editing": True,
        "is_public": True,
        "is_active": True,
    },
]


def _upsert_plan(row: dict) -> None:
    columns = [
        "id",
        "code",
        "name",
        "description",
        "max_admins",
        "max_supervisors",
        "max_technicians",
        "max_projects",
        "max_clients",
        "max_units",
        "max_work_orders_per_month",
        "max_pdf_reports_per_month",
        "storage_limit_mb",
        "allow_offline_mode",
        "allow_custom_checklists",
        "allow_advanced_dashboard",
        "allow_evidence_editing",
        "is_public",
        "is_active",
    ]
    placeholders = ", ".join(
        "CAST(:id AS UUID)" if column == "id" else f":{column}" for column in columns
    )
    update_clause = ", ".join(
        f"{column} = EXCLUDED.{column}" for column in columns if column not in {"id", "code"}
    )

    op.execute(
        sa.text(
            f"""
            INSERT INTO plans ({", ".join(columns)})
            VALUES ({placeholders})
            ON CONFLICT (code) DO UPDATE
            SET {update_clause}
            """
        ).bindparams(**row)
    )


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("max_admins", sa.Integer(), nullable=True),
        sa.Column("max_supervisors", sa.Integer(), nullable=True),
        sa.Column("max_technicians", sa.Integer(), nullable=True),
        sa.Column("max_projects", sa.Integer(), nullable=True),
        sa.Column("max_clients", sa.Integer(), nullable=True),
        sa.Column("max_units", sa.Integer(), nullable=True),
        sa.Column("max_work_orders_per_month", sa.Integer(), nullable=True),
        sa.Column("max_pdf_reports_per_month", sa.Integer(), nullable=True),
        sa.Column("storage_limit_mb", sa.Integer(), nullable=True),
        sa.Column("allow_offline_mode", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("allow_custom_checklists", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("allow_advanced_dashboard", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("allow_evidence_editing", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_public", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_plans_code"),
        sa.UniqueConstraint("name", name="uq_plans_name"),
    )
    op.create_index(op.f("ix_plans_code"), "plans", ["code"], unique=False)
    op.create_index(op.f("ix_plans_id"), "plans", ["id"], unique=False)
    op.create_index(op.f("ix_plans_name"), "plans", ["name"], unique=False)

    op.create_table(
        "company_subscriptions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("billing_period", sa.String(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("current_period_start", sa.Date(), nullable=True),
        sa.Column("current_period_end", sa.Date(), nullable=True),
        sa.Column("trial_ends_at", sa.Date(), nullable=True),
        sa.Column("last_payment_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("next_payment_due_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companias.id"]),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_company_subscriptions_company_id"), "company_subscriptions", ["company_id"], unique=False)
    op.create_index(op.f("ix_company_subscriptions_id"), "company_subscriptions", ["id"], unique=False)
    op.create_index(op.f("ix_company_subscriptions_plan_id"), "company_subscriptions", ["plan_id"], unique=False)
    op.create_index(op.f("ix_company_subscriptions_status"), "company_subscriptions", ["status"], unique=False)

    op.create_table(
        "company_usage",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("period_month", sa.Integer(), nullable=False),
        sa.Column("users_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("admins_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("supervisors_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("technicians_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("projects_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("clients_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("units_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("work_orders_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("pdf_reports_generated", sa.Integer(), server_default="0", nullable=False),
        sa.Column("storage_used_mb", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companias.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "period_year", "period_month", name="uq_company_usage_company_period"),
    )
    op.create_index(op.f("ix_company_usage_company_id"), "company_usage", ["company_id"], unique=False)
    op.create_index(op.f("ix_company_usage_id"), "company_usage", ["id"], unique=False)

    for row in PLAN_ROWS:
        _upsert_plan(row)


def downgrade() -> None:
    op.drop_index(op.f("ix_company_usage_id"), table_name="company_usage")
    op.drop_index(op.f("ix_company_usage_company_id"), table_name="company_usage")
    op.drop_table("company_usage")
    op.drop_index(op.f("ix_company_subscriptions_status"), table_name="company_subscriptions")
    op.drop_index(op.f("ix_company_subscriptions_plan_id"), table_name="company_subscriptions")
    op.drop_index(op.f("ix_company_subscriptions_id"), table_name="company_subscriptions")
    op.drop_index(op.f("ix_company_subscriptions_company_id"), table_name="company_subscriptions")
    op.drop_table("company_subscriptions")
    op.drop_index(op.f("ix_plans_name"), table_name="plans")
    op.drop_index(op.f("ix_plans_id"), table_name="plans")
    op.drop_index(op.f("ix_plans_code"), table_name="plans")
    op.drop_table("plans")
