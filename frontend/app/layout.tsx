import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Playfair_Display } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "FraudDNA — Risk Intelligence & Fraud Operations Platform",
  description:
    "Institutional financial risk, forensic graph discovery, and deterministic policy controls.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} ${playfair.variable} dark`}
    >
      <body className="min-h-screen bg-[#08080A] text-[#E2E3E9] font-sans antialiased selection:bg-[#CC9166]/30 selection:text-[#FFFFFF]">
        {children}
      </body>
    </html>
  );
}
