import logging

import pandas as pd
from sqlalchemy import text

from pipeline_v3.database import get_engine


logger = logging.getLogger("pipeline.staging")


def load_to_staging(
    enriched_orders,
    batch_id,
    engine=None
):
    if engine is None:
        engine = get_engine()

    staged = enriched_orders.copy()

    # Normalize order_date before writing to staging so
    # PostgreSQL receives real date values rather than text.
    staged["order_date"] = pd.to_datetime(
        staged["order_date"],
        errors="raise"
    ).dt.date

    staged["batch_id"] = batch_id
    staged["loaded_at"] = pd.Timestamp.now("UTC")

    staged.to_sql(
        "staging_orders",
        engine,
        if_exists="append",
        index=False
    )

    logger.info(
        "Loaded %s rows into staging_orders for batch %s",
        len(staged),
        batch_id
    )

    return len(staged)


def merge_from_staging(
    batch_id,
    engine=None,
    connection=None
):
    if connection is None:
        if engine is None:
            engine = get_engine()

        with engine.begin() as managed_connection:
            return _merge_from_staging(
                batch_id,
                managed_connection
            )

    return _merge_from_staging(
        batch_id,
        connection
    )


def _merge_from_staging(
    batch_id,
    connection
):
    merge_sql = text(
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
        SELECT
            s.order_id,
            s.customer_id,
            s.product_id,
            s.quantity,
            s.order_date,
            s.product_name,
            s.price,
            s.customer_name,
            s.line_total,
            s.batch_id,
            s.loaded_at
        FROM staging_orders AS s
        WHERE s.batch_id = :batch_id
          AND NOT EXISTS (
              SELECT 1
              FROM orders_enriched AS o
              WHERE o.batch_id = s.batch_id
                AND o.order_id = s.order_id
          )
        """
    )

    result = connection.execute(
        merge_sql,
        {"batch_id": batch_id}
    )

    rows_inserted = result.rowcount

    logger.info(
        "Merged %s new rows from staging for batch %s",
        rows_inserted,
        batch_id
    )

    return rows_inserted


def clear_staging(
    batch_id,
    engine=None
):
    if engine is None:
        engine = get_engine()

    delete_sql = text(
        """
        DELETE FROM staging_orders
        WHERE batch_id = :batch_id
        """
    )

    with engine.begin() as connection:
        result = connection.execute(
            delete_sql,
            {"batch_id": batch_id}
        )

        rows_deleted = result.rowcount

    logger.info(
        "Cleared %s rows from staging for batch %s",
        rows_deleted,
        batch_id
    )

    return rows_deleted