'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ChatMessage } from '@/components/crypto/chat-message'
import type { AnalysisResult } from '@/lib/types'

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
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: '¡Hola! Soy tu asistente de análisis cripto. Pregúntame sobre Ethereum y te daré un análisis completo basado en datos de más de 10 fuentes en tiempo real.',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

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

    try {
      const res = await fetch('/api/analyze?ai=false')
      if (!res.ok) throw new Error('Failed to fetch')
      const data: AnalysisResult = await res.json()
      setMessages((prev) =>
        prev.map((m) => (m.id === loadingMsg.id ? { ...m, loading: false, analysis: data } : m))
      )
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingMsg.id
            ? { ...m, loading: false, content: 'Lo siento, hubo un error al obtener el análisis. Intenta de nuevo.' }
            : m
        )
      )
    } finally {
      setLoading(false)
    }
  }

  const suggestions = [
    '¿Debería comprar ETH hoy?',
    '¿Cuál es el mejor momento para vender?',
    'Análisis técnico de Ethereum',
    '¿Qué dicen las ballenas?',
  ]

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto w-full">
      <header className="border-b px-4 py-3 shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold">Crypto Analysis AI</h1>
            <p className="text-xs text-muted-foreground">¿Qué me aconsejas hoy? ¿Comprar o vender ETH?</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-xs text-muted-foreground">10+ fuentes en vivo</span>
          </div>
        </div>
      </header>

      <ScrollArea ref={scrollRef} className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              role={msg.role}
              content={msg.content}
              analysis={msg.analysis}
              loading={msg.loading}
            />
          ))}
          {messages.length === 1 && (
            <div className="flex flex-wrap gap-2 mt-4">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => { setInput(s) }}
                  className="text-xs px-3 py-1.5 rounded-full border border-border bg-muted/50 hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>

      <footer className="border-t p-4 shrink-0">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Pregunta sobre Ethereum..."
            disabled={loading}
            className="flex-1"
          />
          <Button type="submit" disabled={loading || !input.trim()}>
            {loading ? 'Analizando...' : 'Analizar'}
          </Button>
        </form>
        <p className="text-xs text-muted-foreground mt-2 text-center">
          Los datos se obtienen de CoinGecko, CoinMarketCap, Fear & Greed, CoinDesk, CoinTelegraph, DeFi Llama, y más.
        </p>
      </footer>
    </div>
  )
}
