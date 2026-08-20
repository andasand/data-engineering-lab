import os
import pandas as pd
import logging

from logging_config import setup_logging
from pipeline_v2 import ingest, clean, transform, serve

from config import (
    DATA_FOLDER,
    ARCHIVE_FOLDER,
    INSIGHTS_FOLDER,
    PRODUCTS_PATH,
    CUSTOMERS_PATH,
    INGEST_LOG_PATH
)

setup_logging()

logger = logging.getLogger("pipeline")

# -----------------------------
# Run full pipeline
# -----------------------------

def run_pipeline():

    # Find an orders CSV
    files = os.listdir(DATA_FOLDER)

    file_name = next(
        (
            f for f in files
            if "orders" in f
            and f.endswith(".csv")
        ),
        None
    )

    if not file_name:
        logger.warning("No orders file found.")
        return


    # -----------------------------
    # Duplicate protection
    # -----------------------------

    if os.path.exists(INGEST_LOG_PATH):

        log = pd.read_csv(INGEST_LOG_PATH)

        if file_name in log["file_name"].values:

            logger.warning(
                f"File '{file_name}' has already been ingested. "
                f"Skipping."
            )

            return

        else:
            logger.info(
                "File not found in ingest log. "
                "Proceeding."
            )

    else:

        logger.info(
            "No ingest log found. "
            "Pipeline will create one."
        )


    logger.info(
        f"Starting pipeline for: {file_name}"
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

        enriched_orders, top_products, top_customers = (
            transform.run(
                PRODUCTS_PATH,
                CUSTOMERS_PATH,
                output_folder
            )
        )

        serve.run(
            top_products,
            top_customers,
            output_folder
        )

        logger.info(
            f"Pipeline completed successfully for: {file_name}"
        )

    except Exception as e:

        logger.exception(
            f"\nPipeline failed: {e}"
        )


# -----------------------------
# Entry point
# -----------------------------

if __name__ == "__main__":
    run_pipeline()