import os
import pandas as pd
import pytest

from pipeline_v2 import ingest


def test_ingest_creates_monthly_output_archives_and_logs(tmp_path):
    # -----------------------------
    # Temporary folders
    # -----------------------------

    data_folder = tmp_path / "data"
    archive_folder = data_folder / "archive"
    insights_folder = tmp_path / "insights"
    logs_folder = tmp_path / "logs"

    data_folder.mkdir()
    archive_folder.mkdir()
    insights_folder.mkdir()
    logs_folder.mkdir()

    # -----------------------------
    # Create valid orders file
    # -----------------------------

    file_name = "orders_2025_10.csv"

    orders = pd.DataFrame([
        {
            "order_id": 1,
            "customer_id": 1,
            "product_id": 201,
            "quantity": 2,
            "order_date": "2025-10-01",
        },
        {
            "order_id": 2,
            "customer_id": 2,
            "product_id": 202,
            "quantity": 1,
            "order_date": "2025-10-02",
        },
    ])

    input_path = data_folder / file_name

    orders.to_csv(
        input_path,
        index=False
    )

    log_path = logs_folder / "ingest_log.csv"

    # -----------------------------
    # Run ingestion
    # -----------------------------

    output_folder = ingest.run(
        file_name,
        str(data_folder),
        str(archive_folder),
        str(insights_folder),
        str(log_path)
    )

    # -----------------------------
    # Assertions
    # -----------------------------

    expected_output_folder = (
        insights_folder / "2025_10"
    )

    expected_orders_path = (
        expected_output_folder / "orders.csv"
    )

    expected_archive_path = (
        archive_folder / file_name
    )

    assert output_folder == str(
        expected_output_folder
    )

    assert expected_orders_path.exists()

    assert expected_archive_path.exists()

    assert not input_path.exists()

    assert log_path.exists()

    log = pd.read_csv(log_path)

    assert len(log) == 1
    assert log.iloc[0]["file_name"] == file_name
    assert log.iloc[0]["status"] == "Success"
    assert log.iloc[0]["rows"] == 2

def test_ingest_rejects_bad_schema_and_logs_failure(tmp_path):
    data_folder = tmp_path / "data"
    archive_folder = data_folder / "archive"
    insights_folder = tmp_path / "insights"
    logs_folder = tmp_path / "logs"

    data_folder.mkdir()
    archive_folder.mkdir()
    insights_folder.mkdir()
    logs_folder.mkdir()

    file_name = "orders_bad.csv"

    # Missing the required "quantity" column
    bad_orders = pd.DataFrame([
        {
            "order_id": 1,
            "customer_id": 1,
            "product_id": 201,
            "order_date": "2025-10-01",
        }
    ])

    input_path = data_folder / file_name

    bad_orders.to_csv(
        input_path,
        index=False
    )

    log_path = logs_folder / "ingest_log.csv"

    with pytest.raises(ValueError):
        ingest.run(
            file_name,
            str(data_folder),
            str(archive_folder),
            str(insights_folder),
            str(log_path)
        )

    # Raw file should not have been archived
    assert input_path.exists()

    # Audit log should record the failure
    assert log_path.exists()

    log = pd.read_csv(log_path)

    assert len(log) == 1
    assert log.iloc[0]["file_name"] == file_name
    assert log.iloc[0]["status"] == "Schema Failed"
    assert log.iloc[0]["rows"] == 0