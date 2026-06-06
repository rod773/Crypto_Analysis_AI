import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import ServiceWorkerRegister from "@/components/ServiceWorkerRegister";
import "./globals.css";

const interSans = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Crypto Analysis AI — ¿Comprar o Vender ETH?",
  description:
    "Análisis inteligente de Ethereum con datos en tiempo real de 10+ fuentes. Recomendaciones de compra/venta con IA.",

  openGraph: {
    title: "Crypto Analysis AI",
    description: "Análisis de Ethereum en tiempo real con IA",
  },
};

export const viewport: Viewport = {
    themeColor: "#011627",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className={`${interSans.variable} ${jetbrainsMono.variable} h-full antialiased dark`}
    >
      <head>
        <link rel="manifest" href="/manifest.json" />
        <link rel="apple-touch-icon" sizes="192x192" href="/icon-192x192.png" />
        <link rel="apple-touch-icon" sizes="512x512" href="/icon-512x512.png" />
        <meta name="theme-color" content="#011627" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta
          name="apple-mobile-web-app-status-bar-style"
          content="default"
        />
        <meta name="apple-mobile-web-app-title" content="Crypto AI" />
      </head>
      <body className="min-h-full flex flex-col bg-background text-foreground selection:bg-cyber/20 selection:text-foreground">
        <ServiceWorkerRegister />
        {children}
      </body>
    </html>
  );
}
