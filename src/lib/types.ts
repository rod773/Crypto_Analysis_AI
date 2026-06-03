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

export interface AnalysisResult {
  timestamp: string
  priceData: PriceData
  technical: TechnicalIndicators
  onChain: OnChainData
  sentiment: SentimentData
  fundamental: FundamentalData
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
