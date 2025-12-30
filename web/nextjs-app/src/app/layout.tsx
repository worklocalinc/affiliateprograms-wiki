import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { generateWebsiteJsonLd } from "@/lib/seo";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  metadataBase: new URL("https://affiliateprograms.wiki"),
  title: {
    default: "AffiliatePrograms.wiki - 36,000+ Affiliate Programs Directory",
    template: "%s | AffiliatePrograms.wiki",
  },
  description:
    "Discover 36,000+ affiliate programs with commission rates, cookie durations, payout models, and direct signup links. The most comprehensive affiliate program directory.",
  keywords: [
    "affiliate programs",
    "affiliate marketing",
    "affiliate network",
    "commission rates",
    "referral programs",
    "partner programs",
  ],
  authors: [{ name: "AffiliatePrograms.wiki" }],
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://affiliateprograms.wiki",
    siteName: "AffiliatePrograms.wiki",
    title: "AffiliatePrograms.wiki - Affiliate Program Directory",
    description:
      "Discover 36,000+ affiliate programs with commission rates, cookie durations, and signup links.",
  },
  twitter: {
    card: "summary_large_image",
    title: "AffiliatePrograms.wiki",
    description: "Discover 36,000+ affiliate programs",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(generateWebsiteJsonLd()),
          }}
        />
      </head>
      <body className={`${inter.className} min-h-screen bg-gray-50`}>
        <Header />
        <main className="container mx-auto px-4 py-8">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
