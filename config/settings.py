import os

from dotenv import load_dotenv

load_dotenv()


APP_MODE = os.getenv("APP_MODE", "mock").strip().lower()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()

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
    os.getenv("REQUEST_TIMEOUT_SECONDS", "30")
)


def validate_market_data_settings() -> None:
    if APP_MODE == "mock":
        return

    if not MASSIVE_API_KEY:
        raise ValueError(
            "Missing market-data API key. "
            "Set MASSIVE_API_KEY or POLYGON_API_KEY in .env"
        )
