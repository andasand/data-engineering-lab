import os
import pandas as pd

output_folder = "insights/2025_10"

cleaned_path = os.path.join(
    output_folder,
    "orders_clean.csv"
)

products_path = "data/products.csv"
customers_path = "data/customers.csv"

orders = pd.read_csv(cleaned_path)
products = pd.read_csv(products_path)
customers = pd.read_csv(customers_path)

print("Clean orders:")
print(orders.head())

print("\nProducts:")
print(products.head())

print("\nCustomers:")
print(customers.head())

# Rename generic "name" columns before joining
products_renamed = products.rename(
    columns={"name": "product_name"}
)

customers_renamed = customers.rename(
    columns={"name": "customer_name"}
)

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

orders = orders.merge(customers_renamed[
    [
         "customer_id",
        "customer_name"
    ]
],
on="customer_id",
how="left"
)

orders["line_total"] = (
    orders["quantity"]
    * orders["price"]
)

orders_preview = orders[
    [
        "order_id",
        "customer_name",
        "product_name",
        "quantity",
        "price",
        "line_total",
    ]
].head(10)

print("\nOrder Calculations:")
print(orders_preview)

# Top 3 products by revenue
top_products = (
    orders.groupby("product_id")["line_total"]
    .sum()
    .reset_index()
    .rename(columns={"line_total": "total_revenue"})
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

print("\nTop 3 Products by Revenue:")
print(
    top_products[
        [
            "product_name",
            "total_revenue"
        ]
    ]
)

# Top 3 customers by spend
top_customers = (
    orders.groupby("customer_id")["line_total"]
    .sum()
    .reset_index()
    .rename(columns={"line_total": "total_spend"})
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

print("\nTop 3 Customers by Spend:")
print(
    top_customers[
        [
            "customer_name",
            "total_spend"
        ]
    ]
)

# Save enriched orders
enriched_path = os.path.join(
    output_folder,
    "orders_enriched.csv"
)

orders.to_csv(
    enriched_path,
    index=False
)

print(f"\nSaved enriched orders to: {enriched_path}")

top_products_path = os.path.join(
    output_folder,
    "top_products.csv"
)

top_products.to_csv(
    top_products_path,
    index=False
)

print(f"Saved top products to: {top_products_path}")

top_customers_path = os.path.join(
    output_folder,
    "top_customers.csv"
)

top_customers.to_csv(
    top_customers_path,
    index=False
)

print(f"Saved top customers to: {top_customers_path}")