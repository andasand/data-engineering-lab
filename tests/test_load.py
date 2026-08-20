import pandas as pd

from sqlalchemy import create_engine, text

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
    # Run database load
    # -----------------------------

    load.run(
        enriched_orders,
        top_products,
        top_customers,
        "orders_2025_10"
    )

    # Run the same batch again.
    # Idempotency should prevent duplicates.
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

    assert orders_count == 2
    assert products_count == 2
    assert customers_count == 2