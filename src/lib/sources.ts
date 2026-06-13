import * as cheerio from 'cheerio'
import type { Asset, AssetConfig, SmcOrderBlock, SmcFvg } from './types'
import { getAssetConfig } from './types'

interface RawSourceData {
  name: string
  url: string
  data: Record<string, unknown>
  error?: string
}

const cache = new Map<string, { data: unknown; expiry: number }>()

function getCached<T>(key: string): T | undefined {
  const entry = cache.get(key)
  if (entry && entry.expiry > Date.now()) return entry.data as T
  cache.delete(key)
  return undefined
}

function setCache<T>(key: string, data: T, ttlMs: number): void {
  cache.set(key, { data, expiry: Date.now() + ttlMs })
}

async function fetchWithTimeout(url: string, timeoutMs = 8000): Promise<Response> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' },
    })
    return res
  } finally {
    clearTimeout(timeout)
  }
}

async function scrapeCoinGecko(asset: AssetConfig): Promise<RawSourceData> {
  const name = 'CoinGecko'
  const url = `https://api.coingecko.com/api/v3/simple/price?ids=${asset.coinGeckoId}&vs_currencies=usd&include_24hr_vol=true&include_24hr_change=true&include_market_cap=true`
  const cacheKey = `coingecko:${asset.coinGeckoId}`
  const cached = getCached<Record<string, unknown>>(cacheKey)
  if (cached) return { name, url, data: cached }
  try {
    const res = await fetchWithTimeout(url)
    if (res.status === 429) {
      const cached = getCached<Record<string, unknown>>(cacheKey)
      if (cached) return { name, url, data: cached }
      return { name, url, data: {}, error: 'Rate limited by CoinGecko' }
    }
    const json = await res.json() as Record<string, unknown>
    setCache(cacheKey, json, 30_000)
    return { name, url, data: json }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeFearGreed(): Promise<RawSourceData> {
  const name = 'Fear & Greed Index'
  const url = 'https://api.alternative.me/fng/?limit=1'
  try {
    const res = await fetchWithTimeout(url)
    const json = await res.json() as Record<string, unknown>
    return { name, url, data: json }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeCoinMarketCap(asset: AssetConfig): Promise<RawSourceData> {
  const name = 'CoinMarketCap'
  const url = `https://coinmarketcap.com/currencies/${asset.cmcSlug}/`
  try {
    const res = await fetchWithTimeout(url)
    const html = await res.text()
    const $ = cheerio.load(html)
    const priceEl = $('[data-test="text-cdp-price-display"]').first().text().trim()
    const changeEl = $('[data-test="text-cdp-price-change"]').first().text().trim()
    return { name, url, data: { price: priceEl, change: changeEl } }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeDefiLlama(): Promise<RawSourceData> {
  const name = 'DeFi Llama'
  const url = 'https://api.llama.fi/protocol/ethereum'
  try {
    const res = await fetchWithTimeout(url)
    const json = await res.json() as Record<string, unknown>
    return { name, url, data: { tvl: json } }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeCoinglassFunding(asset: AssetConfig): Promise<RawSourceData> {
  const name = 'Coinglass'
  if (asset.id === 'aud' || asset.id === 'gold') {
    return { name, url: '', data: { note: 'N/A para activos fiat' } }
  }
  const symbol = asset.id === 'btc' ? 'BTC' : 'ETH'
  const url = `https://api.coinglass.com/api/funding-rate/v2/list?symbol=${symbol}`
  try {
    const res = await fetchWithTimeout(url)
    const json = await res.json() as Record<string, unknown>
    return { name, url, data: json }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeCoinDesk(asset: AssetConfig): Promise<RawSourceData> {
  const name = 'CoinDesk'
  const url = `https://www.coindesk.com/price/${asset.cmcSlug}/`
  try {
    const res = await fetchWithTimeout(url)
    const html = await res.text()
    const $ = cheerio.load(html)
    const headlines: string[] = []
    $('h2, h3, .headline, article a').each((_, el) => {
      const text = $(el).text().trim()
      if (text.length > 15 && headlines.length < 5) headlines.push(text)
    })
    return { name, url, data: { headlines } }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeCoinTelegraph(asset: AssetConfig): Promise<RawSourceData> {
  const name = 'CoinTelegraph'
  const tag = asset.id === 'btc' ? 'bitcoin' : asset.id === 'aud' ? 'forex' : 'ethereum'
  const url = `https://cointelegraph.com/tags/${tag}`
  try {
    const res = await fetchWithTimeout(url)
    const html = await res.text()
    const $ = cheerio.load(html)
    const headlines: string[] = []
    $('h2, h3, .post-title, article a').each((_, el) => {
      const text = $(el).text().trim()
      if (text.length > 15 && headlines.length < 5) headlines.push(text)
    })
    return { name, url, data: { headlines } }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeGlassnode(asset: AssetConfig): Promise<RawSourceData> {
  const name = 'Glassnode'
  const tag = asset.id === 'btc' ? 'bitcoin' : asset.id === 'aud' ? 'forex' : 'ethereum'
  const url = `https://glassnode.com/blog/tag/${tag}`
  try {
    const res = await fetchWithTimeout(url)
    const html = await res.text()
    const $ = cheerio.load(html)
    const titles: string[] = []
    $('h2, h3, .blog-title, article a h3').each((_, el) => {
      const text = $(el).text().trim()
      if (text.length > 15 && titles.length < 5) titles.push(text)
    })
    return { name, url, data: { blogTitles: titles } }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeCryptoQuant(): Promise<RawSourceData> {
  const name = 'CryptoQuant'
  const url = 'https://cryptoquant.com/community/c/ethereum'
  try {
    await fetchWithTimeout(url)
    return { name, url, data: { note: 'CryptoQuant requires auth for detailed data' } }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeTradingViewTechnicals(asset: AssetConfig): Promise<RawSourceData> {
  const name = 'TradingView'
  const symbol = asset.id === 'btc' ? 'BTCUSD' : asset.id === 'gold' ? 'XAUUSD' : asset.id === 'aud' ? 'AUDUSD' : 'ETHUSD'
  const url = `https://www.tradingview.com/symbols/${symbol}/technicals/`
  try {
    const res = await fetchWithTimeout(url)
    const html = await res.text()
    const $ = cheerio.load(html)
    const signals: string[] = []
    $('[class*="signal"], [class*="indicator"]').each((_, el) => {
      const text = $(el).text().trim()
      if (text.length > 3 && signals.length < 10) signals.push(text)
    })
    return { name, url, data: { signals } }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeEtherscan(): Promise<RawSourceData> {
  const name = 'Etherscan'
  const url = 'https://etherscan.io/'
  try {
    const res = await fetchWithTimeout(url)
    const html = await res.text()
    const $ = cheerio.load(html)
    const txCount = $('#ContentPlaceHolder1_TransactionCount').text().trim()
    return { name, url, data: { transactionCount24h: txCount } }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeBinanceOrderBook(asset: AssetConfig): Promise<RawSourceData> {
  const name = 'Binance Order Book'
  const symbol = asset.binanceSymbol
  const url = `https://api.binance.com/api/v3/depth?symbol=${symbol}&limit=100`
  try {
    const res = await fetchWithTimeout(url)
    const json = await res.json() as { bids: string[][]; asks: string[][] }
    const bidDepth = json.bids.reduce((sum, b) => sum + parseFloat(b[1]), 0)
    const askDepth = json.asks.reduce((sum, a) => sum + parseFloat(a[1]), 0)
    return { name, url, data: { bidDepth, askDepth, bidAskRatio: bidDepth / (askDepth || 1) } }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeBinanceKlines(symbol: string, interval: string): Promise<{ open: number; high: number; low: number; close: number; volume: number }[]> {
  const url = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=30`
  const res = await fetchWithTimeout(url)
  const json = await res.json() as string[][]
  return json.map((k) => ({
    open: parseFloat(k[1]),
    high: parseFloat(k[2]),
    low: parseFloat(k[3]),
    close: parseFloat(k[4]),
    volume: parseFloat(k[5]),
  }))
}

function calcRsi(closes: number[]): number {
  const gains: number[] = []
  const losses: number[] = []
  for (let i = 1; i < closes.length; i++) {
    const diff = closes[i] - closes[i - 1]
    gains.push(Math.max(0, diff))
    losses.push(Math.max(0, -diff))
  }
  const avgGain = gains.slice(-14).reduce((a, b) => a + b, 0) / 14
  const avgLoss = losses.slice(-14).reduce((a, b) => a + b, 0) / 14
  if (avgLoss === 0) return 100
  const rs = avgGain / avgLoss
  return Math.round(100 - 100 / (1 + rs))
}

function calcMa(prices: number[], period: number): number {
  const slice = prices.slice(-period)
  return slice.reduce((a, b) => a + b, 0) / slice.length
}

async function scrapeMultiTimeframe(asset: AssetConfig): Promise<RawSourceData> {
  const name = 'Multi-Timeframe'
  const symbol = asset.binanceSymbol
  const url = 'https://api.binance.com/api/v3/klines'
  try {
    const [daily, fourHour, oneHour] = await Promise.all([
      scrapeBinanceKlines(symbol, '1d'),
      scrapeBinanceKlines(symbol, '4h'),
      scrapeBinanceKlines(symbol, '1h'),
    ])
    const dailyCloses = daily.map((k) => k.close)
    const fourHourCloses = fourHour.map((k) => k.close)
    const oneHourCloses = oneHour.map((k) => k.close)
    const dailyRsi = calcRsi(dailyCloses)
    const fourHourRsi = calcRsi(fourHourCloses)
    const oneHourRsi = calcRsi(oneHourCloses)
    const lastDaily = dailyCloses[dailyCloses.length - 1] || 0
    const last4h = fourHourCloses[fourHourCloses.length - 1] || 0
    const last1h = oneHourCloses[oneHourCloses.length - 1] || 0
    const dailyMa50 = calcMa(dailyCloses, Math.min(50, dailyCloses.length))
    const dailyMa200 = calcMa(dailyCloses, Math.min(200, dailyCloses.length))
    const dailyTrend = dailyRsi > 55 ? 'bullish' : dailyRsi < 45 ? 'bearish' : 'neutral'
    const fourHourTrend = fourHourRsi > 55 ? 'bullish' : fourHourRsi < 45 ? 'bearish' : 'neutral'
    const oneHourTrend = oneHourRsi > 55 ? 'bullish' : oneHourRsi < 45 ? 'bearish' : 'neutral'
    const trends = [dailyTrend, fourHourTrend, oneHourTrend]
    const unique = new Set(trends)
    const alignment = unique.size === 1 ? 'aligned' : unique.size === 2 ? 'partial' : 'conflicting'
    const dominantTrend = trends.filter((t) => t === 'bullish').length >= 2 ? 'bullish'
      : trends.filter((t) => t === 'bearish').length >= 2 ? 'bearish' : 'neutral'
    const dailyMaStatus = lastDaily > dailyMa200 ? 'above 200 MA' : lastDaily > dailyMa50 ? 'above 50 MA' : 'below key MAs'

    return {
      name, url,
      data: {
        daily: { trend: dailyTrend, rsi: dailyRsi, maStatus: dailyMaStatus },
        fourHour: { trend: fourHourTrend, rsi: fourHourRsi, maStatus: last4h > calcMa(fourHourCloses, Math.min(50, fourHourCloses.length)) ? 'above 50 MA' : 'below 50 MA' },
        oneHour: { trend: oneHourTrend, rsi: oneHourRsi, maStatus: last1h > calcMa(oneHourCloses, Math.min(50, oneHourCloses.length)) ? 'above 50 MA' : 'below 50 MA' },
        alignment, dominantTrend,
        klines: daily,
      },
    }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeWhaleTransactions(asset: AssetConfig): Promise<RawSourceData> {
  const name = 'Whale Transactions'
  const address = asset.id === 'eth'
    ? '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    : asset.id === 'btc'
    ? '3M219KR5vEneSZ47nLaoeNUKL在所难免mwfU' : ''
  const url = address
    ? `https://api.etherscan.io/api?module=account&action=tokentx&address=${address}&sort=desc&limit=20`
    : 'https://api.blockchain.info/v2/eth/data/transactions?limit=10'
  try {
    if (asset.id === 'gold' || asset.id === 'aud') {
      return { name, url, data: { largeTxns24h: 0, totalVolumeUsd: 0, accumulation: 'neutral', topWhaleNetFlow: '—', notableTxns: [] } }
    }
    const res = await fetchWithTimeout(url)
    const json = await res.json() as { status: string; result: Record<string, string>[] }
    const txns = (json.result || []).slice(0, 10)
    const largeTxns = txns.filter((t) => parseFloat(t.value) >= 100)
    const totalVolume = largeTxns.reduce((sum, t) => sum + parseFloat(t.value), 0) / 1e18
    const price = asset.id === 'btc' ? 65000 : 1800
    return {
      name, url,
      data: {
        largeTxns24h: largeTxns.length,
        totalVolumeUsd: totalVolume * price,
        accumulation: totalVolume > 5000 ? 'accumulating' : totalVolume < 1000 ? 'distributing' : 'neutral',
        topWhaleNetFlow: totalVolume > 5000 ? 'net inflows (+)' : 'net outflows (-)',
        notableTxns: largeTxns.slice(0, 5).map((t) => ({
          hash: t.hash, value: parseFloat(t.value) / 1e18, from: t.from, to: t.to, timestamp: t.timeStamp,
        })),
      },
    }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeMacroEvents(): Promise<RawSourceData> {
  const name = 'Macro Calendar'
  const url = 'https://www.forexfactory.com/calendar'
  try {
    const res = await fetchWithTimeout(url, 6000)
    const html = await res.text()
    const $ = cheerio.load(html)
    const events: { name: string; date: string; impact: string; expected: string }[] = []
    $('.calendar__row').each((_, row) => {
      const impactEl = $(row).find('.calendar__impact-icon')
      const impact = impactEl.attr('title') || impactEl.text() || ''
      const isHigh = impact.toLowerCase().includes('high')
      const isMedium = impact.toLowerCase().includes('medium')
      if (isHigh || isMedium) {
        const title = $(row).find('.calendar__event-title').text().trim()
        const date = $(row).find('.calendar__date').text().trim() || $(row).find('td:first').text().trim()
        const expected = $(row).find('.calendar__forecast').text().trim()
        if (title) events.push({
          name: title, date: date || 'Próximamente',
          impact: isHigh ? 'high' : 'medium', expected: expected || '—',
        })
      }
    })
    const hasHighImpact = events.some((e) => e.impact === 'high')
    const cpiRelated = events.some((e) => e.name.toLowerCase().includes('cpi') || e.name.toLowerCase().includes('inflation'))
    const fomcRelated = events.some((e) => e.name.toLowerCase().includes('fomc') || e.name.toLowerCase().includes('fed'))
    return {
      name, url,
      data: {
        upcomingEvents: events.slice(0, 5),
        marketContext: cpiRelated ? 'CPI data ahead—expect volatility' : fomcRelated ? 'FOMC week—rate decision pending' : 'Routine economic calendar',
        riskOn: !hasHighImpact,
      },
    }
  } catch (e) {
    return { name, url, data: { upcomingEvents: [], marketContext: 'No se pudieron cargar eventos macro', riskOn: true }, error: String(e) }
  }
}

function findSmcPatterns(closes: number[], highs: number[], lows: number[], volumes: number[]): {
  marketStructure: 'uptrend' | 'downtrend' | 'ranging'
  structureShift: boolean
  lastBos: 'bullish' | 'bearish' | null
  orderBlocks: { type: 'bullish' | 'bearish'; price: number; strength: 'strong' | 'moderate' | 'weak'; touched: boolean }[]
  fvgs: { type: 'bullish' | 'bearish'; upper: number; lower: number; filled: boolean }[]
  liquidityAbove: number
  liquidityBelow: number
  description: string
} {
  const n = closes.length
  const defaultResult = {
    marketStructure: 'ranging' as const,
    structureShift: false,
    lastBos: null as 'bullish' | 'bearish' | null,
    orderBlocks: [],
    fvgs: [],
    liquidityAbove: 0,
    liquidityBelow: 0,
    description: 'Datos insuficientes para análisis SMC',
  }
  if (n < 20) return defaultResult

  // Find swing points
  const pivots: { index: number; price: number; type: 'high' | 'low' }[] = []
  const lookback = 2
  for (let i = lookback; i < n - lookback; i++) {
    const isHigh = highs[i] === Math.max(...highs.slice(i - lookback, i + lookback + 1))
    const isLow = lows[i] === Math.min(...lows.slice(i - lookback, i + lookback + 1))
    if (isHigh) pivots.push({ index: i, price: highs[i], type: 'high' })
    if (isLow) pivots.push({ index: i, price: lows[i], type: 'low' })
  }

  // Alternate filter
  const filtered: typeof pivots = []
  for (const p of pivots) {
    const last = filtered[filtered.length - 1]
    if (!last || last.type !== p.type) {
      if (!last || Math.abs(p.price - last.price) / last.price > 0.003) {
        filtered.push(p)
      }
    }
  }

  const lastPrice = closes[n - 1]
  const orderBlocks: SmcOrderBlock[] = []
  const fvgs: SmcFvg[] = []

  // Detect order blocks from swing pivots with volume confirmation
  for (let i = 1; i < filtered.length; i++) {
    const prev = filtered[i - 1]
    const curr = filtered[i]
    if (prev.type === 'low' && curr.type === 'high') {
      // Bullish order block: the last bearish candle before the upswing
      const obPrice = prev.price
      const volRatio = volumes[prev.index] / (volumes.slice(0, prev.index).reduce((a, b) => a + b, 0) / Math.max(prev.index, 1))
      const strength: 'strong' | 'moderate' | 'weak' = volRatio > 1.5 ? 'strong' : volRatio > 1 ? 'moderate' : 'weak'
      orderBlocks.push({ type: 'bullish', price: obPrice, strength, touched: lastPrice <= obPrice * 1.02 })
    } else if (prev.type === 'high' && curr.type === 'low') {
      const obPrice = prev.price
      const volRatio = volumes[prev.index] / (volumes.slice(0, prev.index).reduce((a, b) => a + b, 0) / Math.max(prev.index, 1))
      const strength: 'strong' | 'moderate' | 'weak' = volRatio > 1.5 ? 'strong' : volRatio > 1 ? 'moderate' : 'weak'
      orderBlocks.push({ type: 'bearish', price: obPrice, strength, touched: lastPrice >= obPrice * 0.98 })
    }
  }

  // Detect Fair Value Gaps (imbalances between consecutive candles)
  for (let i = 1; i < n - 1; i++) {
    const prevHigh = highs[i - 1]
    const prevLow = lows[i - 1]
    const currHigh = highs[i]
    const currLow = lows[i]
    // Bullish FVG: current low > previous high
    if (currLow > prevHigh && (currLow - prevHigh) / prevHigh > 0.002) {
      fvgs.push({ type: 'bullish', upper: currLow, lower: prevHigh, filled: lastPrice < prevHigh })
    }
    // Bearish FVG: current high < previous low
    if (currHigh < prevLow && (prevLow - currHigh) / prevLow > 0.002) {
      fvgs.push({ type: 'bearish', upper: prevLow, lower: currHigh, filled: lastPrice > prevLow })
    }
  }

  // Determine market structure from pivot sequence
  const recentPivots = filtered.slice(-6)
  const higherHighs = recentPivots.filter((p, i) => p.type === 'high' && i > 0 && p.price > recentPivots[i - 1]?.price)
  const lowerLows = recentPivots.filter((p, i) => p.type === 'low' && i > 0 && p.price < recentPivots[i - 1]?.price)

  let marketStructure: 'uptrend' | 'downtrend' | 'ranging'
  let structureShift = false
  let lastBos: 'bullish' | 'bearish' | null = null
  let description: string

  if (higherHighs.length >= 2 && lowerLows.length < 2) {
    marketStructure = 'uptrend'
    lastBos = 'bullish'
    // Check if last pivot broke previous high
    const lastPivot = filtered[filtered.length - 1]
    const prevHighPivot = [...filtered].reverse().find((p) => p.type === 'high' && p !== lastPivot)
    if (lastPivot && prevHighPivot && lastPivot.type === 'high' && lastPivot.price > prevHighPivot.price) {
      structureShift = true
    }
    description = 'Estructura alcista: máximos y mínimos crecientes. '
    description += orderBlocks.filter((ob) => ob.type === 'bullish').length > 0
      ? 'Zonas de orden alcistas identificadas cerca de los mínimos del movimiento.'
      : 'Operar con sesgo alcista, buscar retrocesos a OB alcistas.'
  } else if (lowerLows.length >= 2 && higherHighs.length < 2) {
    marketStructure = 'downtrend'
    lastBos = 'bearish'
    const lastPivot = filtered[filtered.length - 1]
    const prevLowPivot = [...filtered].reverse().find((p) => p.type === 'low' && p !== lastPivot)
    if (lastPivot && prevLowPivot && lastPivot.type === 'low' && lastPivot.price < prevLowPivot.price) {
      structureShift = true
    }
    description = 'Estructura bajista: máximos y mínimos decrecientes. '
    description += orderBlocks.filter((ob) => ob.type === 'bearish').length > 0
      ? 'Zonas de orden bajistas identificadas cerca de los techos del movimiento.'
      : 'Evitar compras, buscar reacciones en OB bajistas.'
  } else {
    marketStructure = 'ranging'
    description = 'Estructura lateral sin dirección clara. '
    description += fvgs.length > 0
      ? 'Operar los FVGs como soporte/resistencia intradía.'
      : 'Esperar ruptura de estructura para tomar dirección.'
  }

  // Liquidity zones: swing highs/lows as targets
  const allHighs = filtered.filter((p) => p.type === 'high').map((p) => p.price)
  const allLows = filtered.filter((p) => p.type === 'low').map((p) => p.price)
  const liquidityAbove = allHighs.length > 0 ? Math.max(...allHighs) : lastPrice * 1.05
  const liquidityBelow = allLows.length > 0 ? Math.min(...allLows) : lastPrice * 0.95

  return {
    marketStructure, structureShift, lastBos,
    orderBlocks: orderBlocks.slice(-4),
    fvgs: fvgs.slice(-3),
    liquidityAbove: Math.round(liquidityAbove),
    liquidityBelow: Math.round(liquidityBelow),
    description,
  }
}

async function scrapeSmc(asset: AssetConfig): Promise<RawSourceData> {
  const name = 'Smart Money Concepts'
  const symbol = asset.binanceSymbol
  const url = 'https://api.binance.com/api/v3/klines'
  try {
    const klines = await scrapeBinanceKlines(symbol, '1d')
    const closes = klines.map((k) => k.close)
    const highs = klines.map((k) => k.high)
    const lows = klines.map((k) => k.low)
    const volumes = klines.map((k) => k.volume)
    const smc = findSmcPatterns(closes, highs, lows, volumes)
    return { name, url, data: smc as unknown as Record<string, unknown> }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

function findElliottWaves(closes: number[], highs: number[], lows: number[]): {
  waveCount: string; currentWave: number; trend: 'impulse' | 'corrective' | 'neutral'
  completeness: number; nextTarget: number; invalidationLevel: number
  subWaves: { label: string; high: number; low: number }[]
  description: string
} {
  const n = closes.length
  if (n < 30) return {
    waveCount: 'Insufficient data', currentWave: 0, trend: 'neutral',
    completeness: 0, nextTarget: 0, invalidationLevel: 0, subWaves: [],
    description: 'Se necesitan más datos para el análisis de ondas Elliott',
  }

  // Find swing highs and lows using zigzag
  const pivots: { index: number; price: number; type: 'high' | 'low' }[] = []
  const lookback = 3
  for (let i = lookback; i < n - lookback; i++) {
    const isHigh = highs[i] === Math.max(...highs.slice(i - lookback, i + lookback + 1))
    const isLow = lows[i] === Math.min(...lows.slice(i - lookback, i + lookback + 1))
    if (isHigh) pivots.push({ index: i, price: highs[i], type: 'high' })
    if (isLow) pivots.push({ index: i, price: lows[i], type: 'low' })
  }

  // Deduplicate: keep only alternating high/low
  const filtered: typeof pivots = []
  for (const p of pivots) {
    const last = filtered[filtered.length - 1]
    if (!last || last.type !== p.type) {
      if (!last || Math.abs(p.price - last.price) / last.price > 0.005) {
        filtered.push(p)
      } else if (p.type === 'high' && p.price > last.price) {
        filtered[filtered.length - 1] = p
      } else if (p.type === 'low' && p.price < last.price) {
        filtered[filtered.length - 1] = p
      }
    }
  }

  const lastPrice = closes[n - 1]
  const firstPrice = closes[0]
  const totalMove = ((lastPrice - firstPrice) / firstPrice) * 100

  // Simplified wave detection based on pivot count and price action
  const waveCount = filtered.length
  const lastPivot = filtered[filtered.length - 1]
  const prevPivot = filtered[filtered.length - 2]

  let currentWave: number
  let trend: 'impulse' | 'corrective' | 'neutral'
  let waveLabel: string
  let nextTarget: number
  let invalidationLevel: number
  let completeness: number
  let description: string

  // Build sub-waves from pivots
  const subWaves = filtered.slice(-8).map((p, i) => ({
    label: `P${i + 1} ${p.type === 'high' ? '▲' : '▼'}`,
    high: p.price,
    low: p.price,
  }))

  if (totalMove > 5 && waveCount <= 6) {
    // Likely in an impulse wave
    trend = 'impulse'
    currentWave = Math.min(waveCount + 1, 5)
    waveLabel = `Onda ${currentWave} de (5)`
    const avgWave = totalMove / Math.max(waveCount, 1)
    nextTarget = lastPrice * (1 + avgWave / 100 * 0.5)
    invalidationLevel = lastPivot?.type === 'high'
      ? (prevPivot?.price ?? lastPrice * 0.92)
      : lastPrice * 0.92
    completeness = Math.round((waveCount / 5) * 100)
    description = currentWave <= 3
      ? `Onda alcista impulsiva en desarrollo. La onda ${currentWave} está activa con objetivo en $${Math.round(nextTarget).toLocaleString()}.`
      : currentWave <= 5
        ? `Aproximándose al final del impulso alcista (onda ${currentWave} de 5). Zona de toma de ganancias.`
        : 'Estructura impulsiva completa. Esperar corrección A-B-C.'
  } else if (totalMove < -3 && waveCount <= 6) {
    trend = 'impulse'
    currentWave = Math.min(waveCount + 1, 5)
    waveLabel = `Onda ${currentWave} de (5) ▼`
    const avgWave = Math.abs(totalMove) / Math.max(waveCount, 1)
    nextTarget = lastPrice * (1 - avgWave / 100 * 0.5)
    invalidationLevel = lastPivot?.type === 'low'
      ? (prevPivot?.price ?? lastPrice * 1.08)
      : lastPrice * 1.08
    completeness = Math.round((waveCount / 5) * 100)
    description = `Movimiento impulsivo bajista activo. Onda ${currentWave} con objetivo en $${Math.round(nextTarget).toLocaleString()}.`
  } else {
    // Corrective or neutral
    trend = 'corrective'
    currentWave = -(waveCount % 3 || 3)
    const abcWave = Math.abs(currentWave)
    waveLabel = abcWave === 1 ? 'Onda A de (ABC)' : abcWave === 2 ? 'Onda B de (ABC)' : 'Onda C de (ABC)'
    nextTarget = totalMove > 0
      ? lastPrice * (1 + Math.abs(totalMove) / 100 * 0.3)
      : lastPrice * (1 - Math.abs(totalMove) / 100 * 0.3)
    invalidationLevel = lastPrice * (totalMove > 0 ? 0.95 : 1.05)
    completeness = Math.round(((waveCount % 3) / 3) * 100)
    description = `Estructura correctiva A-B-C en desarrollo. ${abcWave === 1 ? 'Onda A corrigiendo el movimiento previo.' : abcWave === 2 ? 'Onda B — rebote temporal dentro de la corrección.' : 'Onda C — etapa final de la corrección.'}`
  }

  return {
    waveCount: waveLabel, currentWave, trend, completeness,
    nextTarget: Math.round(nextTarget), invalidationLevel: Math.round(invalidationLevel),
    subWaves: subWaves.slice(-5), description,
  }
}

async function scrapeElliottWave(asset: AssetConfig): Promise<RawSourceData> {
  const name = 'Elliott Wave'
  const symbol = asset.binanceSymbol
  const url = 'https://api.binance.com/api/v3/klines'
  try {
    const klines = await scrapeBinanceKlines(symbol, '1d')
    const closes = klines.map((k) => k.close)
    const highs = klines.map((k) => k.high)
    const lows = klines.map((k) => k.low)
    const wave = findElliottWaves(closes, highs, lows)
    return { name, url, data: wave as unknown as Record<string, unknown> }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

export async function scrapeAllSources(asset: Asset = 'eth'): Promise<RawSourceData[]> {
  const config = getAssetConfig(asset)
  const isCrypto = asset !== 'gold' && asset !== 'aud'

  const scrapers: Promise<RawSourceData>[] = [
    scrapeCoinGecko(config),
    scrapeMacroEvents(),
  ]

  if (isCrypto) {
    scrapers.push(
      scrapeFearGreed(),
      scrapeCoinMarketCap(config),
      scrapeDefiLlama(),
      scrapeCoinglassFunding(config),
      scrapeCoinDesk(config),
      scrapeCoinTelegraph(config),
      scrapeGlassnode(config),
      scrapeCryptoQuant(),
      scrapeTradingViewTechnicals(config),
      scrapeEtherscan(),
      scrapeBinanceOrderBook(config),
      scrapeMultiTimeframe(config),
      scrapeWhaleTransactions(config),
    )
  } else {
    scrapers.push(
      scrapeMultiTimeframe(config),
    )
  }

  scrapers.push(scrapeElliottWave(config))
  scrapers.push(scrapeSmc(config))

  const results = await Promise.allSettled(scrapers)
  return results.map((r) =>
    r.status === 'fulfilled' ? r.value : { name: 'Unknown', url: '', data: {}, error: r.reason?.toString() }
  )
}

export type { RawSourceData }
