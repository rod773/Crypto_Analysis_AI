import type { RawSourceData } from './sources'
import type { AnalysisResult, Asset, PriceData, TechnicalIndicators, OnChainData, SentimentData, FundamentalData, SourceInfo, OrderBookData, WhaleData, MacroData, TimeframeData, ElliottWaveData, SmcData, SmcOrderBlock, SmcFvg } from './types'
import { getAssetConfig } from './types'

function roundPrice(value: number): number {
  if (Math.abs(value) < 10) {
    return parseFloat(value.toFixed(4))
  }
  return Math.round(value)
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

interface VerdictContext {
  price: number
  technical: TechnicalIndicators
  onChain: OnChainData
  sentiment: SentimentData
  orderBook: OrderBookData
  whaleData: WhaleData
  timeframe: TimeframeData
  elliottWave: ElliottWaveData
  smc: SmcData
  macro: MacroData
}

function calcWeightedScore(ctx: VerdictContext) {
  const { technical, timeframe, sentiment, orderBook, whaleData, elliottWave, smc, macro, price } = ctx
  const rsi = technical.rsi
  const fng = sentiment.fearGreedIndex

  let buyScore = 0
  let sellScore = 0
  let buyWeight = 0
  let sellWeight = 0

  // 1. RSI Momentum (weight: 15%)
  if (rsi < 30) { buyScore += 3; buyWeight += 15 }
  else if (rsi < 40) { buyScore += 2; buyWeight += 10 }
  else if (rsi > 70) { sellScore += 3; sellWeight += 15 }
  else if (rsi > 60) { sellScore += 2; sellWeight += 10 }

  // 2. Trend Direction (weight: 20%)
  if (technical.trend === 'bullish') { buyScore += 3; buyWeight += 20 }
  else if (technical.trend === 'bearish') { sellScore += 3; sellWeight += 20 }

  // 3. Multi-Timeframe Alignment (weight: 20%)
  if (timeframe.alignment === 'aligned') {
    if (timeframe.dominantTrend === 'bullish') { buyScore += 3; buyWeight += 20 }
    else if (timeframe.dominantTrend === 'bearish') { sellScore += 3; sellWeight += 20 }
  } else if (timeframe.alignment === 'partial') {
    if (timeframe.dominantTrend === 'bullish') { buyScore += 1; buyWeight += 8 }
    else if (timeframe.dominantTrend === 'bearish') { sellScore += 1; sellWeight += 8 }
  }

  // 4. SMC Market Structure (weight: 15%)
  if (smc.marketStructure === 'uptrend' && smc.lastBos === 'bullish') { buyScore += 3; buyWeight += 15 }
  else if (smc.marketStructure === 'downtrend' && smc.lastBos === 'bearish') { sellScore += 3; sellWeight += 15 }
  else if (smc.marketStructure === 'uptrend') { buyScore += 2; buyWeight += 10 }
  else if (smc.marketStructure === 'downtrend') { sellScore += 2; sellWeight += 10 }

  // 5. Elliott Wave Position (weight: 10%)
  if (elliottWave.trend === 'impulse') {
    if (elliottWave.currentWave <= 3) { buyScore += 2; buyWeight += 10 }
    else if (elliottWave.currentWave === 4) { buyScore += 1; buyWeight += 5 }
  } else if (elliottWave.trend === 'corrective') {
    if (elliottWave.currentWave >= 3) { sellScore += 2; sellWeight += 10 }
    else { sellScore += 1; sellWeight += 5 }
  }

  // 6. Sentiment / Fear & Greed (weight: 10%) - Contrarian
  if (fng < 20) { buyScore += 2; buyWeight += 10 } // extreme fear = buy
  else if (fng < 30) { buyScore += 1; buyWeight += 5 }
  else if (fng > 80) { sellScore += 2; sellWeight += 10 } // extreme greed = sell
  else if (fng > 70) { sellScore += 1; sellWeight += 5 }

  // 7. Order Book Flow (weight: 5%)
  if (orderBook.bidAskRatio > 1.2) { buyScore += 2; buyWeight += 5 }
  else if (orderBook.bidAskRatio > 1.05) { buyScore += 1; buyWeight += 3 }
  else if (orderBook.bidAskRatio < 0.8) { sellScore += 2; sellWeight += 5 }
  else if (orderBook.bidAskRatio < 0.95) { sellScore += 1; sellWeight += 3 }

  // 8. Whale Activity (weight: 5%)
  if (whaleData.accumulation === 'accumulating') { buyScore += 2; buyWeight += 5 }
  else if (whaleData.accumulation === 'distributing') { sellScore += 2; sellWeight += 5 }

  // 9. On-Chain Funding (weight: 5%)
  const funding = ctx.onChain.fundingRate
  if (funding > 0.05) { sellScore += 1; sellWeight += 5 } // expensive longs
  else if (funding < -0.02) { buyScore += 1; buyWeight += 5 } // shorts pay

  // 10. Macro Risk Environment (weight: 5%)
  if (macro.riskOn) { buyScore += 1; buyWeight += 5 }
  else { sellScore += 1; sellWeight += 5 }

  // Calculate weighted conviction (0-100)
  const totalBuy = buyScore * (buyWeight / 100)
  const totalSell = sellScore * (sellWeight / 100)
  const maxPossible = Math.max(buyWeight, sellWeight) / 100 * 3 // normalize
  const netScore = maxPossible > 0 ? ((totalBuy - totalSell) / maxPossible) * 50 : 0

  return {
    netScore,
    buyScore,
    sellScore,
    buyWeight,
    sellWeight,
    rsi,
    fng,
    price,
    dominantTrend: timeframe.dominantTrend,
    smcStructure: smc.marketStructure,
    ewTrend: elliottWave.trend,
  }
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
  macro: MacroData,
): AnalysisResult['verdict'] {
  const ctx: VerdictContext = { price, technical, onChain, sentiment, orderBook, whaleData, timeframe, elliottWave, smc, macro }
  const score = calcWeightedScore(ctx)
  const netScore = score.netScore
  const fng = score.fng

  let shortTerm: 'buy' | 'sell' | 'hold'
  let longTerm: 'buy' | 'sell' | 'hold'
  let confidence: number
  let summary: string
  let stopLoss: number
  let takeProfitShort: number
  let takeProfitLong: number

  // Strong Buy: +30 or more
  if (netScore >= 30) {
    shortTerm = 'buy'
    longTerm = 'buy'
    confidence = Math.min(92, 65 + netScore * 0.6)
    summary = `Winning signal: Strong bullish convergence. ${score.buyScore}/${score.buyWeight}W buy factors vs ${score.sellScore}/${score.sellWeight}W sell. ${score.smcStructure} structure, ${score.ewTrend} wave, ${score.dominantTrend} alignment. High-probability upward move expected.`
    stopLoss = roundPrice(price * 0.935)
    takeProfitShort = roundPrice(price * 1.14)
    takeProfitLong = roundPrice(price * 1.32)
  }
  // Moderate Buy: +10 to +29
  else if (netScore >= 10) {
    shortTerm = 'hold'
    longTerm = 'buy'
    confidence = Math.min(78, 50 + netScore * 0.7)
    summary = `Bullish bias confirmed. ${score.buyScore} buy signals vs ${score.sellScore} sell. ${score.smcStructure} market structure with ${score.dominantTrend} trend alignment. Good accumulation zone for long-term positions.`
    stopLoss = roundPrice(price * 0.925)
    takeProfitShort = roundPrice(price * 1.10)
    takeProfitLong = roundPrice(price * 1.28)
  }
  // Weak Bullish / Neutral: 0 to +9
  else if (netScore >= 0) {
    shortTerm = 'hold'
    longTerm = 'hold'
    confidence = Math.min(60, 45 + netScore * 1.5)
    summary = `Cautious outlook. Mild bullish edge (${netScore.toFixed(1)}) but not enough conviction. ${score.dominantTrend} dominant trend. Watch for a breakout above resistance or wait for deeper discount before committing.`
    stopLoss = roundPrice(price * 0.91)
    takeProfitShort = roundPrice(price * 1.06)
    takeProfitLong = roundPrice(price * 1.18)
  }
  // Weak Bearish / Neutral: -9 to -1
  else if (netScore > -20) {
    shortTerm = 'hold'
    longTerm = 'hold'
    confidence = Math.min(60, 45 + Math.abs(netScore) * 1.5)
    summary = `Defensive stance. Mild bearish edge (${netScore.toFixed(1)}). ${score.dominantTrend} trend with ${score.smcStructure} structure. Avoid fresh exposure until a clearer bullish setup emerges.`
    stopLoss = roundPrice(price * 1.04)
    takeProfitShort = roundPrice(price * 0.95)
    takeProfitLong = roundPrice(price * 1.08)
  }
  // Moderate Sell: -35 to -20
  else if (netScore >= -50) {
    shortTerm = 'sell'
    longTerm = 'hold'
    confidence = Math.min(78, 50 + Math.abs(netScore) * 0.5)
    summary = `Bearish bias building. ${score.sellScore} sell signals vs ${score.buyScore} buy. ${score.smcStructure} structure, ${score.ewTrend} corrective phase. Reduce long exposure and wait for better entries.`
    stopLoss = roundPrice(price * 1.065)
    takeProfitShort = roundPrice(price * 0.90)
    takeProfitLong = roundPrice(price * 1.05)
  }
  // Strong Sell: below -50
  else {
    shortTerm = 'sell'
    longTerm = 'sell'
    confidence = Math.min(92, 65 + Math.abs(netScore) * 0.4)
    summary = `Winning signal: Strong bearish convergence. ${score.sellScore}/${score.sellWeight}W sell factors vs ${score.buyScore}/${score.buyWeight}W buy. ${score.smcStructure} breakdown, ${score.ewTrend} wave, ${score.dominantTrend} alignment. High-probability downward move expected.`
    stopLoss = roundPrice(price * 1.08)
    takeProfitShort = roundPrice(price * 0.86)
    takeProfitLong = roundPrice(price * 0.78)
  }

  // Contrarian override: extreme fear (< 20) forces at least a hold on shorts
  if (fng < 20 && shortTerm === 'sell') {
    shortTerm = 'hold'
    summary += ' | Contrarian override: extreme fear detected. Avoid shorting into panic.'
  }

  // Contrarian override: extreme greed (> 80) forces caution on longs
  if (fng > 80 && shortTerm === 'buy') {
    shortTerm = 'hold'
    summary += ' | Contrarian override: extreme greed detected. Take profits on longs.'
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
  const verdict = buildVerdict(priceData.price, technical, onChain, sentiment, orderBook, whaleData, timeframe, elliottWave, smc, macro)

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
        target: roundPrice(priceData.price * 0.9),
        trigger: `Losing support at $${technical.supportLevels[0].toLocaleString()}`,
        probability: Math.max(10, Math.min(90, 50 - ((verdict.confidence - 50) / 2))),
      },
      bullish: {
        target: roundPrice(priceData.price * 1.15),
        trigger: `Breaking resistance at $${technical.resistanceLevels[0].toLocaleString()}`,
        probability: Math.max(10, Math.min(90, 50 + ((verdict.confidence - 50) / 2))),
      },
    },
  }
}
