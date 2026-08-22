import os
import uuid

import pandas as pd
import pytest

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from pipeline_v3 import load
from pipeline_v3.schema import metadata


def _postgres_test_engine(schema_name):
    required = {
        "POSTGRES_HOST": os.getenv("POSTGRES_HOST"),
        "POSTGRES_PORT": os.getenv("POSTGRES_PORT", "5432"),
        "POSTGRES_DB": os.getenv("POSTGRES_DB"),
        "POSTGRES_USER": os.getenv("POSTGRES_USER"),
        "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD"),
    }

    missing = [
        key
        for key, value in required.items()
        if not value
    ]

    if missing:
        pytest.skip(
            "PostgreSQL integration test skipped. Missing environment variables: "
            + ", ".join(missing)
        )

    url = URL.create(
        drivername="postgresql+psycopg2",
        username=required["POSTGRES_USER"],
        password=required["POSTGRES_PASSWORD"],
        host=required["POSTGRES_HOST"],
        port=int(required["POSTGRES_PORT"]),
        database=required["POSTGRES_DB"],
    )

    return create_engine(
        url,
        connect_args={
            "options": f"-csearch_path={schema_name}"
        },
    )


@pytest.mark.postgres
def test_postgres_pipeline_load_uses_real_schema_and_types(monkeypatch):
    schema_name = "test_pipeline_" + uuid.uuid4().hex[:12]

    admin_engine = None
    engine = None

    try:
        admin_engine = _postgres_test_engine("public")

        with admin_engine.begin() as connection:
            connection.execute(
                text(
                    f'CREATE SCHEMA "{schema_name}"'
                )
            )

        engine = _postgres_test_engine(schema_name)

        metadata.create_all(engine)

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
                "order_date": "2026-01-05",
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
                "order_date": "2026-01-06",
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
            "orders_2026_01",
        )

        with engine.connect() as connection:
            orders = connection.execute(
                text(
                    """
                    SELECT
                        order_id,
                        order_date,
                        batch_id
                    FROM orders_enriched
                    ORDER BY order_id
                    """
                )
            ).mappings().all()

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
                    "batch_id": "orders_2026_01"
                },
            ).mappings().first()

            staging_count = connection.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM staging_orders
                    """
                )
            ).scalar()

            order_date_type = connection.execute(
                text(
                    """
                    SELECT data_type
                    FROM information_schema.columns
                    WHERE table_schema = :schema_name
                      AND table_name = 'orders_enriched'
                      AND column_name = 'order_date'
                    """
                ),
                {
                    "schema_name": schema_name
                },
            ).scalar()

        assert len(orders) == 2
        assert orders[0]["order_id"] == 1001
        assert str(orders[0]["order_date"]) == "2026-01-05"
        assert orders[1]["order_id"] == 1002
        assert str(orders[1]["order_date"]) == "2026-01-06"

        assert all(
            row["batch_id"] == "orders_2026_01"
            for row in orders
        )

        assert batch is not None
        assert batch["status"] == "SUCCESS"
        assert batch["rows_loaded"] == 2

        assert staging_count == 0
        assert order_date_type == "date"

        load.run(
            enriched_orders,
            top_products,
            top_customers,
            "orders_2026_01",
        )

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
                    "batch_id": "orders_2026_01"
                },
            ).scalar()

        assert final_count == 2

    finally:
        if engine is not None:
            engine.dispose()

        if admin_engine is not None:
            with admin_engine.begin() as connection:
                connection.execute(
                    text(
                        f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'
                    )
                )

            admin_engine.dispose()
        