from config.settings import APP_MODE
from mock_engine.provider import get_market_data


def get_signal():
    if APP_MODE == "mock":
        return get_market_data()

    return {
        "error": "Real provider not implemented"
    }