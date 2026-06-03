import * as cheerio from 'cheerio'

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

async function scrapeCoinGecko(): Promise<RawSourceData> {
  const name = 'CoinGecko'
  const url = 'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd&include_24hr_vol=true&include_24hr_change=true&include_market_cap=true'
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

async function scrapeCoinMarketCap(): Promise<RawSourceData> {
  const name = 'CoinMarketCap'
  const url = 'https://coinmarketcap.com/currencies/ethereum/'
  try {
    const res = await fetchWithTimeout(url)
    const html = await res.text()
    const $ = cheerio.load(html)
    const priceEl = $('[data-test="text-cdp-price-display"]').first().text().trim()
    const changeEl = $('[data-test="text-cdp-price-change"]').first().text().trim()
    return {
      name,
      url,
      data: { price: priceEl, change: changeEl },
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

async function scrapeCoinglassFunding(): Promise<RawSourceData> {
  const name = 'Coinglass'
  const url = 'https://api.coinglass.com/api/funding-rate/v2/list?symbol=ETH'
  try {
    const res = await fetchWithTimeout(url)
    const json = await res.json() as Record<string, unknown>
    return { name, url, data: json }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeCoinDesk(): Promise<RawSourceData> {
  const name = 'CoinDesk'
  const url = 'https://www.coindesk.com/price/ethereum/'
  try {
    const res = await fetchWithTimeout(url)
    const html = await res.text()
    const $ = cheerio.load(html)
    const headlines: string[] = []
    $('h2, h3, .headline, article a').each((_, el) => {
      const text = $(el).text().trim()
      if (text.length > 15 && headlines.length < 5) {
        headlines.push(text)
      }
    })
    return { name, url, data: { headlines } }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeCoinTelegraph(): Promise<RawSourceData> {
  const name = 'CoinTelegraph'
  const url = 'https://cointelegraph.com/tags/ethereum'
  try {
    const res = await fetchWithTimeout(url)
    const html = await res.text()
    const $ = cheerio.load(html)
    const headlines: string[] = []
    $('h2, h3, .post-title, article a').each((_, el) => {
      const text = $(el).text().trim()
      if (text.length > 15 && headlines.length < 5) {
        headlines.push(text)
      }
    })
    return { name, url, data: { headlines } }
  } catch (e) {
    return { name, url, data: {}, error: String(e) }
  }
}

async function scrapeGlassnode(): Promise<RawSourceData> {
  const name = 'Glassnode'
  const url = 'https://glassnode.com/blog/tag/ethereum'
  try {
    const res = await fetchWithTimeout(url)
    const html = await res.text()
    const $ = cheerio.load(html)
    const titles: string[] = []
    $('h2, h3, .blog-title, article a h3').each((_, el) => {
      const text = $(el).text().trim()
      if (text.length > 15 && titles.length < 5) {
        titles.push(text)
      }
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

async function scrapeTradingViewTechnicals(): Promise<RawSourceData> {
  const name = 'TradingView'
  const url = 'https://www.tradingview.com/symbols/ETHUSD/technicals/'
  try {
    const res = await fetchWithTimeout(url)
    const html = await res.text()
    const $ = cheerio.load(html)
    const signals: string[] = []
    $('[class*="signal"], [class*="indicator"]').each((_, el) => {
      const text = $(el).text().trim()
      if (text.length > 3 && signals.length < 10) {
        signals.push(text)
      }
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

export async function scrapeAllSources(): Promise<RawSourceData[]> {
  const results = await Promise.allSettled([
    scrapeCoinGecko(),
    scrapeFearGreed(),
    scrapeCoinMarketCap(),
    scrapeDefiLlama(),
    scrapeCoinglassFunding(),
    scrapeCoinDesk(),
    scrapeCoinTelegraph(),
    scrapeGlassnode(),
    scrapeCryptoQuant(),
    scrapeTradingViewTechnicals(),
    scrapeEtherscan(),
  ])
  return results.map((r) =>
    r.status === 'fulfilled' ? r.value : { name: 'Unknown', url: '', data: {}, error: r.reason?.toString() }
  )
}

export type { RawSourceData }
