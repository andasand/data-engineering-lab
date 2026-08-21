"""add staging orders schema

Revision ID: 4d17adec9a3e
Revises: 3f7a2784ec7e
Create Date: 2026-08-21 10:09:05.396204
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4d17adec9a3e"
down_revision: Union[str, Sequence[str], None] = "3f7a2784ec7e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the staging orders table."""

    op.create_table(
        "staging_orders",

        sa.Column(
            "order_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "customer_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "product_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "quantity",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "order_date",
            sa.Date(),
            nullable=False
        ),

        sa.Column(
            "product_name",
            sa.String(length=255),
            nullable=False
        ),

        sa.Column(
            "price",
            sa.Float(),
            nullable=False
        ),

        sa.Column(
            "customer_name",
            sa.String(length=255),
            nullable=False
        ),

        sa.Column(
            "line_total",
            sa.Float(),
            nullable=False
        ),

        sa.Column(
            "batch_id",
            sa.String(length=255),
            nullable=False
        ),

        sa.Column(
            "loaded_at",
            sa.DateTime(timezone=True),
            nullable=False
        ),
    )


def downgrade() -> None:
    """Remove the staging orders table."""

    op.drop_table(
        "staging_orders"
    )