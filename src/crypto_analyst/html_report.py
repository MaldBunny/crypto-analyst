from datetime import datetime
from html import escape
from pathlib import Path
from typing import Optional

from crypto_analyst.analysis import AnalystRead
from crypto_analyst.market import MarketAsset
from crypto_analyst.news import NewsItem
from crypto_analyst.sentiment import FearGreedIndex


def save_html_report(
    market_snapshot: list[MarketAsset],
    news_items: list[NewsItem],
    analyst_read: AnalystRead,
    fear_greed: FearGreedIndex,
    output_path: str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        build_html_report(market_snapshot, news_items, analyst_read, fear_greed),
        encoding="utf-8",
    )
    return path


def build_html_report(
    market_snapshot: list[MarketAsset],
    news_items: list[NewsItem],
    analyst_read: AnalystRead,
    fear_greed: FearGreedIndex,
) -> str:
    generated_at = datetime.now()
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Crypto Analyst Report - {generated_at.strftime('%Y-%m-%d')}</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0b0f14;
      --panel: #111821;
      --panel-2: #16202b;
      --text: #e8edf2;
      --muted: #96a3b3;
      --line: #263241;
      --green: #44d07b;
      --red: #ff6370;
      --blue: #70b7ff;
      --gold: #f3c969;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.55;
    }}
    main {{
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 52px;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      padding-bottom: 18px;
      margin-bottom: 22px;
    }}
    h1, h2, h3 {{ margin: 0; letter-spacing: 0; }}
    h1 {{ font-size: clamp(28px, 4vw, 44px); }}
    h2 {{ font-size: 20px; margin-bottom: 14px; }}
    h3 {{ font-size: 16px; margin-bottom: 8px; }}
    .muted {{ color: var(--muted); }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 14px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .span-8 {{ grid-column: span 8; }}
    .span-4 {{ grid-column: span 4; }}
    .span-6 {{ grid-column: span 6; }}
    .span-12 {{ grid-column: span 12; }}
    .market-row {{
      display: grid;
      grid-template-columns: 70px 1fr auto auto;
      gap: 12px;
      align-items: center;
      padding: 12px 0;
      border-top: 1px solid var(--line);
    }}
    .market-row:first-child {{ border-top: 0; }}
    .symbol {{ font-weight: 700; font-size: 18px; }}
    .price {{ font-size: 18px; }}
    .move {{ color: var(--muted); font-variant-numeric: tabular-nums; }}
    .up {{ color: var(--green); }}
    .down {{ color: var(--red); }}
    .pill {{
      display: inline-block;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 4px 10px;
      color: var(--muted);
      font-size: 13px;
      margin: 4px 6px 4px 0;
    }}
    ul {{ margin: 0; padding-left: 20px; }}
    li {{ margin: 8px 0; }}
    a {{ color: var(--blue); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .mood-value {{ font-size: 34px; font-weight: 750; color: var(--gold); }}
    .section {{ margin-top: 14px; }}
    .theme {{
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      margin-top: 10px;
    }}
    @media (max-width: 760px) {{
      .grid {{ grid-template-columns: 1fr; }}
      .span-8, .span-4, .span-6, .span-12 {{ grid-column: span 1; }}
      .market-row {{ grid-template-columns: 1fr; gap: 4px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Crypto Analyst Report</h1>
      <div class="muted">Generated at {escape(generated_at.strftime('%Y-%m-%d %H:%M'))}</div>
    </header>

    <section class="grid">
      <div class="card span-8">
        <h2>Analyst Read</h2>
        <p>{escape(analyst_read.summary)}</p>
        <div><strong>Evidence Strength:</strong> {escape(analyst_read.confidence)}</div>
      </div>
      <div class="card span-4">
        <h2>Mood Index</h2>
        {_render_mood(fear_greed)}
      </div>
    </section>

    <section class="card section">
      <h2>Market Movement</h2>
      {_render_market(market_snapshot)}
    </section>

    <section class="grid section">
      <div class="card span-6">
        <h2>Best Analysis</h2>
        {_render_list(_best_analysis_points(analyst_read))}
      </div>
      <div class="card span-6">
        <h2>Watch Next</h2>
        {_render_list(analyst_read.watch_next)}
      </div>
    </section>

    <section class="card section">
      <h2>Themes & Evidence</h2>
      {_render_themes(analyst_read)}
    </section>

    <section class="card section">
      <h2>Source Links</h2>
      {_render_sources(news_items)}
    </section>
  </main>
</body>
</html>
"""


def _render_market(assets: list[MarketAsset]) -> str:
    return "\n".join(_render_asset(asset) for asset in assets)


def _render_asset(asset: MarketAsset) -> str:
    if asset.error:
        return f'<div class="market-row"><div class="symbol">{escape(asset.symbol)}</div><div class="muted">Unavailable</div></div>'
    return f"""
      <div class="market-row">
        <div class="symbol">{escape(asset.symbol)}</div>
        <div class="price">{_format_price(asset.price_usd)}</div>
        <div class="move {_move_class(asset.change_4h_percent)}">4h {_format_change(asset.change_4h_percent)}</div>
        <div class="move {_move_class(asset.change_8h_percent)}">8h {_format_change(asset.change_8h_percent)}</div>
      </div>
    """


def _render_mood(fear_greed: FearGreedIndex) -> str:
    if fear_greed.error or fear_greed.value is None:
        return '<div class="muted">Unavailable</div><div class="muted">0 = Fear, 100 = Greed</div>'
    return f"""
      <div class="mood-value">{fear_greed.value}/100</div>
      <div class="muted">0 = Fear, 100 = Greed</div>
      <div class="muted">Source: {escape(fear_greed.source)}</div>
    """


def _best_analysis_points(analyst_read: AnalystRead) -> list[str]:
    points = []
    points.extend(analyst_read.possible_drivers[:2])
    points.extend(analyst_read.source_insights[:3])
    if not points:
        return ["No strong source-backed explanation found yet."]
    return points


def _render_themes(analyst_read: AnalystRead) -> str:
    if not analyst_read.themes:
        return '<p class="muted">No strong headline themes detected.</p>'
    blocks = []
    for theme in analyst_read.themes:
        links = "".join(f"<li>{_source_link(item)}</li>" for item in theme.matched_items)
        blocks.append(
            f"""
            <div class="theme">
              <h3>{escape(theme.name)}</h3>
              <p class="muted">{escape(theme.description)}</p>
              <p>{escape(theme.insight)}</p>
              <ul>{links}</ul>
            </div>
            """
        )
    return "\n".join(blocks)


def _render_sources(news_items: list[NewsItem]) -> str:
    if not news_items:
        return '<p class="muted">No RSS headlines found.</p>'
    return "<ul>" + "".join(f"<li>{_source_link(item)}</li>" for item in news_items) + "</ul>"


def _render_list(items: list[str]) -> str:
    if not items:
        return '<p class="muted">No items.</p>'
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def _source_link(item: NewsItem) -> str:
    published = ""
    if item.published_at:
        published = f" - {item.published_at.strftime('%Y-%m-%d %H:%M')}"
    return f'<a href="{escape(item.url)}">{escape(item.title)}</a> <span class="muted">({escape(item.source)}{published})</span>'


def _format_price(value: Optional[float]) -> str:
    if value is None:
        return "$n/a"
    return f"${value:,.2f}"


def _format_change(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value:+.2f}%"


def _move_class(value: Optional[float]) -> str:
    if value is None:
        return ""
    if value > 0:
        return "up"
    if value < 0:
        return "down"
    return ""
