import os
import pandas as pd


def run(
    products_path,
    customers_path,
    output_folder
):
    # -----------------------------
    # Define paths
    # -----------------------------

    cleaned_path = os.path.join(
        output_folder,
        "orders_clean.csv"
    )

    # -----------------------------
    # Load data
    # -----------------------------

    orders = pd.read_csv(cleaned_path)
    products = pd.read_csv(products_path)
    customers = pd.read_csv(customers_path)

    print(f"Loaded cleaned orders from: {cleaned_path}")

    # -----------------------------
    # Rename overlapping columns
    # -----------------------------

    products_renamed = products.rename(
        columns={"name": "product_name"}
    )

    customers_renamed = customers.rename(
        columns={"name": "customer_name"}
    )

    # -----------------------------
    # Enrich orders with products
    # -----------------------------

    orders = orders.merge(
        products_renamed[
            [
                "product_id",
                "product_name",
                "price"
            ]
        ],
        on="product_id",
        how="left"
    )

    # -----------------------------
    # Enrich orders with customers
    # -----------------------------

    orders = orders.merge(
        customers_renamed[
            [
                "customer_id",
                "customer_name"
            ]
        ],
        on="customer_id",
        how="left"
    )

    # -----------------------------
    # Calculate line revenue
    # -----------------------------

    orders["line_total"] = (
        orders["quantity"]
        * orders["price"]
    )

    # -----------------------------
    # Top products by revenue
    # -----------------------------

    top_products = (
        orders.groupby("product_id")["line_total"]
        .sum()
        .reset_index()
        .rename(
            columns={
                "line_total": "total_revenue"
            }
        )
        .merge(
            products_renamed,
            on="product_id",
            how="left"
        )
        .sort_values(
            "total_revenue",
            ascending=False
        )
        .head(3)
    )

    # -----------------------------
    # Top customers by spend
    # -----------------------------

    top_customers = (
        orders.groupby("customer_id")["line_total"]
        .sum()
        .reset_index()
        .rename(
            columns={
                "line_total": "total_spend"
            }
        )
        .merge(
            customers_renamed[
                [
                    "customer_id",
                    "customer_name"
                ]
            ],
            on="customer_id",
            how="left"
        )
        .sort_values(
            "total_spend",
            ascending=False
        )
        .head(3)
    )

    # -----------------------------
    # Save enriched dataset
    # -----------------------------

    enriched_path = os.path.join(
        output_folder,
        "orders_enriched.csv"
    )

    orders.to_csv(
        enriched_path,
        index=False
    )

    print(
        f"Saved enriched orders to: "
        f"{enriched_path}"
    )

    # -----------------------------
    # Display analytics
    # -----------------------------

    print("\nTop 3 Products by Revenue:")
    print(
        top_products[
            [
                "product_name",
                "total_revenue"
            ]
        ]
    )

    print("\nTop 3 Customers by Spend:")
    print(
        top_customers[
            [
                "customer_name",
                "total_spend"
            ]
        ]
    )

    # -----------------------------
    # Return analytics to serving
    # -----------------------------

    return top_products, top_customers