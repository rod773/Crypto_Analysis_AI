export interface PriceData {
  price: number
  change24h: number
  high24h: number
  low24h: number
  volume24h: number
  marketCap: number
}

export interface TechnicalIndicators {
  rsi: number
  macd: string
  ma50: number
  ma200: number
  supportLevels: number[]
  resistanceLevels: number[]
  trend: 'bullish' | 'bearish' | 'neutral'
}

export interface OnChainData {
  fundingRate: number
  exchangeNetFlow: string
  stakingYield: number
  totalStaked: number
  exchangeReserve: number
  liquidationLevels: { long: number; short: number }
}

export interface SentimentData {
  fearGreedIndex: number
  fearGreedLabel: string
  newsHeadlines: { title: string; source: string; sentiment: 'positive' | 'negative' | 'neutral' }[]
  socialVolume: number
  socialSentiment: 'bullish' | 'bearish' | 'neutral'
}

export interface FundamentalData {
  defiTvl: number
  stablecoinSupply: number
  networkRevenue: number
  activeAddresses: number
  transactionCount: number
}

export interface SourceInfo {
  name: string
  url: string
  status: 'ok' | 'error'
  error?: string
}

export interface OrderBookData {
  bidDepth: number
  askDepth: number
  bidAskRatio: number
  optionFlow: string
  optionFlowSentiment: 'bullish' | 'bearish' | 'neutral'
  maxPain: number
}

export interface WhaleData {
  largeTxns24h: number
  totalVolumeUsd: number
  accumulation: 'accumulating' | 'distributing' | 'neutral'
  topWhaleNetFlow: string
  notableTxns: { hash: string; value: number; from: string; to: string; timestamp: string }[]
}

export interface MacroData {
  upcomingEvents: { name: string; date: string; impact: 'high' | 'medium' | 'low'; expected: string }[]
  marketContext: string
  riskOn: boolean
}

export interface TimeframeData {
  daily: { trend: 'bullish' | 'bearish' | 'neutral'; rsi: number; maStatus: string }
  fourHour: { trend: 'bullish' | 'bearish' | 'neutral'; rsi: number; maStatus: string }
  oneHour: { trend: 'bullish' | 'bearish' | 'neutral'; rsi: number; maStatus: string }
  alignment: 'aligned' | 'partial' | 'conflicting'
  dominantTrend: 'bullish' | 'bearish' | 'neutral'
}

export type Asset = 'eth' | 'btc' | 'gold'

export interface AssetConfig {
  id: Asset
  name: string
  symbol: string
  coinGeckoId: string
  binanceSymbol: string
  cmcSlug: string
  icon: string
}

export const ASSETS: AssetConfig[] = [
  { id: 'eth', name: 'Ethereum', symbol: 'ETH', coinGeckoId: 'ethereum', binanceSymbol: 'ETHUSDT', cmcSlug: 'ethereum', icon: '⟠' },
  { id: 'btc', name: 'Bitcoin', symbol: 'BTC', coinGeckoId: 'bitcoin', binanceSymbol: 'BTCUSDT', cmcSlug: 'bitcoin', icon: '₿' },
  { id: 'gold', name: 'Gold', symbol: 'XAU', coinGeckoId: '', binanceSymbol: '', cmcSlug: '', icon: '👑' },
]

export function getAssetConfig(id: Asset): AssetConfig {
  return ASSETS.find((a) => a.id === id) ?? ASSETS[0]
}

export interface SmcOrderBlock {
  type: 'bullish' | 'bearish'
  price: number
  strength: 'strong' | 'moderate' | 'weak'
  touched: boolean
}

export interface SmcFvg {
  type: 'bullish' | 'bearish'
  upper: number
  lower: number
  filled: boolean
}

export interface SmcData {
  marketStructure: 'uptrend' | 'downtrend' | 'ranging'
  structureShift: boolean
  lastBos: 'bullish' | 'bearish' | null
  orderBlocks: SmcOrderBlock[]
  fvgs: SmcFvg[]
  liquidityAbove: number
  liquidityBelow: number
  description: string
}

export interface ElliottWaveData {
  waveCount: string       // e.g. "Wave 3 of (5)"
  trend: 'impulse' | 'corrective' | 'neutral'
  currentWave: number     // 1-5 for impulse, or -1/-2/-3 for A-B-C
  completeness: number    // 0-100 how complete the current pattern is
  nextTarget: number
  invalidationLevel: number
  subWaves: { label: string; high: number; low: number }[]
  description: string
}

export interface AnalysisResult {
  asset: Asset
  timestamp: string
  priceData: PriceData
  technical: TechnicalIndicators
  onChain: OnChainData
  sentiment: SentimentData
  fundamental: FundamentalData
  orderBook: OrderBookData
  whaleData: WhaleData
  macro: MacroData
  timeframe: TimeframeData
  elliottWave: ElliottWaveData
  smc: SmcData
  verdict: {
    shortTerm: 'buy' | 'sell' | 'hold'
    longTerm: 'buy' | 'sell' | 'hold'
    confidence: number
    summary: string
    keyLevels: {
      stopLoss: number
      takeProfitShort: number
      takeProfitLong: number
    }
  }
  sources: SourceInfo[]
  scenarios: {
    bearish: { target: number; trigger: string; probability: number }
    bullish: { target: number; trigger: string; probability: number }
  }
}
