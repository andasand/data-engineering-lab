import os
import pandas as pd
import logging

from logging_config import setup_logging

from pipeline_v2 import (
    ingest,
    clean,
    transform,
    serve
)

from pipeline_v3 import load

from config import (
    DATA_FOLDER,
    ARCHIVE_FOLDER,
    INSIGHTS_FOLDER,
    PRODUCTS_PATH,
    CUSTOMERS_PATH,
    INGEST_LOG_PATH
)


setup_logging()

logger = logging.getLogger("pipeline.v3")


def run_pipeline():

    # -----------------------------
    # Find orders file
    # -----------------------------

    files = os.listdir(
        DATA_FOLDER
    )

    file_name = next(
        (
            f for f in files
            if "orders" in f
            and f.endswith(".csv")
        ),
        None
    )

    if not file_name:

        logger.warning(
            "No orders file found."
        )

        return

    batch_id = os.path.splitext(file_name)[0]

    # -----------------------------
    # Duplicate protection
    # -----------------------------

    if os.path.exists(
        INGEST_LOG_PATH
    ):

        log = pd.read_csv(
            INGEST_LOG_PATH
        )

        if file_name in log["file_name"].values:

            logger.warning(
                "File '%s' has already been ingested. Skipping.",
                file_name
            )

            return

        logger.info(
            "File not found in ingest log. Proceeding."
        )

    else:

        logger.info(
            "No ingest log found. Pipeline will create one."
        )

    logger.info(
        "Starting v3 pipeline for %s",
        file_name
    )

    # -----------------------------
    # Execute pipeline stages
    # -----------------------------

    try:

        output_folder = ingest.run(
            file_name,
            DATA_FOLDER,
            ARCHIVE_FOLDER,
            INSIGHTS_FOLDER,
            INGEST_LOG_PATH
        )

        clean.run(
            PRODUCTS_PATH,
            CUSTOMERS_PATH,
            output_folder
        )

        (
            enriched_orders,
            top_products,
            top_customers
        ) = transform.run(
            PRODUCTS_PATH,
            CUSTOMERS_PATH,
            output_folder
        )

        load.run(
            enriched_orders,
            top_products,
            top_customers,
            batch_id
        )

        serve.run(
            top_products,
            top_customers,
            output_folder
        )

        logger.info(
            "v3 pipeline completed successfully for %s",
            file_name
        )

    except Exception:

        logger.exception(
            "v3 pipeline failed for %s",
            file_name
        )


if __name__ == "__main__":
    run_pipeline()