import os

from dotenv import load_dotenv

load_dotenv()


APP_MODE = os.getenv(
    "APP_MODE",
    "mock",
).strip().lower()

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO",
).strip().upper()


MASSIVE_API_KEY = (
    os.getenv("MASSIVE_API_KEY")
    or os.getenv("POLYGON_API_KEY")
    or os.getenv("MARKET_DATA_API_KEY")
    or ""
).strip()

MASSIVE_BASE_URL = os.getenv(
    "MASSIVE_BASE_URL",
    "https://api.polygon.io",
).rstrip("/")

REQUEST_TIMEOUT_SECONDS = int(
    os.getenv(
        "REQUEST_TIMEOUT_SECONDS",
        "30",
    )
)


EMAIL_ENABLED = os.getenv(
    "EMAIL_ENABLED",
    "false",
).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

SMTP_HOST = os.getenv(
    "SMTP_HOST",
    "smtp.gmail.com",
).strip()

SMTP_PORT = int(
    os.getenv(
        "SMTP_PORT",
        "587",
    )
)

SMTP_USE_TLS = os.getenv(
    "SMTP_USE_TLS",
    "true",
).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

SMTP_USERNAME = os.getenv(
    "SMTP_USERNAME",
    "",
).strip()

SMTP_PASSWORD = os.getenv(
    "SMTP_PASSWORD",
    "",
).strip()

EMAIL_FROM = os.getenv(
    "EMAIL_FROM",
    SMTP_USERNAME,
).strip()

EMAIL_TO = tuple(
    item.strip()
    for item in os.getenv(
        "EMAIL_TO",
        "",
    ).split(",")
    if item.strip()
)

EMAIL_MAX_RETRIES = int(
    os.getenv(
        "EMAIL_MAX_RETRIES",
        "3",
    )
)

EMAIL_RETRY_DELAY_SECONDS = float(
    os.getenv(
        "EMAIL_RETRY_DELAY_SECONDS",
        "2",
    )
)


def validate_market_data_settings() -> None:
    if APP_MODE == "mock":
        return

    if not MASSIVE_API_KEY:
        raise ValueError(
            "Missing market-data API key. "
            "Set MASSIVE_API_KEY or "
            "POLYGON_API_KEY in .env"
        )


def validate_email_settings() -> None:
    if not EMAIL_ENABLED:
        return

    if not SMTP_HOST:
        raise ValueError(
            "SMTP_HOST must not be empty"
        )

    if not (
        1
        <= SMTP_PORT
        <= 65535
    ):
        raise ValueError(
            "SMTP_PORT must be between "
            "1 and 65535"
        )

    if not SMTP_USERNAME:
        raise ValueError(
            "SMTP_USERNAME must not be empty"
        )

    if not SMTP_PASSWORD:
        raise ValueError(
            "SMTP_PASSWORD must not be empty"
        )

    if not EMAIL_FROM:
        raise ValueError(
            "EMAIL_FROM must not be empty"
        )

    if not EMAIL_TO:
        raise ValueError(
            "EMAIL_TO must contain at least "
            "one recipient"
        )

    if EMAIL_MAX_RETRIES < 1:
        raise ValueError(
            "EMAIL_MAX_RETRIES must be "
            "at least one"
        )

    if EMAIL_RETRY_DELAY_SECONDS < 0:
        raise ValueError(
            "EMAIL_RETRY_DELAY_SECONDS must "
            "be zero or greater"
        )
        