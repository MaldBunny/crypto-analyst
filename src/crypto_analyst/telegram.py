from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import os

from crypto_analyst.config import get_setting


@dataclass(frozen=True)
class TelegramResult:
    sent: bool
    message: str


def send_pulse_to_telegram(pulse_text: str) -> TelegramResult:
    bot_token = get_setting("TELEGRAM_BOT_TOKEN")
    chat_ids = _get_chat_ids()

    if not bot_token or not chat_ids:
        return TelegramResult(
            sent=False,
            message="Telegram not configured. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to .env.",
        )

    failures = []
    for chat_id in chat_ids:
        result = _send_message(bot_token, chat_id, pulse_text)
        if not result.sent:
            failures.append(f"{chat_id}: {result.message}")

    if failures:
        return TelegramResult(sent=False, message="Telegram send failed for " + "; ".join(failures))

    return TelegramResult(sent=True, message=f"Telegram Pulse sent to {len(chat_ids)} chat(s).")


def _get_chat_ids() -> list[str]:
    chat_ids = []
    for key, value in os.environ.items():
        if key == "TELEGRAM_CHAT_ID" or key.startswith("TELEGRAM_CHAT_ID_"):
            chat_id = value.strip()
            if chat_id and chat_id not in chat_ids:
                chat_ids.append(chat_id)
    return chat_ids


def _send_message(bot_token: str, chat_id: str, pulse_text: str) -> TelegramResult:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = urlencode(
        {
            "chat_id": chat_id,
            "text": pulse_text,
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")

    try:
        request = Request(url, data=payload, method="POST")
        with urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return TelegramResult(sent=False, message=f"Telegram HTTP error: {exc.code}")
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return TelegramResult(sent=False, message=f"Telegram send failed: {exc}")

    if not body.get("ok"):
        return TelegramResult(sent=False, message=f"Telegram rejected message: {body}")

    return TelegramResult(sent=True, message="Telegram Pulse sent.")
