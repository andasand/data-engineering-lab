import os
import pandas as pd
import shutil
import logging
from datetime import datetime

logger = logging.getLogger("pipeline.ingest")


def run(
    file_name,
    data_folder,
    archive_folder,
    insights_folder,
    log_path
):
    # -----------------------------
    # Build paths
    # -----------------------------

    file_path = os.path.join(
        data_folder,
        file_name
    )

    file_id = os.path.splitext(
        file_name
    )[0]

    logger.info(
        "Found file: %s",
        file_name
    )

    logger.info(
        "File ID: %s",
        file_id
    )

    # -----------------------------
    # Load file
    # -----------------------------

    orders = pd.read_csv(
        file_path
    )

    # -----------------------------
    # Validate schema
    # -----------------------------

    expected_cols = [
        "order_id",
        "customer_id",
        "product_id",
        "quantity",
        "order_date",
    ]

    actual_cols = list(
        orders.columns
    )

    schema_ok = (
        expected_cols == actual_cols
    )

    if not schema_ok:

        logger.error(
            "Schema validation failed for %s",
            file_name
        )

        if set(expected_cols) != set(actual_cols):

            logger.error(
                "Expected columns: %s",
                expected_cols
            )

            logger.error(
                "Found columns: %s",
                actual_cols
            )

        else:

            logger.error(
                "Columns are present but in the wrong order."
            )

        status = "Schema Failed"
        row_count = 0

    else:

        logger.info(
            "Schema validation passed for %s",
            file_name
        )

        status = "Success"
        row_count = len(orders)

        logger.info(
            "Rows found: %s",
            row_count
        )

    # -----------------------------
    # Log schema failure and stop
    # -----------------------------

    if not schema_ok:

        log_entry = pd.DataFrame([{
            "file_name": file_name,
            "status": status,
            "rows": row_count,
            "timestamp": datetime.now()
                .replace(microsecond=0)
                .isoformat()
        }])

        if os.path.exists(
            log_path
        ):

            log = pd.read_csv(
                log_path
            )

            log = pd.concat(
                [log, log_entry],
                ignore_index=True
            )

        else:

            log = log_entry

        log.to_csv(
            log_path,
            index=False
        )

        logger.error(
            "Schema failure logged to: %s",
            log_path
        )

        raise ValueError(
            f"Schema validation failed for {file_name}"
        )

    # -----------------------------
    # Determine monthly output folder
    # -----------------------------

    order_date = pd.to_datetime(
        orders["order_date"].iloc[0]
    )

    month_folder = (
        f"{order_date.year}_"
        f"{order_date.month:02}"
    )

    output_folder = os.path.join(
        insights_folder,
        month_folder
    )

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    # -----------------------------
    # Save validated copy
    # -----------------------------

    output_path = os.path.join(
        output_folder,
        "orders.csv"
    )

    orders.to_csv(
        output_path,
        index=False
    )

    logger.info(
        "Saved orders data to: %s",
        output_path
    )

    # -----------------------------
    # Archive raw file
    # -----------------------------

    archive_path = os.path.join(
        archive_folder,
        file_name
    )

    shutil.move(
        file_path,
        archive_path
    )

    logger.info(
        "Moved raw file to: %s",
        archive_path
    )

    # -----------------------------
    # Log ingestion outcome
    # -----------------------------

    log_entry = pd.DataFrame([{
        "file_name": file_name,
        "status": status,
        "rows": row_count,
        "timestamp": datetime.now()
            .replace(microsecond=0)
            .isoformat()
    }])

    if os.path.exists(
        log_path
    ):

        log = pd.read_csv(
            log_path
        )

        log = pd.concat(
            [log, log_entry],
            ignore_index=True
        )

    else:

        log = log_entry

    log.to_csv(
        log_path,
        index=False
    )

    logger.info(
        "Logged ingestion outcome to: %s",
        log_path
    )

    logger.info(
        "Ingestion completed successfully for %s",
        file_name
    )

    # -----------------------------
    # Return location for downstream stages
    # -----------------------------

    return output_folder