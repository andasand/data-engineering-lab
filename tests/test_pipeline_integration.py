import pandas as pd

from pipeline_v2 import ingest, clean, transform, serve


def test_full_pipeline_end_to_end(tmp_path):
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
    # Source data
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
            "quantity": 3,
            "order_date": "2025-10-02",
        },
        {
            "order_id": 3,
            "customer_id": 99,
            "product_id": 201,
            "quantity": 1,
            "order_date": "2025-10-03",
        },
        {
            "order_id": 4,
            "customer_id": 1,
            "product_id": 201,
            "quantity": -1,
            "order_date": "2025-10-04",
        },
    ])

    customers = pd.DataFrame([
        {
            "customer_id": 1,
            "name": "Luke Skywalker",
        },
        {
            "customer_id": 2,
            "name": "Leia Organa",
        },
    ])

    products = pd.DataFrame([
        {
            "product_id": 201,
            "name": "Blue Milk Latte",
            "price": 4.5,
        },
        {
            "product_id": 202,
            "name": "Death Star Espresso",
            "price": 3.0,
        },
    ])

    orders_path = data_folder / file_name
    customers_path = data_folder / "customers.csv"
    products_path = data_folder / "products.csv"
    log_path = logs_folder / "ingest_log.csv"

    orders.to_csv(
        orders_path,
        index=False
    )

    customers.to_csv(
        customers_path,
        index=False
    )

    products.to_csv(
        products_path,
        index=False
    )

    # -----------------------------
    # 1. Ingest
    # -----------------------------

    output_folder = ingest.run(
        file_name,
        str(data_folder),
        str(archive_folder),
        str(insights_folder),
        str(log_path)
    )

    # -----------------------------
    # 2. Clean
    # -----------------------------

    cleaned_path = clean.run(
        str(products_path),
        str(customers_path),
        output_folder
    )

    # -----------------------------
    # 3. Transform
    # -----------------------------

    enriched_orders, top_products, top_customers = transform.run(
        str(products_path),
        str(customers_path),
        output_folder
    )

    # -----------------------------
    # 4. Serve
    # -----------------------------

    serve.run(
        top_products,
        top_customers,
        output_folder
    )

    # -----------------------------
    # Validate ingestion
    # -----------------------------

    assert (
        archive_folder / file_name
    ).exists()

    assert log_path.exists()

    # -----------------------------
    # Validate cleaning
    # -----------------------------

    cleaned = pd.read_csv(
        cleaned_path
    )

    # 4 input rows, 2 invalid rows
    assert len(cleaned) == 2

    assert set(
        cleaned["order_id"]
    ) == {1, 2}

    dropped_path = (
        insights_folder
        / "2025_10"
        / "orders_dropped.csv"
    )

    assert dropped_path.exists()

    dropped = pd.read_csv(
        dropped_path
    )

    assert set(
        dropped["order_id"]
    ) == {3, 4}

    # -----------------------------
    # Validate transformation
    # -----------------------------

    enriched_path = (
        insights_folder
        / "2025_10"
        / "orders_enriched.csv"
    )

    assert enriched_path.exists()

    enriched = pd.read_csv(
        enriched_path
    )

    assert len(enriched) == 2

    assert "line_total" in enriched.columns

    # Luke: 2 * 4.5
    luke_order = enriched[
        enriched["order_id"] == 1
    ].iloc[0]

    assert luke_order["line_total"] == 9.0

    # -----------------------------
    # Validate serving
    # -----------------------------

    output_dir = (
        insights_folder / "2025_10"
    )

    assert (
        output_dir / "top_products.csv"
    ).exists()

    assert (
        output_dir / "top_customers.csv"
    ).exists()

    assert (
        output_dir / "top_products.png"
    ).exists()

    assert (
        output_dir / "top_customers.png"
    ).exists()