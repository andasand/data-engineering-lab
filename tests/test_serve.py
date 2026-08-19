import pandas as pd

from pipeline_v2 import serve


def test_serve_creates_analytics_and_charts(tmp_path):

    # -----------------------------
    # Test analytics data
    # -----------------------------

    top_products = pd.DataFrame([
        {
            "product_id": 201,
            "product_name": "Blue Milk Latte",
            "total_revenue": 100.0,
        },
        {
            "product_id": 202,
            "product_name": "Death Star Espresso",
            "total_revenue": 75.0,
        },
    ])

    top_customers = pd.DataFrame([
        {
            "customer_id": 1,
            "customer_name": "Luke Skywalker",
            "total_spend": 90.0,
        },
        {
            "customer_id": 2,
            "customer_name": "Leia Organa",
            "total_spend": 70.0,
        },
    ])

    # -----------------------------
    # Run serving stage
    # -----------------------------

    serve.run(
        top_products,
        top_customers,
        str(tmp_path)
    )

    # -----------------------------
    # Expected artifacts
    # -----------------------------

    top_products_csv = (
        tmp_path / "top_products.csv"
    )

    top_customers_csv = (
        tmp_path / "top_customers.csv"
    )

    top_products_chart = (
        tmp_path / "top_products.png"
    )

    top_customers_chart = (
        tmp_path / "top_customers.png"
    )

    # -----------------------------
    # Verify files exist
    # -----------------------------

    assert top_products_csv.exists()
    assert top_customers_csv.exists()

    assert top_products_chart.exists()
    assert top_customers_chart.exists()

    # Charts should not be empty files
    assert top_products_chart.stat().st_size > 0
    assert top_customers_chart.stat().st_size > 0

    # -----------------------------
    # Verify CSV contents
    # -----------------------------

    saved_products = pd.read_csv(
        top_products_csv
    )

    saved_customers = pd.read_csv(
        top_customers_csv
    )

    assert len(saved_products) == 2
    assert len(saved_customers) == 2

    assert (
        saved_products.iloc[0]["product_name"]
        == "Blue Milk Latte"
    )

    assert (
        saved_customers.iloc[0]["customer_name"]
        == "Luke Skywalker"
    )