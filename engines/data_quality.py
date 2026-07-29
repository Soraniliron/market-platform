from typing import Any

from config.home_list import HOME_LIST
from database.connection import get_connection


def get_data_quality_report() -> list[dict[str, Any]]:
    connection = get_connection()
    cursor = connection.cursor()

    report: list[dict[str, Any]] = []

    for ticker in HOME_LIST:
        cursor.execute(
            """
            SELECT
                COUNT(*),
                MIN(trade_date),
                MAX(trade_date),
                COUNT(*) FILTER (
                    WHERE open IS NULL
                       OR high IS NULL
                       OR low IS NULL
                       OR close IS NULL
                       OR volume IS NULL
                ),
                COUNT(*) FILTER (
                    WHERE high < low
                       OR high < open
                       OR high < close
                       OR low > open
                       OR low > close
                       OR volume < 0
                )
            FROM daily_prices
            WHERE ticker = %s;
            """,
            (ticker,),
        )

        row = cursor.fetchone()

        report.append(
            {
                "ticker": ticker,
                "rows_count": row[0],
                "first_date": row[1],
                "last_date": row[2],
                "null_rows": row[3],
                "invalid_ohlcv_rows": row[4],
                "status": (
                    "OK"
                    if row[0] > 0 and row[3] == 0 and row[4] == 0
                    else "CHECK"
                ),
            }
        )

    cursor.close()
    connection.close()

    return report


def print_data_quality_report() -> None:
    report = get_data_quality_report()

    ok_count = 0
    check_count = 0

    for item in report:
        if item["status"] == "OK":
            ok_count += 1
        else:
            check_count += 1

        print(
            f"{item['ticker']}: "
            f"rows={item['rows_count']}, "
            f"from={item['first_date']}, "
            f"to={item['last_date']}, "
            f"nulls={item['null_rows']}, "
            f"invalid={item['invalid_ohlcv_rows']}, "
            f"status={item['status']}"
        )

    print("-" * 50)
    print(f"OK tickers: {ok_count}")
    print(f"CHECK tickers: {check_count}")


if __name__ == "__main__":
    print_data_quality_report()
