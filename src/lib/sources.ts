import * as cheerio from 'cheerio'
import type { Asset, AssetConfig } from './types'
import { getAssetConfig } from './types'

interface RawSourceData {
  name: string
  url: string
  data: Record<string, unknown>
  error?: string
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
  try {
    const res = await fetchWithTimeout(url)
    const json = await res.json() as Record<string, unknown>
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

async function scrapeGoldPrice(): Promise<RawSourceData> {
  const name = 'Gold Price'
  const url = 'https://api.metals.live/v1/spot/gold'
  try {
    const res = await fetchWithTimeout(url)
    const json = await res.json() as Record<string, unknown>[]
    const usd = json.find((r: Record<string, unknown>) => r.currency === 'USD')
    return {
      name, url,
      data: {
        ethereum: {
          usd: usd?.price ?? 2300,
          usd_24h_change: 0,
          usd_24h_vol: 0,
          usd_market_cap: 0,
        },
      },
    }
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
  const tag = asset.id === 'btc' ? 'bitcoin' : 'ethereum'
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
  const tag = asset.id === 'btc' ? 'bitcoin' : 'ethereum'
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
  const symbol = asset.id === 'btc' ? 'BTCUSD' : asset.id === 'gold' ? 'XAUUSD' : 'ETHUSD'
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
  const symbol = asset.id === 'btc' ? 'BTCUSDT' : 'ETHUSDT'
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
  const symbol = asset.id === 'btc' ? 'BTCUSDT' : asset.id === 'gold' ? 'XAUUSDT' : 'ETHUSDT'
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
    if (asset.id === 'gold') {
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

export async function scrapeAllSources(asset: Asset = 'eth'): Promise<RawSourceData[]> {
  const config = getAssetConfig(asset)
  const isCrypto = asset !== 'gold'

  const scrapers: Promise<RawSourceData>[] = [
    asset === 'gold' ? scrapeGoldPrice() : scrapeCoinGecko(config),
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

  const results = await Promise.allSettled(scrapers)
  return results.map((r) =>
    r.status === 'fulfilled' ? r.value : { name: 'Unknown', url: '', data: {}, error: r.reason?.toString() }
  )
}

export type { RawSourceData }
