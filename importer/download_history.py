from datetime import date
from time import sleep

from dateutil.relativedelta import relativedelta

from config.home_list import HOME_LIST
from database.init_db import create_tables
from database.price_repository import save_daily_prices
from importer.polygon_client import PolygonClient


def main() -> None:
    end_date = date.today()
    start_date = end_date - relativedelta(months=60)

    create_tables()
    client = PolygonClient()

    successful_tickers = []
    failed_tickers = []
    total_rows_downloaded = 0
    total_rows_saved = 0

    print(f"Tickers: {len(HOME_LIST)}")
    print(f"From: {start_date}")
    print(f"To: {end_date}")
    print("-" * 50)

    for index, ticker in enumerate(HOME_LIST, start=1):
        try:
            print(f"[{index}/{len(HOME_LIST)}] Downloading {ticker}...")

            rows = client.get_daily_history(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
            )

            saved_rows = save_daily_prices(
                ticker=ticker,
                rows=rows,
            )

            successful_tickers.append(ticker)
            total_rows_downloaded += len(rows)
            total_rows_saved += saved_rows

            print(
                f"{ticker}: downloaded={len(rows)}, saved={saved_rows}"
            )

        except Exception as error:
            failed_tickers.append(ticker)
            print(f"{ticker}: FAILED - {error}")

        sleep(1)

    print("-" * 50)
    print("IMPORT SUMMARY")
    print(f"Successful tickers: {len(successful_tickers)}")
    print(f"Failed tickers: {len(failed_tickers)}")
    print(f"Rows downloaded: {total_rows_downloaded}")
    print(f"Rows saved: {total_rows_saved}")

    if failed_tickers:
        print(f"Failed list: {', '.join(failed_tickers)}")


if __name__ == "__main__":
    main()
