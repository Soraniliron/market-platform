from datetime import date

from dateutil.relativedelta import relativedelta

from importer.polygon_client import PolygonClient


def main() -> None:
    ticker = "META"
    end_date = date.today()
    start_date = end_date - relativedelta(months=60)

    client = PolygonClient()
    rows = client.get_daily_history(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
    )

    print(f"Ticker: {ticker}")
    print(f"From: {start_date}")
    print(f"To: {end_date}")
    print(f"Rows downloaded: {len(rows)}")


if __name__ == "__main__":
    main()
    