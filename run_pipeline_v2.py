import os
import pandas as pd

from pipeline_v2 import ingest, clean, transform, serve


# -----------------------------
# Define folders and paths
# -----------------------------

data_folder = "data"
archive_folder = os.path.join(
    data_folder,
    "archive"
)

insights_folder = "insights"
logs_folder = "logs"

products_path = os.path.join(
    data_folder,
    "products.csv"
)

customers_path = os.path.join(
    data_folder,
    "customers.csv"
)

log_path = os.path.join(
    logs_folder,
    "ingest_log.csv"
)


# -----------------------------
# Run full pipeline
# -----------------------------

def run_pipeline():

    # Find an orders CSV
    files = os.listdir(data_folder)

    file_name = next(
        (
            f for f in files
            if "orders" in f
            and f.endswith(".csv")
        ),
        None
    )

    if not file_name:
        print("No orders file found.")
        return


    # -----------------------------
    # Duplicate protection
    # -----------------------------

    if os.path.exists(log_path):

        log = pd.read_csv(log_path)

        if file_name in log["file_name"].values:

            print(
                f"File '{file_name}' "
                f"has already been ingested. "
                f"Skipping."
            )

            return

        else:
            print(
                "File not found in ingest log. "
                "Proceeding."
            )

    else:

        print(
            "No ingest log found. "
            "Pipeline will create one."
        )


    print(
        f"\nStarting pipeline for: "
        f"{file_name}"
    )


    # -----------------------------
    # Execute pipeline stages
    # -----------------------------

    try:

        output_folder = ingest.run(
            file_name,
            data_folder,
            archive_folder,
            insights_folder,
            log_path
        )

        clean.run(
            products_path,
            customers_path,
            output_folder
        )

        top_products, top_customers = (
            transform.run(
                products_path,
                customers_path,
                output_folder
            )
        )

        serve.run(
            top_products,
            top_customers,
            output_folder
        )

        print(
            f"\nPipeline completed successfully "
            f"for: {file_name}"
        )

    except Exception as e:

        print(
            f"\nPipeline failed: {e}"
        )


# -----------------------------
# Entry point
# -----------------------------

if __name__ == "__main__":
    run_pipeline()