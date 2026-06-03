import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
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
  icons: {
    icon: '/favicon.svg',
  },
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
      <body className="min-h-full flex flex-col bg-background text-foreground selection:bg-cyber/20 selection:text-foreground">
        {children}
      </body>
    </html>
  );
}
