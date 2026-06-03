'use client'

import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { ArrowUpIcon, ArrowDownIcon, MinusIcon, TrendingUpIcon, TrendingDownIcon, AlertTriangleIcon } from 'lucide-react'
import type { AnalysisResult } from '@/lib/types'

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content?: string
  analysis?: AnalysisResult | null
  loading?: boolean
}

function SentimentBadge({ label, value }: { label: string; value: number }) {
  const color = value <= 25 ? 'bg-red-500/10 text-red-500 border-red-500/20' :
    value <= 45 ? 'bg-orange-500/10 text-orange-500 border-orange-500/20' :
      value <= 55 ? 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20' :
        value <= 75 ? 'bg-lime-500/10 text-lime-500 border-lime-500/20' :
          'bg-green-500/10 text-green-500 border-green-500/20'
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-muted-foreground">{label}:</span>
      <Badge variant="outline" className={`${color} font-mono`}>{value}</Badge>
    </div>
  )
}

function VerdictCard({ verdict }: { verdict: AnalysisResult['verdict'] }) {
  const isBuy = verdict.shortTerm === 'buy'
  const isSell = verdict.shortTerm === 'sell'
  const verdictColor = isBuy ? 'border-green-500/50 bg-green-500/5' :
    isSell ? 'border-red-500/50 bg-red-500/5' :
      'border-yellow-500/50 bg-yellow-500/5'
  const verdictIcon = isBuy ? <TrendingUpIcon className="h-5 w-5 text-green-500" /> :
    isSell ? <TrendingDownIcon className="h-5 w-5 text-red-500" /> :
      <MinusIcon className="h-5 w-5 text-yellow-500" />

  return (
    <Card className={`p-4 border-2 ${verdictColor} mb-3`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {verdictIcon}
          <span className="font-bold text-lg uppercase">{verdict.shortTerm === 'hold' ? 'ESPERAR' : verdict.shortTerm === 'buy' ? 'COMPRAR' : 'VENDER'}</span>
          <Badge variant="secondary" className="text-xs">
            Corto plazo
          </Badge>
        </div>
        <span className="text-sm text-muted-foreground">Confianza: {verdict.confidence}%</span>
      </div>
      <div className="flex items-center gap-2 mb-2">
        <span className="font-bold text-lg uppercase">{verdict.longTerm === 'hold' ? 'ESPERAR' : verdict.longTerm === 'buy' ? 'COMPRAR' : 'VENDER'}</span>
        <Badge variant="secondary" className="text-xs">
          Largo plazo
        </Badge>
      </div>
      <p className="text-sm text-muted-foreground">{verdict.summary}</p>
    </Card>
  )
}

function PriceDisplay({ price, change }: { price: number; change: number }) {
  const isPositive = change >= 0
  return (
    <div className="flex items-baseline gap-3 mb-3">
      <span className="text-3xl font-bold font-mono">
        ${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </span>
      <span className={`flex items-center gap-1 text-lg font-mono ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
        {isPositive ? <ArrowUpIcon className="h-4 w-4" /> : <ArrowDownIcon className="h-4 w-4" />}
        {change.toFixed(2)}%
      </span>
    </div>
  )
}

function KeyLevels({ verdict }: { verdict: AnalysisResult['verdict'] }) {
  return (
    <div className="grid grid-cols-3 gap-2 mb-3">
      <div className="bg-red-500/10 rounded-lg p-2 text-center">
        <div className="text-xs text-muted-foreground">Stop Loss</div>
        <div className="text-sm font-mono font-bold text-red-500">${verdict.keyLevels.stopLoss.toLocaleString()}</div>
      </div>
      <div className="bg-green-500/10 rounded-lg p-2 text-center">
        <div className="text-xs text-muted-foreground">Take Profit (Corto)</div>
        <div className="text-sm font-mono font-bold text-green-500">${verdict.keyLevels.takeProfitShort.toLocaleString()}</div>
      </div>
      <div className="bg-blue-500/10 rounded-lg p-2 text-center">
        <div className="text-xs text-muted-foreground">Take Profit (Largo)</div>
        <div className="text-sm font-mono font-bold text-blue-500">${verdict.keyLevels.takeProfitLong.toLocaleString()}</div>
      </div>
    </div>
  )
}

function Scenarios({ scenarios }: { scenarios: AnalysisResult['scenarios'] }) {
  return (
    <div className="space-y-2 mb-3">
      <div className="flex items-start gap-2 bg-red-500/5 rounded-lg p-3">
        <AlertTriangleIcon className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
        <div>
          <div className="text-sm font-medium text-red-500">Escenario Bajista ({scenarios.bearish.probability}%)</div>
          <div className="text-xs text-muted-foreground">Objetivo: ${scenarios.bearish.target.toLocaleString()}</div>
          <div className="text-xs text-muted-foreground">Si: {scenarios.bearish.trigger}</div>
        </div>
      </div>
      <div className="flex items-start gap-2 bg-green-500/5 rounded-lg p-3">
        <TrendingUpIcon className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
        <div>
          <div className="text-sm font-medium text-green-500">Escenario Alcista ({scenarios.bullish.probability}%)</div>
          <div className="text-xs text-muted-foreground">Objetivo: ${scenarios.bullish.target.toLocaleString()}</div>
          <div className="text-xs text-muted-foreground">Si: {scenarios.bullish.trigger}</div>
        </div>
      </div>
    </div>
  )
}

function TechnicalIndicators({ tech }: { tech: AnalysisResult['technical'] }) {
  return (
    <div className="grid grid-cols-2 gap-2 mb-3">
      <div className="bg-card rounded-lg p-2 border">
        <div className="text-xs text-muted-foreground">RSI (14)</div>
        <div className="text-sm font-mono font-bold">{tech.rsi}</div>
      </div>
      <div className="bg-card rounded-lg p-2 border">
        <div className="text-xs text-muted-foreground">Tendencia</div>
        <div className={`text-sm font-bold capitalize ${tech.trend === 'bullish' ? 'text-green-500' : tech.trend === 'bearish' ? 'text-red-500' : ''}`}>{tech.trend}</div>
      </div>
      <div className="bg-card rounded-lg p-2 border">
        <div className="text-xs text-muted-foreground">MA 50</div>
        <div className="text-sm font-mono">${tech.ma50.toLocaleString()}</div>
      </div>
      <div className="bg-card rounded-lg p-2 border">
        <div className="text-xs text-muted-foreground">MA 200</div>
        <div className="text-sm font-mono">${tech.ma200.toLocaleString()}</div>
      </div>
    </div>
  )
}

function OnChainSummary({ onChain }: { onChain: AnalysisResult['onChain'] }) {
  return (
    <div className="grid grid-cols-2 gap-2 mb-3">
      <div className="bg-card rounded-lg p-2 border">
        <div className="text-xs text-muted-foreground">Funding Rate</div>
        <div className={`text-sm font-mono font-bold ${onChain.fundingRate > 0.005 ? 'text-red-500' : 'text-green-500'}`}>
          {(onChain.fundingRate * 100).toFixed(4)}%
        </div>
      </div>
      <div className="bg-card rounded-lg p-2 border">
        <div className="text-xs text-muted-foreground">Flujo Exchanges</div>
        <div className={`text-sm font-bold ${onChain.exchangeNetFlow.includes('outflows') ? 'text-green-500' : 'text-red-500'}`}>
          {onChain.exchangeNetFlow}
        </div>
      </div>
      <div className="bg-card rounded-lg p-2 border">
        <div className="text-xs text-muted-foreground">Staking APY</div>
        <div className="text-sm font-mono font-bold">{onChain.stakingYield.toFixed(1)}%</div>
      </div>
      <div className="bg-card rounded-lg p-2 border">
        <div className="text-xs text-muted-foreground">ETH Staked</div>
        <div className="text-sm font-mono">{(onChain.totalStaked / 1e6).toFixed(1)}M</div>
      </div>
    </div>
  )
}

function NewsHeadlines({ sentiment }: { sentiment: AnalysisResult['sentiment'] }) {
  return (
    <div className="space-y-1 mb-3">
      <div className="text-xs font-medium text-muted-foreground mb-1">Noticias Recientes</div>
      {sentiment.newsHeadlines.length === 0 ? (
        <div className="text-xs text-muted-foreground italic">No se pudieron cargar noticias</div>
      ) : (
        sentiment.newsHeadlines.map((h, i) => (
          <div key={i} className="flex items-start gap-2">
            <span className={`text-xs mt-0.5 ${h.sentiment === 'positive' ? 'text-green-500' : h.sentiment === 'negative' ? 'text-red-500' : 'text-muted-foreground'}`}>
              {h.sentiment === 'positive' ? '▲' : h.sentiment === 'negative' ? '▼' : '■'}
            </span>
            <span className="text-xs text-muted-foreground line-clamp-1">{h.title}</span>
          </div>
        ))
      )}
    </div>
  )
}

function SourcesList({ sources }: { sources: AnalysisResult['sources'] }) {
  const ok = sources.filter((s) => s.status === 'ok').length
  return (
    <div className="text-xs text-muted-foreground">
      {ok}/{sources.length} fuentes consultadas
    </div>
  )
}

export function ChatMessage({ role, content, analysis, loading }: ChatMessageProps) {
  if (loading) {
    return (
      <div className={`flex gap-3 ${role === 'user' ? 'justify-end' : 'justify-start'}`}>
        {role === 'assistant' && (
          <Avatar className="h-8 w-8">
            <AvatarFallback className="bg-primary text-primary-foreground text-xs">AI</AvatarFallback>
          </Avatar>
        )}
        <div className="max-w-[80%] space-y-2">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-64" />
          <Skeleton className="h-4 w-40" />
        </div>
      </div>
    )
  }

  if (role === 'user') {
    return (
      <div className="flex gap-3 justify-end">
        <Card className="bg-primary text-primary-foreground p-3 max-w-[80%]">
          <p className="text-sm">{content}</p>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex gap-3 justify-start">
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback className="bg-primary text-primary-foreground text-xs">AI</AvatarFallback>
      </Avatar>
      <div className="max-w-[85%] space-y-3">
        {analysis ? (
          <>
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">Análisis de Ethereum</h3>
              <span className="text-xs text-muted-foreground">
                {new Date(analysis.timestamp).toLocaleTimeString()}
              </span>
            </div>

            <PriceDisplay price={analysis.priceData.price} change={analysis.priceData.change24h} />
            <VerdictCard verdict={analysis.verdict} />
            <KeyLevels verdict={analysis.verdict} />
            <Scenarios scenarios={analysis.scenarios} />

            <details className="group">
              <summary className="text-sm font-medium text-muted-foreground cursor-pointer hover:text-foreground transition-colors">
                Ver análisis detallado
              </summary>
              <div className="mt-2 space-y-3">
                <div>
                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Técnico</h4>
                  <TechnicalIndicators tech={analysis.technical} />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">On-Chain</h4>
                  <OnChainSummary onChain={analysis.onChain} />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Sentimiento</h4>
                  <div className="space-y-2">
                    <SentimentBadge label="Fear & Greed" value={analysis.sentiment.fearGreedIndex} />
                    <NewsHeadlines sentiment={analysis.sentiment} />
                  </div>
                </div>
              </div>
            </details>

            <SourcesList sources={analysis.sources} />
          </>
        ) : (
          <p className="text-sm text-muted-foreground">{content}</p>
        )}
      </div>
    </div>
  )
}
