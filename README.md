# Crypto Analysis AI - Multi-Framework Technical Analysis Engine

Intelligent assistant that analyzes crypto assets in real-time by consulting multiple data sources and advanced technical analysis frameworks. Recommends whether to **buy, sell, or hold** for both short and long term.

```bash
yarn dev
# Open http://localhost:3000 and ask what to do with ETH, BTC, Gold or AUD
```

---

## Project Strategy

### 1. Architecture

```
Client (Next.js App Router)
  │
  ├─ Chat UI → Natural language questions
  │
  └─ /api/analyze
       ├─ scrapeAllSources() → Multiple sources in parallel
       ├─ analyze()           → Proprietary multi-framework analysis engine
       └─ [Optional] AI       → GPT-4o-mini via OpenRouter
```

### 2. Data Sources

| Source | Data Type | Method |
|--------|-----------|--------|
| **CoinGecko** | Price, volume, market cap | Public REST API |
| **Fear & Greed Index** | Market sentiment | alternative.me API |
| **CoinDesk** | News headlines | Web scraping |
| **CoinTelegraph** | ETH news headlines | Web scraping |
| **Coinglass** | Funding rate, liquidations | REST API |
| **Binance** | Order book depth | REST API |
| **Macro Calendar** | Economic events | REST API |

`Promise.allSettled` is used for fault tolerance: if one source fails (timeout, block), the others continue working.

---

## Technical Analysis Engine

The analysis is NOT traditional technical analysis calculated on historical OHLC candlestick series. It is a **hybrid system** that synthesizes multiple signals (technical, on-chain, sentiment, SMC, Elliott) into a single aggregated score to generate trading recommendations with entry, exit, and risk levels.

### Analysis Modules

#### 1. Classic Technical Analysis (`parseTechnicalIndicators`)

Generates synthetic indicators based on 24h price change:

| Indicator | Calculation |
|-----------|-------------|
| **RSI** | `50 + (change24h * 1.5)`, clamp 15-85 |
| **MACD** | Bullish crossover (RSI>60), bearish (RSI<40) |
| **MA50** | Price × 0.97 or × 1.03 depending on direction |
| **MA200** | Price × 0.92 or × 1.08 depending on direction |
| **Trend** | Bullish if >2%, bearish if <-2% |
| **Supports** | Price × 0.95, 0.90, 0.85 |
| **Resistances** | Price × 1.04, 1.08, 1.15 |

> **Note:** These are synthetic indicators calculated from 24h price change, not from real historical candlestick series.

#### 2. Elliott Wave Analysis (`parseElliottWaveData`)

Identifies wave structure based on the magnitude of price variation:

| 24h Variation | Result |
|---------------|--------|
| < 1% | Neutral structure - no clear pattern |
| > 4% bullish | Wave 3 of (5) - strong bullish impulse |
| 1-4% bullish | Possible Wave 1 - start of impulse |
| > 4% bearish | Wave C of (A)(B)(C) - active correction |
| 1-4% bearish | Possible Wave A - pullback |

Generates price targets, invalidation levels, and projected sub-waves for each scenario.

#### 3. Smart Money Concepts (SMC) (`parseSmcData`)

Analyzes market structure from the smart money perspective:

| Component | Description |
|-----------|-------------|
| **Market Structure** | Uptrend / Downtrend / Ranging |
| **BOS** | Break of Structure - confirmed if movement > 3% |
| **MSS** | Market Structure Shift - direction change |
| **Order Blocks** | Accumulation/distribution zones |
| **FVGs** | Fair Value Gaps - price gaps |
| **Liquidity** | Dynamically calculated pools |

#### 4. On-Chain Analysis (`parseOnChainData`)

Extracts data from Coinglass and other sources:
- **Funding Rate**: Futures financing rate
- **Exchange Flows**: Inflows (+) / Outflows (-)
- **Staking**: Yield and staked amounts
- **Liquidation Levels**: Squeeze projections

#### 5. Market Sentiment (`parseSentimentData`)

Combines multiple sentiment sources:
- **Fear & Greed Index**: Quantitative fear/greed index
- **News NLP**: Keyword analysis (dump/crash/surge/rally) on CoinDesk and CoinTelegraph headlines
- **Social Sentiment**: Derived from Fear & Greed Index

#### 6. Order Book Analysis (`parseOrderBookData`)

Uses Binance depth data to calculate:
- Bid/Ask ratio
- Options sentiment (Calls vs Puts)
- Market directional flow

#### 7. Whale Data (`parseWhaleData`)

| Metric | Description |
|--------|-------------|
| Large transactions 24h | Number of large txs |
| Total volume USD | Aggregated value moved |
| Accumulation | Pattern: accumulating/distributing/neutral |
| Net flow | Direction of top wallet flows |

---

### Verdict Algorithm (`buildVerdict`)

Multi-factor scoring system with bearish and bullish weights.

#### Key Weights:

| Factor | Bearish Weight | Bullish Weight |
|--------|:--------------:|:--------------:|
| Technical trend | 3 | 3 |
| RSI extreme | 2/-1 | 2/-1 |
| High/low funding rate | 3 | 2 |
| Fear & Greed | 2 | 2 |
| Bid/Ask ratio | 2 | 2 |
| Timeframe trend | 3/-1 | 3/-1 |
| Elliott Waves | 3/2 | 3/-2 |
| SMC structure | 2 | 2 |
| BOS/MSS | 2 | 3 |

#### Verdict Thresholds:

| Net Score | Verdict |
|:---------:|---------|
| >= 4 | **BUY** (short and long term) |
| 1 to 3 | **HOLD** short, **BUY** long |
| -2 to 0 | **HOLD** both |
| < -2 | **SELL** short, **HOLD** long |

> If Fear & Greed Index < 20 (Extreme Fear), confidence is reduced and any **BUY** signal becomes **HOLD**, applying extreme caution.

---

### Probabilistic Scenarios

Two scenarios are always generated with trigger and probability:

- **Bearish**: "If it loses support at $X..." → target $Y (probability ~45%)
- **Bullish**: "If it breaks resistance at $X..." → target $Y (probability ~55%)

---

## Supported Assets

- **ETH** (Ethereum)
- **BTC** (Bitcoin)
- **Gold** (XAU - Tether Gold)
- **AUD** (Australian Dollar)

---

## Tech Stack

- **Framework**: Next.js 16 (App Router, TypeScript, Turbopack)
- **UI**: shadcn/ui (Radix, Tailwind CSS v4)
- **Scraping**: cheerio, native fetch
- **Icons**: lucide-react
- **Packaging**: Yarn

## Commands

```bash
yarn dev       # Development on localhost:3000
yarn build     # Production build
yarn lint      # Code verification
```

## Environment Variables

```env
# Optional — for AI analysis
OPENROUTER_API_KEY=sk-or-v1-...
```

## Future Improvements

- [ ] WebSockets for real-time data
- [ ] Support for more cryptos (SOL, etc.)
- [ ] Price alerts with Web Push
- [ ] Analysis history and interactive charts
- [ ] Connection to exchange APIs (Binance, Coinbase) for order book data
