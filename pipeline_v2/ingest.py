import os
import pandas as pd
import shutil
from datetime import datetime

def run(
        file_name,
        data_folder,
        archive_folder,
        insights_folder,
        log_path
):
    # Build paths
    file_path = os.path.join(data_folder, file_name)
    file_id = os.path.splitext(file_name)[0]

    print(f"Found file: {file_name}")
    print(f"File ID: {file_id}")

    # Load file
    orders = pd.read_csv(file_path)

    # Validate schema
    expected_cols = [
        "order_id",
        "customer_id",
        "product_id",
        "quantity",
        "order_date",
    ]

    actual_cols = list(orders.columns)

    schema_ok = expected_cols == actual_cols

    if not schema_ok:
        print("Schema validation failed.")

        if set(expected_cols) != set(actual_cols):
            print(f"Expected: {expected_cols}")
            print(f"Found:    {actual_cols}")
        else:
            print(
                "Columns are present "
                "but in the wrong order."
            )

        status = "Schema Failed"
        row_count = 0

    else:
        print("Schema validation passed.")
        status = "Success"
        row_count = len(orders)

        print(f"Rows found: {row_count}")

    # Log schema failure and stop
    if not schema_ok:
        log_entry = pd.DataFrame([{
            "file_name": file_name,
            "status": status,
            "row_count": row_count,
            "timestamp": datetime.now()
                .replace(microsecond=0)
                .isoformat()
        }])

        if os.path.exists(log_path):
            log = pd.read_csv(log_path)
            log = pd.concat([log, log_entry], ignore_index=True)
        else:
            log = log_entry

        log.to_csv(log_path, index=False)

        raise ValueError(f"Schema validation failed for {file_name}")

    # Determine monthly output folder
    order_date = pd.to_datetime(orders["order_date"].iloc[0])
    month_folder = (
        f"{order_date.year}_"
        f"{order_date.month:02}"
    )

    output_folder = os.path.join(
        insights_folder,
        month_folder
    )

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    # Save validated copy
    output_path = os.path.join(
        output_folder,
        "orders.csv"
    )

    orders.to_csv(
        output_path,
        index=False
    )

    print(
        f"Saved orders data to: "
        f"{output_path}"
    )

    # Archive raw file
    archive_path = os.path.join(
        archive_folder,
        file_name
    )

    shutil.move(
        file_path,
        archive_path
    )

    print(
        f"Moved raw file to: "
        f"{archive_path}"
    )

    # Log ingestion
    log_entry = pd.DataFrame([{
        "file_name": file_name,
        "status": status,
        "rows": row_count,
        "timestamp": datetime.now()
            .replace(microsecond=0)
            .isoformat()
    }])

    if os.path.exists(log_path):
        log = pd.read_csv(log_path)
        log = pd.concat([log, log_entry], ignore_index=True)
    else:
        log = log_entry

    log.to_csv(log_path, index=False)

    print( 
        f"Logged ingestion outcome to: "
        f"{log_path}"
    )

    # Return location for downstream stages
    return output_folder