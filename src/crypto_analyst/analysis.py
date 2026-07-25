from dataclasses import dataclass
import re

from crypto_analyst.market import MarketAsset
from crypto_analyst.news import NewsItem


@dataclass(frozen=True)
class ThemeSignal:
    name: str
    description: str
    insight: str
    matched_items: list[NewsItem]


@dataclass(frozen=True)
class AnalystRead:
    summary: str
    confidence: str
    themes: list[ThemeSignal]
    source_insights: list[str]
    possible_drivers: list[str]
    watch_next: list[str]


THEME_KEYWORDS = {
    "Bitcoin positioning": {
        "description": "BTC-specific flow, whale, premium, or positioning headlines.",
        "keywords": ["bitcoin", "btc", "whale", "coinbase premium", "miner", "halving"],
    },
    "Ethereum ecosystem": {
        "description": "ETH-specific ecosystem, staking, scaling, or protocol headlines.",
        "keywords": ["ethereum", "eth", "staking", "layer 2", "l2", "rollup"],
    },
    "Solana ecosystem": {
        "description": "SOL-specific ecosystem, network, app, or institutional Solana headlines.",
        "keywords": ["solana", "sol", "jito", "pump.fun", "raydium", "helium"],
    },
    "Macro / policy": {
        "description": "Rates, inflation, central banks, economic data, or broad policy headlines.",
        "keywords": ["fed", "federal reserve", "rate", "inflation", "cpi", "ppi", "jobs", "treasury", "dollar"],
    },
    "Regulation": {
        "description": "Government, regulator, licensing, enforcement, or legal headlines.",
        "keywords": ["sec", "regulation", "regulatory", "mika", "mica", "cbdc", "law", "court", "charges", "approval", "license"],
    },
    "Stablecoins / liquidity": {
        "description": "Stablecoin, USDC, Tether, CBDC, or liquidity infrastructure headlines.",
        "keywords": ["stablecoin", "stablecoins", "usdc", "tether", "usdt", "circle", "cbdc", "liquidity"],
    },
    "Institutional activity": {
        "description": "ETF, bank, asset manager, treasury, or corporate adoption headlines.",
        "keywords": ["etf", "blackrock", "bank", "institutional", "wall street", "treasury", "company", "corporate"],
    },
    "Security / exchange risk": {
        "description": "Exchange, exploit, hack, laundering, custody, or operational risk headlines.",
        "keywords": ["exchange", "hack", "exploit", "laundering", "custody", "custodian", "kraken", "binance", "coinbase"],
    },
}


def build_analyst_read(
    market_snapshot: list[MarketAsset],
    news_items: list[NewsItem],
) -> AnalystRead:
    significant_moves = [
        asset
        for asset in market_snapshot
        if _has_significant_move(asset)
    ]
    themes = _detect_themes(news_items)
    source_insights = _build_source_insights(themes)
    possible_drivers = _build_possible_drivers(significant_moves, themes)
    summary = _build_summary(market_snapshot, significant_moves, themes)
    confidence = _confidence_label(significant_moves, themes)
    watch_next = _build_watch_next(significant_moves, themes)

    return AnalystRead(
        summary=summary,
        confidence=confidence,
        themes=themes,
        source_insights=source_insights,
        possible_drivers=possible_drivers,
        watch_next=watch_next,
    )


def _detect_themes(news_items: list[NewsItem]) -> list[ThemeSignal]:
    signals = []

    for theme_name, config in THEME_KEYWORDS.items():
        matched = [
            item
            for item in news_items
            if _contains_keyword(item.title, config["keywords"])
        ]
        if matched:
            signals.append(
                ThemeSignal(
                    name=theme_name,
                    description=config["description"],
                    insight=_theme_insight(theme_name, matched[:3]),
                    matched_items=matched[:3],
                )
            )

    signals.sort(key=lambda signal: len(signal.matched_items), reverse=True)
    return signals[:5]


def _contains_keyword(text: str, keywords: list[str]) -> bool:
    normalized = text.lower()
    return any(_keyword_matches(normalized, keyword) for keyword in keywords)


def _keyword_matches(text: str, keyword: str) -> bool:
    normalized_keyword = keyword.lower()
    if " " in normalized_keyword:
        return normalized_keyword in text
    return re.search(rf"\b{re.escape(normalized_keyword)}\b", text) is not None


def _build_possible_drivers(
    significant_moves: list[MarketAsset],
    themes: list[ThemeSignal],
) -> list[str]:
    if not significant_moves:
        return [
            "No sharp BTC, ETH, or SOL movement was detected, so the headlines are treated as market context rather than movement drivers."
        ]

    if not themes:
        return [
            "A sharp market move was detected, but the current RSS headlines do not point to a clear driver."
        ]

    top_themes = ", ".join(theme.name for theme in themes[:3])
    return [
        f"Recent headlines cluster around {top_themes}. These are possible drivers or context, not confirmed causes yet.",
        _asset_specific_driver_note(significant_moves, themes),
    ]


def _build_source_insights(themes: list[ThemeSignal]) -> list[str]:
    if not themes:
        return [
            "The current sources do not cluster around a strong theme. This usually means either the market move is technical/positioning-driven, or the relevant catalyst has not appeared in the connected news feeds yet."
        ]

    insights = [theme.insight for theme in themes[:5]]
    if len(themes) >= 3:
        insights.append(
            "The headline mix is broad rather than single-catalyst. Treat this as a market context read, not proof that one story caused the price move."
        )
    return insights


def _theme_insight(theme_name: str, matched_items: list[NewsItem]) -> str:
    source_count = len({item.source for item in matched_items})
    source_text = "multiple sources" if source_count > 1 else "one source"

    if theme_name == "Bitcoin positioning":
        return (
            f"Bitcoin positioning is appearing in {source_text}. This can help explain BTC-specific momentum, "
            "but it needs confirmation from funding, open interest, liquidations, or ETF flow data."
        )
    if theme_name == "Ethereum ecosystem":
        return (
            f"Ethereum-specific headlines are appearing in {source_text}. If ETH is moving more than BTC, "
            "these items may be relevant, but they should be treated as ecosystem context unless multiple sources point to the same catalyst."
        )
    if theme_name == "Solana ecosystem":
        return (
            f"Solana-specific headlines are appearing in {source_text}. This may matter most if SOL is moving differently from BTC and ETH."
        )
    if theme_name == "Macro / policy":
        return (
            f"Macro or policy headlines are appearing in {source_text}. These can affect crypto broadly, "
            "especially when BTC, ETH, and SOL move together instead of one asset moving alone."
        )
    if theme_name == "Regulation":
        return (
            f"Regulatory headlines are appearing in {source_text}. This suggests policy risk or policy clarity is part of today's market backdrop."
        )
    if theme_name == "Stablecoins / liquidity":
        return (
            f"Stablecoin and liquidity headlines are appearing in {source_text}. This may matter because stablecoins influence crypto market liquidity, settlement rails, and institutional access."
        )
    if theme_name == "Institutional activity":
        return (
            f"Institutional activity is appearing in {source_text}. These stories can shape medium-term confidence, but are not automatically short-term price catalysts."
        )
    if theme_name == "Security / exchange risk":
        return (
            f"Exchange or security-risk headlines are appearing in {source_text}. These can affect trust and risk appetite, especially if they involve major exchanges or custody."
        )

    return f"{theme_name} is appearing in {source_text}. Treat it as context until stronger confirmation appears."


def _build_summary(
    market_snapshot: list[MarketAsset],
    significant_moves: list[MarketAsset],
    themes: list[ThemeSignal],
) -> str:
    unavailable = [asset for asset in market_snapshot if asset.error]
    if len(unavailable) == len(market_snapshot):
        return "Market data could not be fetched, so this report focuses only on available headlines."

    move_text = _movement_summary(significant_moves)
    if themes:
        theme_text = ", ".join(theme.name for theme in themes[:3])
        return f"{move_text} The main headline themes detected are {theme_text}."

    return f"{move_text} No strong headline theme was detected from the current RSS sample."


def _asset_specific_driver_note(
    significant_moves: list[MarketAsset],
    themes: list[ThemeSignal],
) -> str:
    moved_symbols = {asset.symbol for asset in significant_moves}
    theme_names = {theme.name for theme in themes}

    if "ETH" in moved_symbols and "Ethereum ecosystem" not in theme_names:
        return "ETH moved sharply, but the current headlines do not show a clear ETH-specific catalyst."

    if "BTC" in moved_symbols and "Bitcoin positioning" not in theme_names:
        return "BTC moved sharply, but the current headlines do not show a clear BTC-specific catalyst."

    if "SOL" in moved_symbols and "Solana ecosystem" not in theme_names:
        return "SOL moved sharply, but the current headlines do not show a clear SOL-specific catalyst."

    return "The report needs more market structure data, such as funding and liquidations, before treating these themes as stronger evidence."


def _movement_summary(significant_moves: list[MarketAsset]) -> str:
    if not significant_moves:
        return "BTC, ETH, and SOL are not showing a sharp move based on the current 8h and 24h thresholds."

    moves = ", ".join(
        _format_move_summary(asset)
        for asset in significant_moves
    )
    return f"Significant movement detected: {moves}."


def _has_significant_move(asset: MarketAsset) -> bool:
    if asset.change_4h_percent is not None and abs(asset.change_4h_percent) >= 1.5:
        return True
    if asset.change_8h_percent is not None and abs(asset.change_8h_percent) >= 2:
        return True
    if asset.change_24h_percent is not None and abs(asset.change_24h_percent) >= 3:
        return True
    return False


def _format_move_summary(asset: MarketAsset) -> str:
    parts = []
    if asset.change_4h_percent is not None:
        parts.append(f"4h {asset.change_4h_percent:+.2f}%")
    if asset.change_8h_percent is not None:
        parts.append(f"8h {asset.change_8h_percent:+.2f}%")
    if asset.change_24h_percent is not None:
        parts.append(f"24h {asset.change_24h_percent:+.2f}%")
    return f"{asset.symbol} ({', '.join(parts)})"


def _confidence_label(
    significant_moves: list[MarketAsset],
    themes: list[ThemeSignal],
) -> str:
    if not significant_moves:
        return "Low: no sharp market move was detected."
    if len(themes) >= 2:
        return "Medium: market movement exists and multiple headline themes are present, but causation is not confirmed."
    if len(themes) == 1:
        return "Low-Medium: market movement exists, but only one headline theme stands out."
    return "Low: market movement exists, but no clear headline theme was detected."


def _build_watch_next(
    significant_moves: list[MarketAsset],
    themes: list[ThemeSignal],
) -> list[str]:
    watch_items = ["Confirm whether later headlines support the same explanation."]

    if significant_moves:
        watch_items.append("Check whether the move continues or fades over the next few hours.")
        watch_items.append("Add funding, liquidation, and ETF flow data for stronger confirmation.")

    theme_names = {theme.name for theme in themes}
    if "Macro / policy" in theme_names:
        watch_items.append("Watch official macro or central bank sources for confirmation.")
    if "Regulation" in theme_names:
        watch_items.append("Check official regulator or government announcements.")
    if "Stablecoins / liquidity" in theme_names:
        watch_items.append("Watch stablecoin and liquidity headlines for follow-through.")
    if "Bitcoin positioning" in theme_names:
        watch_items.append("Check BTC positioning data such as premium, funding, and open interest.")
    if "Solana ecosystem" in theme_names:
        watch_items.append("Check Solana ecosystem headlines and SOL-specific market structure.")

    return watch_items
