import pandas as pd

from pipeline_v2 import transform


def test_transform_enriches_and_aggregates(tmp_path):
    # -----------------------------
    # Temporary folders
    # -----------------------------

    output_folder = tmp_path / "insights"
    data_folder = tmp_path / "data"

    output_folder.mkdir()
    data_folder.mkdir()

    # -----------------------------
    # Create cleaned orders
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
            "customer_id": 2,
            "product_id": 202,
            "quantity": 3,
            "order_date": "2025-10-02",
        },
        {
            "order_id": 3,
            "customer_id": 1,
            "product_id": 201,
            "quantity": 1,
            "order_date": "2025-10-03",
        },
    ])

    cleaned_path = output_folder / "orders_clean.csv"
    orders.to_csv(cleaned_path, index=False)

    # -----------------------------
    # Create products reference
    # -----------------------------

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

    products_path = data_folder / "products.csv"
    products.to_csv(products_path, index=False)

    # -----------------------------
    # Create customers reference
    # -----------------------------

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

    customers_path = data_folder / "customers.csv"
    customers.to_csv(customers_path, index=False)

    # -----------------------------
    # Run transformation
    # -----------------------------

    top_products, top_customers = transform.run(
        str(products_path),
        str(customers_path),
        str(output_folder)
    )

    # -----------------------------
    # Validate enriched output
    # -----------------------------

    enriched_path = output_folder / "orders_enriched.csv"

    assert enriched_path.exists()

    enriched = pd.read_csv(enriched_path)

    assert "product_name" in enriched.columns
    assert "customer_name" in enriched.columns
    assert "price" in enriched.columns
    assert "line_total" in enriched.columns

    # 2 * 4.5
    assert enriched.iloc[0]["line_total"] == 9.0

    # -----------------------------
    # Validate product aggregation
    # -----------------------------

    assert top_products.iloc[0]["product_name"] == "Blue Milk Latte"
    assert top_products.iloc[0]["total_revenue"] == 13.5

    # -----------------------------
    # Validate customer aggregation
    # -----------------------------

    assert top_customers.iloc[0]["customer_name"] == "Luke Skywalker"
    assert top_customers.iloc[0]["total_spend"] == 13.5