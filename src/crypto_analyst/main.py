import argparse

from crypto_analyst.analysis import build_analyst_read
from crypto_analyst.config import get_setting, load_env
from crypto_analyst.market import get_market_snapshot
from crypto_analyst.news import get_recent_news
from crypto_analyst.html_report import save_html_report
from crypto_analyst.pulse import build_pulse
from crypto_analyst.sentiment import get_fear_greed_index
from crypto_analyst.telegram import send_pulse_to_telegram


def main() -> None:
    args = _parse_args()
    load_env()
    market_snapshot = get_market_snapshot()
    news_items = get_recent_news()
    fear_greed = get_fear_greed_index()
    analyst_read = build_analyst_read(market_snapshot, news_items)

    if args.html_output:
        html_path = save_html_report(
            market_snapshot,
            news_items,
            analyst_read,
            fear_greed,
            args.html_output,
        )
        print(f"HTML report saved: {html_path}")
        print()

    report_url = args.report_url or get_setting("REPORT_URL")
    pulse = build_pulse(market_snapshot, analyst_read, fear_greed, report_url)

    if args.pulse_output:
        from pathlib import Path

        pulse_path = Path(args.pulse_output)
        pulse_path.parent.mkdir(parents=True, exist_ok=True)
        pulse_path.write_text(pulse, encoding="utf-8")

    print(pulse)
    print()

    if args.skip_telegram:
        print("Telegram skipped.")
        return

    telegram_result = send_pulse_to_telegram(pulse)
    print(telegram_result.message)

    if not telegram_result.sent:
        raise SystemExit(1)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Crypto Analyst outputs.")
    parser.add_argument(
        "--html-output",
        default="",
        help="Write a designed HTML full report to this path.",
    )
    parser.add_argument(
        "--report-url",
        default="",
        help="Full report URL to include in the Pulse.",
    )
    parser.add_argument(
        "--pulse-output",
        default="",
        help="Write the Pulse text to this path.",
    )
    parser.add_argument(
        "--skip-telegram",
        action="store_true",
        help="Generate outputs without sending the Telegram Pulse.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
