from types import SimpleNamespace

from earnings.report_engine import (
    build_report,
    format_report_text,
    report_to_dict,
)


def build_engine_result() -> SimpleNamespace:
    return SimpleNamespace(
        ticker="MSFT",
        selected_entry=SimpleNamespace(
            entry_price=90.0,
            entry_probability=66.67,
        ),
        selected_exit=SimpleNamespace(
            exit_price=100.8,
            target_probability_after_entry=75.0,
        ),
        production_ready=True,
        sample_status="PRODUCTION_READY",
        selected_entry_percentile=0.60,
        selected_exit_percentile=0.70,
        statistics=SimpleNamespace(
            average_drop_pct=-8.5,
            median_drop_pct=-8.0,
            average_rebound_pct=14.0,
            median_rebound_pct=12.0,
        ),
    )


def test_build_report_maps_engine_result() -> None:
    report = build_report(
        build_engine_result()
    )

    assert report.ticker == "MSFT"
    assert report.entry_price == 90.0
    assert report.exit_price == 100.8
    assert report.entry_probability == 66.67
    assert report.exit_probability == 75.0
    assert report.production_ready is True
    assert report.sample_status == "PRODUCTION_READY"
    assert report.entry_percentile == 60.0
    assert report.exit_percentile == 70.0
    assert report.average_drop_pct == -8.5
    assert report.median_drop_pct == -8.0
    assert report.average_rebound_pct == 14.0
    assert report.median_rebound_pct == 12.0


def test_report_to_dict() -> None:
    report = build_report(
        build_engine_result()
    )

    result = report_to_dict(report)

    assert result["ticker"] == "MSFT"
    assert result["entry_price"] == 90.0
    assert result["exit_price"] == 100.8
    assert result["production_ready"] is True
    assert result["sample_status"] == "PRODUCTION_READY"


def test_format_report_text() -> None:
    report = build_report(
        build_engine_result()
    )

    text = format_report_text(report)

    assert "IDB PRIME LONG - MSFT" in text
    assert "Entry: 90.00" in text
    assert "Exit: 100.80" in text
    assert "Entry probability: 66.67%" in text
    assert "Exit probability after entry: 75.00%" in text
    assert "Entry percentile: 60%" in text
    assert "Exit percentile: 70%" in text
    assert "Sample status: PRODUCTION_READY" in text
    assert "Production: READY" in text


def test_format_report_text_not_ready() -> None:
    result = build_engine_result()
    result.production_ready = False

    report = build_report(result)

    text = format_report_text(report)

    assert "Production: NOT READY" in text
