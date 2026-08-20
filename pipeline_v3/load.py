import logging

import pandas as pd
from sqlalchemy import inspect, text

from pipeline_v3.database import get_engine


logger = logging.getLogger("pipeline.load")


def run(
    enriched_orders,
    top_products,
    top_customers,
    batch_id
):
    engine = get_engine()

    # -----------------------------
    # Check whether batch already exists
    # -----------------------------

    inspector = inspect(engine)

    if inspector.has_table("orders_enriched"):

        with engine.connect() as connection:

            batch_count = connection.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM orders_enriched
                    WHERE batch_id = :batch_id
                    """
                ),
                {"batch_id": batch_id}
            ).scalar()

        if batch_count > 0:

            logger.warning(
                "Batch %s already exists in database. Skipping database load.",
                batch_id
            )

            return

    # -----------------------------
    # Add batch metadata
    # -----------------------------

    loaded_at = pd.Timestamp.utcnow()

    enriched_orders = enriched_orders.copy()
    top_products = top_products.copy()
    top_customers = top_customers.copy()

    enriched_orders["batch_id"] = batch_id
    enriched_orders["loaded_at"] = loaded_at

    top_products["batch_id"] = batch_id
    top_products["loaded_at"] = loaded_at

    top_customers["batch_id"] = batch_id
    top_customers["loaded_at"] = loaded_at

    # -----------------------------
    # Append enriched orders
    # -----------------------------

    enriched_orders.to_sql(
        "orders_enriched",
        engine,
        if_exists="append",
        index=False
    )

    logger.info(
        "Loaded %s rows into orders_enriched for batch %s",
        len(enriched_orders),
        batch_id
    )

    # -----------------------------
    # Append product analytics
    # -----------------------------

    top_products.to_sql(
        "top_products",
        engine,
        if_exists="append",
        index=False
    )

    logger.info(
        "Loaded %s rows into top_products for batch %s",
        len(top_products),
        batch_id
    )

    # -----------------------------
    # Append customer analytics
    # -----------------------------

    top_customers.to_sql(
        "top_customers",
        engine,
        if_exists="append",
        index=False
    )

    logger.info(
        "Loaded %s rows into top_customers for batch %s",
        len(top_customers),
        batch_id
    )

    logger.info(
        "Database loading completed successfully for batch %s",
        batch_id
    )