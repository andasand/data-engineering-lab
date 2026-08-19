import logging
import os

from config import LOGS_FOLDER


def setup_logging():
    os.makedirs(
        LOGS_FOLDER,
        exist_ok=True
    )

    log_path = os.path.join(
        LOGS_FOLDER,
        "pipeline.log"
    )

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s "
            "%(levelname)-8s "
            "%(name)s - "
            "%(message)s"
        ),
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )