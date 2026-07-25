from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json

FEAR_GREED_URL = "https://pro-api.coinmarketcap.com/public-api/v3/fear-and-greed/latest"


@dataclass(frozen=True)
class FearGreedIndex:
    value: Optional[int]
    source: str = "CoinMarketCap Fear and Greed Index"
    timestamp: Optional[datetime] = None
    error: Optional[str] = None


def get_fear_greed_index() -> FearGreedIndex:
    try:
        request = Request(
            FEAR_GREED_URL,
            headers={"Accept": "application/json", "User-Agent": "CryptoAnalyst/0.1"},
        )
        with urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return _unavailable(f"Fear & Greed API returned HTTP {exc.code}.")
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return _unavailable(f"Fear & Greed API failed: {exc}")

    item = data.get("data", {})
    if not item:
        return _unavailable("Fear & Greed API returned no data.")

    try:
        value = int(item["value"])
    except (KeyError, TypeError, ValueError):
        return _unavailable("Fear & Greed API returned an invalid value.")

    timestamp = _parse_timestamp(item.get("update_time"))
    return FearGreedIndex(
        value=value,
        timestamp=timestamp,
    )


def _parse_timestamp(value: object) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    try:
        return datetime.fromtimestamp(int(value))
    except (TypeError, ValueError, OSError):
        return None


def _unavailable(error: str) -> FearGreedIndex:
    return FearGreedIndex(value=None, error=error)
