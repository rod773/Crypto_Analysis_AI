'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { gsap } from 'gsap'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  ArrowUpIcon, ArrowDownIcon, MinusIcon, TrendingUpIcon, TrendingDownIcon,
  AlertTriangleIcon, ChevronDownIcon, ActivityIcon, WalletIcon,
  NewspaperIcon, BarChart3Icon, BookOpenIcon, FishSymbolIcon, GlobeIcon, LayersIcon, ZapIcon, BrainCircuitIcon,
} from 'lucide-react'
import type { AnalysisResult, Asset } from '@/lib/types'

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content?: string
  analysis?: AnalysisResult | null
  loading?: boolean
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.06 },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.25, 0.1, 0.25, 1] as const } },
}

function SentimentBadge({ label, value }: { label: string; value: number }) {
  const color = value <= 25
    ? 'bg-red-500/10 text-red-500 border-red-500/20'
    : value <= 45
    ? 'bg-orange-500/10 text-orange-500 border-orange-500/20'
    : value <= 55
    ? 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
    : value <= 75
    ? 'bg-lime-500/10 text-lime-500 border-lime-500/20'
    : 'bg-green-500/10 text-green-500 border-green-500/20'
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-muted-foreground">{label}:</span>
      <Badge variant="outline" className={`${color} font-mono text-sm`}>{value}</Badge>
    </div>
  )
}

function VerdictCard({ verdict }: { verdict: AnalysisResult['verdict'] }) {
  const isBuy = verdict.shortTerm === 'buy'
  const isSell = verdict.shortTerm === 'sell'
  const verdictColor = isBuy
    ? 'border-green-500/30 bg-gradient-to-br from-green-500/8 to-green-500/3'
    : isSell
    ? 'border-red-500/30 bg-gradient-to-br from-red-500/8 to-red-500/3'
    : 'border-yellow-500/30 bg-gradient-to-br from-yellow-500/8 to-yellow-500/3'
  const verdictIcon = isBuy
    ? <TrendingUpIcon className="h-5 w-5 text-green-500" />
    : isSell
    ? <TrendingDownIcon className="h-5 w-5 text-red-500" />
    : <MinusIcon className="h-5 w-5 text-yellow-500" />
  const shortLabel = verdict.shortTerm === 'hold' ? 'ESPERAR' : verdict.shortTerm === 'buy' ? 'COMPRAR' : 'VENDER'
  const longLabel = verdict.longTerm === 'hold' ? 'ESPERAR' : verdict.longTerm === 'buy' ? 'COMPRAR' : 'VENDER'

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
    >
      <Card className={`overflow-hidden border-2 ${verdictColor} backdrop-blur-sm`}>
        <div className="p-3.5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {verdictIcon}
              <span className="font-bold text-base tracking-tight">{shortLabel}</span>
              <Badge variant="secondary" className="text-xs h-5 px-2 font-normal bg-background/50">Corto</Badge>
            </div>
            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <span className="text-xs">Confianza</span>
              <span className="font-semibold font-mono text-foreground">{verdict.confidence}%</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-base tracking-tight">{longLabel}</span>
            <Badge variant="secondary" className="text-xs h-5 px-1.5 font-normal bg-background/50">Largo</Badge>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">{verdict.summary}</p>
        </div>
      </Card>
    </motion.div>
  )
}

function PriceDisplay({ price, change }: { price: number; change: number }) {
  const priceRef = useRef<HTMLSpanElement>(null)
  const isPositive = change >= 0

  useEffect(() => {
    if (!priceRef.current) return
    const ctx = gsap.context(() => {
      gsap.fromTo(
        priceRef.current,
        { textContent: '0' },
        {
          textContent: price,
          duration: 1.2,
          ease: 'power2.out',
          snap: { textContent: 1 },
        }
      )
    }, priceRef.current)
    return () => ctx.revert()
  }, [price])

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="flex items-baseline gap-3"
    >
      <span className="text-3xl font-bold font-mono tracking-tight">
        $<span ref={priceRef}>{price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
      </span>
      <motion.span
        initial={{ opacity: 0, x: -5 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3, delay: 0.2 }}
        className={`flex items-center gap-1 text-base font-mono font-semibold ${isPositive ? 'text-green-500' : 'text-red-500'}`}
      >
        {isPositive ? <ArrowUpIcon className="h-3.5 w-3.5" /> : <ArrowDownIcon className="h-3.5 w-3.5" />}
        {change.toFixed(2)}%
      </motion.span>
    </motion.div>
  )
}

function KeyLevels({ verdict }: { verdict: AnalysisResult['verdict'] }) {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-3 gap-2"
    >
      {[
        { label: 'Stop Loss', value: verdict.keyLevels.stopLoss, color: 'red', border: 'border-red-500/15', bg: 'bg-red-500/5' },
        { label: 'TP Corto', value: verdict.keyLevels.takeProfitShort, color: 'green', border: 'border-green-500/15', bg: 'bg-green-500/5' },
        { label: 'TP Largo', value: verdict.keyLevels.takeProfitLong, color: 'blue', border: 'border-cyber/15', bg: 'bg-cyber/5' },
      ].map((item) => (
        <motion.div
          key={item.label}
          variants={itemVariants}
          whileHover={{ scale: 1.04 }}
          className={`${item.bg} ${item.border} rounded-xl border p-2.5 text-center transition-colors`}
        >
            <div className="text-sm text-muted-foreground font-medium tracking-wide">{item.label}</div>
            <div className={`text-base font-mono font-bold text-${item.color}-500`}>
            ${item.value.toLocaleString()}
          </div>
        </motion.div>
      ))}
    </motion.div>
  )
}

function Scenarios({ scenarios }: { scenarios: AnalysisResult['scenarios'] }) {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-2"
    >
      <motion.div variants={itemVariants} className="flex items-start gap-2.5 rounded-xl border border-red-500/15 bg-gradient-to-br from-red-500/5 to-transparent p-3">
        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-red-500/10">
          <AlertTriangleIcon className="h-3.5 w-3.5 text-red-500" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-red-500">Bajista</span>
            <Badge variant="outline" className="text-xs h-5 px-2 font-mono text-red-500/80 border-red-500/20 bg-red-500/5">{scenarios.bearish.probability}%</Badge>
          </div>
          <div className="mt-0.5 text-sm text-muted-foreground">
            Objetivo: <span className="font-mono font-semibold text-red-400">${scenarios.bearish.target.toLocaleString()}</span>
          </div>
          <div className="text-sm text-muted-foreground/70 mt-0.5 leading-tight">{scenarios.bearish.trigger}</div>
        </div>
      </motion.div>
      <motion.div variants={itemVariants} className="flex items-start gap-2.5 rounded-xl border border-green-500/15 bg-gradient-to-br from-green-500/5 to-transparent p-3">
        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-green-500/10">
          <TrendingUpIcon className="h-3.5 w-3.5 text-green-500" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-green-500">Alcista</span>
            <Badge variant="outline" className="text-xs h-5 px-2 font-mono text-green-500/80 border-green-500/20 bg-green-500/5">{scenarios.bullish.probability}%</Badge>
          </div>
          <div className="mt-0.5 text-sm text-muted-foreground">
            Objetivo: <span className="font-mono font-semibold text-green-400">${scenarios.bullish.target.toLocaleString()}</span>
          </div>
          <div className="text-sm text-muted-foreground/70 mt-0.5 leading-tight">{scenarios.bullish.trigger}</div>
        </div>
      </motion.div>
    </motion.div>
  )
}

function TechnicalIndicators({ tech }: { tech: AnalysisResult['technical'] }) {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-2 gap-2"
    >
      {[
        { label: 'RSI (14)', value: String(tech.rsi), color: '' },
        { label: 'Tendencia', value: tech.trend === 'bullish' ? 'Alcista' : tech.trend === 'bearish' ? 'Bajista' : 'Neutral', color: tech.trend === 'bullish' ? 'text-green-500' : tech.trend === 'bearish' ? 'text-red-500' : '' },
        { label: 'MA 50', value: `$${tech.ma50.toLocaleString()}`, color: '' },
        { label: 'MA 200', value: `$${tech.ma200.toLocaleString()}`, color: '' },
      ].map((item) => (
        <motion.div key={item.label} variants={itemVariants} className="rounded-xl border border-border/50 bg-card/30 p-2.5 backdrop-blur-sm">
          <div className="text-sm text-muted-foreground font-medium tracking-wide">{item.label}</div>
          <div className={`text-base font-mono font-bold mt-0.5 ${item.color || ''}`}>{item.value}</div>
        </motion.div>
      ))}
    </motion.div>
  )
}

function OnChainSummary({ onChain }: { onChain: AnalysisResult['onChain'] }) {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-2 gap-2"
    >
      {[
        { label: 'Funding Rate', value: `${(onChain.fundingRate * 100).toFixed(4)}%`, color: onChain.fundingRate > 0.005 ? 'text-red-500' : 'text-green-500' },
        { label: 'Flujo Exchanges', value: onChain.exchangeNetFlow, color: onChain.exchangeNetFlow.includes('outflows') ? 'text-green-500' : 'text-red-500' },
        { label: 'Staking APY', value: `${onChain.stakingYield.toFixed(1)}%`, color: '' },
        { label: 'ETH Staked', value: `${(onChain.totalStaked / 1e6).toFixed(1)}M`, color: '' },
      ].map((item) => (
        <motion.div key={item.label} variants={itemVariants} className="rounded-xl border border-border/50 bg-card/30 p-2.5 backdrop-blur-sm">
          <div className="text-xs text-muted-foreground font-medium tracking-wide uppercase">{item.label}</div>
          <div className={`text-sm font-mono font-bold mt-0.5 ${item.color || ''}`}>{item.value}</div>
        </motion.div>
      ))}
    </motion.div>
  )
}

function NewsHeadlines({ sentiment }: { sentiment: AnalysisResult['sentiment'] }) {
  return (
    <div className="space-y-1.5">
      <div className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Noticias Recientes</div>
      {sentiment.newsHeadlines.length === 0 ? (
        <div className="text-xs text-muted-foreground/60 italic">No se pudieron cargar noticias</div>
      ) : (
        sentiment.newsHeadlines.map((h, i) => (
          <div key={i} className="flex items-start gap-2 rounded-lg border border-border/30 bg-card/20 p-2">
            <span className={`mt-0.5 text-xs shrink-0 ${h.sentiment === 'positive' ? 'text-green-500' : h.sentiment === 'negative' ? 'text-red-500' : 'text-muted-foreground'}`}>
              {h.sentiment === 'positive' ? '▲' : h.sentiment === 'negative' ? '▼' : '■'}
            </span>
            <span className="text-sm text-muted-foreground leading-tight line-clamp-2">{h.title}</span>
          </div>
        ))
      )}
    </div>
  )
}

function SourcesList({ sources }: { sources: AnalysisResult['sources'] }) {
  const ok = sources.filter((s) => s.status === 'ok').length
  return (
    <div className="text-sm text-muted-foreground/60 font-medium">
      {ok}/{sources.length} fuentes consultadas
    </div>
  )
}

function OrderBookSummary({ orderBook }: { orderBook: AnalysisResult['orderBook'] }) {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-2 gap-2"
    >
      {[
        { label: 'Bid Depth', value: `${(orderBook.bidDepth / 1000).toFixed(0)}K ETH`, color: 'text-green-500' },
        { label: 'Ask Depth', value: `${(orderBook.askDepth / 1000).toFixed(0)}K ETH`, color: 'text-red-500' },
        { label: 'Bid/Ask Ratio', value: orderBook.bidAskRatio.toFixed(2), color: orderBook.bidAskRatio > 1 ? 'text-green-500' : 'text-red-500' },
        { label: 'Opción Flow', value: orderBook.optionFlowSentiment === 'bullish' ? 'Calls ▲' : orderBook.optionFlowSentiment === 'bearish' ? 'Puts ▼' : '—', color: orderBook.optionFlowSentiment === 'bullish' ? 'text-green-500' : orderBook.optionFlowSentiment === 'bearish' ? 'text-red-500' : '' },
      ].map((item) => (
        <motion.div key={item.label} variants={itemVariants} className="rounded-xl border border-border/50 bg-card/30 p-2.5 backdrop-blur-sm">
          <div className="text-sm text-muted-foreground font-medium tracking-wide">{item.label}</div>
          <div className={`text-base font-mono font-bold mt-0.5 ${item.color || ''}`}>{item.value}</div>
        </motion.div>
      ))}
    </motion.div>
  )
}

function WhaleSummary({ whaleData }: { whaleData: AnalysisResult['whaleData'] }) {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-2 gap-2"
    >
      {[
        { label: 'Txns Grandes (24h)', value: String(whaleData.largeTxns24h), color: '' },
        { label: 'Volumen', value: `$${(whaleData.totalVolumeUsd / 1e6).toFixed(1)}M`, color: '' },
        { label: 'Acumulación', value: whaleData.accumulation === 'accumulating' ? 'Comprando' : whaleData.accumulation === 'distributing' ? 'Vendiendo' : 'Neutral', color: whaleData.accumulation === 'accumulating' ? 'text-green-500' : whaleData.accumulation === 'distributing' ? 'text-red-500' : '' },
        { label: 'Flujo Ballenas', value: whaleData.topWhaleNetFlow, color: whaleData.topWhaleNetFlow.includes('inflow') ? 'text-green-500' : whaleData.topWhaleNetFlow.includes('outflow') ? 'text-red-500' : '' },
      ].map((item) => (
        <motion.div key={item.label} variants={itemVariants} className="rounded-xl border border-border/50 bg-card/30 p-2.5 backdrop-blur-sm">
          <div className="text-sm text-muted-foreground font-medium tracking-wide">{item.label}</div>
          <div className={`text-base font-mono font-bold mt-0.5 ${item.color || ''}`}>{item.value}</div>
        </motion.div>
      ))}
    </motion.div>
  )
}

function MacroSummary({ macro }: { macro: AnalysisResult['macro'] }) {
  return (
    <div className="space-y-2">
      <div className={`text-sm font-medium ${macro.riskOn ? 'text-green-500' : 'text-yellow-500'}`}>
        {macro.riskOn ? 'Entorno favorable al riesgo' : 'Precaución — eventos macro esta semana'}
      </div>
      {macro.upcomingEvents.length > 0 ? (
        <div className="space-y-1.5">
          {macro.upcomingEvents.map((e, i) => (
            <div key={i} className="flex items-center justify-between rounded-lg border border-border/30 bg-card/20 px-3 py-2">
              <div className="min-w-0 flex-1">
                <div className="text-sm text-muted-foreground truncate">{e.name}</div>
                <div className="text-xs text-muted-foreground/60">{e.date}</div>
              </div>
              <Badge variant="outline" className={`text-xs h-5 shrink-0 ml-2 ${e.impact === 'high' ? 'border-red-500/30 text-red-500' : 'border-yellow-500/30 text-yellow-500'}`}>
                {e.impact === 'high' ? 'Alto' : 'Medio'}
              </Badge>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-sm text-muted-foreground/60 italic">{macro.marketContext}</div>
      )}
    </div>
  )
}

function TimeframeSummary({ timeframe }: { timeframe: AnalysisResult['timeframe'] }) {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-2"
    >
      <div className="flex items-center gap-2">
        <div className={`text-sm font-semibold ${timeframe.alignment === 'aligned' ? 'text-green-500' : timeframe.alignment === 'partial' ? 'text-yellow-500' : 'text-red-500'}`}>
          {timeframe.alignment === 'aligned' ? '✅ Alineado' : timeframe.alignment === 'partial' ? '⚠️ Parcial' : '❌ Conflictivo'}
        </div>
        <Badge variant="secondary" className="text-xs h-5 px-2 font-normal capitalize">
          Dom: {timeframe.dominantTrend === 'bullish' ? 'Alcista' : timeframe.dominantTrend === 'bearish' ? 'Bajista' : 'Neutral'}
        </Badge>
      </div>
      <div className="grid grid-cols-3 gap-2">
        {[
          { label: 'Diario', trend: timeframe.daily.trend, rsi: timeframe.daily.rsi, ma: timeframe.daily.maStatus },
          { label: '4H', trend: timeframe.fourHour.trend, rsi: timeframe.fourHour.rsi, ma: timeframe.fourHour.maStatus },
          { label: '1H', trend: timeframe.oneHour.trend, rsi: timeframe.oneHour.rsi, ma: timeframe.oneHour.maStatus },
        ].map((tf) => (
          <motion.div key={tf.label} variants={itemVariants} className="rounded-xl border border-border/50 bg-card/30 p-2 backdrop-blur-sm text-center">
            <div className="text-sm text-muted-foreground font-medium">{tf.label}</div>
            <div className={`text-base font-bold ${tf.trend === 'bullish' ? 'text-green-500' : tf.trend === 'bearish' ? 'text-red-500' : ''}`}>
              {tf.trend === 'bullish' ? '▲' : tf.trend === 'bearish' ? '▼' : '—'}
            </div>
            <div className="text-sm font-mono text-muted-foreground/70">RSI {tf.rsi}</div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

function SmcSummary({ smc }: { smc?: AnalysisResult['smc'] }) {
  if (!smc) return <div className="text-sm text-muted-foreground/60 italic">Datos SMC no disponibles</div>
  const structIcon = smc.marketStructure === 'uptrend' ? '📈' : smc.marketStructure === 'downtrend' ? '📉' : '➡️'
  const structColor = smc.marketStructure === 'uptrend' ? 'text-green-500' : smc.marketStructure === 'downtrend' ? 'text-red-500' : 'text-yellow-500'

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-2"
    >
      <div className="flex items-center gap-2">
        <span className={`text-sm font-semibold ${structColor}`}>
          {structIcon} {smc.marketStructure === 'uptrend' ? 'Uptrend' : smc.marketStructure === 'downtrend' ? 'Downtrend' : 'Rango'}
        </span>
        {smc.structureShift && (
          <Badge variant="outline" className="text-xs border-yellow-500/30 text-yellow-500 bg-yellow-500/5">
            MSS detectado
          </Badge>
        )}
        {smc.lastBos && (
          <Badge variant="outline" className={`text-xs ${smc.lastBos === 'bullish' ? 'border-green-500/30 text-green-500 bg-green-500/5' : 'border-red-500/30 text-red-500 bg-red-500/5'}`}>
            BOS {smc.lastBos === 'bullish' ? 'Alcista' : 'Bajista'}
          </Badge>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <motion.div variants={itemVariants} className="rounded-xl border border-border/50 bg-card/30 p-2.5 backdrop-blur-sm">
          <div className="text-sm text-muted-foreground font-medium">Liquidez Arriba</div>
          <div className="text-base font-mono font-bold text-green-500">${smc.liquidityAbove.toLocaleString()}</div>
        </motion.div>
        <motion.div variants={itemVariants} className="rounded-xl border border-border/50 bg-card/30 p-2.5 backdrop-blur-sm">
          <div className="text-sm text-muted-foreground font-medium">Liquidez Abajo</div>
          <div className="text-base font-mono font-bold text-red-500">${smc.liquidityBelow.toLocaleString()}</div>
        </motion.div>
      </div>

      {smc.orderBlocks.length > 0 && (
        <div>
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">Order Blocks</div>
          <div className="space-y-1">
            {smc.orderBlocks.map((ob, i) => (
              <motion.div key={i} variants={itemVariants} className="flex items-center justify-between rounded-lg border border-border/30 bg-card/20 px-2.5 py-1.5">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-mono ${ob.type === 'bullish' ? 'text-green-500' : 'text-red-500'}`}>
                    {ob.type === 'bullish' ? '▲' : '▼'} OB
                  </span>
                  <span className="text-sm font-mono text-foreground/80">${ob.price.toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-medium ${ob.touched ? 'text-yellow-500' : 'text-muted-foreground/60'}`}>
                    {ob.touched ? 'Tocado' : 'Intacto'}
                  </span>
                  <Badge variant="outline" className={`text-[10px] h-4 px-1.5 ${ob.strength === 'strong' ? 'border-green-500/30 text-green-500' : ob.strength === 'moderate' ? 'border-yellow-500/30 text-yellow-500' : 'border-border/30 text-muted-foreground'}`}>
                    {ob.strength === 'strong' ? 'Fuerte' : ob.strength === 'moderate' ? 'Medio' : 'Débil'}
                  </Badge>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {smc.fvgs.length > 0 && (
        <div>
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">Fair Value Gaps</div>
          <div className="space-y-1">
            {smc.fvgs.map((fvg, i) => (
              <motion.div key={i} variants={itemVariants} className="flex items-center justify-between rounded-lg border border-border/30 bg-card/20 px-2.5 py-1.5">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-mono ${fvg.type === 'bullish' ? 'text-green-500' : 'text-red-500'}`}>
                    {fvg.type === 'bullish' ? '▲' : '▼'} FVG
                  </span>
                  <span className="text-xs font-mono text-foreground/80">
                    ${fvg.lower.toLocaleString()} – ${fvg.upper.toLocaleString()}
                  </span>
                </div>
                <span className={`text-[10px] font-medium ${fvg.filled ? 'text-muted-foreground/60' : 'text-yellow-500'}`}>
                  {fvg.filled ? 'Relleno' : 'Abierto'}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      <p className="text-sm text-muted-foreground/80 leading-relaxed">{smc.description}</p>
    </motion.div>
  )
}

function ElliottWaveSummary({ ew }: { ew?: AnalysisResult['elliottWave'] }) {
  if (!ew) return <div className="text-sm text-muted-foreground/60 italic">Datos de ondas Elliott no disponibles</div>
  const isImpulse = ew.trend === 'impulse'
  const isBullishWave = isImpulse && ew.currentWave <= 3
  const isLateWave = isImpulse && ew.currentWave >= 4
  const color = isBullishWave ? 'text-green-500' : isLateWave ? 'text-yellow-500' : ew.trend === 'corrective' ? 'text-red-500' : 'text-muted-foreground'

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-2"
    >
      <div className="flex items-center gap-2">
        <Badge variant="outline" className={`font-mono text-xs ${color} border-current/20 bg-current/5`}>
          {ew.waveCount}
        </Badge>
        <div className="flex-1 h-2 rounded-full bg-border/30 overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${ew.completeness}%` }}
            transition={{ duration: 1, ease: 'easeOut' }}
            className={`h-full rounded-full ${isBullishWave ? 'bg-green-500' : isLateWave ? 'bg-yellow-500' : 'bg-red-500'}`}
          />
        </div>
        <span className="text-xs font-mono text-muted-foreground">{ew.completeness}%</span>
      </div>

      {ew.subWaves.length > 0 && (
        <div className="grid grid-cols-5 gap-1">
          {ew.subWaves.map((w, i) => (
            <motion.div
              key={i}
              variants={itemVariants}
              className="rounded-lg border border-border/30 bg-card/20 p-1.5 text-center"
            >
              <div className="text-[10px] font-mono text-muted-foreground truncate">{w.label}</div>
              <div className="text-[10px] font-mono font-bold text-foreground/80">
                ${w.high.toLocaleString()}
              </div>
            </motion.div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-3 text-sm">
        <div>
          <span className="text-muted-foreground/60 text-xs">Objetivo: </span>
          <span className={`font-mono font-semibold ${color}`}>${ew.nextTarget.toLocaleString()}</span>
        </div>
        <div>
          <span className="text-muted-foreground/60 text-xs">Invalida: </span>
          <span className="font-mono font-semibold text-red-400">${ew.invalidationLevel.toLocaleString()}</span>
        </div>
      </div>

      <p className="text-sm text-muted-foreground/80 leading-relaxed">{ew.description}</p>
    </motion.div>
  )
}

function SectionHeader({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className="text-muted-foreground/60">{icon}</div>
      <span className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">{label}</span>
    </div>
  )
}

export function ChatMessage({ role, content, analysis, loading }: ChatMessageProps) {
  const [detailsOpen, setDetailsOpen] = useState(false)

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`flex gap-3 ${role === 'user' ? 'justify-end' : 'justify-start'}`}
      >
        {role === 'assistant' && (
          <Avatar className="mt-0.5 h-7 w-7 shrink-0">
            <AvatarFallback className="bg-gradient-to-br from-cyber/30 to-cyber/10 text-xs font-bold text-cyber ring-1 ring-cyber/20">AI</AvatarFallback>
          </Avatar>
        )}
        <div className="space-y-2.5 rounded-2xl bg-card/30 p-4 backdrop-blur-sm border border-border/30 min-w-[200px]">
          <Skeleton className="h-3 w-3/4 rounded-full" />
          <Skeleton className="h-3 w-full rounded-full" />
          <Skeleton className="h-3 w-1/2 rounded-full" />
        </div>
      </motion.div>
    )
  }

  if (role === 'user') {
    return (
      <motion.div
        initial={{ opacity: 0, x: 10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        className="flex gap-3 justify-end"
      >
        <div className="rounded-2xl bg-gradient-to-br from-primary/90 to-primary/70 px-4 py-2.5 max-w-[80%] shadow-lg shadow-primary/10">
          <p className="text-sm text-primary-foreground leading-relaxed">{content}</p>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="flex gap-3 justify-start group"
    >
      <Avatar className="mt-1 h-7 w-7 shrink-0">
        <AvatarFallback className="bg-gradient-to-br from-cyber/30 to-cyber/10 text-xs font-bold text-cyber ring-1 ring-cyber/20">AI</AvatarFallback>
      </Avatar>
      <div className="min-w-0 max-w-[85%] space-y-3">
        {analysis ? (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
              className="flex items-center justify-between"
            >
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">{`Análisis de ${analysis.asset === 'btc' ? 'Bitcoin' : analysis.asset === 'gold' ? 'Gold' : 'Ethereum'}`}</h3>
              <span className="text-xs text-muted-foreground/50 font-mono">
                {new Date(analysis.timestamp).toLocaleTimeString()}
              </span>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, ease: 'easeOut' }}
            >
              <Card className="overflow-hidden border-border/40 bg-card/40 backdrop-blur-sm shadow-lg shadow-black/5">
                <div className="p-4 space-y-4">
                  <PriceDisplay price={analysis.priceData.price} change={analysis.priceData.change24h} />
                  <VerdictCard verdict={analysis.verdict} />
                  <KeyLevels verdict={analysis.verdict} />
                  <Scenarios scenarios={analysis.scenarios} />

                  <div className="border-t border-border/30 pt-3">
                    <motion.button
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setDetailsOpen(!detailsOpen)}
                      className="flex w-full items-center justify-between rounded-lg border border-border/40 bg-card/40 px-3 py-2 text-sm font-medium text-foreground backdrop-blur-sm transition-all hover:bg-card/60 hover:border-cyber/30"
                    >
                      <span>Análisis detallado</span>
                      <motion.div
                        animate={{ rotate: detailsOpen ? 180 : 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <ChevronDownIcon className="h-3.5 w-3.5" />
                      </motion.div>
                    </motion.button>
                    <AnimatePresence initial={false}>
                      {detailsOpen && (
                        <motion.div
                          key="details"
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
                          className="overflow-hidden"
                        >
                          <div className="mt-3 space-y-4">
                            <div className="space-y-2">
                              <SectionHeader icon={<BarChart3Icon className="h-3 w-3" />} label="Técnico" />
                              <TechnicalIndicators tech={analysis.technical} />
                            </div>
                            <div className="space-y-2">
                              <SectionHeader icon={<ActivityIcon className="h-3 w-3" />} label="On-Chain" />
                              <OnChainSummary onChain={analysis.onChain} />
                            </div>
                            <div className="space-y-2">
                              <SectionHeader icon={<BookOpenIcon className="h-3 w-3" />} label="Order Book" />
                              <OrderBookSummary orderBook={analysis.orderBook} />
                            </div>
                            <div className="space-y-2">
                              <SectionHeader icon={<FishSymbolIcon className="h-3 w-3" />} label="Ballenas" />
                              <WhaleSummary whaleData={analysis.whaleData} />
                            </div>
                            <div className="space-y-2">
                              <SectionHeader icon={<LayersIcon className="h-3 w-3" />} label="Multi-Timeframe" />
                              <TimeframeSummary timeframe={analysis.timeframe} />
                            </div>
                            {analysis.elliottWave && (
                              <div className="space-y-2">
                                <SectionHeader icon={<ZapIcon className="h-3 w-3" />} label="Ondas Elliott" />
                                <ElliottWaveSummary ew={analysis.elliottWave} />
                              </div>
                            )}
                            {analysis.smc && (
                              <div className="space-y-2">
                                <SectionHeader icon={<BrainCircuitIcon className="h-3 w-3" />} label="Smart Money" />
                                <SmcSummary smc={analysis.smc} />
                              </div>
                            )}
                            <div className="space-y-2">
                              <SectionHeader icon={<GlobeIcon className="h-3 w-3" />} label="Macro" />
                              <MacroSummary macro={analysis.macro} />
                            </div>
                            <div className="space-y-2">
                              <SectionHeader icon={<NewspaperIcon className="h-3 w-3" />} label="Sentimiento" />
                              <div className="space-y-2.5 pl-1">
                                <SentimentBadge label="Fear & Greed" value={analysis.sentiment.fearGreedIndex} />
                                <NewsHeadlines sentiment={analysis.sentiment} />
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3, delay: 0.15 }}
            >
              <SourcesList sources={analysis.sources} />
            </motion.div>
          </>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
            className="rounded-2xl bg-card/30 px-4 py-2.5 border border-border/30 backdrop-blur-sm"
          >
            <p className="text-sm text-muted-foreground leading-relaxed">{content}</p>
          </motion.div>
        )}
      </div>
    </motion.div>
  )
}
