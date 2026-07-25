import argparse
from pathlib import Path

from crypto_analyst.telegram import send_pulse_to_telegram


def main() -> None:
    args = _parse_args()
    pulse_text = Path(args.path).read_text(encoding="utf-8")
    result = send_pulse_to_telegram(pulse_text)
    print(result.message)
    if not result.sent:
        raise SystemExit(1)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a generated Pulse text file to Telegram.")
    parser.add_argument("path", help="Path to the Pulse text file.")
    return parser.parse_args()


if __name__ == "__main__":
    main()
