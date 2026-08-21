import pandas as pd

from sqlalchemy import create_engine, text

from pipeline_v3 import load
from pipeline_v3.schema import create_tables


def test_v05_incremental_pipeline_flow(
    tmp_path,
    monkeypatch
):
    db_path = tmp_path / "pipeline_v05.db"

    engine = create_engine(
        f"sqlite:///{db_path}"
    )

    create_tables(engine)

    monkeypatch.setattr(
        load,
        "get_engine",
        lambda: engine
    )

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
            "quantity": 1,
            "order_date": "2025-10-02",
            "product_name": "Death Star Espresso",
            "price": 3.0,
            "customer_name": "Leia Organa",
            "line_total": 3.0,
        },
    ])

    top_products = pd.DataFrame([
        {
            "product_id": 201,
            "product_name": "Blue Milk Latte",
            "price": 4.5,
            "total_revenue": 9.0,
        },
        {
            "product_id": 202,
            "product_name": "Death Star Espresso",
            "price": 3.0,
            "total_revenue": 3.0,
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
            "total_spend": 3.0,
        },
    ])

    load.run(
        enriched_orders,
        top_products,
        top_customers,
        "orders_2025_10"
    )

    with engine.connect() as connection:

        orders_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM orders_enriched
                """
            )
        ).scalar()

        products_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM top_products
                """
            )
        ).scalar()

        customers_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM top_customers
                """
            )
        ).scalar()

        staging_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM staging_orders
                """
            )
        ).scalar()

        batch = connection.execute(
            text(
                """
                SELECT
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
    assert staging_count == 0

    assert batch is not None
    assert batch["status"] == "SUCCESS"
    assert batch["rows_loaded"] == 2