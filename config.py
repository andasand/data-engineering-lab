import os


# -----------------------------
# Project directories
# -----------------------------

DATA_FOLDER = "data"

ARCHIVE_FOLDER = os.path.join(
    DATA_FOLDER,
    "archive"
)

INSIGHTS_FOLDER = "insights"

LOGS_FOLDER = "logs"


# -----------------------------
# Reference datasets
# -----------------------------

PRODUCTS_PATH = os.path.join(
    DATA_FOLDER,
    "products.csv"
)

CUSTOMERS_PATH = os.path.join(
    DATA_FOLDER,
    "customers.csv"
)


# -----------------------------
# Pipeline logs
# -----------------------------

INGEST_LOG_PATH = os.path.join(
    LOGS_FOLDER,
    "ingest_log.csv"
)