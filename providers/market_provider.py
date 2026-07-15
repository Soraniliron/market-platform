from config.settings import APP_MODE


def get_signal():
    if APP_MODE == "mock":
        return {
            "ticker": "META",
            "entry_price": 100.5,
            "stop_price": 98.0,
            "tp1_price": 102.5,
            "tp2_price": 105.0,
            "signal": "BUY",
        }

    return {
        "error": "Real provider not implemented"
    }
    