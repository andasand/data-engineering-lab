import os
import pandas as pd

output_folder = "insights/2025_10"

orders_path = os.path.join(
    output_folder,
    "orders.csv"
)

products_path = "data/products.csv"
customers_path = "data/customers.csv"

orders = pd.read_csv(orders_path)
products = pd.read_csv(products_path)
customers = pd.read_csv(customers_path)

print("Orders:")
print(orders.head())

print("\nProducts:")
print(products.head())

print("\nCustomers:")
print(customers.head())

# Keep a backup of the original orders
orders_raw = orders.copy()

# Required columns
expected_cols = [
    "order_id",
    "customer_id",
    "product_id",
    "quantity",
    "order_date"]

# Find rows with any missing required values
missing_mask = orders[expected_cols].isnull().any(axis=1)

dropped_ids = orders.loc[missing_mask, "order_id"].tolist()

orders = orders[~missing_mask]

print(
    f"\nRemoved {len(dropped_ids)} rows "
    f"with missing required values: {dropped_ids}"
)

# Parse order_date values
orders["order_date_parsed"] = pd.to_datetime(orders["order_date"], errors="coerce")

# Identify invalid dates
invalid_dates = orders["order_date_parsed"].isnull()

dropped_ids = orders.loc[invalid_dates, "order_id"].tolist()

orders = orders[~invalid_dates]

print(
    f"Removed {len(dropped_ids)} rows "
    f"with invalid order_date: {dropped_ids}"
)

# Validate numeric fields
numeric_fields = [
    "customer_id",
    "product_id",
    "quantity"
]

invalid_numeric_mask = pd.Series(False, index=orders.index)

for field in numeric_fields:

    orders[f"{field}_checked"] = pd.to_numeric(
        orders[field], 
        errors="coerce"
        )

    invalids = (
        orders[f"{field}_checked"].isnull()
        | (orders[f"{field}_checked"] < 0)
    )

    if invalids.any():
        dropped = orders.loc[
            invalids,
            "order_id"
        ].tolist()

        print(
            f"Removed {len(dropped)} rows "
            f"with invalid {field}: {dropped}"
        )

        invalid_numeric_mask |= invalids

orders = orders[~invalid_numeric_mask]

orders["customer_id"] = (
    orders["customer_id_checked"].astype(int)
)

orders["product_id"] = (
    orders["product_id_checked"].astype(int)
)

orders["quantity"] = (
    orders["quantity_checked"].astype(int)
)

orders.drop(
    columns=[
        f"{field}_checked"
        for field in numeric_fields
    ],
    inplace=True
)

# Remove duplicate rows
duplicates = orders.duplicated()

dropped_ids = orders.loc[
    duplicates,
    "order_id"
].tolist()

orders = orders[~duplicates]

print(
    f"Removed {len(dropped_ids)} duplicate rows: "
    f"{dropped_ids}"
)

# Validate customer_id against customers table
valid_customer_ids = set(customers["customer_id"])

invalid_customers = ~orders["customer_id"].isin(valid_customer_ids)

dropped_ids = orders.loc[
    invalid_customers,
    "order_id"
].tolist()

orders = orders[~invalid_customers]

print(
    f"Removed {len(dropped_ids)} rows "
    f"with invalid customer_id: {dropped_ids}"
)

# Validate product_id against products table
valid_product_ids = set(products["product_id"])

invalid_products = ~orders["product_id"].isin(valid_product_ids)

dropped_ids = orders.loc[
    invalid_products,
    "order_id"].tolist()

orders = orders[~invalid_products]

print(
    f"Removed {len(dropped_ids)} rows "
    f"with invalid product_id: {dropped_ids}"
)

# Collect all dropped rows from the original dataset
dropped_rows = orders_raw.loc[
    ~orders_raw["order_id"].isin(orders["order_id"])
].copy()

if not dropped_rows.empty:
    dropped_path = os.path.join(
        output_folder,
        "orders_dropped.csv"
    )
    dropped_rows.to_csv(dropped_path, index=False)

    print(
        f"Saved {len(dropped_rows)} dropped rows to: "
        f"{dropped_path}"
        )
else:
    print("No rows were dropped during cleaning.") 

orders = orders.drop(
    columns=["order_date_parsed"]
).reset_index(drop=True)

cleaned_path = os.path.join(
    output_folder,
    "orders_clean.csv")

orders.to_csv(cleaned_path, index=False)

print(f"Cleaned data saved to: "
      f"{cleaned_path}"
      )

print(
    f"Final clean row count: {len(orders)}"
)