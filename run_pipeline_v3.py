import os
import logging

import pandas as pd

from logging_config import setup_logging

from pipeline_v2 import (
    ingest,
    clean,
    transform,
    serve,
)

from pipeline_v3 import (
    load,
    batches,
)

from pipeline_v3.database import get_engine

from config import (
    DATA_FOLDER,
    ARCHIVE_FOLDER,
    INSIGHTS_FOLDER,
    PRODUCTS_PATH,
    CUSTOMERS_PATH,
    INGEST_LOG_PATH,
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

    batch_id = os.path.splitext(
        file_name
    )[0]

    engine = get_engine()

    # -----------------------------
    # Determine ingestion state
    # -----------------------------

    already_ingested = False

    if os.path.exists(
        INGEST_LOG_PATH
    ):

        log = pd.read_csv(
            INGEST_LOG_PATH
        )

        already_ingested = (
            file_name
            in log["file_name"].values
        )

    # -----------------------------
    # Decide whether to skip
    # or resume
    # -----------------------------

    if already_ingested:

        batch = batches.get_batch(
            batch_id,
            engine=engine
        )

        if (
            batch is not None
            and batch["status"] == "SUCCESS"
        ):

            logger.warning(
                "File '%s' has already been ingested "
                "and batch %s completed successfully. "
                "Skipping.",
                file_name,
                batch_id,
            )

            return

        logger.warning(
            "File '%s' was already ingested, "
            "but batch %s is not complete. "
            "Resuming downstream processing.",
            file_name,
            batch_id,
        )

    else:

        if os.path.exists(
            INGEST_LOG_PATH
        ):

            logger.info(
                "File not found in ingest log. "
                "Proceeding with full pipeline."
            )

        else:

            logger.info(
                "No ingest log found. "
                "Pipeline will create one."
            )

    logger.info(
        "Starting v3 pipeline for %s",
        file_name
    )

    # -----------------------------
    # Execute pipeline stages
    # -----------------------------

    try:

        if already_ingested:

            # Reuse the existing monthly
            # output folder.
            parts = batch_id.split("_")

            year = parts[-2]
            month = parts[-1]

            output_folder = os.path.join(
                INSIGHTS_FOLDER,
                f"{year}_{month}"
            )

            cleaned_path = os.path.join(
                output_folder,
                "orders_clean.csv"
            )

            if not os.path.exists(
                cleaned_path
            ):
                raise FileNotFoundError(
                    "Cannot resume batch "
                    f"{batch_id}: "
                    f"{cleaned_path} "
                    "does not exist."
                )

            logger.info(
                "Resuming pipeline from existing "
                "output folder: %s",
                output_folder,
            )

        else:

            output_folder = ingest.run(
                file_name,
                DATA_FOLDER,
                ARCHIVE_FOLDER,
                INSIGHTS_FOLDER,
                INGEST_LOG_PATH,
            )

            clean.run(
                PRODUCTS_PATH,
                CUSTOMERS_PATH,
                output_folder,
            )

        (
            enriched_orders,
            top_products,
            top_customers,
        ) = transform.run(
            PRODUCTS_PATH,
            CUSTOMERS_PATH,
            output_folder,
        )

        load.run(
            enriched_orders,
            top_products,
            top_customers,
            batch_id,
        )

        serve.run(
            top_products,
            top_customers,
            output_folder,
        )

        logger.info(
            "v3 pipeline completed successfully for %s",
            file_name,
        )

    except Exception:

        logger.exception(
            "v3 pipeline failed for %s",
            file_name,
        )


if __name__ == "__main__":
    run_pipeline()