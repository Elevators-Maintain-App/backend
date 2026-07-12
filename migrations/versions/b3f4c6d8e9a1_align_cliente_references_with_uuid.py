"""align cliente references with uuid

Revision ID: b3f4c6d8e9a1
Revises: 7b8d4f2c1a90
Create Date: 2026-07-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision = "b3f4c6d8e9a1"
down_revision = "7b8d4f2c1a90"
branch_labels = None
depends_on = None


ORDER_FK = "fk_ordenes_de_trabajo_cliente_id_clientes"
UNIT_FK = "fk_unidades_cliente_id_clientes"


def _column_data_type(table_name: str, column_name: str) -> str | None:
    bind = op.get_bind()
    return bind.execute(
        text(
            """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table_name
              AND column_name = :column_name
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    ).scalar_one_or_none()


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            text(
                """
                SELECT 1
                FROM information_schema.table_constraints
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                  AND constraint_name = :constraint_name
                """
            ),
            {"table_name": table_name, "constraint_name": constraint_name},
        ).scalar_one_or_none()
    )


def _drop_fk_if_exists(table_name: str, constraint_name: str) -> None:
    if _constraint_exists(table_name, constraint_name):
        op.drop_constraint(constraint_name, table_name, type_="foreignkey")


def _create_fk_if_missing(table_name: str, constraint_name: str) -> None:
    if not _constraint_exists(table_name, constraint_name):
        op.create_foreign_key(
            constraint_name,
            table_name,
            "clientes",
            ["cliente_id"],
            ["id"],
        )


def upgrade() -> None:
    order_type = _column_data_type("ordenes_de_trabajo", "cliente_id")
    if order_type in {"character varying", "text"}:
        op.alter_column(
            "ordenes_de_trabajo",
            "cliente_id",
            existing_type=sa.String(),
            type_=sa.UUID(),
            existing_nullable=False,
            nullable=False,
            postgresql_using="cliente_id::uuid",
        )
    else:
        op.alter_column(
            "ordenes_de_trabajo",
            "cliente_id",
            existing_type=sa.UUID(),
            nullable=False,
        )

    unit_type = _column_data_type("unidades", "cliente_id")
    if unit_type in {"character varying", "text"}:
        op.alter_column(
            "unidades",
            "cliente_id",
            existing_type=sa.String(),
            type_=sa.UUID(),
            existing_nullable=True,
            nullable=True,
            postgresql_using="cliente_id::uuid",
        )
    else:
        op.alter_column(
            "unidades",
            "cliente_id",
            existing_type=sa.UUID(),
            nullable=True,
        )

    _create_fk_if_missing("ordenes_de_trabajo", ORDER_FK)
    _create_fk_if_missing("unidades", UNIT_FK)


def downgrade() -> None:
    _drop_fk_if_exists("ordenes_de_trabajo", ORDER_FK)
    _drop_fk_if_exists("unidades", UNIT_FK)

    op.alter_column(
        "ordenes_de_trabajo",
        "cliente_id",
        existing_type=sa.UUID(),
        type_=sa.String(),
        existing_nullable=False,
        nullable=False,
        postgresql_using="cliente_id::text",
    )
    op.alter_column(
        "unidades",
        "cliente_id",
        existing_type=sa.UUID(),
        type_=sa.String(),
        existing_nullable=True,
        nullable=True,
        postgresql_using="cliente_id::text",
    )
