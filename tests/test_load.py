import pandas as pd
import pytest

from sqlalchemy import create_engine, inspect, text

from pipeline_v3 import load


def test_load_writes_expected_tables(tmp_path, monkeypatch):
    # -----------------------------
    # Temporary test database
    # -----------------------------

    db_path = tmp_path / "test.db"

    engine = create_engine(
        f"sqlite:///{db_path}"
    )

    # Force load.run() to use our
    # temporary database instead
    # of PostgreSQL.
    monkeypatch.setattr(
        load,
        "get_engine",
        lambda: engine
    )

    # -----------------------------
    # Test datasets
    # -----------------------------

    enriched_orders = pd.DataFrame([
        {
            "order_id": 1,
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
            "order_id": 2,
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

    top_products = pd.DataFrame([
        {
            "product_id": 201,
            "product_name": "Blue Milk Latte",
            "total_revenue": 9.0,
        },
        {
            "product_id": 202,
            "product_name": "Death Star Espresso",
            "total_revenue": 9.0,
        },
    ])

    top_customers = pd.DataFrame([
        {
            "customer_id": 1,
            "customer_name": "Luke Skywalker",
            "total_spend": 9.0,
        },
        {
            "customer_id": 2,
            "customer_name": "Leia Organa",
            "total_spend": 9.0,
        },
    ])

    # -----------------------------
    # First load
    # -----------------------------

    load.run(
        enriched_orders,
        top_products,
        top_customers,
        "orders_2025_10"
    )

    # -----------------------------
    # Duplicate load
    # -----------------------------

    load.run(
        enriched_orders,
        top_products,
        top_customers,
        "orders_2025_10"
    )

    # -----------------------------
    # Verify tables and row counts
    # -----------------------------

    with engine.connect() as connection:

        orders_count = connection.execute(
            text(
                "SELECT COUNT(*) "
                "FROM orders_enriched"
            )
        ).scalar()

        products_count = connection.execute(
            text(
                "SELECT COUNT(*) "
                "FROM top_products"
            )
        ).scalar()

        customers_count = connection.execute(
            text(
                "SELECT COUNT(*) "
                "FROM top_customers"
            )
        ).scalar()

        batch = connection.execute(
            text(
                """
                SELECT
                    batch_id,
                    status,
                    rows_loaded
                FROM pipeline_batches
                WHERE batch_id = :batch_id
                """
            ),
            {
                "batch_id": "orders_2025_10"
            }
        ).mappings().first()

    assert orders_count == 2
    assert products_count == 2
    assert customers_count == 2

    assert batch is not None
    assert batch["batch_id"] == "orders_2025_10"
    assert batch["status"] == "SUCCESS"
    assert batch["rows_loaded"] == 2


def test_load_rolls_back_and_marks_batch_failed(
    tmp_path,
    monkeypatch
):
    # -----------------------------
    # Temporary test database
    # -----------------------------

    db_path = tmp_path / "test_failed.db"

    engine = create_engine(
        f"sqlite:///{db_path}"
    )

    monkeypatch.setattr(
        load,
        "get_engine",
        lambda: engine
    )

    # -----------------------------
    # Test datasets
    # -----------------------------

    enriched_orders = pd.DataFrame([
        {
            "order_id": 1,
            "customer_id": 1,
            "product_id": 201,
            "quantity": 2,
            "order_date": "2025-10-01",
            "product_name": "Blue Milk Latte",
            "price": 4.5,
            "customer_name": "Luke Skywalker",
            "line_total": 9.0,
        }
    ])

    top_products = pd.DataFrame([
        {
            "product_id": 201,
            "product_name": "Blue Milk Latte",
            "total_revenue": 9.0,
        }
    ])

    top_customers = pd.DataFrame([
        {
            "customer_id": 1,
            "customer_name": "Luke Skywalker",
            "total_spend": 9.0,
        }
    ])

    # -----------------------------
    # Fail on the second to_sql()
    # -----------------------------

    call_count = {
        "value": 0
    }

    original_to_sql = pd.DataFrame.to_sql

    def fail_on_second_write(
        self,
        *args,
        **kwargs
    ):
        call_count["value"] += 1

        if call_count["value"] == 2:
            raise RuntimeError(
                "Simulated database failure"
            )

        return original_to_sql(
            self,
            *args,
            **kwargs
        )

    monkeypatch.setattr(
        pd.DataFrame,
        "to_sql",
        fail_on_second_write
    )

    # -----------------------------
    # Run load and expect failure
    # -----------------------------

    with pytest.raises(
        RuntimeError,
        match="Simulated database failure"
    ):

        load.run(
            enriched_orders,
            top_products,
            top_customers,
            "orders_failed_batch"
        )

    # -----------------------------
    # Verify rollback
    # -----------------------------

    inspector = inspect(engine)

    if inspector.has_table("orders_enriched"):

        with engine.connect() as connection:

            orders_count = connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM orders_enriched"
                )
            ).scalar()

    else:

        orders_count = 0

    # -----------------------------
    # Verify FAILED batch status
    # -----------------------------

    with engine.connect() as connection:

        batch = connection.execute(
            text(
                """
                SELECT
                    batch_id,
                    status,
                    rows_loaded
                FROM pipeline_batches
                WHERE batch_id = :batch_id
                """
            ),
            {
                "batch_id": "orders_failed_batch"
            }
        ).mappings().first()

    assert orders_count == 0

    assert batch is not None
    assert batch["batch_id"] == "orders_failed_batch"
    assert batch["status"] == "FAILED"
    assert batch["rows_loaded"] == 0