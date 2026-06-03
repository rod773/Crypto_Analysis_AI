import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
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
  themeColor: "#0a0e1a",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground selection:bg-cyber/20 selection:text-foreground">
        {children}
      </body>
    </html>
  );
}
