# Crypto Analyst

A local-first crypto research assistant that helps answer one painful question:

> The crypto market moved sharply. Why?

Crypto Analyst collects market movement, news, macro events, regulatory updates, and ecosystem information from free sources, then turns the useful parts into concise intelligence.

The goal is not to predict prices or generate hype. The goal is to reduce noise and help explain what may have driven meaningful market moves.

## Why This Exists

Crypto markets often move up or down drastically.

When that happens, it is hard to find a clear explanation. Information is scattered across news sites, exchange announcements, social platforms, macro calendars, and market dashboards. Many sources are noisy, repetitive, speculative, or late.

Crypto Analyst should solve that pain point by:

- Detecting meaningful market movement.
- Gathering relevant information from reliable, free sources.
- Connecting market moves with possible causes.
- Separating confirmed information from weak signals.
- Sending a useful Telegram Pulse.
- Publishing a fuller HTML report for deeper review.

## MVP

The first version should do two things well:

1. Gather news, information, and market movement.
2. Ping me with a Telegram Pulse and generate a fuller HTML report.

## Core Workflow

```text
Collect market data
Collect relevant news and events
Detect important movement
Find possible explanations
Generate Pulse
Send Telegram Pulse
Publish detailed HTML report
```

## What The Analyst Should Answer

Every useful report should try to answer:

- What moved?
- How significant was the move?
- What likely caused it?
- Is the cause confirmed or only a possible explanation?
- Which assets or sectors are affected?
- Why does it matter?
- What should I watch next?

If no clear cause is found, the system should say so instead of inventing an explanation.

## Product Principles

- Cost-free to build and run wherever possible.
- Prefer free APIs, RSS feeds, and public data.
- Prefer official or primary sources.
- Avoid hype, rumours, and low-quality speculation.
- Explain impact, not just headlines.
- Keep the project simple and maintainable.
- Build useful software, not excessive documentation.

## Not In Scope

Crypto Analyst is not:

- A trading bot.
- A price prediction engine.
- Financial advice.
- A generic news aggregator.
- A social media summarizer.
- A paid-data platform.

## Initial Source Ideas

The MVP should start with a small number of free, practical sources:

- Market data: CoinGecko and exchange public APIs.
- News: free RSS feeds from reputable crypto publications.
- Macro: official economic calendars and central bank/government sources.
- Regulation: official regulator announcements.
- Exchange/project updates: official announcement pages or RSS feeds where available.

Sources can be added later only when they improve the quality of the explanation.

## Outputs

### Pulse

The Pulse is the short Telegram message. It should stay concise and link to the full HTML report when a public report URL is available.

Example shape:

```text
Crypto Analyst Pulse

Market
BTC: +0.20% 4h / -0.50% 8h
ETH: +1.00% 4h / +1.80% 8h
SOL: -0.80% 4h / -1.10% 8h

Mood Index: 23/100
(0 = Fear, 100 = Greed)

Why?
No clear single reason found yet. Sources point to: Ethereum ecosystem, Regulation, Stablecoins / liquidity.

Evidence Strength: Medium
```

### HTML Report

The HTML Report is the fuller visual report with:

- Market movement summary.
- Possible drivers.
- Supporting sources.
- Evidence strength.
- Mood Index.
- Affected assets/sectors.
- Risks and next things to monitor.

## Build Direction

Start small:

1. Create a local command that fetches market data.
2. Add a few free information sources.
3. Generate a designed HTML report.
4. Add Telegram delivery.
5. Add scheduling after the manual flow works.

The project should stay practical. When a document helps us build, we write it. When code is the clearer next step, we code.

## Run

```bash
cd path/to/crypto-analyst
PYTHONPATH=src python3 -m crypto_analyst.main
```

## Telegram Setup

Create a local `.env` file:

```text
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_CHAT_ID_2=optional_second_chat_id
REPORT_URL=optional_public_html_report_url
```

The `.env` file is ignored by Git and should not be committed.

## Schedule

The project uses macOS `launchd` for automatic runs.

Default schedule:

- 12:00 local time
- 18:00 local time

Install the schedule:

```bash
cd path/to/crypto-analyst
./scripts/install_schedule.sh
```

Uninstall the schedule:

```bash
cd path/to/crypto-analyst
./scripts/uninstall_schedule.sh
```

Check whether the schedule is loaded:

```bash
cd path/to/crypto-analyst
./scripts/check_schedule.sh
```

Logs are written to:

```text
logs/launchd.out.log
logs/launchd.err.log
```

## GitHub Pulse Schedule

GitHub Actions can send the Telegram Pulse without relying on the MacBook.

It generates:

- Telegram Pulse
- Hosted HTML full report via GitHub Pages

Schedule:

- 12:00 Malaysia time
- 18:00 Malaysia time

Required GitHub repository secrets:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
TELEGRAM_CHAT_ID_2
```

Manual test in GitHub:

```text
Actions -> Telegram Pulse -> Run workflow
```

Full report URL:

```text
https://maldbunny.github.io/crypto-analyst/reports/latest.html
```

The Pulse includes this link automatically.
# crypto-analyst
