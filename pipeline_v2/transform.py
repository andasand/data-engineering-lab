import os
import pandas as pd
import logging

logger = logging.getLogger("pipeline.transform")


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

    logger.info(
        "Loaded %s cleaned orders from %s",
        len(orders),
        cleaned_path
    )

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

    logger.info(
        "Enriched orders with product data."
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

    logger.info(
        "Enriched orders with customer data."
    )

    # -----------------------------
    # Calculate line revenue
    # -----------------------------

    orders["line_total"] = (
        orders["quantity"]
        * orders["price"]
    )

    logger.info(
        "Calculated line_total for %s orders.",
        len(orders)
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

    logger.info(
        "Calculated top %s products and top %s customers.",
        len(top_products),
        len(top_customers)
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

    logger.info(
        "Saved enriched orders to: %s",
        enriched_path
    )

    # -----------------------------
    # Stage summary
    # -----------------------------

    logger.info(
        "Transformation completed: %s enriched orders, %s product aggregates, %s customer aggregates",
        len(orders),
        len(top_products),
        len(top_customers)
    )

    # -----------------------------
    # Return analytics to serving
    # -----------------------------

    return orders, top_products, top_customers