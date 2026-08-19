import os
import pandas as pd

from pipeline_v2 import clean


def test_clean_pipeline_removes_invalid_rows(tmp_path):
    # Temporary output folder
    output_folder = tmp_path / "insights"
    output_folder.mkdir()

    # Temporary data folder
    data_folder = tmp_path / "data"
    data_folder.mkdir()

    # -----------------------------
    # Create orders input
    # -----------------------------

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
            "customer_id": 1,
            "product_id": 201,
            "quantity": -1,
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
            "product_id": 999,
            "quantity": 1,
            "order_date": "2025-10-04",
        },
        {
            "order_id": 5,
            "customer_id": 1,
            "product_id": 201,
            "quantity": 1,
            "order_date": "not-a-date",
        },
    ])

    orders_path = output_folder / "orders.csv"

    orders.to_csv(
        orders_path,
        index=False
    )

    # -----------------------------
    # Create customers reference
    # -----------------------------

    customers = pd.DataFrame([
        {
            "customer_id": 1,
            "name": "Luke Skywalker"
        }
    ])

    customers_path = data_folder / "customers.csv"

    customers.to_csv(
        customers_path,
        index=False
    )

    # -----------------------------
    # Create products reference
    # -----------------------------

    products = pd.DataFrame([
        {
            "product_id": 201,
            "name": "Blue Milk Latte",
            "price": 4.5
        }
    ])

    products_path = data_folder / "products.csv"

    products.to_csv(
        products_path,
        index=False
    )

    # -----------------------------
    # Run cleaning stage
    # -----------------------------

    cleaned_path = clean.run(
        str(products_path),
        str(customers_path),
        str(output_folder)
    )

    # -----------------------------
    # Assertions
    # -----------------------------

    cleaned = pd.read_csv(
        cleaned_path
    )

    assert len(cleaned) == 1

    assert cleaned.iloc[0]["order_id"] == 1

    assert os.path.exists(
        output_folder / "orders_dropped.csv"
    )