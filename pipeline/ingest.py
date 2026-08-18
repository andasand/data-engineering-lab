import os
import pandas as pd
import shutil
from datetime import datetime

# Define folders and paths
data_folder = "data"
archive_folder = os.path.join(data_folder, "archive")
insights_folder = "insights"
logs_folder = "logs"

log_path = os.path.join(logs_folder, "ingest_log.csv")

# Create folders if they don't exist
for folder in [data_folder, archive_folder, insights_folder, logs_folder]:
    os.makedirs(folder, exist_ok=True)

print("Folder structure and paths set up.")

# Find the orders file
files = os.listdir(data_folder)

file_name = next(
    (
        f for f in files
        if "orders" in f and f.endswith(".csv")
    ),
    None
)

if not file_name:
    print("No orders file found.")
else:
    file_path = os.path.join(data_folder, file_name)
    file_id = os.path.splitext(file_name)[0]

    print(f"Found file: {file_name}")
    print(f"Full path: {file_path}")
    print(f"File ID: {file_id}")

    # Check ingest log for duplicates
    if os.path.exists(log_path):
        log = pd.read_csv(log_path)

        if file_name in log["file_name"].values:
            print(f"File '{file_name}' has already been ingested.")
            raise SystemExit(0)
        else:
            print("File has not been ingested before. Proceeding.")

            # Load the orders CSV
            orders = pd.read_csv(file_path)

            # Define expected schema
            expected_cols = ["order_id", "customer_id", "product_id", "quantity", "order_date"]

            actual_cols = list(orders.columns)

            schema_ok = expected_cols == actual_cols

            if not schema_ok:
                print("Schema validation failed")

                if set(expected_cols) != set(actual_cols):
                    print(f"Expected columns: {expected_cols}")
                    print(f"Found columns:    {actual_cols}")
                else:
                    print("Columns are present, but they are in the wrong order.")

                status = "Schmea Failed"
                row_count = 0
            else:
                print("Schema validation passed.")
                status = "Success"
                row_count = len(orders)

                print(f"Rows found: {row_count}")

        # Save validated data to a month-based insights folder
        if schema_ok:
            order_date = pd.to_datetime(orders["order_date"].iloc[0])
            month_folder = f"{order_date.year}_{order_date.month:02}"

            output_folder = os.path.join(
                insights_folder,
                month_folder
            )

            os.makedirs(
                output_folder,
                exist_ok = True
            )

            output_path = os.path.join(
                output_folder,
                "orders.csv"
            )

            orders.to_csv(
                output_path,
                index=False
            )
            print(f"Saved orders data to: {output_path}")

            # Archive the original raw file
            archive_path = os.path.join(
                archive_folder,
                file_name
            )
            shutil.move(
                file_path,
                archive_path
            )
            print(f"Moved raw file to: {archive_path}")

            # Log the outcome
            log_entry = pd.DataFrame([{
                "file_name": file_name,
                "status": status,
                "rows": row_count,
                "timestamp": datetime.now().replace(microsecond=0).isoformat()
            }])

            if os.path.exists(log_path):
                log = pd.read_csv(log_path)
                log = pd.concat([log, log_entry], ignore_index=True)
            else:
                log = log_entry

            log.to_csv(log_path, index=False)

            print(f"Logged ingestion outcome to: {log_path}")
    else:
        print("No ingest log found. This will be the first ingestion.")