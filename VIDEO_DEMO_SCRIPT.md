# Video Demo Guide: Crypto Analysis AI

## Prerequisites
- App running: `yarn dev` → http://localhost:3000
- Screen recorder (OBS, Clipchamp, etc.)
- Microphone for narration (or use TTS tool like ElevenLabs, TTSMaker)

---

## Step-by-Step Demo Actions

### Scene 1: App Load / Intro (0:00 – 0:25)

| Time | Action | Screen Shows |
|------|--------|-------------|
| 0:00 | Open browser at `localhost:3000` | Full app loads — dark chat UI, header with "Crypto Analysis AI", ETH selected, welcome message, suggestion buttons |
| 0:05 | Mouse hover slowly over header elements | Logo, title, ETH/BTC/Gold asset switcher, green "10+ fuentes" badge |
| 0:12 | Mouse hover over suggestion buttons | 4 suggestion chips glow on hover |
| 0:18 | Mouse hover over input field + ⌘K hint | Input field highlights |

**Narration:** *"Welcome to Crypto Analysis AI..."* (full intro paragraph)

---

### Scene 2: Asset Switcher (0:25 – 0:55)

| Time | Action | Screen Shows |
|------|--------|-------------|
| 0:25 | Click **BTC** button in header | Chat resets, welcome message now says "Bitcoin", symbol changes, subtitle says "¿Comprar o vender BTC?" |
| 0:32 | Pause 2s, hover BTC active state | BTC button glows with cyber color |
| 0:35 | Click **Gold (👑)** button | Chat resets, says "Gold", subtitle "¿Comprar o vender XAU?", badge changes to "5+ fuentes" |
| 0:42 | Pause 2s | Shows XAU context |
| 0:45 | Click **ETH (⟠)** button | Back to Ethereum, badge back to "10+ fuentes" |

**Narration:** *"You can switch between three assets instantly..."*

---

### Scene 3: Quick Suggestions (0:55 – 1:20)

| Time | Action | Screen Shows |
|------|--------|-------------|
| 0:55 | Welcome message visible with 4 suggestion chips | "Sugerencias rápidas" label, chips staggered in with animation |
| 1:00 | Hover over first chip "¿Debería comprar ETH hoy?" | Chip glows with border/shadow effect |
| 1:05 | Click the chip | Text populates the input field automatically |
| 1:10 | Pause 1s to show filled input | Input now contains "¿Debería comprar ETH hoy?" |

**Narration:** *"To help you get started, the app provides quick suggestion buttons..."*

---

### Scene 4: Sending Query + Loading (1:20 – 1:40)

| Time | Action | Screen Shows |
|------|--------|-------------|
| 1:20 | Click **Analyze** button (or press Enter) | Button changes to "Analizando" with pulse animation on Zap icon |
| 1:23 | Watch the chat | User message bubble appears ("¿Debería comprar ETH hoy?") |
| 1:25 | Immediately after | AI loading skeleton appears — 3 animated shimmer bars in a card |
| 1:30～1:40 | Wait for response | Skeleton animates while data loads (~5-15s depending on APIs) |

**Narration:** *"We click Analyze, and the app immediately starts scraping data from 10+ sources..."*

---

### Scene 5: Analysis Result — Verdict & Price (1:40 – 2:10)

*(Wait for the analysis to fully render before speaking)*

| Time | Action | Screen Shows |
|------|--------|-------------|
| 1:40 | Analysis appears | AI avatar + "Análisis de Ethereum" header + timestamp |
| 1:42 | Watch price | Price counter animates from 0 to current price (GSAP tween) |
| 1:45 | Watch change badge | Green/red 24h change appears with arrow icon |
| 1:48 | Verdict card | Card slides in — BUY/SELL/HOLD badge with green/red/yellow gradient, confidence %, summary text |
| 1:55 | Key Levels row | 3 cards: Stop Loss, TP Corto, TP Largo — staggered animation |

**Narration:** *"And here's the result. First, we see the current price with an animated counter..."*

---

### Scene 6: Scenarios (2:10 – 2:30)

| Time | Action | Screen Shows |
|------|--------|-------------|
| 2:10 | Scenarios section visible | Two cards: "Bajista" (red) and "Alcista" (green) |
| 2:12 | Mouse hover bearish card | Card scales up slightly (whileHover effect) |
| 2:15 | Mouse hover bullish card | Same hover effect |
| 2:18 | Read details | Each card shows: probability %, target price, trigger condition |

**Narration:** *"Next, the app shows probabilistic scenarios..."*

---

### Scene 7: Expand Detailed Analysis (2:30 – 2:45)

| Time | Action | Screen Shows |
|------|--------|-------------|
| 2:30 | Mouse hover "Análisis detallado" button | Button highlights with cyber border |
| 2:33 | Click the button | Chevron rotates 180°, section expands smoothly with height animation |
| 2:36 | Wait for expansion | All sub-sections reveal with staggered fade-in |

**Narration:** *"Now, let's expand the detailed analysis section..."*

---

### Scene 8: Detailed Sections Walkthrough (2:45 – 3:15)

*Scroll slowly through each section. Pause 2-3s on each.*

| Time | Action | Screen Shows |
|------|--------|-------------|
| 2:45 | Técnico section visible | RSI, Trend, MA50, MA200 — 2x2 grid with icons |
| 2:50 | On-Chain section | Funding Rate, Exchange Flows, Staking APY, ETH Staked |
| 2:53 | Order Book section | Bid/Ask Depth, Ratio, Option Flow |
| 2:56 | Ballenas (Whales) section | Large Txns, Volume, Accumulation status |
| 2:59 | Multi-Timeframe section | 3 columns (Daily, 4H, 1H) with trend arrows + RSI + alignment badge |
| 3:02 | Ondas Elliott section | Wave count label, progress bar, sub-waves grid, target/invalidation |
| 3:05 | Smart Money section | Market structure badge, liquidity zones, Order Blocks list, FVGs list |
| 3:08 | Macro section | Risk environment label, upcoming events with high/medium badges |
| 3:11 | Sentimiento section | Fear & Greed badge + news headlines with ▲/▼ sentiment indicators |

**Narration:** *"Here's where the power of Crypto Analysis AI really shines..."* (walk through each module)

---

### Scene 9: Sources + Reset (3:15 – 3:25)

| Time | Action | Screen Shows |
|------|--------|-------------|
| 3:15 | Scroll to bottom of analysis | "8/11 fuentes consultadas" footer |
| 3:17 | Pause briefly | Source counter visible |
| 3:19 | Scroll to bottom of chat | "Volver al inicio" button |
| 3:21 | Click "Volver al inicio" | Chat resets to initial welcome message + suggestions |
| 3:23 | Pause | Clean initial state |

**Narration:** *"At the bottom of each analysis, you'll see exactly how many sources were successfully queried..."*

---

### Scene 10: Outro (3:25 – 3:35)

| Time | Action | Screen Shows |
|------|--------|-------------|
| 3:25 | App in initial state | Clean chat, suggestions visible |
| 3:28 | (Optional) Slowly fade out | Or cut to black |

**Narration:** *"Crypto Analysis AI — real-time, multi-source, AI-powered market intelligence..."*

---

## Recording Tips

1. **Resolution:** Record at 1920×1080 or 2560×1440
2. **FPS:** 30 or 60 fps
3. **Cursor:** Use a visible cursor highlight (OBS has a cursor filter)
4. **Audio:** Speak clearly, pace at ~150 words/min
5. **Background:** Close other tabs/windows to avoid distractions
6. **API speed:** If network calls are slow, edit the video to cut waiting time; keep just 2-3s of the skeleton loader
7. **Retakes:** It's easier to record narration separately and sync in editing

## Post-Processing (Optional)

- Add subtle background music (low volume, synthwave/lo-fi)
- Add lower-third captions for key metrics (e.g., "RSI: 62", "Confidence: 72%")
- Zoom in on specific sections during the detailed walkthrough
