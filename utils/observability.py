import json
import logging
import sys


LOGGER_NAME = "financial_intelligence"


def get_logger() -> logging.Logger:
    """
    Return the application logger.

    The logger writes structured JSON-style records
    to stdout so logs remain easy to inspect locally
    and easy to ingest later in a cloud platform.
    """

    logger = logging.getLogger(LOGGER_NAME)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        "%(message)s"
    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)

    logger.propagate = False

    return logger


def log_event(
    logger: logging.Logger,
    event: str,
    **fields,
) -> None:
    """
    Write one structured operational event.

    Do not pass secrets, full prompts, or full
    retrieved evidence into this function.
    """

    payload = {
        "event": event,
        **fields,
    }

    logger.info(
        json.dumps(
            payload,
            default=str,
        )
    )
    