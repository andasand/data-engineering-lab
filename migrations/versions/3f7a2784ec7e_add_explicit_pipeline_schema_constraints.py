"""add explicit pipeline schema constraints

Revision ID: 3f7a2784ec7e
Revises:
Create Date: 2026-08-21 04:16:58.405771
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "3f7a2784ec7e"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Backfill historical batches before adding foreign keys.
    op.execute(
        """
        INSERT INTO pipeline_batches (
            batch_id,
            status,
            rows_loaded,
            started_at,
            completed_at
        )
        SELECT
            oe.batch_id,
            'SUCCESS',
            COUNT(*)::INTEGER,
            MIN(oe.loaded_at)::TIMESTAMP,
            MAX(oe.loaded_at)::TIMESTAMP
        FROM orders_enriched AS oe
        LEFT JOIN pipeline_batches AS pb
            ON pb.batch_id = oe.batch_id
        WHERE pb.batch_id IS NULL
        GROUP BY oe.batch_id
        """
    )

    op.alter_column(
        "pipeline_batches",
        "started_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        postgresql_using="started_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "pipeline_batches",
        "completed_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
        postgresql_using="completed_at AT TIME ZONE 'UTC'",
    )
    op.create_check_constraint(
        "ck_pipeline_batches_status",
        "pipeline_batches",
        "status IN ('RUNNING', 'SUCCESS', 'FAILED')",
    )

    op.alter_column(
        "orders_enriched",
        "order_id",
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "orders_enriched",
        "customer_id",
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "orders_enriched",
        "product_id",
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "orders_enriched",
        "quantity",
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "orders_enriched",
        "order_date",
        existing_type=sa.TEXT(),
        type_=sa.Date(),
        nullable=False,
        postgresql_using="order_date::date",
    )
    op.alter_column(
        "orders_enriched",
        "product_name",
        existing_type=sa.TEXT(),
        type_=sa.String(length=255),
        nullable=False,
    )
    op.alter_column(
        "orders_enriched",
        "price",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )
    op.alter_column(
        "orders_enriched",
        "customer_name",
        existing_type=sa.TEXT(),
        type_=sa.String(length=255),
        nullable=False,
    )
    op.alter_column(
        "orders_enriched",
        "line_total",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )
    op.alter_column(
        "orders_enriched",
        "batch_id",
        existing_type=sa.TEXT(),
        type_=sa.String(length=255),
        nullable=False,
    )
    op.alter_column(
        "orders_enriched",
        "loaded_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )
    op.create_primary_key(
        "pk_orders_enriched",
        "orders_enriched",
        ["batch_id", "order_id"],
    )
    op.create_foreign_key(
        "fk_orders_enriched_batch_id",
        "orders_enriched",
        "pipeline_batches",
        ["batch_id"],
        ["batch_id"],
    )

    op.alter_column(
        "top_customers",
        "customer_id",
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "top_customers",
        "customer_name",
        existing_type=sa.TEXT(),
        type_=sa.String(length=255),
        nullable=False,
    )
    op.alter_column(
        "top_customers",
        "total_spend",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )
    op.alter_column(
        "top_customers",
        "batch_id",
        existing_type=sa.TEXT(),
        type_=sa.String(length=255),
        nullable=False,
    )
    op.alter_column(
        "top_customers",
        "loaded_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )
    op.create_primary_key(
        "pk_top_customers",
        "top_customers",
        ["batch_id", "customer_id"],
    )
    op.create_foreign_key(
        "fk_top_customers_batch_id",
        "top_customers",
        "pipeline_batches",
        ["batch_id"],
        ["batch_id"],
    )

    op.alter_column(
        "top_products",
        "product_id",
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "top_products",
        "product_name",
        existing_type=sa.TEXT(),
        type_=sa.String(length=255),
        nullable=False,
    )
    op.alter_column(
        "top_products",
        "price",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )
    op.alter_column(
        "top_products",
        "total_revenue",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )
    op.alter_column(
        "top_products",
        "batch_id",
        existing_type=sa.TEXT(),
        type_=sa.String(length=255),
        nullable=False,
    )
    op.alter_column(
        "top_products",
        "loaded_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )
    op.create_primary_key(
        "pk_top_products",
        "top_products",
        ["batch_id", "product_id"],
    )
    op.create_foreign_key(
        "fk_top_products_batch_id",
        "top_products",
        "pipeline_batches",
        ["batch_id"],
        ["batch_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "fk_top_products_batch_id",
        "top_products",
        type_="foreignkey",
    )
    op.drop_constraint(
        "pk_top_products",
        "top_products",
        type_="primary",
    )
    op.alter_column(
        "top_products",
        "loaded_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "top_products",
        "batch_id",
        existing_type=sa.String(length=255),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "top_products",
        "total_revenue",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        nullable=True,
    )
    op.alter_column(
        "top_products",
        "price",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        nullable=True,
    )
    op.alter_column(
        "top_products",
        "product_name",
        existing_type=sa.String(length=255),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "top_products",
        "product_id",
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        nullable=True,
    )

    op.drop_constraint(
        "fk_top_customers_batch_id",
        "top_customers",
        type_="foreignkey",
    )
    op.drop_constraint(
        "pk_top_customers",
        "top_customers",
        type_="primary",
    )
    op.alter_column(
        "top_customers",
        "loaded_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "top_customers",
        "batch_id",
        existing_type=sa.String(length=255),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "top_customers",
        "total_spend",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        nullable=True,
    )
    op.alter_column(
        "top_customers",
        "customer_name",
        existing_type=sa.String(length=255),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "top_customers",
        "customer_id",
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        nullable=True,
    )

    op.drop_constraint(
        "fk_orders_enriched_batch_id",
        "orders_enriched",
        type_="foreignkey",
    )
    op.drop_constraint(
        "pk_orders_enriched",
        "orders_enriched",
        type_="primary",
    )
    op.alter_column(
        "orders_enriched",
        "loaded_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "orders_enriched",
        "batch_id",
        existing_type=sa.String(length=255),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "orders_enriched",
        "line_total",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        nullable=True,
    )
    op.alter_column(
        "orders_enriched",
        "customer_name",
        existing_type=sa.String(length=255),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "orders_enriched",
        "price",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        nullable=True,
    )
    op.alter_column(
        "orders_enriched",
        "product_name",
        existing_type=sa.String(length=255),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "orders_enriched",
        "order_date",
        existing_type=sa.Date(),
        type_=sa.TEXT(),
        nullable=True,
        postgresql_using="order_date::text",
    )
    op.alter_column(
        "orders_enriched",
        "quantity",
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        nullable=True,
    )
    op.alter_column(
        "orders_enriched",
        "product_id",
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        nullable=True,
    )
    op.alter_column(
        "orders_enriched",
        "customer_id",
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        nullable=True,
    )
    op.alter_column(
        "orders_enriched",
        "order_id",
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        nullable=True,
    )

    op.drop_constraint(
        "ck_pipeline_batches_status",
        "pipeline_batches",
        type_="check",
    )
    op.alter_column(
        "pipeline_batches",
        "completed_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
        postgresql_using="completed_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "pipeline_batches",
        "started_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False,
        postgresql_using="started_at AT TIME ZONE 'UTC'",
    )

    # Historical control rows inserted during upgrade are intentionally retained.