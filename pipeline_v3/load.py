import logging

import pandas as pd

from pipeline_v3.database import get_engine
from pipeline_v3 import batches, staging


logger = logging.getLogger("pipeline.load")


def run(
    enriched_orders,
    top_products,
    top_customers,
    batch_id
):
    engine = get_engine()

    # -----------------------------
    # Check batch control table
    # -----------------------------

    if batches.batch_exists(
        batch_id,
        engine=engine
    ):
        logger.warning(
            "Batch %s already completed successfully. Skipping database load.",
            batch_id
        )
        return

    # -----------------------------
    # Mark batch as running
    # -----------------------------

    batches.start_batch(
        batch_id,
        engine=engine
    )

    try:
        # -----------------------------
        # Add metadata to aggregates
        # -----------------------------

        loaded_at = pd.Timestamp.now("UTC")

        top_products = top_products.copy()
        top_customers = top_customers.copy()

        top_products["batch_id"] = batch_id
        top_products["loaded_at"] = loaded_at

        top_customers["batch_id"] = batch_id
        top_customers["loaded_at"] = loaded_at

        # -----------------------------
        # Stage enriched orders
        # -----------------------------

        staging.load_to_staging(
            enriched_orders,
            batch_id,
            engine=engine
        )

        # -----------------------------
        # Atomic curated promotion
        # -----------------------------

        with engine.begin() as connection:

            merged_rows = staging.merge_from_staging(
                batch_id,
                connection=connection
            )

            logger.info(
                "Merged %s rows into orders_enriched for batch %s",
                merged_rows,
                batch_id
            )

            top_products.to_sql(
                "top_products",
                connection,
                if_exists="append",
                index=False
            )

            logger.info(
                "Loaded %s rows into top_products for batch %s",
                len(top_products),
                batch_id
            )

            top_customers.to_sql(
                "top_customers",
                connection,
                if_exists="append",
                index=False
            )

            logger.info(
                "Loaded %s rows into top_customers for batch %s",
                len(top_customers),
                batch_id
            )

        # -----------------------------
        # Clear staging only after
        # successful curated commit
        # -----------------------------

        staging.clear_staging(
            batch_id,
            engine=engine
        )

        # -----------------------------
        # Mark batch successful
        # -----------------------------

        batches.complete_batch(
            batch_id,
            rows_loaded=merged_rows,
            engine=engine
        )

        logger.info(
            "Database loading completed successfully for batch %s",
            batch_id
        )

    except Exception:
        # Staging is intentionally retained on failure
        # so the batch can be inspected or retried.

        batches.fail_batch(
            batch_id,
            engine=engine
        )

        logger.exception(
            "Database loading failed for batch %s",
            batch_id
        )

        raise