import os
import logging
import matplotlib.pyplot as plt

logger = logging.getLogger("pipeline.serve")


def run(
    top_products,
    top_customers,
    output_folder
):
    # -----------------------------
    # Save analytics as CSV
    # -----------------------------

    top_products_path = os.path.join(
        output_folder,
        "top_products.csv"
    )

    top_customers_path = os.path.join(
        output_folder,
        "top_customers.csv"
    )

    top_products.to_csv(
        top_products_path,
        index=False
    )

    top_customers.to_csv(
        top_customers_path,
        index=False
    )

    logger.info(
        "Saved analytics CSV files to %s and %s",
        top_products_path,
        top_customers_path
    )

    # -----------------------------
    # Top products chart
    # -----------------------------

    plt.figure(figsize=(8, 4))

    plt.bar(
        top_products["product_name"],
        top_products["total_revenue"]
    )

    plt.title(
        "Top 3 Products by Revenue"
    )

    plt.ylabel("Revenue")
    plt.tight_layout()

    products_chart_path = os.path.join(
        output_folder,
        "top_products.png"
    )

    plt.savefig(products_chart_path)
    plt.close()

    logger.info(
        "Saved top products chart to: %s",
        products_chart_path
    )

    # -----------------------------
    # Top customers chart
    # -----------------------------

    plt.figure(figsize=(8, 4))

    plt.bar(
        top_customers["customer_name"],
        top_customers["total_spend"]
    )

    plt.title(
        "Top 3 Customers by Spend"
    )

    plt.ylabel("Total Spend")
    plt.tight_layout()

    customers_chart_path = os.path.join(
        output_folder,
        "top_customers.png"
    )

    plt.savefig(customers_chart_path)
    plt.close()

    logger.info(
        "Saved top customers chart to: %s",
        customers_chart_path
    )

    logger.info(
        "Serving completed: 2 analytics CSV files and 2 chart files created"
    )