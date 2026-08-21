import pandas as pd

from sqlalchemy import create_engine, text

from pipeline_v3 import staging
from pipeline_v3.schema import create_tables


def test_load_to_staging_writes_orders(tmp_path, monkeypatch):

    # -----------------------------
    # Temporary test database
    # -----------------------------

    db_path = tmp_path / "staging_test.db"

    engine = create_engine(
        f"sqlite:///{db_path}"
    )

    create_tables(engine)

    # Force staging code to use
    # temporary SQLite database.
    monkeypatch.setattr(
        staging,
        "get_engine",
        lambda: engine
    )

    # -----------------------------
    # Test dataset
    # -----------------------------

    enriched_orders = pd.DataFrame([
        {
            "order_id": 1001,
            "customer_id": 1,
            "product_id": 201,
            "quantity": 2,
            "order_date": "2025-10-01",
            "product_name": "Blue Milk Latte",
            "price": 4.5,
            "customer_name": "Luke Skywalker",
            "line_total": 9.0,
        },
        {
            "order_id": 1002,
            "customer_id": 2,
            "product_id": 202,
            "quantity": 3,
            "order_date": "2025-10-02",
            "product_name": "Death Star Espresso",
            "price": 3.0,
            "customer_name": "Leia Organa",
            "line_total": 9.0,
        },
    ])

    # -----------------------------
    # Load staging table
    # -----------------------------

    rows_loaded = staging.load_to_staging(
        enriched_orders,
        "orders_2025_10"
    )

    # -----------------------------
    # Verify staged data
    # -----------------------------

    with engine.connect() as connection:

        rows = connection.execute(
            text(
                """
                SELECT
                    order_id,
                    batch_id,
                    loaded_at
                FROM staging_orders
                ORDER BY order_id
                """
            )
        ).mappings().all()

    assert rows_loaded == 2
    assert len(rows) == 2

    assert rows[0]["order_id"] == 1001
    assert rows[1]["order_id"] == 1002

    assert rows[0]["batch_id"] == "orders_2025_10"
    assert rows[1]["batch_id"] == "orders_2025_10"

    assert rows[0]["loaded_at"] is not None
    assert rows[1]["loaded_at"] is not None


def test_merge_from_staging_inserts_only_new_rows(
    tmp_path,
    monkeypatch
):
    db_path = tmp_path / "staging_merge_test.db"

    engine = create_engine(
        f"sqlite:///{db_path}"
    )

    create_tables(engine)

    monkeypatch.setattr(
        staging,
        "get_engine",
        lambda: engine
    )

    # -----------------------------
    # Create batch control record
    # -----------------------------

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
                    'SUCCESS',
                    1,
                    CURRENT_TIMESTAMP
                )
                """
            ),
            {
                "batch_id": "orders_2025_10"
            }
        )

    # -----------------------------
    # Existing curated row
    # -----------------------------

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

    # -----------------------------
    # Stage three rows
    # -----------------------------

    staged_orders = pd.DataFrame([
        {
            "order_id": 1001,
            "customer_id": 1,
            "product_id": 201,
            "quantity": 2,
            "order_date": "2025-10-01",
            "product_name": "Blue Milk Latte",
            "price": 4.5,
            "customer_name": "Luke Skywalker",
            "line_total": 9.0,
        },
        {
            "order_id": 1002,
            "customer_id": 2,
            "product_id": 202,
            "quantity": 1,
            "order_date": "2025-10-02",
            "product_name": "Death Star Espresso",
            "price": 3.0,
            "customer_name": "Leia Organa",
            "line_total": 3.0,
        },
        {
            "order_id": 1003,
            "customer_id": 3,
            "product_id": 203,
            "quantity": 2,
            "order_date": "2025-10-03",
            "product_name": "Tatooine Mocha",
            "price": 4.0,
            "customer_name": "Han Solo",
            "line_total": 8.0,
        },
    ])

    staging.load_to_staging(
        staged_orders,
        "orders_2025_10"
    )

    # -----------------------------
    # First merge
    # -----------------------------

    rows_inserted = staging.merge_from_staging(
        "orders_2025_10"
    )

    assert rows_inserted == 2

    # -----------------------------
    # Second merge should be idempotent
    # -----------------------------

    rows_inserted_again = staging.merge_from_staging(
        "orders_2025_10"
    )

    assert rows_inserted_again == 0

    # -----------------------------
    # Final curated count
    # -----------------------------

    with engine.connect() as connection:

        final_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM orders_enriched
                WHERE batch_id = :batch_id
                """
            ),
            {
                "batch_id": "orders_2025_10"
            }
        ).scalar()

    assert final_count == 3


def test_clear_staging_removes_only_requested_batch(
    tmp_path,
    monkeypatch
):
    db_path = tmp_path / "staging_clear_test.db"

    engine = create_engine(
        f"sqlite:///{db_path}"
    )

    create_tables(engine)

    monkeypatch.setattr(
        staging,
        "get_engine",
        lambda: engine
    )

    batch_one = pd.DataFrame([
        {
            "order_id": 1001,
            "customer_id": 1,
            "product_id": 201,
            "quantity": 1,
            "order_date": "2025-10-01",
            "product_name": "Blue Milk Latte",
            "price": 4.5,
            "customer_name": "Luke Skywalker",
            "line_total": 4.5,
        }
    ])

    batch_two = pd.DataFrame([
        {
            "order_id": 2001,
            "customer_id": 2,
            "product_id": 202,
            "quantity": 1,
            "order_date": "2025-11-01",
            "product_name": "Death Star Espresso",
            "price": 3.0,
            "customer_name": "Leia Organa",
            "line_total": 3.0,
        }
    ])

    staging.load_to_staging(
        batch_one,
        "orders_2025_10"
    )

    staging.load_to_staging(
        batch_two,
        "orders_2025_11"
    )

    rows_deleted = staging.clear_staging(
        "orders_2025_10"
    )

    assert rows_deleted == 1

    with engine.connect() as connection:

        remaining_batches = connection.execute(
            text(
                """
                SELECT DISTINCT batch_id
                FROM staging_orders
                ORDER BY batch_id
                """
            )
        ).scalars().all()

    assert remaining_batches == [
        "orders_2025_11"
    ]