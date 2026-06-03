'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ChatMessage } from '@/components/crypto/chat-message'
import { Logo } from '@/components/ui/logo'
import { Zap, SendHorizonal, Sparkles, RotateCcw, Coins, Bitcoin, Globe } from 'lucide-react'
import type { AnalysisResult, Asset } from '@/lib/types'
import { getAssetConfig, ASSETS } from '@/lib/types'
import { useScrollReveal } from '@/hooks/useScrollAnimations'

gsap.registerPlugin(ScrollTrigger)

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  analysis?: AnalysisResult | null
  loading?: boolean
}

function generateId() {
  return Math.random().toString(36).substring(2, 11)
}

export default function Home() {
  const [asset, setAsset] = useState<Asset>('eth')
  const assetConfig = getAssetConfig(asset)

  const welcomeMessage = `¡Hola! Soy tu asistente de análisis. Pregúntame sobre ${assetConfig.name} y te daré un análisis completo basado en datos de múltiples fuentes en tiempo real.`

  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: welcomeMessage,
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)

  useScrollReveal(contentRef, '[data-reveal]', { distance: '20px', interval: 60 })

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMsg: Message = { id: generateId(), role: 'user', content: input }
    const loadingMsg: Message = { id: generateId(), role: 'assistant', content: '', loading: true }
    setMessages((prev) => [...prev, userMsg, loadingMsg])
    setInput('')
    setLoading(true)

    let data: AnalysisResult | null = null

    // Try Vercel API first (works in web mode)
    try {
      const res = await fetch(`/api/analyze?ai=false&asset=${asset}`)
      if (res.ok) data = await res.json()
    } catch { /* fall through to client-side */ }

    // Fallback: client-side analysis with free APIs
    if (!data) {
      try {
        const { analyzeClientSide } = await import('@/lib/client-analysis')
        data = await analyzeClientSide(asset)
      } catch (err) {
        console.error('Client analysis failed:', err)
      }
    }

    if (data) {
      setMessages((prev) =>
        prev.map((m) => (m.id === loadingMsg.id ? { ...m, loading: false, analysis: data } : m))
      )
    } else {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingMsg.id
            ? { ...m, loading: false, content: 'Lo siento, hubo un error al obtener el análisis. Intenta de nuevo.' }
            : m
        )
      )
    }
    setLoading(false)
  }

  function switchAsset(newAsset: Asset) {
    setAsset(newAsset)
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: `¡Hola! Soy tu asistente de análisis. Pregúntame sobre ${getAssetConfig(newAsset).name} y te daré un análisis completo basado en datos de múltiples fuentes en tiempo real.`,
      },
    ])
  }

  function resetChat() {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: welcomeMessage,
      },
    ])
  }

  const hasAnalysis = messages.some((m) => m.analysis)

  const suggestions = [
    { label: `¿Debería comprar ${assetConfig.symbol} hoy?`, icon: '📈' },
    { label: `¿Cuál es el mejor momento para vender?`, icon: '⏰' },
    { label: `Análisis técnico de ${assetConfig.name}`, icon: '📊' },
    { label: asset === 'gold' ? '¿Qué dicen los bancos centrales?' : '¿Qué dicen las ballenas?', icon: asset === 'gold' ? '🏦' : '🐋' },
  ]

  const headerRef = useRef<HTMLElement>(null)
  const footerRef = useRef<HTMLElement>(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(
        headerRef.current,
        { y: -20, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.5, ease: 'power3.out' }
      )
      gsap.fromTo(
        footerRef.current,
        { y: 20, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.5, delay: 0.15, ease: 'power3.out' }
      )
    })
    return () => ctx.revert()
  }, [])

  return (
    <div className="relative flex flex-col h-screen max-w-4xl mx-auto w-full">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--glow-subtle)_0%,_transparent_60%)]" />

      <header ref={headerRef} className="relative shrink-0 border-b border-border/40 bg-background/60 backdrop-blur-xl">
        <div className="flex items-center justify-between px-5 py-3">
          <div className="flex items-center gap-3">
            <Logo size={36} />
            <div>
              <h1 className="text-lg font-bold tracking-tight">Crypto Analysis AI</h1>
              <p className="text-xs text-muted-foreground leading-tight">{`¿Comprar o vender ${assetConfig.symbol}?`}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex gap-1 rounded-lg border border-border/30 bg-card/40 p-0.5 backdrop-blur-sm">
              {ASSETS.map((a) => (
                <motion.button
                  key={a.id}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => switchAsset(a.id)}
                  className={`flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all ${
                    asset === a.id
                      ? 'bg-cyber/20 text-cyber shadow-sm shadow-cyber/10'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <span className="text-sm">{a.icon}</span>
                  <span className="hidden sm:inline">{a.symbol}</span>
                </motion.button>
              ))}
            </div>
            <div className="flex items-center gap-1.5 rounded-full bg-green-500/10 px-2.5 py-1 ring-1 ring-green-500/20">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
              </span>
              <span className="text-[11px] font-medium text-green-400">{asset === 'gold' ? '5+ fuentes' : '10+ fuentes'}</span>
            </div>
          </div>
        </div>
      </header>

      <ScrollArea ref={scrollRef} className="relative flex-1">
        <div ref={contentRef} className="space-y-5 px-5 py-6">
          <AnimatePresence mode="popLayout">
            {messages.map((msg, i) => (
              <motion.div
                key={msg.id}
                layout
                initial={{ opacity: 0, y: 20, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.97 }}
                transition={{ duration: 0.35, delay: i * 0.05, ease: [0.25, 0.1, 0.25, 1] }}
                data-reveal
              >
                <ChatMessage
                  role={msg.role}
                  content={msg.content}
                  analysis={msg.analysis}
                  loading={msg.loading}
                />
              </motion.div>
            ))}
          </AnimatePresence>

          {messages.length === 1 && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3, ease: 'easeOut' }}
              className="space-y-3 pt-4"
              data-reveal
            >
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Sparkles className="h-4 w-4" />
                <span>Sugerencias rápidas</span>
              </div>
              <motion.div
                className="flex flex-wrap gap-2"
                initial="hidden"
                animate="visible"
                variants={{
                  visible: { transition: { staggerChildren: 0.07 } },
                }}
              >
                {suggestions.map((s) => (
                  <motion.button
                    key={s.label}
                    variants={{
                      hidden: { opacity: 0, y: 12 },
                      visible: { opacity: 1, y: 0 },
                    }}
                    whileHover={{ scale: 1.04 }}
                    whileTap={{ scale: 0.96 }}
                    onClick={() => { setInput(s.label) }}
                    className="group inline-flex items-center gap-1.5 rounded-full border border-border/50 bg-card/50 px-4 py-2 text-sm text-muted-foreground backdrop-blur-sm transition-colors hover:border-cyber/30 hover:bg-cyber/5 hover:text-foreground hover:shadow-[0_0_12px_var(--glow-subtle)]"
                  >
                    <span className="text-sm leading-none">{s.icon}</span>
                    {s.label}
                  </motion.button>
                ))}
              </motion.div>
            </motion.div>
          )}

          {hasAnalysis && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
              className="flex justify-center pt-2"
              data-reveal
            >
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={resetChat}
                className="inline-flex items-center gap-1.5 rounded-full border border-border/30 bg-card/30 px-5 py-2.5 text-sm text-muted-foreground backdrop-blur-sm transition-colors hover:border-cyber/30 hover:text-foreground hover:shadow-[0_0_12px_var(--glow-subtle)]"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Volver al inicio
              </motion.button>
            </motion.div>
          )}
        </div>
      </ScrollArea>

      <footer ref={footerRef} className="relative shrink-0 border-t border-border/40 bg-background/60 backdrop-blur-xl">
        <div className="px-5 py-4">
          <form onSubmit={handleSubmit} className="flex gap-2.5">
            <div className="relative flex-1">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={`Pregunta sobre ${assetConfig.name}...`}
                disabled={loading}
                className="h-11 border-border/50 bg-card/50 pl-4 pr-10 text-sm backdrop-blur-sm transition-all placeholder:text-muted-foreground/50 focus-visible:border-cyber/40 focus-visible:shadow-[0_0_16px_var(--glow-subtle)]"
              />
              <kbd className="pointer-events-none absolute right-3 top-1/2 hidden -translate-y-1/2 items-center gap-0.5 rounded border border-border/30 bg-muted/50 px-1.5 text-xs text-muted-foreground/60 md:flex">
                <span>⌘</span>K
              </kbd>
            </div>
            <Button
              type="submit"
              disabled={loading || !input.trim()}
              className="h-11 gap-1.5 bg-gradient-to-r from-cyber/80 to-cyber/60 text-white shadow-lg shadow-cyber/20 transition-all hover:from-cyber hover:to-cyber/80 hover:shadow-xl hover:shadow-cyber/30 disabled:opacity-40"
            >
              {loading ? (
                <>
                  <Zap className="h-4 w-4 animate-pulse" />
                  Analizando
                </>
              ) : (
                <>
                  <SendHorizonal className="h-4 w-4" />
                  Analizar
                </>
              )}
            </Button>
          </form>
          <p className="mt-2.5 text-center text-[11px] text-muted-foreground/60">
            Datos de CoinGecko · CoinMarketCap · Fear &amp; Greed · CoinDesk · CoinTelegraph · DeFi Llama y más
          </p>
        </div>
      </footer>
    </div>
  )
}
