import { NextRequest } from 'next/server'
import { scrapeAllSources } from '@/lib/sources'
import { analyze } from '@/lib/analysis'

export const dynamic = 'force-dynamic'
export const maxDuration = 60

export async function GET(request: NextRequest) {
  const useAI = request.nextUrl.searchParams.get('ai') === 'true'
  try {
    const sources = await scrapeAllSources()
    const analysis = analyze(sources)
    if (useAI) {
      try {
        const aiAnalysis = await generateAIAnalysis(analysis)
        return Response.json({ ...analysis, aiAnalysis })
      } catch {
        return Response.json({ ...analysis, aiAnalysis: null })
      }
    }
    return Response.json(analysis)
  } catch (error) {
    console.error('Analysis error:', error)
    return Response.json({ error: 'Failed to analyze' }, { status: 500 })
  }
}

async function generateAIAnalysis(analysis: unknown): Promise<string> {
  const apiKey = process.env.OPENROUTER_API_KEY
  if (!apiKey) throw new Error('No API key configured')
  const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: 'openai/gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content: 'Eres un analista de criptomonedas experto. Basado en los datos proporcionados, da una recomendación clara de COMPRAR o VENDER ETH. Responde en español, máximo 3 párrafos, con el veredicto al inicio en negrita.',
        },
        {
          role: 'user',
          content: `Analiza estos datos de Ethereum y da tu veredicto: ${JSON.stringify(analysis)}`,
        },
      ],
      max_tokens: 500,
    }),
  })
  const json = await res.json() as { choices?: { message?: { content?: string } }[] }
  return json.choices?.[0]?.message?.content ?? ''
}
