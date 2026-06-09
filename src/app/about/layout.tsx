import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Crypto Analysis AI — Technical Analysis Engine',
  description: 'Multi-framework hybrid technical analysis engine combining synthetic indicators, Elliott Waves, SMC, on-chain data, sentiment, order book, and whale analysis.',
}

export default function AboutLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
