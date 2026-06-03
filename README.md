# Crypto Analysis AI — ¿Comprar o Vender ETH?

Asistente inteligente que analiza Ethereum en tiempo real consultando **10+ fuentes** y te recomienda si **comprar, vender o esperar**, tanto a corto como a largo plazo.

```bash
yarn dev
# Abre http://localhost:3000 y pregunta qué hacer con ETH
```

---

## Estrategia del Proyecto

### 1. Arquitectura

```
Cliente (Next.js App Router)
  │
  ├─ Chat UI → Preguntas en lenguaje natural
  │
  └─ /api/analyze
       ├─ scrapeAllSources() → 11 fuentes en paralelo
       ├─ analyze()           → Motor de análisis propio
       └─ [Opcional] IA      → GPT-4o-mini vía OpenRouter
```

### 2. Fuentes de Datos (11 en total)

| Fuente | Tipo de Dato | Método |
|--------|-------------|--------|
| **CoinGecko** | Precio, volumen, market cap | API REST pública |
| **CoinMarketCap** | Precio, cambio % | Web scraping con cheerio |
| **Fear & Greed Index** | Sentimiento del mercado | API alternativa.me |
| **CoinDesk** | Titulares de noticias | Web scraping |
| **CoinTelegraph** | Titulares de noticias ETH | Web scraping |
| **Glassnode** | Tendencias on-chain | Web scraping (blog) |
| **CryptoQuant** | Flujos de exchange | Web scraping |
| **TradingView** | Señales técnicas | Web scraping |
| **Coinglass** | Funding rate, liquidaciones | API REST |
| **DeFi Llama** | TVL de Ethereum | API REST |
| **Etherscan** | Conteo de transacciones | Web scraping |

Se usa `Promise.allSettled` para tolerancia a fallos: si una fuente falla (timeout, bloqueo), las demás siguen funcionando.

### 3. Motor de Análisis (sin IA)

El análisis se compone de 4 módulos independientes que se combinan para generar el veredicto:

#### Técnico (`parseTechnicalIndicators`)
- **RSI** aproximado a partir del cambio de precio 24h (normalizado entre 15-85)
- **MACD** inferido del RSI
- **MA-50 / MA-200** calculados como % del precio actual
- **Soportes y resistencias** en 3 niveles (95%, 90%, 85% y 104%, 108%, 115%)
- **Tendencia** (alcista/bajista/neutral) según el cambio %

#### On-Chain (`parseOnChainData`)
- **Funding rate**: detecta si es >0.005% (señal de sobreapalancamiento en longs)
- **Flujo de exchanges**: inferido del funding rate
- **Staking APY** y **ETH total staked** (estimaciones basadas en datos públicos)

#### Sentimiento (`parseSentimentData`)
- **Fear & Greed Index** del API de alternative.me
- **Análisis de titulares**: clasificación positiva/negativa/neutral por palabras clave (dump, crash, rally, surge, etc.)
- **Sentimiento social** correlacionado con el Fear & Greed

#### Fundamental (`parseFundamentalData`)
- TVL en DeFi, supply de stablecoins, revenue de red, direcciones activas, transacciones

### 4. Sistema de Veredicto (`buildVerdict`)

Cada módulo aporta puntos a un score **bajista** y otro **alcista**:

| Factor | Puntos Bajista | Puntos Alcista |
|--------|:---:|:---:|
| Tendencia bajista | +3 | — |
| Tendencia alcista | — | +3 |
| RSI > 70 (sobrecompra) | +2 | — |
| RSI < 30 (sobreventa) | — | +2 |
| Funding rate alto (>0.005%) | +3 | — |
| Funding rate bajo (<0.001%) | — | +2 |
| Fear & Greed < 25 (miedo extremo) | +2 | — |
| Fear & Greed > 70 (codicia extrema) | — | +2 |

**Score neto** = puntos alcistas − puntos bajistas

| Score | Corto Plazo | Largo Plazo | Confianza |
|-------|:-----------:|:-----------:|:---------:|
| ≥ 4 | **COMPRAR** | **COMPRAR** | 58-85% |
| 1 a 3 | ESPERAR | **COMPRAR** | 48-70% |
| −2 a 0 | ESPERAR | ESPERAR | 30-60% |
| ≤ −3 | **VENDER** | ESPERAR | 36-80% |

El veredicto incluye niveles concretos de **Stop Loss** y **Take Profit** para cada escenario.

### 5. Escenarios Probabilísticos

Siempre se generan dos escenarios con trigger y probabilidad:

- **Bajista**: "Si pierde soporte en $X..." → objetivo $Y (probabilidad ~45%)
- **Alcista**: "Si rompe resistencia en $X..." → objetivo $Y (probabilidad ~55%)

### 6. Interfaz de Chat

- Diseño tipo mensajería con scroll infinito
- Sugerencias de preguntas al iniciar
- Sección "Ver análisis detallado" colapsable con datos técnicos, on-chain y sentimiento
- Indicador de fuentes consultadas (ej: "8/11 fuentes consultadas")

### 7. Integración con IA (Opcional)

Si se configura `OPENROUTER_API_KEY` en `.env`, el endpoint acepta `?ai=true` y añade un análisis generado por GPT-4o-mini con el prompt:

> "Eres un analista de criptomonedas experto. Basado en los datos proporcionados, da una recomendación clara de COMPRAR o VENDER ETH. Responde en español, máximo 3 párrafos, con el veredicto al inicio en negrita."

---

## Stack Tecnológico

- **Framework**: Next.js 16 (App Router, TypeScript, Turbopack)
- **UI**: shadcn/ui (Radix, Tailwind CSS v4)
- **Scraping**: cheerio, fetch nativo
- **Iconos**: lucide-react
- **Paquetería**: Yarn

## Comandos

```bash
yarn dev       # Desarrollo en localhost:3000
yarn build     # Build de producción
yarn lint      # Verificar código
```

## Variables de Entorno

```env
# Opcional — para análisis con IA
OPENROUTER_API_KEY=sk-or-v1-...
```

## Mejoras Futuras

- [ ] WebSockets para datos en tiempo real
- [ ] Soporte para múltiples criptos (BTC, SOL, etc.)
- [ ] Alertas de precio con Web Push
- [ ] Historial de análisis y gráficos interactivos
- [ ] Conexión a APIs de exchanges (Binance, Coinbase) para datos de order book
