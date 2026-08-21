import pytest

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from pipeline_v3.schema import create_tables


def test_create_tables_creates_expected_schema(tmp_path):

    db_path = tmp_path / "schema_test.db"

    engine = create_engine(
        f"sqlite:///{db_path}"
    )

    # -----------------------------
    # Create schema
    # -----------------------------

    create_tables(engine)

    # -----------------------------
    # Inspect database
    # -----------------------------

    inspector = inspect(engine)

    table_names = set(
        inspector.get_table_names()
    )

    # -----------------------------
    # Verify expected tables
    # -----------------------------

    expected_tables = {
        "pipeline_batches",
        "orders_enriched",
        "top_products",
        "top_customers",
    }

    assert expected_tables.issubset(
        table_names
    )

def test_pipeline_batches_rejects_invalid_status(tmp_path):

    db_path = tmp_path / "schema_constraint_test.db"

    engine = create_engine(
        f"sqlite:///{db_path}"
    )

    create_tables(engine)

    with pytest.raises(IntegrityError):

        with engine.begin() as connection:

            connection.execute(
                text(
                    """
                    INSERT INTO pipeline_batches (
                        batch_id,
                        status,
                        rows_loaded,
                        started_at
                    )
                    VALUES (
                        :batch_id,
                        :status,
                        :rows_loaded,
                        CURRENT_TIMESTAMP
                    )
                    """
                ),
                {
                    "batch_id": "orders_bad_status",
                    "status": "DARTH_VADER",
                    "rows_loaded": 0,
                }
            )

def test_orders_enriched_composite_primary_key(tmp_path):

    db_path = tmp_path / "composite_key_test.db"

    engine = create_engine(
        f"sqlite:///{db_path}"
    )

    create_tables(engine)

    with engine.begin() as connection:

        # Create two batches
        connection.execute(
            text(
                """
                INSERT INTO pipeline_batches (
                    batch_id,
                    status,
                    rows_loaded,
                    started_at
                )
                VALUES
                    ('orders_2025_10', 'SUCCESS', 1, CURRENT_TIMESTAMP),
                    ('orders_2025_11', 'SUCCESS', 1, CURRENT_TIMESTAMP)
                """
            )
        )

        # Same order_id in first batch
        connection.execute(
            text(
                """
                INSERT INTO orders_enriched (
                    order_id,
                    customer_id,
                    product_id,
                    quantity,
                    order_date,
                    product_name,
                    price,
                    customer_name,
                    line_total,
                    batch_id,
                    loaded_at
                )
                VALUES (
                    1001,
                    1,
                    201,
                    2,
                    '2025-10-01',
                    'Blue Milk Latte',
                    4.5,
                    'Luke Skywalker',
                    9.0,
                    'orders_2025_10',
                    CURRENT_TIMESTAMP
                )
                """
            )
        )

        # Same order_id is allowed in a different batch
        connection.execute(
            text(
                """
                INSERT INTO orders_enriched (
                    order_id,
                    customer_id,
                    product_id,
                    quantity,
                    order_date,
                    product_name,
                    price,
                    customer_name,
                    line_total,
                    batch_id,
                    loaded_at
                )
                VALUES (
                    1001,
                    1,
                    201,
                    2,
                    '2025-11-01',
                    'Blue Milk Latte',
                    4.5,
                    'Luke Skywalker',
                    9.0,
                    'orders_2025_11',
                    CURRENT_TIMESTAMP
                )
                """
            )
        )

    # Same order_id + same batch_id should fail
    with pytest.raises(IntegrityError):

        with engine.begin() as connection:

            connection.execute(
                text(
                    """
                    INSERT INTO orders_enriched (
                        order_id,
                        customer_id,
                        product_id,
                        quantity,
                        order_date,
                        product_name,
                        price,
                        customer_name,
                        line_total,
                        batch_id,
                        loaded_at
                    )
                    VALUES (
                        1001,
                        1,
                        201,
                        1,
                        '2025-10-02',
                        'Blue Milk Latte',
                        4.5,
                        'Luke Skywalker',
                        4.5,
                        'orders_2025_10',
                        CURRENT_TIMESTAMP
                    )
                    """
                )
            )