import os
import logging

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


logger = logging.getLogger("pipeline.database")

# Load variables from .env
load_dotenv()


def get_engine():

    db_name = os.getenv("POSTGRES_DB")
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT")

    database_url = (
        f"postgresql+psycopg2://"
        f"{db_user}:"
        f"{db_password}@"
        f"{db_host}:"
        f"{db_port}/"
        f"{db_name}"
    )

    return create_engine(
        database_url
    )


def test_connection():

    engine = get_engine()

    with engine.connect() as connection:

        result = connection.execute(
            text("SELECT version();")
        )

        version = result.scalar()

        logger.info(
            "Connected to PostgreSQL successfully."
        )

        return version