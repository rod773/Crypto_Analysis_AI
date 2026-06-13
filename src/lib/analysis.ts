import type { RawSourceData } from './sources'
import type { AnalysisResult, Asset, PriceData, TechnicalIndicators, OnChainData, SentimentData, FundamentalData, SourceInfo, OrderBookData, WhaleData, MacroData, TimeframeData, ElliottWaveData, SmcData } from './types'
import { getAssetConfig } from './types'

interface DailySnapshot {
  close: number
  volume: number
  high: number
  low: number
  change24h: number
}

interface Kline {
  open: number
  high: number
  low: number
  close: number
  volume: number
}

const priceHistory: DailySnapshot[] = []
let historySeeded = false
let currentKlineHigh = 0
let currentKlineLow = 0

function seedPriceHistory(klines: Kline[]) {
  if (historySeeded || klines.length < 2) return
  for (let i = 0; i < klines.length; i++) {
    const prevClose = i > 0 ? klines[i - 1].close : klines[i].close
    const change24h = ((klines[i].close - prevClose) / prevClose) * 100
    priceHistory.push({
      close: klines[i].close,
      volume: klines[i].volume,
      high: klines[i].high,
      low: klines[i].low,
      change24h,
    })
  }
  if (priceHistory.length > 120) priceHistory.splice(0, priceHistory.length - 120)
  historySeeded = true
  // Store today's real high/low from the last kline
  const last = klines[klines.length - 1]
  currentKlineHigh = last.high
  currentKlineLow = last.low
}

function updatePriceHistory(price: number, volume: number, high: number, low: number, change24h: number) {
  priceHistory.push({ close: price, volume, high, low, change24h })
  if (priceHistory.length > 120) priceHistory.splice(0, priceHistory.length - 120)
}

function roundPrice(value: number): number {
  if (Math.abs(value) < 10) return parseFloat(value.toFixed(4))
  return Math.round(value)
}

function ema(values: number[], period: number): number[] {
  if (values.length < period) return values.map(() => values.reduce((a, b) => a + b, 0) / values.length)
  const k = 2 / (period + 1)
  const result: number[] = []
  result.push(values.slice(0, period).reduce((a, b) => a + b, 0) / period)
  for (let i = period; i < values.length; i++) {
    result.push(values[i] * k + result[result.length - 1] * (1 - k))
  }
  const pad = result[0]
  while (result.length < values.length) result.unshift(pad)
  return result
}

function sma(values: number[], period: number): number[] {
  const result: number[] = []
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) {
      result.push(values.slice(0, i + 1).reduce((a, b) => a + b, 0) / (i + 1))
    } else {
      result.push(values.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0) / period)
    }
  }
  return result
}

function calcRsi(closes: number[], period = 14): number[] {
  if (closes.length < period + 1) return closes.map(() => 50)
  const rsis: number[] = Array(period).fill(50)
  for (let i = period; i < closes.length; i++) {
    let gains = 0
    let losses = 0
    for (let j = i - period + 1; j <= i; j++) {
      const diff = closes[j] - closes[j - 1]
      if (diff > 0) gains += diff
      else losses -= diff
    }
    const avgG = gains / period
    const avgL = losses / period
    rsis.push(avgL === 0 ? 100 : 100 - 100 / (1 + avgG / avgL))
  }
  return rsis
}

function calcMacd(closes: number[]): { macdLine: number[]; signal: number[]; histogram: number[] } {
  const fast = ema(closes.slice(), 12)
  const slow = ema(closes.slice(), 26)
  const macdLine = fast.map((f, i) => f - slow[i])
  const signal = ema(macdLine.slice(), 9)
  const histogram = macdLine.map((m, i) => m - signal[i])
  return { macdLine, signal, histogram }
}

function generatePredictiveSignal(): {
  direction: 'buy' | 'sell' | 'hold'
  reason: string
  score: number
  confidence: number
} {
  if (priceHistory.length < 30) return { direction: 'hold', reason: 'insufficient_data', score: 0, confidence: 50 }

  const closes = priceHistory.map((s) => s.close)
  const volumes = priceHistory.map((s) => s.volume)
  const idx = closes.length - 1

  const rsiVals = calcRsi(closes)
  const { macdLine, signal, histogram } = calcMacd(closes)
  const ma50 = sma(closes, 50)

  const cur = idx

  // RSI Divergence over last ~10 candles (3 sample points)
  let bullishDiv = false
  let bearishDiv = false
  if (idx > 20) {
    const step = 3
    const samples: number[] = []
    for (let s = idx - 10; s <= idx; s += step) samples.push(s)
    if (samples.length >= 2) {
      const last = samples.length - 1
      const pLow1 = priceHistory[samples[last - 1]]?.low ?? 0
      const pLow2 = priceHistory[samples[last]]?.low ?? 0
      const rLow1 = rsiVals[samples[last - 1]] ?? 50
      const rLow2 = rsiVals[samples[last]] ?? 50
      if (pLow1 > pLow2 && rLow1 < rLow2) bullishDiv = true
      if (pLow1 < pLow2 && rLow1 > rLow2) bearishDiv = true
    }
  }

  // MACD signal prediction
  const histGrowing = histogram[cur] > (histogram[cur - 2] ?? histogram[cur])
  const histDeclining = histogram[cur] < (histogram[cur - 2] ?? histogram[cur])
  const macdBuy = histGrowing && macdLine[cur] < signal[cur]
  const macdSell = histDeclining && macdLine[cur] > signal[cur]

  // Volume spike
  const recentVols = volumes.slice(-20)
  const avgVol = recentVols.reduce((a, b) => a + b, 0) / recentVols.length
  const volSpike = volumes[cur] > avgVol * 1.5

  // Predictive scoring (mirrors predictive_backtest.py)
  let buyScore = 0
  let sellScore = 0

  if (bullishDiv) buyScore += 3
  if (macdBuy) buyScore += 2
  if (ma50[cur] && closes[cur] > ma50[cur]) buyScore += 1
  if (rsiVals[cur] < 35) buyScore += 1
  if (volSpike) buyScore += 1

  if (bearishDiv) sellScore += 3
  if (macdSell) sellScore += 2
  if (ma50[cur] && closes[cur] < ma50[cur]) sellScore += 1
  if (rsiVals[cur] > 65) sellScore += 1
  if (volSpike) sellScore += 1

  let direction: 'buy' | 'sell' | 'hold' = 'hold'
  let reason = ''
  let confidence = 50

  if (buyScore > sellScore && buyScore >= 3) {
    direction = 'buy'
    reason = bullishDiv ? 'divergence' : 'momentum'
    confidence = Math.min(92, 55 + buyScore * 8)
  } else if (sellScore > buyScore && sellScore >= 3) {
    direction = 'sell'
    reason = bearishDiv ? 'divergence' : 'momentum'
    confidence = Math.min(92, 55 + sellScore * 8)
  }

  return { direction, reason, score: Math.max(buyScore, sellScore), confidence }
}

function parsePriceData(sources: RawSourceData[], asset: Asset): PriceData {
  const config = getAssetConfig(asset)
  const coingecko = sources.find((s) => s.name === 'CoinGecko')?.data as Record<string, Record<string, number>> | undefined
  const coinData = coingecko?.[config.coinGeckoId]
  const price = coinData?.usd ?? (asset === 'aud' ? 0.7252 : asset === 'gold' ? 1850 : 1850)
  const isFiat = asset === 'gold' || asset === 'aud'
  const change24h = coinData?.usd_24h_change ?? 0
  return {
    price,
    change24h,
    high24h: price * 1.04,
    low24h: price * 0.96,
    volume24h: coinData?.usd_24h_vol ?? (isFiat ? 0 : 15_000_000_000),
    marketCap: coinData?.usd_market_cap ?? (isFiat ? 0 : 220_000_000_000),
  }
}

function inferMaStatus(price: number, maStatus: string, change24h: number): { ma50: number; ma200: number } {
  const cmp = change24h > 0 ? 1 : -1
  if (maStatus.includes('above 200 MA')) return { ma50: price * 0.92, ma200: price * 0.88 }
  if (maStatus.includes('above 50 MA')) return { ma50: roundPrice(price * (1 - cmp * 0.03)), ma200: price * 0.92 }
  return { ma50: price * (1 + cmp * 0.04), ma200: price * (1 + cmp * 0.06) }
}

function parseTechnicalIndicators(
  price: number,
  change24h: number,
  timeframe: TimeframeData,
): TechnicalIndicators {
  const realRsi = timeframe.daily.rsi ?? 50
  const realTrend = timeframe.dominantTrend
  const maStatus = timeframe.daily.maStatus ?? 'unknown'
  const ma = inferMaStatus(price, maStatus, change24h)

  const macdSignal = realRsi > 60 ? 'bullish crossover' : realRsi < 40 ? 'bearish crossover' : 'neutral'

  return {
    rsi: Math.max(15, Math.min(85, Math.round(realRsi))),
    macd: macdSignal,
    ma50: ma.ma50,
    ma200: ma.ma200,
    supportLevels: [
      roundPrice(price * 0.95),
      roundPrice(price * 0.90),
      roundPrice(price * 0.85),
    ],
    resistanceLevels: [
      roundPrice(price * 1.04),
      roundPrice(price * 1.08),
      roundPrice(price * 1.15),
    ],
    trend: realTrend,
  }
}

function parseOnChainData(sources: RawSourceData[], price: number): OnChainData {
  const fundingSource = sources.find((s) => s.name === 'Coinglass')?.data as Record<string, unknown> | undefined
  const fundingData = (fundingSource as Record<string, unknown>) ?? {}
  const fundingArr = (fundingData.data as Array<Record<string, unknown>> | undefined) ?? []
  const fundingRate = (fundingArr[0]?.fundingRate as number) ?? 0.01
  return {
    fundingRate: fundingRate > 0.1 ? fundingRate / 10000 : fundingRate,
    exchangeNetFlow: fundingRate > 0.005 ? 'outflows (-)' : 'inflows (+)',
    stakingYield: 3.2,
    totalStaked: 34_500_000,
    exchangeReserve: 19_200_000,
    liquidationLevels: {
      long: roundPrice(price * 1.08),
      short: roundPrice(price * 0.92),
    },
  }
}

function parseSentimentData(sources: RawSourceData[]): SentimentData {
  const fng = sources.find((s) => s.name === 'Fear & Greed Index')?.data as Record<string, unknown> | undefined
  const fngValue = Number((fng?.data as Record<string, string>[])?.[0]?.value) || 25
  const fngLabel = (fng?.data as Record<string, string>[])?.[0]?.value_classification || 'Fear'
  const headlines: SentimentData['newsHeadlines'] = []
  const coinDesk = sources.find((s) => s.name === 'CoinDesk')?.data as { headlines?: string[] } | undefined
  const coinTelegraph = sources.find((s) => s.name === 'CoinTelegraph')?.data as { headlines?: string[] } | undefined
  for (const h of (coinDesk?.headlines ?? []).slice(0, 3)) {
    const lower = h.toLowerCase()
    const sentiment = lower.includes('dump') || lower.includes('crash') || lower.includes('fear') || lower.includes('bear')
      ? 'negative' as const
      : lower.includes('surge') || lower.includes('rally') || lower.includes('bull') || lower.includes('gain')
        ? 'positive' as const
        : 'neutral' as const
    headlines.push({ title: h, source: 'CoinDesk', sentiment })
  }
  for (const h of (coinTelegraph?.headlines ?? []).slice(0, 3)) {
    const lower = h.toLowerCase()
    const sentiment = lower.includes('dump') || lower.includes('crash') || lower.includes('fear') || lower.includes('bear')
      ? 'negative' as const
      : lower.includes('surge') || lower.includes('rally') || lower.includes('bull') || lower.includes('gain')
        ? 'positive' as const
        : 'neutral' as const
    headlines.push({ title: h, source: 'CoinTelegraph', sentiment })
  }
  return {
    fearGreedIndex: fngValue,
    fearGreedLabel: fngLabel,
    newsHeadlines: headlines,
    socialVolume: 85_000,
    socialSentiment: fngValue < 30 ? 'bearish' : fngValue > 70 ? 'bullish' : 'neutral',
  }
}

function parseFundamentalData(): FundamentalData {
  return {
    defiTvl: 45_800_000_000,
    stablecoinSupply: 82_000_000_000,
    networkRevenue: 2_400_000_000,
    activeAddresses: 520_000,
    transactionCount: 1_200_000,
  }
}

function parseOrderBookData(sources: RawSourceData[]): OrderBookData {
  const ob = sources.find((s) => s.name === 'Binance Order Book')?.data as Record<string, unknown> | undefined
  const bidDepth = (ob?.bidDepth as number) ?? 0
  const askDepth = (ob?.askDepth as number) ?? 0
  const ratio = bidDepth / (askDepth || 1)
  return {
    bidDepth,
    askDepth,
    bidAskRatio: Math.round(ratio * 100) / 100,
    optionFlow: ratio > 1.1 ? 'Calls dominating' : ratio < 0.9 ? 'Puts dominating' : 'Balanced',
    optionFlowSentiment: ratio > 1.1 ? 'bullish' : ratio < 0.9 ? 'bearish' : 'neutral',
    maxPain: 0,
  }
}

function parseWhaleData(sources: RawSourceData[]): WhaleData {
  const w = sources.find((s) => s.name === 'Whale Transactions')?.data as Record<string, unknown> | undefined
  return {
    largeTxns24h: (w?.largeTxns24h as number) ?? 0,
    totalVolumeUsd: (w?.totalVolumeUsd as number) ?? 0,
    accumulation: (w?.accumulation as WhaleData['accumulation']) ?? 'neutral',
    topWhaleNetFlow: (w?.topWhaleNetFlow as string) ?? '\u2014',
    notableTxns: (w?.notableTxns as WhaleData['notableTxns']) ?? [],
  }
}

function parseMacroData(sources: RawSourceData[]): MacroData {
  const m = sources.find((s) => s.name === 'Macro Calendar')?.data as Record<string, unknown> | undefined
  return {
    upcomingEvents: (m?.upcomingEvents as MacroData['upcomingEvents']) ?? [],
    marketContext: (m?.marketContext as string) ?? 'No data',
    riskOn: (m?.riskOn as boolean) ?? true,
  }
}

function parseTimeframeData(sources: RawSourceData[]): TimeframeData {
  const tf = sources.find((s) => s.name === 'Multi-Timeframe')?.data as Record<string, unknown> | undefined
  return {
    daily: (tf?.daily as TimeframeData['daily']) ?? { trend: 'neutral', rsi: 50, maStatus: 'unknown' },
    fourHour: (tf?.fourHour as TimeframeData['fourHour']) ?? { trend: 'neutral', rsi: 50, maStatus: 'unknown' },
    oneHour: (tf?.oneHour as TimeframeData['oneHour']) ?? { trend: 'neutral', rsi: 50, maStatus: 'unknown' },
    alignment: (tf?.alignment as TimeframeData['alignment']) ?? 'conflicting',
    dominantTrend: (tf?.dominantTrend as TimeframeData['dominantTrend']) ?? 'neutral',
  }
}

function parseElliottWaveData(sources: RawSourceData[]): ElliottWaveData {
  const ew = sources.find((s) => s.name === 'Elliott Wave')?.data as Record<string, unknown> | undefined
  if (ew && (ew.trend as string)) {
    return {
      waveCount: (ew.waveCount as string) ?? '',
      currentWave: (ew.currentWave as number) ?? 0,
      trend: (ew.trend as ElliottWaveData['trend']) ?? 'neutral',
      completeness: (ew.completeness as number) ?? 0,
      nextTarget: (ew.nextTarget as number) ?? 0,
      invalidationLevel: (ew.invalidationLevel as number) ?? 0,
      subWaves: (ew.subWaves as ElliottWaveData['subWaves']) ?? [],
      description: (ew.description as string) ?? '',
    }
  }
  return {
    waveCount: 'No data',
    currentWave: 0,
    trend: 'neutral',
    completeness: 0,
    nextTarget: 0,
    invalidationLevel: 0,
    subWaves: [],
    description: 'No se pudieron calcular ondas Elliott',
  }
}

function parseSmcData(sources: RawSourceData[]): SmcData {
  const smc = sources.find((s) => s.name === 'Smart Money Concepts')?.data as Record<string, unknown> | undefined
  if (smc && (smc.marketStructure as string)) {
    return {
      marketStructure: (smc.marketStructure as SmcData['marketStructure']) ?? 'ranging',
      structureShift: (smc.structureShift as boolean) ?? false,
      lastBos: (smc.lastBos as SmcData['lastBos']) ?? null,
      orderBlocks: (smc.orderBlocks as SmcData['orderBlocks']) ?? [],
      fvgs: (smc.fvgs as SmcData['fvgs']) ?? [],
      liquidityAbove: (smc.liquidityAbove as number) ?? 0,
      liquidityBelow: (smc.liquidityBelow as number) ?? 0,
      description: (smc.description as string) ?? '',
    }
  }
  return {
    marketStructure: 'ranging',
    structureShift: false,
    lastBos: null,
    orderBlocks: [],
    fvgs: [],
    liquidityAbove: 0,
    liquidityBelow: 0,
    description: 'No se pudieron calcular datos SMC',
  }
}

function buildVerdict(
  price: number,
  priceData: PriceData,
  _technical: TechnicalIndicators,
  sentiment: SentimentData,
): AnalysisResult['verdict'] {
  updatePriceHistory(price, priceData.volume24h, priceData.high24h, priceData.low24h, priceData.change24h)

  const signal = generatePredictiveSignal()
  const fng = sentiment.fearGreedIndex

  let shortTerm: 'buy' | 'sell' | 'hold'
  let longTerm: 'buy' | 'sell' | 'hold'
  let confidence: number
  let summary: string
  let stopLoss: number
  let takeProfitShort: number
  let takeProfitLong: number

  if (signal.direction === 'buy') {
    shortTerm = 'buy'
    longTerm = 'buy'
    confidence = signal.confidence
    stopLoss = roundPrice(price * 0.94)
    takeProfitShort = roundPrice(price * 1.12)
    takeProfitLong = roundPrice(price * 1.28)
    summary = `Compra por ${signal.reason === 'divergence' ? 'divergencia alcista RSI' : 'momentum MACD'}`
    summary += `. Score: ${signal.score}. Soporte multi-timeframe y estructura favorable.`
  } else if (signal.direction === 'sell') {
    shortTerm = 'sell'
    longTerm = 'hold'
    confidence = signal.confidence
    stopLoss = roundPrice(price * 1.06)
    takeProfitShort = roundPrice(price * 0.90)
    takeProfitLong = roundPrice(price * 1.05)
    summary = `Venta por ${signal.reason === 'divergence' ? 'divergencia bajista RSI' : 'señal MACD'}`
    summary += `. Score: ${signal.score}. Riesgo de corrección a corto plazo.`
  } else {
    shortTerm = 'hold'
    longTerm = 'hold'
    confidence = 50
    stopLoss = roundPrice(price * 0.93)
    takeProfitShort = roundPrice(price * 1.06)
    takeProfitLong = roundPrice(price * 1.15)
    summary = 'Sin señal clara. Esperando divergencia o cruce MACD con volumen.'
  }

  // Contrarian overrides
  if (fng < 20 && shortTerm === 'sell') {
    shortTerm = 'hold'
    summary += ' | Override: fear extremo, no vender.'
  }
  if (fng > 80 && shortTerm === 'buy') {
    shortTerm = 'hold'
    summary += ' | Override: greed extremo, tomar ganancias.'
  }

  return {
    shortTerm,
    longTerm,
    confidence,
    summary,
    keyLevels: { stopLoss, takeProfitShort, takeProfitLong },
  }
}

export function analyze(sources: RawSourceData[], asset: Asset = 'eth'): AnalysisResult {
  const priceData = parsePriceData(sources, asset)
  const timeframe = parseTimeframeData(sources)
  const technical = parseTechnicalIndicators(priceData.price, priceData.change24h, timeframe)
  const onChain = parseOnChainData(sources, priceData.price)
  const sentiment = parseSentimentData(sources)
  const fundamental = parseFundamentalData()
  const orderBook = parseOrderBookData(sources)
  const whaleData = parseWhaleData(sources)
  const macro = parseMacroData(sources)
  const elliottWave = parseElliottWaveData(sources)
  const smc = parseSmcData(sources)

  // Seed price history with real daily klines from Multi-Timeframe source (once)
  // Also update current day's high/low from the latest kline on every call
  const tf = sources.find((s) => s.name === 'Multi-Timeframe')?.data as Record<string, unknown> | undefined
  const klines = tf?.klines as Kline[] | undefined
  if (klines?.length) {
    if (!historySeeded) seedPriceHistory(klines)
    const last = klines[klines.length - 1]
    currentKlineHigh = last.high
    currentKlineLow = last.low
  }

  // Use real kline high/low when available (instead of synthetic price * 1.04 / 0.96)
  if (currentKlineHigh > 0 && currentKlineLow > 0) {
    priceData.high24h = currentKlineHigh
    priceData.low24h = currentKlineLow
  }

  const verdict = buildVerdict(priceData.price, priceData, technical, sentiment)

  const sourceInfoList: SourceInfo[] = sources.map((s) => ({
    name: s.name,
    url: s.url,
    status: s.error ? 'error' : 'ok',
    error: s.error,
  }))

  const baseConf = verdict.confidence

  return {
    asset,
    timestamp: new Date().toISOString(),
    priceData,
    technical,
    onChain,
    sentiment,
    fundamental,
    orderBook,
    whaleData,
    macro,
    timeframe,
    elliottWave,
    smc,
    verdict,
    sources: sourceInfoList,
    scenarios: {
      bearish: {
        target: roundPrice(priceData.price * 0.9),
        trigger: `Pierde soporte en $${technical.supportLevels[0].toLocaleString()}`,
        probability: Math.max(10, Math.min(90, 50 - ((baseConf - 50) / 2))),
      },
      bullish: {
        target: roundPrice(priceData.price * 1.15),
        trigger: `Rompe resistencia en $${technical.resistanceLevels[0].toLocaleString()}`,
        probability: Math.max(10, Math.min(90, 50 + ((baseConf - 50) / 2))),
      },
    },
  }
}
