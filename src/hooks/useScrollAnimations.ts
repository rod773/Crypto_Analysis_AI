'use client'

import { useEffect, useRef, type RefObject } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
gsap.registerPlugin(ScrollTrigger)

export function useGsapScrollReveal(
  containerRef: RefObject<HTMLDivElement | null>,
  selector: string,
  options?: {
    stagger?: number
    y?: number
    duration?: number
    triggerOnce?: boolean
  }
) {
  const { stagger = 0.08, y = 30, duration = 0.6, triggerOnce = true } = options ?? {}

  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const targets = el.querySelectorAll(selector)
    if (!targets.length) return

    const ctx = gsap.context(() => {
      targets.forEach((target) => {
        gsap.fromTo(
          target,
          { y, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration,
            ease: 'power3.out',
            scrollTrigger: {
              trigger: target as HTMLElement,
              scroller: el,
              start: 'top 90%',
              toggleActions: triggerOnce ? 'play none none none' : 'play none none reset',
            },
          }
        )
      })
    }, el)

    return () => ctx.revert()
  }, [containerRef, selector, stagger, y, duration, triggerOnce])
}

export function useScrollReveal(
  containerRef: RefObject<HTMLDivElement | null>,
  selector: string,
  options?: { delay?: number; distance?: string; duration?: number; interval?: number; origin?: string }
) {
  useEffect(() => {
    if (typeof window === 'undefined') return
    const el = containerRef.current
    if (!el) return

    let sr: ReturnType<typeof ScrollReveal> | null = null

    import('scrollreveal').then((mod) => {
      const ScrollRevealLib = mod.default
      sr = ScrollRevealLib({
        distance: options?.distance ?? '30px',
        duration: options?.duration ?? 600,
        delay: options?.delay ?? 100,
        interval: options?.interval ?? 80,
        origin: options?.origin ?? 'bottom',
        easing: 'cubic-bezier(0.5, 0, 0, 1)',
        reset: false,
      })
      sr.reveal(el.querySelectorAll(selector))
    })

    return () => {
      if (sr) sr.destroy()
    }
  }, [containerRef, selector, JSON.stringify(options)])
}

export function useGsapStagger(
  containerRef: RefObject<HTMLDivElement | null>,
  selector: string,
  options?: { stagger?: number; y?: number; duration?: number }
) {
  const { stagger = 0.06, y = 20, duration = 0.5 } = options ?? {}

  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const targets = el.querySelectorAll(selector)
    if (!targets.length) return

    const ctx = gsap.context(() => {
      gsap.fromTo(
        targets,
        { y, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration,
          stagger,
          ease: 'power2.out',
        }
      )
    }, el)

    return () => ctx.revert()
  }, [containerRef, selector, stagger, y, duration])
}
