'use client'

import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import Link from 'next/link'
import { ArrowLeft, Info, BarChart3, Waves, Cpu, Globe, Database, MessageSquareText, Brain, Coins, Zap, Gauge, ChartCandlestick, ArrowUp, ArrowDown } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Logo } from '@/components/ui/logo'

gsap.registerPlugin(ScrollTrigger)

function Section({ id, title, icon: Icon, children, className = '' }: {
  id: string
  title: string
  icon: React.ElementType
  children: React.ReactNode
  className?: string
}) {
  return (
    <section id={id} data-reveal className={`scroll-mt-20 ${className}`}>
      <div className="flex items-center gap-3 mb-6">
        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-cyber/10 ring-1 ring-cyber/20">
          <Icon className="h-5 w-5 text-cyber" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight">{title}</h2>
      </div>
      {children}
    </section>
  )
}

function Table({ headers, rows }: { headers: string[], rows: string[][] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border/40">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-cyber/10 border-b border-border/40">
            {headers.map((h, i) => (
              <th key={i} className="px-4 py-3 text-left font-semibold text-cyber whitespace-nowrap">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className="border-b border-border/20 last:border-0 hover:bg-muted/30 transition-colors">
              {row.map((cell, ci) => (
                <td key={ci} className="px-4 py-2.5 text-muted-foreground">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function InfoBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-cyber/20 bg-cyber/5 px-5 py-4 text-sm text-muted-foreground">
      <div className="flex gap-3">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-cyber" />
        <div>{children}</div>
      </div>
    </div>
  )
}

function ModuleCard({ children }: { children: React.ReactNode }) {
  return (
    <Card className="bg-card/50 backdrop-blur-sm ring-1 ring-border/30 border-0">
      <CardContent className="pt-4">
        {children}
      </CardContent>
    </Card>
  )
}

function Tag({ children, color = 'default' }: { children: React.ReactNode, color?: 'green' | 'red' | 'yellow' | 'blue' | 'default' }) {
  const colors = {
    green: 'bg-green-500/10 text-green-400 ring-green-500/20',
    red: 'bg-red-500/10 text-red-400 ring-red-500/20',
    yellow: 'bg-yellow-500/10 text-yellow-400 ring-yellow-500/20',
    blue: 'bg-cyber/10 text-cyber ring-cyber/20',
    default: 'bg-muted/50 text-muted-foreground ring-border/40',
  }
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ${colors[color]}`}>
      {children}
    </span>
  )
}

export default function AboutPage() {
  const contentRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(
        '[data-reveal]',
        { y: 24, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.6,
          stagger: 0.08,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: '[data-reveal]',
            start: 'top 90%',
            toggleActions: 'play none none reverse',
          },
        }
      )
    }, contentRef)
    return () => ctx.revert()
  }, [])

  const fadeUp = {
    initial: { opacity: 0, y: 16 },
    animate: { opacity: 1, y: 0 },
  }

  return (
    <div ref={contentRef} className="relative min-h-screen bg-background text-foreground">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--glow-subtle)_0%,_transparent_60%)]" />

      {/* Nav */}
      <header className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-xl">
        <div className="max-w-4xl mx-auto flex items-center justify-between px-5 py-3">
          <Link href="/" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors group">
            <ArrowLeft className="h-4 w-4 transition-transform group-hover:-translate-x-0.5" />
            Volver al análisis
          </Link>
          <div className="flex items-center gap-2">
            <Logo size={28} />
            <span className="text-sm font-bold">Crypto Analysis AI</span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-5 py-12 space-y-16">
        {/* Hero */}
        <motion.div {...fadeUp} transition={{ duration: 0.5 }} data-reveal>
          <div className="flex items-center gap-4 mb-4">
            <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-cyber/20 to-purple-500/20 ring-1 ring-cyber/30">
              <Brain className="h-7 w-7 text-cyber" />
            </div>
            <div>
              <Badge variant="outline" className="mb-2 text-xs border-cyber/30 text-cyber bg-cyber/5">v0.1 — Multi-Framework Engine</Badge>
              <h1 className="text-3xl font-bold tracking-tight">Technical Analysis Engine</h1>
            </div>
          </div>
          <p className="text-lg text-muted-foreground max-w-2xl">
            This application is a <strong className="text-foreground">hybrid technical analysis engine</strong> that synthesizes multiple signals — technical, on-chain, sentiment, SMC, and Elliott Wave — into a single aggregated score to generate trading recommendations with entry, exit, and risk levels.
          </p>
          <InfoBox>
            <strong className="text-foreground">Not traditional TA.</strong> The indicators are <strong className="text-foreground">synthetic</strong>, calculated from current 24h price change and market structure, not from historical OHLC candlestick series. This is a multi-framework projection system, not a lagging indicator calculator.
          </InfoBox>
        </motion.div>

        {/* 1. Classic Technical */}
        <Section id="technical" title="1. Classic Technical Analysis" icon={ChartCandlestick}>
          <p className="text-muted-foreground mb-4">
            The <code className="rounded bg-muted px-1.5 py-0.5 text-sm font-mono">parseTechnicalIndicators</code> module generates synthetic indicators based on 24h price change:
          </p>
          <Table
            headers={['Indicator', 'Calculation']}
            rows={[
              ['RSI', '50 + (change24h × 1.5), clamped 15–85'],
              ['MACD', 'Bullish crossover (RSI>60), bearish (RSI<40)'],
              ['MA50', 'Price × 0.97 (bullish) or × 1.03 (bearish)'],
              ['MA200', 'Price × 0.92 (bullish) or × 1.08 (bearish)'],
              ['Trend', 'Bullish if change24h > 2%, bearish if < -2%'],
              ['Supports', 'Price × 0.95, 0.90, 0.85'],
              ['Resistances', 'Price × 1.04, 1.08, 1.15'],
            ]}
          />
        </Section>

        {/* 2. Elliott Wave */}
        <Section id="elliott" title="2. Elliott Wave Analysis" icon={Waves}>
          <p className="text-muted-foreground mb-4">
            The <code className="rounded bg-muted px-1.5 py-0.5 text-sm font-mono">parseElliottWaveData</code> module identifies wave structure based on the magnitude of the price move. It&apos;s a simplified Elliott model that detects impulse vs corrective phases and assigns completeness percentages:
          </p>
          <Table
            headers={['24h Variation', 'Identified Pattern']}
            rows={[
              ['< 1%', 'Neutral — no clear pattern'],
              ['> 4% bullish', 'Wave 3 of (5) — strong bullish impulse'],
              ['1–4% bullish', 'Possible Wave 1 — impulse start'],
              ['> 4% bearish', 'Wave C of (A)(B)(C) — active correction'],
              ['1–4% bearish', 'Possible Wave A — pullback'],
            ]}
          />
          <p className="text-muted-foreground mt-4">
            Generates price targets, invalidation levels, and projected sub-waves for each scenario.
          </p>
        </Section>

        {/* 3. SMC */}
        <Section id="smc" title="3. Smart Money Concepts (SMC)" icon={Gauge}>
          <p className="text-muted-foreground mb-4">
            The <code className="rounded bg-muted px-1.5 py-0.5 text-sm font-mono">parseSmcData</code> module analyzes market structure from the <strong className="text-foreground">smart money</strong> perspective — the same framework used by institutional ICT traders:
          </p>
          <Table
            headers={['Component', 'Description']}
            rows={[
              ['Market Structure', 'Uptrend / Downtrend / Ranging (from price direction)'],
              ['BOS', 'Break of Structure — confirmed if move > 3%'],
              ['MSS', 'Market Structure Shift — detected on directional change'],
              ['Order Blocks', 'Accumulation/distribution zones at key levels'],
              ['FVGs', 'Fair Value Gaps — projected price inefficiencies'],
              ['Liquidity', 'Stop-loss pools calculated above/below price dynamically'],
            ]}
          />
        </Section>

        {/* 4. On-Chain */}
        <Section id="onchain" title="4. On-Chain Analysis" icon={Database}>
          <p className="text-muted-foreground mb-4">
            The <code className="rounded bg-muted px-1.5 py-0.5 text-sm font-mono">parseOnChainData</code> module extracts data from Coinglass and other sources:
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <ModuleCard>
              <div className="flex items-center gap-2 mb-1">
                <Zap className="h-4 w-4 text-yellow-400" />
                <span className="font-medium">Funding Rate</span>
              </div>
              <p className="text-sm text-muted-foreground">Futures perpetual swap financing rate. High rates (&gt;0.005%) signal crowded longs and potential liquidation cascade risk.</p>
            </ModuleCard>
            <ModuleCard>
              <div className="flex items-center gap-2 mb-1">
                <ArrowUp className="h-4 w-4 text-green-400" />
                <ArrowDown className="h-4 w-4 text-red-400" />
                <span className="font-medium">Exchange Flows</span>
              </div>
              <p className="text-sm text-muted-foreground">Inferred from funding rate: positive funding → outflows (holders moving to cold storage).</p>
            </ModuleCard>
            <ModuleCard>
              <div className="flex items-center gap-2 mb-1">
                <Coins className="h-4 w-4 text-cyber" />
                <span className="font-medium">Staking Yield</span>
              </div>
              <p className="text-sm text-muted-foreground">Estimated APY and total staked amounts based on public network data.</p>
            </ModuleCard>
            <ModuleCard>
              <div className="flex items-center gap-2 mb-1">
                <BarChart3 className="h-4 w-4 text-orange-400" />
                <span className="font-medium">Liquidation Levels</span>
              </div>
              <p className="text-sm text-muted-foreground">Projected price levels where cascading liquidations could trigger, calculated as % from current price.</p>
            </ModuleCard>
          </div>
        </Section>

        {/* 5. Sentiment */}
        <Section id="sentiment" title="5. Market Sentiment" icon={MessageSquareText}>
          <p className="text-muted-foreground mb-4">
            The <code className="rounded bg-muted px-1.5 py-0.5 text-sm font-mono">parseSentimentData</code> module combines multiple sentiment signals:
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            <ModuleCard>
              <span className="font-medium block mb-1">Fear &amp; Greed Index</span>
              <p className="text-sm text-muted-foreground">Quantitative index from alternative.me. Values &lt;25 signal fear, &gt;70 signal greed. Directly affects verdict confidence.</p>
            </ModuleCard>
            <ModuleCard>
              <span className="font-medium block mb-1">News NLP</span>
              <p className="text-sm text-muted-foreground">Keyword-based classification (dump/crash/surge/rally/bull/bear) on headlines from CoinDesk and CoinTelegraph.</p>
            </ModuleCard>
            <ModuleCard>
              <span className="font-medium block mb-1">Social Sentiment</span>
              <p className="text-sm text-muted-foreground">Derived from Fear &amp; Greed: bearish when extreme fear, bullish when extreme greed.</p>
            </ModuleCard>
          </div>
        </Section>

        {/* 6. Order Book */}
        <Section id="orderbook" title="6. Order Book Analysis" icon={Cpu}>
          <p className="text-muted-foreground mb-4">
            The <code className="rounded bg-muted px-1.5 py-0.5 text-sm font-mono">parseOrderBookData</code> module uses Binance depth data to calculate:
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            <ModuleCard>
              <span className="font-medium block mb-1">Bid/Ask Ratio</span>
              <p className="text-sm text-muted-foreground">Depth ratio of buy vs sell orders. &gt;1.1 indicates buying pressure, &lt;0.9 indicates selling pressure.</p>
            </ModuleCard>
            <ModuleCard>
              <span className="font-medium block mb-1">Options Flow</span>
              <p className="text-sm text-muted-foreground">Calls dominating (bullish) or puts dominating (bearish) inferred from the ratio.</p>
            </ModuleCard>
            <ModuleCard>
              <span className="font-medium block mb-1">Max Pain</span>
              <p className="text-sm text-muted-foreground">Strike price where most options expire worthless (reserved for future implementation).</p>
            </ModuleCard>
          </div>
        </Section>

        {/* 7. Whales */}
        <Section id="whales" title="7. Whale Data" icon={Globe}>
          <Table
            headers={['Metric', 'Description']}
            rows={[
              ['Large transactions 24h', 'Count of high-value transactions detected on-chain'],
              ['Total volume USD', 'Aggregated USD value moved by large holders'],
              ['Accumulation pattern', 'Accumulating, distributing, or neutral behavior'],
              ['Top whale net flow', 'Directional flow of the largest wallets'],
              ['Notable transactions', 'Individual large txns with hash, value, and addresses'],
            ]}
          />
        </Section>

        {/* 8. Verdict */}
        <Section id="verdict" title="8. Verdict Algorithm" icon={Zap}>
          <p className="text-muted-foreground mb-4">
            The <code className="rounded bg-muted px-1.5 py-0.5 text-sm font-mono">buildVerdict</code> function implements a <strong className="text-foreground">multi-factor scoring system</strong> that assigns bearish and bullish weights to each analytical module:
          </p>

          <h3 className="font-semibold mb-3">Scoring Weights</h3>
          <Table
            headers={['Factor', 'Bearish', 'Bullish']}
            rows={[
              ['Technical trend', '3', '3'],
              ['RSI extreme (>70 / <30)', '2 / -1', '2 / -1'],
              ['Funding rate high (>0.005) / low (<0.001)', '3', '2'],
              ['Fear & Greed (<25 / >70)', '2', '2'],
              ['Bid/Ask ratio (<0.9 / >1.1)', '2', '2'],
              ['Dominant timeframe trend', '3 / -1', '3 / -1'],
              ['Elliott Waves (late impulse / early impulse)', '3 / 2', '3 / -2'],
              ['SMC market structure (downtrend / uptrend)', '2', '2'],
              ['BOS (bearish / bullish)', '2', '2'],
              ['MSS (structure shift)', '—', '3'],
            ]}
          />

          <div className="mt-6 mb-4">
            <h3 className="font-semibold mb-3">Net Score = BullishScore − BearishScore</h3>
            <Table
              headers={['Net Score', 'Short Term', 'Long Term', 'Confidence']}
              rows={[
                ['≥ 4', 'BUY', 'BUY', '58–85%'],
                ['1 to 3', 'HOLD', 'BUY', '48–70%'],
                ['−2 to 0', 'HOLD', 'HOLD', '30–60%'],
                ['< −2', 'SELL', 'HOLD', '36–80%'],
              ]}
            />
          </div>

          <InfoBox>
            If the <strong className="text-foreground">Fear &amp; Greed Index is below 20</strong> (Extreme Fear), the confidence score is reduced by 10 points (floor 30%) and any BUY signal is downgraded to HOLD — applying extreme caution during panic conditions.
          </InfoBox>
        </Section>

        {/* 9. Scenarios */}
        <Section id="scenarios" title="9. Probabilistic Scenarios" icon={BarChart3}>
          <p className="text-muted-foreground mb-4">
            Every analysis generates two probabilistic scenarios with specific triggers and targets:
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            <Card className="border-red-500/20 bg-red-500/5">
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 mb-2">
                  <ArrowDown className="h-4 w-4 text-red-400" />
                  <span className="font-semibold text-red-400">Bearish Scenario</span>
                  <Tag color="red">~45%</Tag>
                </div>
                <p className="text-sm text-muted-foreground">&quot;If price loses support at $&#123;X&#125;...&quot; &rarr; target $&#123;Y&#125;</p>
              </CardContent>
            </Card>
            <Card className="border-green-500/20 bg-green-500/5">
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 mb-2">
                  <ArrowUp className="h-4 w-4 text-green-400" />
                  <span className="font-semibold text-green-400">Bullish Scenario</span>
                  <Tag color="green">~55%</Tag>
                </div>
                <p className="text-sm text-muted-foreground">&quot;If price breaks resistance at $&#123;X&#125;...&quot; &rarr; target $&#123;Y&#125;</p>
              </CardContent>
            </Card>
          </div>
        </Section>

        {/* 10. Sources */}
        <Section id="sources" title="10. Data Sources" icon={Globe}>
          <p className="text-muted-foreground mb-4">
            The engine fetches data from multiple sources using <code className="rounded bg-muted px-1.5 py-0.5 text-sm font-mono">Promise.allSettled</code> for fault tolerance:
          </p>
          <Table
            headers={['Source', 'Data Provided', 'Method']}
            rows={[
              ['CoinGecko', 'Price, volume, market cap', 'REST API'],
              ['Fear & Greed Index', 'Sentiment index', 'API (alternative.me)'],
              ['CoinDesk', 'News headlines', 'Web scraping'],
              ['CoinTelegraph', 'News headlines', 'Web scraping'],
              ['Coinglass', 'Funding rate, liquidation data', 'REST API'],
              ['Binance', 'Order book depth (bid/ask)', 'REST API'],
              ['Macro Calendar', 'Economic events', 'REST API'],
              ['DeFi Llama', 'Ethereum TVL', 'REST API'],
              ['CoinMarketCap', 'Price, 24h change', 'Web scraping'],
              ['TradingView', 'Technical signals', 'Web scraping'],
            ]}
          />
        </Section>

        {/* 11. Assets */}
        <Section id="assets" title="Supported Assets" icon={Coins}>
          <div className="grid gap-3 sm:grid-cols-4">
            {[
              { icon: '⟠', name: 'Ethereum', symbol: 'ETH', desc: 'Smart contract platform' },
              { icon: '₿', name: 'Bitcoin', symbol: 'BTC', desc: 'Digital gold' },
              { icon: '👑', name: 'Gold', symbol: 'XAU', desc: 'Tether Gold token' },
              { icon: '🇦🇺', name: 'AUD', symbol: 'AUD', desc: 'Australian Dollar (forex)' },
            ].map((a) => (
              <Card key={a.symbol} className="bg-card/50 backdrop-blur-sm ring-1 ring-border/30 border-0">
                <CardContent className="pt-4 flex flex-col items-center text-center gap-2">
                  <span className="text-2xl">{a.icon}</span>
                  <span className="font-bold">{a.symbol}</span>
                  <span className="text-xs text-muted-foreground">{a.name}</span>
                  <span className="text-xs text-muted-foreground/70">{a.desc}</span>
                </CardContent>
              </Card>
            ))}
          </div>
        </Section>

        {/* Footer */}
        <div className="border-t border-border/30 pt-8 text-center" data-reveal>
          <p className="text-sm text-muted-foreground">
            Built with Next.js 16 · shadcn/ui · Tailwind CSS v4 · Framer Motion · GSAP
          </p>
          <p className="text-xs text-muted-foreground/60 mt-1">
            Data from CoinGecko, Coinglass, Binance, Fear &amp; Greed Index, CoinDesk, CoinTelegraph, DeFi Llama, and more.
          </p>
          <Link href="/" className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium hover:bg-muted hover:text-foreground transition-all">
              <ArrowLeft className="h-4 w-4" />
              Back to Analysis
            </Link>
        </div>
      </main>
    </div>
  )
}
