from typing import Optional

from crypto_analyst.analysis import AnalystRead
from crypto_analyst.market import MarketAsset
from crypto_analyst.sentiment import FearGreedIndex
from crypto_analyst.time_utils import MALAYSIA_TZ_LABEL, malaysia_now


def build_pulse(
    market_snapshot: list[MarketAsset],
    analyst_read: AnalystRead,
    fear_greed: FearGreedIndex,
    report_url: str = "",
) -> str:
    generated_at = malaysia_now()
    lines = [
        f"Crypto Analyst Pulse - {generated_at.strftime('%Y-%m-%d')}",
        f"Generated at {generated_at.strftime('%H:%M')} {MALAYSIA_TZ_LABEL}",
        "",
        "Market",
    ]

    for asset in market_snapshot:
        lines.append(_format_asset_move(asset))

    lines.extend(
        [
            "",
            _format_mood_index(fear_greed),
            "(0 = Fear, 100 = Greed)",
            "",
            "Why?",
            _summarize_why(analyst_read),
            *_report_link_lines(report_url),
            "",
            f"Evidence Strength: {_compact_evidence_strength(analyst_read.confidence)}",
        ]
    )

    return "\n".join(lines)


def _format_asset_move(asset: MarketAsset) -> str:
    if asset.error:
        return f"{asset.symbol}: unavailable"

    return (
        f"{asset.symbol}: "
        f"{_format_price(asset.price_usd)} | "
        f"{_format_change(asset.change_4h_percent)} 4h / "
        f"{_format_change(asset.change_8h_percent)} 8h"
    )


def _format_price(value: Optional[float]) -> str:
    if value is None:
        return "$n/a"
    return f"${value:,.2f}"


def _format_change(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value:+.2f}%"


def _format_mood_index(fear_greed: FearGreedIndex) -> str:
    if fear_greed.error or fear_greed.value is None:
        return "Mood Index: unavailable"
    return f"Mood Index: {fear_greed.value}/100"


def _summarize_why(analyst_read: AnalystRead) -> str:
    if not analyst_read.themes:
        return "No clear reason found yet. Move may be technical or positioning-driven."

    top_themes = ", ".join(theme.name for theme in analyst_read.themes[:3])
    first_driver = analyst_read.possible_drivers[0] if analyst_read.possible_drivers else ""

    if "No sharp" in first_driver:
        return f"No sharp move detected. Sources mostly point to: {top_themes}."

    return f"No clear single reason found yet. Sources point to: {top_themes}."


def _report_link_lines(report_url: str) -> list[str]:
    if not report_url:
        return []
    return ["", f"Full report here: {report_url}"]


def _compact_evidence_strength(confidence: str) -> str:
    return confidence.split(":", 1)[0]
