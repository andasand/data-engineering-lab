import os

import pandas as pd

import run_pipeline_v3


def test_failed_ingested_batch_resumes_downstream(
    tmp_path,
    monkeypatch
):
    # -----------------------------
    # Temporary project paths
    # -----------------------------

    data_folder = tmp_path / "data"
    insights_folder = tmp_path / "insights"
    logs_folder = tmp_path / "logs"

    data_folder.mkdir()
    insights_folder.mkdir()
    logs_folder.mkdir()

    batch_id = "orders_2026_01"
    file_name = f"{batch_id}.csv"

    # File still exists in data/
    (data_folder / file_name).write_text(
        "placeholder"
    )

    # Existing downstream artifact
    output_folder = (
        insights_folder / "2026_01"
    )

    output_folder.mkdir()

    pd.DataFrame([
        {
            "order_id": 1,
            "customer_id": 1,
            "product_id": 201,
            "quantity": 1,
            "order_date": "2026-01-01",
        }
    ]).to_csv(
        output_folder / "orders_clean.csv",
        index=False
    )

    # Existing ingest log says file
    # was already ingested.
    ingest_log = logs_folder / "ingest_log.csv"

    pd.DataFrame([
        {
            "file_name": file_name,
            "status": "Success",
            "rows": 1,
            "timestamp": "2026-08-21T00:00:00",
        }
    ]).to_csv(
        ingest_log,
        index=False
    )

    # -----------------------------
    # Patch config paths
    # -----------------------------

    monkeypatch.setattr(
        run_pipeline_v3,
        "DATA_FOLDER",
        str(data_folder)
    )

    monkeypatch.setattr(
        run_pipeline_v3,
        "INSIGHTS_FOLDER",
        str(insights_folder)
    )

    monkeypatch.setattr(
        run_pipeline_v3,
        "INGEST_LOG_PATH",
        str(ingest_log)
    )

    monkeypatch.setattr(
        run_pipeline_v3,
        "PRODUCTS_PATH",
        "products.csv"
    )

    monkeypatch.setattr(
        run_pipeline_v3,
        "CUSTOMERS_PATH",
        "customers.csv"
    )

    # -----------------------------
    # Fake database state
    # -----------------------------

    fake_engine = object()

    monkeypatch.setattr(
        run_pipeline_v3,
        "get_engine",
        lambda: fake_engine
    )

    monkeypatch.setattr(
        run_pipeline_v3.batches,
        "get_batch",
        lambda batch_id, engine=None: {
            "batch_id": batch_id,
            "status": "FAILED",
            "rows_loaded": 0,
        }
    )

    # -----------------------------
    # Track stage calls
    # -----------------------------

    calls = {
        "ingest": 0,
        "clean": 0,
        "transform": 0,
        "load": 0,
        "serve": 0,
    }

    def fake_ingest(*args, **kwargs):
        calls["ingest"] += 1

    def fake_clean(*args, **kwargs):
        calls["clean"] += 1

    def fake_transform(
        products_path,
        customers_path,
        output_folder
    ):
        calls["transform"] += 1

        assert output_folder == str(
            insights_folder / "2026_01"
        )

        enriched_orders = pd.DataFrame([
            {
                "order_id": 1
            }
        ])

        top_products = pd.DataFrame([
            {
                "product_id": 201
            }
        ])

        top_customers = pd.DataFrame([
            {
                "customer_id": 1
            }
        ])

        return (
            enriched_orders,
            top_products,
            top_customers,
        )

    def fake_load(
        enriched_orders,
        top_products,
        top_customers,
        batch_id
    ):
        calls["load"] += 1

        assert batch_id == "orders_2026_01"

    def fake_serve(
        top_products,
        top_customers,
        output_folder
    ):
        calls["serve"] += 1

    monkeypatch.setattr(
        run_pipeline_v3.ingest,
        "run",
        fake_ingest
    )

    monkeypatch.setattr(
        run_pipeline_v3.clean,
        "run",
        fake_clean
    )

    monkeypatch.setattr(
        run_pipeline_v3.transform,
        "run",
        fake_transform
    )

    monkeypatch.setattr(
        run_pipeline_v3.load,
        "run",
        fake_load
    )

    monkeypatch.setattr(
        run_pipeline_v3.serve,
        "run",
        fake_serve
    )

    # -----------------------------
    # Run resumable pipeline
    # -----------------------------

    run_pipeline_v3.run_pipeline()

    # -----------------------------
    # Verify resume behavior
    # -----------------------------

    assert calls["ingest"] == 0
    assert calls["clean"] == 0

    assert calls["transform"] == 1
    assert calls["load"] == 1
    assert calls["serve"] == 1