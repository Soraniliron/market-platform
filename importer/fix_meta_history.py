from datetime import date

from database.price_repository import (
    delete_daily_prices,
    save_daily_prices,
)
from importer.polygon_client import PolygonClient


def main() -> None:
    client = PolygonClient()

    fb_rows = client.get_daily_history(
        ticker="FB",
        start_date=date(2021, 7, 28),
        end_date=date(2022, 6, 8),
    )

    meta_rows = client.get_daily_history(
        ticker="META",
        start_date=date(2022, 6, 9),
        end_date=date.today(),
    )

    deleted_rows = delete_daily_prices("META")

    fb_saved = save_daily_prices(
        ticker="META",
        rows=fb_rows,
    )

    meta_saved = save_daily_prices(
        ticker="META",
        rows=meta_rows,
    )

    print(f"Deleted META rows: {deleted_rows}")
    print(f"Downloaded FB rows: {len(fb_rows)}")
    print(f"Saved FB rows as META: {fb_saved}")
    print(f"Downloaded META rows: {len(meta_rows)}")
    print(f"Saved META rows: {meta_saved}")
    print(f"Total META rows saved: {fb_saved + meta_saved}")


if __name__ == "__main__":
    main()
