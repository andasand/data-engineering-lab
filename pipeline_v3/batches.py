import logging

import pandas as pd
from sqlalchemy import inspect, text

from pipeline_v3.database import get_engine


logger = logging.getLogger("pipeline.batches")


TABLE_NAME = "pipeline_batches"


def ensure_table(engine=None):
    """
    Create the pipeline_batches control table if it does not already exist.
    """

    if engine is None:
        engine = get_engine()

    inspector = inspect(engine)

    if inspector.has_table(TABLE_NAME):
        return

    create_table_sql = text(
        """
        CREATE TABLE pipeline_batches (
            batch_id VARCHAR(255) PRIMARY KEY,
            status VARCHAR(20) NOT NULL,
            rows_loaded INTEGER NOT NULL DEFAULT 0,
            started_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP NULL
        )
        """
    )

    with engine.begin() as connection:
        connection.execute(create_table_sql)

    logger.info(
        "Created control table: %s",
        TABLE_NAME
    )


def get_batch(batch_id, engine=None):
    """
    Return batch metadata as a dictionary.
    Return None if the batch does not exist.
    """

    if engine is None:
        engine = get_engine()

    ensure_table(engine)

    query = text(
        """
        SELECT
            batch_id,
            status,
            rows_loaded,
            started_at,
            completed_at
        FROM pipeline_batches
        WHERE batch_id = :batch_id
        """
    )

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {"batch_id": batch_id}
        ).mappings().first()

    if row is None:
        return None

    return dict(row)


def batch_exists(batch_id, engine=None):
    """
    Return True when the batch already has a SUCCESS record.
    """

    batch = get_batch(
        batch_id,
        engine=engine
    )

    return (
        batch is not None
        and batch["status"] == "SUCCESS"
    )


def start_batch(batch_id, engine=None):
    """
    Insert a RUNNING record for a new batch.

    If a prior FAILED or RUNNING record exists for the same batch,
    reset it to RUNNING so the batch can be retried.
    """

    if engine is None:
        engine = get_engine()

    ensure_table(engine)

    started_at = pd.Timestamp.now("UTC").to_pydatetime()

    existing = get_batch(
        batch_id,
        engine=engine
    )

    if existing is None:

        statement = text(
            """
            INSERT INTO pipeline_batches (
                batch_id,
                status,
                rows_loaded,
                started_at,
                completed_at
            )
            VALUES (
                :batch_id,
                'RUNNING',
                0,
                :started_at,
                NULL
            )
            """
        )

        with engine.begin() as connection:
            connection.execute(
                statement,
                {
                    "batch_id": batch_id,
                    "started_at": started_at
                }
            )

    else:

        statement = text(
            """
            UPDATE pipeline_batches
            SET
                status = 'RUNNING',
                rows_loaded = 0,
                started_at = :started_at,
                completed_at = NULL
            WHERE batch_id = :batch_id
            """
        )

        with engine.begin() as connection:
            connection.execute(
                statement,
                {
                    "batch_id": batch_id,
                    "started_at": started_at
                }
            )

    logger.info(
        "Batch %s marked RUNNING",
        batch_id
    )


def complete_batch(
    batch_id,
    rows_loaded,
    engine=None
):
    """
    Mark a batch as SUCCESS.
    """

    if engine is None:
        engine = get_engine()

    ensure_table(engine)

    completed_at = pd.Timestamp.now("UTC").to_pydatetime()

    statement = text(
        """
        UPDATE pipeline_batches
        SET
            status = 'SUCCESS',
            rows_loaded = :rows_loaded,
            completed_at = :completed_at
        WHERE batch_id = :batch_id
        """
    )

    with engine.begin() as connection:
        connection.execute(
            statement,
            {
                "batch_id": batch_id,
                "rows_loaded": rows_loaded,
                "completed_at": completed_at
            }
        )

    logger.info(
        "Batch %s marked SUCCESS with %s rows",
        batch_id,
        rows_loaded
    )


def fail_batch(batch_id, engine=None):
    """
    Mark a batch as FAILED.
    """

    if engine is None:
        engine = get_engine()

    ensure_table(engine)

    completed_at = pd.Timestamp.utcnow().to_pydatetime()

    statement = text(
        """
        UPDATE pipeline_batches
        SET
            status = 'FAILED',
            completed_at = :completed_at
        WHERE batch_id = :batch_id
        """
    )

    with engine.begin() as connection:
        connection.execute(
            statement,
            {
                "batch_id": batch_id,
                "completed_at": completed_at
            }
        )

    logger.error(
        "Batch %s marked FAILED",
        batch_id
    )