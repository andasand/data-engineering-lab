import os
import pandas as pd
import logging

logger = logging.getLogger("pipeline.clean")


def run(
    products_path,
    customers_path,
    output_folder
):
    # -----------------------------
    # Define input paths
    # -----------------------------

    orders_path = os.path.join(
        output_folder,
        "orders.csv"
    )

    # -----------------------------
    # Load data
    # -----------------------------

    orders = pd.read_csv(orders_path)
    products = pd.read_csv(products_path)
    customers = pd.read_csv(customers_path)

    input_row_count = len(orders)

    logger.info(
        "Loaded %s orders from %s",
        input_row_count,
        orders_path
    )

    # Keep original copy for dropped-row audit
    orders_raw = orders.copy()

    expected_cols = [
        "order_id",
        "customer_id",
        "product_id",
        "quantity",
        "order_date",
    ]

    # -----------------------------
    # Missing required values
    # -----------------------------

    missing_mask = (
        orders[expected_cols]
        .isnull()
        .any(axis=1)
    )

    dropped_ids = orders.loc[
        missing_mask,
        "order_id"
    ].tolist()

    orders = orders[~missing_mask]

    if dropped_ids:
        logger.warning(
            "Removed %s rows with missing required values: %s",
            len(dropped_ids),
            dropped_ids
        )
    else:
        logger.info(
            "No rows with missing required values detected."
        )

    # -----------------------------
    # Invalid dates
    # -----------------------------

    orders["order_date_parsed"] = pd.to_datetime(
        orders["order_date"],
        errors="coerce"
    )

    invalid_dates = (
        orders["order_date_parsed"]
        .isnull()
    )

    dropped_ids = orders.loc[
        invalid_dates,
        "order_id"
    ].tolist()

    orders = orders[~invalid_dates]

    if dropped_ids:
        logger.warning(
            "Removed %s rows with invalid order_date: %s",
            len(dropped_ids),
            dropped_ids
        )
    else:
        logger.info(
            "No invalid order_date values detected."
        )

    # -----------------------------
    # Numeric validation
    # -----------------------------

    numeric_fields = [
        "customer_id",
        "product_id",
        "quantity",
    ]

    invalid_numeric_mask = pd.Series(
        False,
        index=orders.index
    )

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

            logger.warning(
                "Removed %s rows with invalid %s: %s",
                len(dropped),
                field,
                dropped
            )

            invalid_numeric_mask |= invalids

        else:
            logger.info(
                "No invalid %s values detected.",
                field
            )

    orders = orders[
        ~invalid_numeric_mask
    ]

    # Convert valid numeric columns to integers
    orders["customer_id"] = (
        orders["customer_id_checked"]
        .astype(int)
    )

    orders["product_id"] = (
        orders["product_id_checked"]
        .astype(int)
    )

    orders["quantity"] = (
        orders["quantity_checked"]
        .astype(int)
    )

    # Remove temporary checked columns
    orders.drop(
        columns=[
            f"{field}_checked"
            for field in numeric_fields
        ],
        inplace=True
    )

    # -----------------------------
    # Duplicate rows
    # -----------------------------

    duplicates = orders.duplicated()

    dropped_ids = orders.loc[
        duplicates,
        "order_id"
    ].tolist()

    orders = orders[
        ~duplicates
    ]

    if dropped_ids:
        logger.warning(
            "Removed %s duplicate rows: %s",
            len(dropped_ids),
            dropped_ids
        )
    else:
        logger.info(
            "No duplicate rows detected."
        )

    # -----------------------------
    # Customer referential integrity
    # -----------------------------

    valid_customer_ids = set(
        customers["customer_id"]
    )

    invalid_customers = (
        ~orders["customer_id"]
        .isin(valid_customer_ids)
    )

    dropped_ids = orders.loc[
        invalid_customers,
        "order_id"
    ].tolist()

    orders = orders[
        ~invalid_customers
    ]

    if dropped_ids:
        logger.warning(
            "Removed %s rows with invalid customer_id: %s",
            len(dropped_ids),
            dropped_ids
        )
    else:
        logger.info(
            "All customer_id values passed referential integrity checks."
        )

    # -----------------------------
    # Product referential integrity
    # -----------------------------

    valid_product_ids = set(
        products["product_id"]
    )

    invalid_products = (
        ~orders["product_id"]
        .isin(valid_product_ids)
    )

    dropped_ids = orders.loc[
        invalid_products,
        "order_id"
    ].tolist()

    orders = orders[
        ~invalid_products
    ]

    if dropped_ids:
        logger.warning(
            "Removed %s rows with invalid product_id: %s",
            len(dropped_ids),
            dropped_ids
        )
    else:
        logger.info(
            "All product_id values passed referential integrity checks."
        )

    # -----------------------------
    # Save dropped rows
    # -----------------------------

    dropped_rows = orders_raw.loc[
        ~orders_raw["order_id"]
        .isin(orders["order_id"])
    ].copy()

    rejected_row_count = len(dropped_rows)

    if not dropped_rows.empty:

        dropped_path = os.path.join(
            output_folder,
            "orders_dropped.csv"
        )

        dropped_rows.to_csv(
            dropped_path,
            index=False
        )

        logger.info(
            "Saved %s rejected rows to %s",
            rejected_row_count,
            dropped_path
        )

    else:
        logger.info(
            "No rows were dropped during cleaning."
        )

    # -----------------------------
    # Final cleanup
    # -----------------------------

    orders = orders.drop(
        columns=["order_date_parsed"]
    ).reset_index(drop=True)

    # -----------------------------
    # Save cleaned data
    # -----------------------------

    cleaned_path = os.path.join(
        output_folder,
        "orders_clean.csv"
    )

    orders.to_csv(
        cleaned_path,
        index=False
    )

    clean_row_count = len(orders)

    logger.info(
        "Cleaned data saved to: %s",
        cleaned_path
    )

    logger.info(
        "Cleaning completed: %s input rows, %s clean rows, %s rejected rows",
        input_row_count,
        clean_row_count,
        rejected_row_count
    )

    return cleaned_path