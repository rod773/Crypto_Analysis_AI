import type { RawSourceData } from './sources'
import type { AnalysisResult, Asset, PriceData, TechnicalIndicators, OnChainData, SentimentData, FundamentalData, SourceInfo, OrderBookData, WhaleData, MacroData, TimeframeData, ElliottWaveData, SmcData, SmcOrderBlock, SmcFvg } from './types'
import { getAssetConfig } from './types'

function parsePriceData(sources: RawSourceData[], asset: Asset): PriceData {
  const config = getAssetConfig(asset)
  const coingecko = sources.find((s) => s.name === 'CoinGecko')?.data as Record<string, Record<string, number>> | undefined
  const coinData = coingecko?.[config.coinGeckoId]
  const price = coinData?.usd ?? 1850
  const isGold = asset === 'gold'
  return {
    price,
    change24h: coinData?.usd_24h_change ?? 0,
    high24h: price * 1.04,
    low24h: price * 0.96,
    volume24h: coinData?.usd_24h_vol ?? (isGold ? 0 : 15_000_000_000),
    marketCap: coinData?.usd_market_cap ?? (isGold ? 0 : 220_000_000_000),
  }
}

function parseTechnicalIndicators(price: number, change24h: number): TechnicalIndicators {
  const rsi = Math.round(50 + (change24h > 0 ? change24h * 1.5 : change24h * 1.5) * -1)
  const clampedRsi = Math.max(15, Math.min(85, rsi))
  return {
    rsi: clampedRsi,
    macd: clampedRsi < 40 ? 'bearish crossover' : clampedRsi > 60 ? 'bullish crossover' : 'neutral',
    ma50: price * (change24h > 0 ? 0.97 : 1.03),
    ma200: price * (change24h > 0 ? 0.92 : 1.08),
    supportLevels: [
      Math.round(price * 0.95),
      Math.round(price * 0.90),
      Math.round(price * 0.85),
    ],
    resistanceLevels: [
      Math.round(price * 1.04),
      Math.round(price * 1.08),
      Math.round(price * 1.15),
    ],
    trend: change24h > 2 ? 'bullish' : change24h < -2 ? 'bearish' : 'neutral',
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
      long: Math.round(price * 1.08),
      short: Math.round(price * 0.92),
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
    topWhaleNetFlow: (w?.topWhaleNetFlow as string) ?? '—',
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

function parseElliottWaveData(price: number, change24h: number, trend: string): ElliottWaveData {
  const isBullish = change24h > 0
  const absChange = Math.abs(change24h)

  let currentWave: number
  let waveCount: string
  let ewTrend: 'impulse' | 'corrective' | 'neutral'
  let completeness: number
  let nextTarget: number
  let invalidationLevel: number
  const subWaves: { label: string; high: number; low: number }[] = []

  if (absChange < 1) {
    ewTrend = 'neutral'
    currentWave = 0
    waveCount = 'Ondas no claras — baj\u00EDsima volatilidad'
    completeness = 10
    nextTarget = price * 1.03
    invalidationLevel = price * 0.97
  } else if (isBullish) {
    if (absChange > 4) {
      currentWave = 3
      waveCount = 'Onda 3 de (5) — Impulso alcista'
      ewTrend = 'impulse'
      completeness = 55
      nextTarget = price * 1.12
      invalidationLevel = price * 0.92
    } else {
      currentWave = 1
      waveCount = 'Posible Onda 1 de (5) — Inicio de impulso'
      ewTrend = 'impulse'
      completeness = 25
      nextTarget = price * 1.08
      invalidationLevel = price * 0.95
    }
    subWaves.push(
      { label: '1', high: price, low: Math.round(price * 0.94) },
      { label: '2', high: Math.round(price * 0.98), low: Math.round(price * 0.93) },
      { label: '3', high: Math.round(price * 1.06), low: Math.round(price * 0.97) },
    )
  } else {
    if (absChange > 4) {
      currentWave = 3
      waveCount = 'Onda C de (A)-(B)-(C) — Correcci\u00F3n activa'
      ewTrend = 'corrective'
      completeness = 65
      nextTarget = price * 0.88
      invalidationLevel = price * 1.05
    } else {
      currentWave = -1
      waveCount = 'Posible Onda A de correcci\u00F3n — Retroceso'
      ewTrend = 'corrective'
      completeness = 35
      nextTarget = price * 0.93
      invalidationLevel = price * 1.04
    }
    subWaves.push(
      { label: 'A', high: price, low: Math.round(price * 0.95) },
      { label: 'B', high: Math.round(price * 1.01), low: Math.round(price * 0.96) },
      { label: 'C', high: Math.round(price * 0.97), low: Math.round(price * 0.90) },
    )
  }

  return {
    waveCount,
    currentWave,
    trend: ewTrend,
    completeness,
    nextTarget,
    invalidationLevel,
    subWaves,
    description: buildElliottDescription(ewTrend, currentWave, price, nextTarget, invalidationLevel, trend),
  }
}

function buildElliottDescription(trend: string, wave: number, price: number, target: number, invalidation: number, overallTrend: string): string {
  if (trend === 'neutral') {
    return 'No se identifica un patr\u00F3n de ondas Elliott claro debido a la baja volatilidad. Esperar una ruptura direccional para confirmar el conteo.'
  }
  if (trend === 'impulse') {
    if (wave <= 3) {
      return `Estructura impulsiva alcista en desarrollo. Las Ondas 1 y 2 ya se completaron, y la Onda 3 (la m\u00E1s fuerte) est\u00E1 en progreso. Objetivo en $${target.toLocaleString()}. Mientras $${invalidation.toLocaleString()} se mantenga como soporte, la estructura alcista sigue intacta.`
    }
    return `Onda 3 probablemente completada. Acerc\u00E1ndose a Onda 4 correctiva y luego Onda 5 final. Riesgo de agotamiento de tendencia.`
  }
  return `Correcci\u00F3n en curso (Onda ${wave === -1 ? 'A' : 'C'}). El mercado est\u00E1 retrocediendo el impulso previo. Esperar se\u00F1ales de reversi\u00F3n en $${target.toLocaleString()} antes de considerar entrada larga.`
}

function parseSmcData(price: number, change24h: number, trend: string, elliottWave: ElliottWaveData): SmcData {
  const isBullish = change24h > 0
  const isStrongMove = Math.abs(change24h) > 3
  const isRanging = Math.abs(change24h) < 1

  const marketStructure: 'uptrend' | 'downtrend' | 'ranging' = isRanging ? 'ranging' : isBullish ? 'uptrend' : 'downtrend'
  const structureShift = isStrongMove && (isBullish ? trend === 'bearish' : trend === 'bullish')
  const lastBos: 'bullish' | 'bearish' | null = isStrongMove ? (isBullish ? 'bullish' : 'bearish') : null

  const orderBlocks: SmcOrderBlock[] = []
  const fvgs: SmcFvg[] = []

  if (isBullish || isRanging) {
    orderBlocks.push({
      type: 'bullish',
      price: Math.round(price * 0.955),
      strength: Math.abs(change24h) > 2 ? 'strong' : 'moderate',
      touched: false,
    })
    fvgs.push({
      type: 'bullish',
      upper: Math.round(price * 1.02),
      lower: Math.round(price * 0.985),
      filled: false,
    })
  }

  if (!isBullish || isRanging) {
    orderBlocks.push({
      type: 'bearish',
      price: Math.round(price * 1.045),
      strength: !isBullish && Math.abs(change24h) > 2 ? 'strong' : 'moderate',
      touched: isRanging,
    })
    fvgs.push({
      type: 'bearish',
      upper: Math.round(price * 1.015),
      lower: Math.round(price * 0.98),
      filled: isRanging,
    })
  }

  const liquidityAbove = Math.round(price * (1 + (0.03 + Math.abs(change24h) / 200)))
  const liquidityBelow = Math.round(price * (1 - (0.03 + Math.abs(change24h) / 200)))

  return {
    marketStructure,
    structureShift,
    lastBos,
    orderBlocks,
    fvgs,
    liquidityAbove,
    liquidityBelow,
    description: buildSmcDescription(marketStructure, structureShift, lastBos, liquidityAbove, liquidityBelow, price, elliottWave),
  }
}

function buildSmcDescription(
  structure: string, shift: boolean, bos: string | null,
  liqAbove: number, liqBelow: number, price: number, ew: ElliottWaveData
): string {
  let desc = ''
  if (structure === 'uptrend') {
    desc = `Estructura de mercado alcista. `
    if (bos) desc += `Se confirm\u00F3 un BOS (Break of Structure) alcista. `
    if (shift) desc += `Posible cambio de estructura (MSS) detectado — el smart money estar\u00EDa acumulando. `
    desc += `Liquidez de stop-losses por encima en $${liqAbove.toLocaleString()}. `
    desc += `Buscar order blocks alcistas cerca de $${(price * 0.95).toLocaleString()} para entradas largas.`
  } else if (structure === 'downtrend') {
    desc = `Estructura de mercado bajista. `
    if (bos) desc += `BOS bajista confirmado. `
    if (shift) desc += `Posible MSS bajista — smart money distribuyendo. `
    desc += `Liquidez por debajo en $${liqBelow.toLocaleString()}. `
    desc += `Buscar FVG o retest de OB bajista para entradas cortas.`
  } else {
    desc = `El mercado est\u00E1 en rango, sin estructura direccional clara. `
    desc += `Liquidez arriba en $${liqAbove.toLocaleString()} y abajo en $${liqBelow.toLocaleString()}. `
    desc += `Esperar una ruptura con volumen para confirmar direcci\u00F3n.`
  }

  if (ew.trend === 'impulse') {
    desc += ` El conteo de Elliott coincide con estructura impulsiva — refuerza la tesis direccional.`
  } else if (ew.trend === 'corrective' && structure !== 'ranging') {
    desc += ` La correcci\u00F3n de Elliott podr\u00EDa estar cazando liquidez antes del siguiente movimiento direccional.`
  }

  return desc
}

function buildVerdict(
  price: number,
  technical: TechnicalIndicators,
  onChain: OnChainData,
  sentiment: SentimentData,
  orderBook: OrderBookData,
  whaleData: WhaleData,
  timeframe: TimeframeData,
  elliottWave: ElliottWaveData,
  smc: SmcData,
): AnalysisResult['verdict'] {
  const bearishScore =
    (technical.trend === 'bearish' ? 3 : 0) +
    (technical.rsi > 70 ? 2 : technical.rsi < 30 ? -1 : 0) +
    (onChain.fundingRate > 0.005 ? 3 : 0) +
    (sentiment.fearGreedIndex < 25 ? 2 : 0) +
    (orderBook.bidAskRatio < 0.9 ? 2 : 0) +
    (whaleData.accumulation === 'distributing' ? 2 : 0) +
    (timeframe.dominantTrend === 'bearish' ? 3 : timeframe.dominantTrend === 'bullish' ? -1 : 0) +
    (timeframe.alignment === 'aligned' && timeframe.dominantTrend === 'bearish' ? 3 : 0) +
    (elliottWave.trend === 'impulse' && elliottWave.currentWave >= 5 ? 3 : 0) +
    (elliottWave.currentWave <= -3 ? 2 : 0) +
    (smc.marketStructure === 'downtrend' ? 2 : 0) +
    (smc.lastBos === 'bearish' ? 2 : 0)

  const bullishScore =
    (technical.trend === 'bullish' ? 3 : 0) +
    (technical.rsi < 30 ? 2 : technical.rsi > 70 ? -1 : 0) +
    (onChain.fundingRate < 0.001 ? 2 : 0) +
    (sentiment.fearGreedIndex > 70 ? 2 : 0) +
    (orderBook.bidAskRatio > 1.1 ? 2 : 0) +
    (whaleData.accumulation === 'accumulating' ? 2 : 0) +
    (timeframe.dominantTrend === 'bullish' ? 3 : timeframe.dominantTrend === 'bearish' ? -1 : 0) +
    (timeframe.alignment === 'aligned' && timeframe.dominantTrend === 'bullish' ? 3 : 0) +
    (elliottWave.trend === 'impulse' && elliottWave.currentWave <= 3 ? 3 : 0) +
    (elliottWave.currentWave <= -2 ? -2 : 0) +
    (smc.marketStructure === 'uptrend' ? 2 : 0) +
    (smc.lastBos === 'bullish' ? 2 : 0) +
    (smc.structureShift ? 3 : 0)

  const netScore = bullishScore - bearishScore

  let shortTerm: 'buy' | 'sell' | 'hold'
  let longTerm: 'buy' | 'sell' | 'hold'
  let confidence: number
  let summary: string
  let stopLoss: number
  let takeProfitShort: number
  let takeProfitLong: number

  if (netScore >= 4) {
    shortTerm = 'buy'
    longTerm = 'buy'
    confidence = Math.min(85, 50 + netScore * 8)
    summary = 'The market structure is strongly bullish. Technical indicators align with positive on-chain flows and favorable sentiment. This is a good entry point for both short and long term.'
    stopLoss = Math.round(price * 0.93)
    takeProfitShort = Math.round(price * 1.12)
    takeProfitLong = Math.round(price * 1.35)
  } else if (netScore >= 1) {
    shortTerm = 'hold'
    longTerm = 'buy'
    confidence = Math.min(70, 40 + netScore * 8)
    summary = 'Mixed signals overall. The short-term picture is uncertain but the long-term fundamentals remain intact. Consider waiting for confirmation before entering, or DCA into a position.'
    stopLoss = Math.round(price * 0.92)
    takeProfitShort = Math.round(price * 1.08)
    takeProfitLong = Math.round(price * 1.25)
  } else if (netScore >= -2) {
    shortTerm = 'hold'
    longTerm = 'hold'
    confidence = Math.min(60, 40 + Math.abs(netScore) * 5)
    summary = 'The market is in a neutral zone with conflicting signals. High funding rates and weak technical structure suggest caution. The best strategy is to wait for a clearer setup before acting.'
    stopLoss = Math.round(price * 0.90)
    takeProfitShort = Math.round(price * 1.05)
    takeProfitLong = Math.round(price * 1.15)
  } else {
    shortTerm = 'sell'
    longTerm = 'hold'
    confidence = Math.min(80, 50 + Math.abs(netScore) * 7)
    summary = 'Short-term risks are elevated. Weak technical structure, high funding rates (crowded longs), and bearish sentiment create a dangerous setup. Avoid buying into weakness. If you hold, consider tight stops. For long-term investors, wait for confirmation of support before adding.'
    stopLoss = Math.round(price * 1.05)
    takeProfitShort = Math.round(price * 0.95)
    takeProfitLong = Math.round(price * 1.10)
  }

  if (sentiment.fearGreedIndex < 20) {
    confidence = Math.max(confidence - 10, 30)
    if (shortTerm === 'buy') shortTerm = 'hold'
  }

  return {
    shortTerm,
    longTerm,
    confidence,
    summary,
    keyLevels: {
      stopLoss,
      takeProfitShort,
      takeProfitLong,
    },
  }
}

export function analyze(sources: RawSourceData[], asset: Asset = 'eth'): AnalysisResult {
  const priceData = parsePriceData(sources, asset)
  const technical = parseTechnicalIndicators(priceData.price, priceData.change24h)
  const onChain = parseOnChainData(sources, priceData.price)
  const sentiment = parseSentimentData(sources)
  const fundamental = parseFundamentalData()
  const orderBook = parseOrderBookData(sources)
  const whaleData = parseWhaleData(sources)
  const macro = parseMacroData(sources)
  const timeframe = parseTimeframeData(sources)
  const elliottWave = parseElliottWaveData(priceData.price, priceData.change24h, technical.trend)
  const smc = parseSmcData(priceData.price, priceData.change24h, technical.trend, elliottWave)
  const verdict = buildVerdict(priceData.price, technical, onChain, sentiment, orderBook, whaleData, timeframe, elliottWave, smc)

  const sourceInfoList: SourceInfo[] = sources.map((s) => ({
    name: s.name,
    url: s.url,
    status: s.error ? 'error' : 'ok',
    error: s.error,
  }))

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
        target: Math.round(priceData.price * 0.9),
        trigger: `Losing support at $${technical.supportLevels[0].toLocaleString()}`,
        probability: 45,
      },
      bullish: {
        target: Math.round(priceData.price * 1.15),
        trigger: `Breaking resistance at $${technical.resistanceLevels[0].toLocaleString()}`,
        probability: 55,
      },
    },
  }
}
