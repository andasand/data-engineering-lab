import os
import pandas as pd

from pipeline_v2 import ingest, clean, transform, serve

from config import (
    DATA_FOLDER,
    ARCHIVE_FOLDER,
    INSIGHTS_FOLDER,
    PRODUCTS_PATH,
    CUSTOMERS_PATH,
    INGEST_LOG_PATH
)


# -----------------------------
# Run full pipeline
# -----------------------------

def run_pipeline():

    # Find an orders CSV
    files = os.listdir(DATA_FOLDER)

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

    if os.path.exists(INGEST_LOG_PATH):

        log = pd.read_csv(INGEST_LOG_PATH)

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
            DATA_FOLDER,
            ARCHIVE_FOLDER,
            INSIGHTS_FOLDER,
            INGEST_LOG_PATH
        )

        clean.run(
            PRODUCTS_PATH,
            CUSTOMERS_PATH,
            output_folder
        )

        top_products, top_customers = (
            transform.run(
                PRODUCTS_PATH,
                CUSTOMERS_PATH,
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