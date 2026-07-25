from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
from typing import Optional

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
BINANCE_24HR_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"
COINGECKO_SIMPLE_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"
COINGECKO_MARKET_CHART_URL = "https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
CMC_SIMPLE_PRICE_URL = "https://pro-api.coinmarketcap.com/public-api/v1/simple/price"

TRACKED_ASSETS = {
    "bitcoin": ("BTC", "Bitcoin", "BTCUSDT", "1"),
    "ethereum": ("ETH", "Ethereum", "ETHUSDT", "1027"),
    "solana": ("SOL", "Solana", "SOLUSDT", "5426"),
}


@dataclass(frozen=True)
class MarketAsset:
    symbol: str
    name: str
    price_usd: Optional[float]
    change_4h_percent: Optional[float]
    change_8h_percent: Optional[float]
    change_24h_percent: Optional[float]
    source: str = "Binance"
    error: Optional[str] = None


def get_market_snapshot() -> list[MarketAsset]:
    """Fetch BTC, ETH, and SOL movement, with CoinGecko fallback for cloud runners."""
    coingecko_snapshot = _fetch_coingecko_snapshot()
    cmc_prices = _fetch_cmc_prices()
    assets = []
    for asset_id, (symbol, name, binance_symbol, cmc_id) in TRACKED_ASSETS.items():
        ticker = _fetch_24hr_ticker(binance_symbol)
        coingecko_item = coingecko_snapshot.get(asset_id, {})
        coingecko_changes = {}

        price = (
            _as_float(ticker.get("lastPrice"))
            or _as_float(coingecko_item.get("usd"))
            or cmc_prices.get(cmc_id)
        )
        change_24h = _as_float(ticker.get("priceChangePercent")) or _as_float(
            coingecko_item.get("usd_24h_change")
        )
        change_4h = _fetch_hour_change(binance_symbol, 4)
        change_8h = _fetch_hour_change(binance_symbol, 8)

        if change_4h is None or change_8h is None:
            coingecko_changes = _fetch_coingecko_hour_changes(asset_id)
            change_4h = change_4h if change_4h is not None else coingecko_changes.get(4)
            change_8h = change_8h if change_8h is not None else coingecko_changes.get(8)

        if price is None:
            assets.append(
                MarketAsset(
                    symbol=symbol,
                    name=name,
                    price_usd=None,
                    change_4h_percent=None,
                    change_8h_percent=None,
                    change_24h_percent=None,
                    error="Market data unavailable from Binance and CoinGecko.",
                )
            )
            continue

        assets.append(
            MarketAsset(
                symbol=symbol,
                name=name,
                price_usd=price,
                change_4h_percent=change_4h,
                change_8h_percent=change_8h,
                change_24h_percent=change_24h,
                source="Binance/CoinGecko/CMC",
            )
        )

    return assets


def _unavailable_snapshot(error: str) -> list[MarketAsset]:
    return [
        MarketAsset(
            symbol=symbol,
            name=name,
            price_usd=None,
            change_4h_percent=None,
            change_8h_percent=None,
            change_24h_percent=None,
            error=error,
        )
        for symbol, name, _binance_symbol, _cmc_id in TRACKED_ASSETS.values()
    ]


def _fetch_24hr_ticker(binance_symbol: str) -> dict[str, object]:
    try:
        query = urlencode({"symbol": binance_symbol})
        url = f"{BINANCE_24HR_TICKER_URL}?{query}"
        with urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


def _fetch_coingecko_snapshot() -> dict[str, dict[str, object]]:
    try:
        query = urlencode(
            {
                "ids": ",".join(TRACKED_ASSETS.keys()),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            }
        )
        url = f"{COINGECKO_SIMPLE_PRICE_URL}?{query}"
        with urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


def _fetch_cmc_prices() -> dict[str, float]:
    try:
        query = urlencode(
            {
                "ids": ",".join(asset[3] for asset in TRACKED_ASSETS.values()),
                "convert": "USD",
            }
        )
        request = Request(
            f"{CMC_SIMPLE_PRICE_URL}?{query}",
            headers={"Accept": "application/json", "User-Agent": "CryptoAnalyst/0.1"},
        )
        with urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return {}

    prices = {}
    for item in data.get("data", []):
        if not isinstance(item, dict):
            continue
        cmc_id = str(item.get("id", ""))
        price = _as_float(item.get("price"))
        if cmc_id and price is not None:
            prices[cmc_id] = price
    return prices


def _fetch_coingecko_hour_changes(coin_id: str) -> dict[int, float]:
    try:
        query = urlencode({"vs_currency": "usd", "days": "1"})
        url = f"{COINGECKO_MARKET_CHART_URL.format(coin_id=coin_id)}?{query}"
        with urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return {}

    prices = data.get("prices", [])
    if not prices:
        return {}

    latest_timestamp_ms = prices[-1][0]
    latest_price = _as_float(prices[-1][1])
    if latest_price is None:
        return {}

    changes = {}
    for hours in (4, 8):
        target_timestamp_ms = latest_timestamp_ms - (hours * 60 * 60 * 1000)
        closest_price_point = min(
            prices,
            key=lambda point: abs(point[0] - target_timestamp_ms),
        )
        starting_price = _as_float(closest_price_point[1])
        if starting_price and starting_price > 0:
            changes[hours] = ((latest_price - starting_price) / starting_price) * 100
    return changes


def _fetch_hour_change(binance_symbol: str, hours: int) -> Optional[float]:
    try:
        query = urlencode(
            {
                "symbol": binance_symbol,
                "interval": "1h",
                "limit": str(hours + 1),
            }
        )
        url = f"{BINANCE_KLINES_URL}?{query}"
        with urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return None

    if len(data) < hours + 1:
        return None

    starting_price = float(data[0][4])
    latest_price = float(data[-1][4])
    if starting_price <= 0:
        return None

    return ((latest_price - starting_price) / starting_price) * 100


def _as_float(value: object) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
