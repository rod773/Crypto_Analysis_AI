'use client'

import { motion } from 'framer-motion'

interface LogoProps {
  size?: number
  className?: string
}

export function Logo({ size = 36, className = '' }: LogoProps) {
  return (
    <motion.svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: [0.25, 0.1, 0.25, 1] }}
    >
      <defs>
        <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#82aaff" />
          <stop offset="50%" stopColor="#c792ea" />
          <stop offset="100%" stopColor="#22da6e" />
        </linearGradient>
        <linearGradient id="candleGreen" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#22da6e" />
          <stop offset="100%" stopColor="#1a9e54" />
        </linearGradient>
        <linearGradient id="candleRed" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#ef5350" />
          <stop offset="100%" stopColor="#c62828" />
        </linearGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="2" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Outer hexagon */}
      <motion.path
        d="M50 5 L90 27.5 L90 72.5 L50 95 L10 72.5 L10 27.5 Z"
        stroke="url(#logoGrad)"
        strokeWidth="2.5"
        fill="none"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 1.2, ease: 'easeInOut' }}
      />

      {/* Inner hexagon bg */}
      <motion.path
        d="M50 12 L84 31 L84 69 L50 88 L16 69 L16 31 Z"
        fill="#011627"
        fillOpacity="0.8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.8 }}
        transition={{ duration: 0.6, delay: 0.3 }}
      />

      {/* Candlestick bars */}
      <motion.g filter="url(#glow)">
        {/* Candle 1 - Green */}
        <motion.rect
          x="25" y="55" width="4" height="18" rx="1"
          fill="url(#candleGreen)"
          initial={{ scaleY: 0, originY: '100%' }}
          animate={{ scaleY: 1 }}
          transition={{ duration: 0.4, delay: 0.5 }}
        />
        <motion.line
          x1="27" y1="48" x2="27" y2="55"
          stroke="#22da6e" strokeWidth="1.5" strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3, delay: 0.6 }}
        />
        <motion.line
          x1="27" y1="73" x2="27" y2="80"
          stroke="#22da6e" strokeWidth="1.5" strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3, delay: 0.7 }}
        />

        {/* Candle 2 - Red */}
        <motion.rect
          x="35" y="40" width="4" height="22" rx="1"
          fill="url(#candleRed)"
          initial={{ scaleY: 0, originY: '100%' }}
          animate={{ scaleY: 1 }}
          transition={{ duration: 0.4, delay: 0.7 }}
        />
        <motion.line
          x1="37" y1="33" x2="37" y2="40"
          stroke="#ef5350" strokeWidth="1.5" strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3, delay: 0.8 }}
        />
        <motion.line
          x1="37" y1="62" x2="37" y2="68"
          stroke="#ef5350" strokeWidth="1.5" strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3, delay: 0.9 }}
        />

        {/* Candle 3 - Green */}
        <motion.rect
          x="45" y="48" width="4" height="26" rx="1"
          fill="url(#candleGreen)"
          initial={{ scaleY: 0, originY: '100%' }}
          animate={{ scaleY: 1 }}
          transition={{ duration: 0.4, delay: 0.9 }}
        />
        <motion.line
          x1="47" y1="40" x2="47" y2="48"
          stroke="#22da6e" strokeWidth="1.5" strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3, delay: 1.0 }}
        />
        <motion.line
          x1="47" y1="74" x2="47" y2="82"
          stroke="#22da6e" strokeWidth="1.5" strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3, delay: 1.1 }}
        />

        {/* Candle 4 - Red */}
        <motion.rect
          x="55" y="35" width="4" height="20" rx="1"
          fill="url(#candleRed)"
          initial={{ scaleY: 0, originY: '100%' }}
          animate={{ scaleY: 1 }}
          transition={{ duration: 0.4, delay: 1.1 }}
        />
        <motion.line
          x1="57" y1="28" x2="57" y2="35"
          stroke="#ef5350" strokeWidth="1.5" strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3, delay: 1.2 }}
        />
        <motion.line
          x1="57" y1="55" x2="57" y2="62"
          stroke="#ef5350" strokeWidth="1.5" strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3, delay: 1.3 }}
        />

        {/* Candle 5 - Green (tallest) */}
        <motion.rect
          x="65" y="28" width="4" height="34" rx="1"
          fill="url(#candleGreen)"
          initial={{ scaleY: 0, originY: '100%' }}
          animate={{ scaleY: 1 }}
          transition={{ duration: 0.4, delay: 1.3 }}
        />
        <motion.line
          x1="67" y1="20" x2="67" y2="28"
          stroke="#22da6e" strokeWidth="1.5" strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3, delay: 1.4 }}
        />
        <motion.line
          x1="67" y1="62" x2="67" y2="70"
          stroke="#22da6e" strokeWidth="1.5" strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3, delay: 1.5 }}
        />
      </motion.g>

      {/* Pulse ring */}
      <motion.circle
        cx="50" cy="50" r="42"
        stroke="#82aaff"
        strokeWidth="1"
        fill="none"
        initial={{ scale: 0.9, opacity: 0.6 }}
        animate={{ scale: [0.9, 1.05, 0.9], opacity: [0.6, 0.2, 0.6] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
      />

      {/* AI text at bottom */}
      <motion.text
        x="50" y="92"
        textAnchor="middle"
        fill="#82aaff"
        fontSize="8"
        fontWeight="bold"
        fontFamily="monospace"
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 1.6 }}
      >
        AI
      </motion.text>
    </motion.svg>
  )
}
