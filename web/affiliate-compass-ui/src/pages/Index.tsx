import { Link } from "react-router-dom";
import { ArrowRight, Search, TrendingUp, Building2 } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { SearchBar } from "@/components/SearchBar";
import { ProgramCard } from "@/components/ProgramCard";
import { NicheCard } from "@/components/NicheCard";
import { NetworkCard } from "@/components/NetworkCard";
import { StatsStrip } from "@/components/StatsStrip";
import { Button } from "@/components/ui/button";

const featuredNiches = [
  { name: "Fashion & Apparel", slug: "fashion-apparel", description: "Clothing, accessories, and fashion brands", programCount: 94, icon: "👗" },
  { name: "Beauty & Cosmetics", slug: "beauty-cosmetics", description: "Skincare, makeup, and beauty products", programCount: 78, icon: "💄" },
  { name: "Health & Wellness", slug: "health-wellness", description: "Supplements, fitness, and health products", programCount: 45, icon: "💪" },
  { name: "Technology", slug: "technology", description: "Software, gadgets, and tech services", programCount: 32, icon: "💻" },
  { name: "Food & Beverage", slug: "food-beverage", description: "Grocery, restaurants, and meal services", programCount: 38, icon: "🍽️" },
  { name: "Sports & Outdoors", slug: "sports-outdoors", description: "Athletic gear, outdoor equipment, and fitness", programCount: 28, icon: "⚽" },
];

const recentPrograms = [
  {
    name: "Notion",
    slug: "notion",
    description: "All-in-one workspace for notes, docs, and collaboration. High-converting SaaS product.",
    payoutModel: "Recurring",
    commission: "50%",
    cookieLength: "90 days",
    network: "Direct",
    verified: "Dec 2024",
  },
  {
    name: "Shopify",
    slug: "shopify",
    description: "Leading e-commerce platform. Excellent for business and entrepreneurship audiences.",
    payoutModel: "CPA + Recurring",
    commission: "$150 + 20%",
    cookieLength: "30 days",
    network: "Impact",
    verified: "Dec 2024",
  },
  {
    name: "NordVPN",
    slug: "nordvpn",
    description: "Top VPN provider with global recognition. Strong conversion rates.",
    payoutModel: "CPA",
    commission: "40-100%",
    cookieLength: "30 days",
    network: "CJ",
    verified: "Dec 2024",
  },
];

const popularNetworks = [
  {
    name: "CJ Affiliate",
    slug: "cj-affiliate",
    description: "One of the largest affiliate networks with premium brand partners.",
    offerTypes: ["CPA", "CPL", "RevShare"],
    payoutFrequency: "Net 20",
    verified: "Dec 2024",
  },
  {
    name: "ShareASale",
    slug: "shareasale",
    description: "Diverse network with thousands of merchants across all niches.",
    offerTypes: ["CPA", "CPL", "CPC"],
    payoutFrequency: "Net 20",
    verified: "Dec 2024",
  },
  {
    name: "Impact",
    slug: "impact",
    description: "Modern partnership platform with enterprise brands.",
    offerTypes: ["CPA", "RevShare", "Hybrid"],
    payoutFrequency: "Net 30",
    verified: "Dec 2024",
  },
];

export default function Index() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      
      <main className="flex-1">
        {/* Hero Section */}
        <section className="py-16 md:py-24">
          <div className="container">
            <div className="max-w-3xl mx-auto text-center">
              <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-6 text-balance">
                The open wiki for affiliate programs
              </h1>
              <p className="text-xl text-muted-foreground mb-8 text-balance">
                Discover, compare, and research affiliate programs, CPA networks, and performance marketing resources. Community-verified and always up to date.
              </p>
              <div className="max-w-xl mx-auto">
                <SearchBar size="large" />
              </div>
              <div className="flex flex-wrap items-center justify-center gap-4 mt-6 text-sm text-muted-foreground">
                <span>Popular:</span>
                <Link to="/programs/amazon-associates" className="wiki-link">Amazon Associates</Link>
                <Link to="/programs/shopify" className="wiki-link">Shopify Partners</Link>
                <Link to="/networks/cj-affiliate" className="wiki-link">CJ Affiliate</Link>
                <Link to="/niches/fashion-apparel" className="wiki-link">Fashion Programs</Link>
              </div>
            </div>
          </div>
        </section>

        {/* Stats Strip */}
        <StatsStrip />

        {/* Featured Niches */}
        <section className="py-16">
          <div className="container">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-semibold text-foreground">Browse by Niche</h2>
              <Link to="/niches" className="text-sm font-medium text-primary hover:text-primary/80 flex items-center gap-1">
                View all niches <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {featuredNiches.map((niche) => (
                <NicheCard key={niche.slug} {...niche} />
              ))}
            </div>
          </div>
        </section>

        {/* Recently Verified Programs */}
        <section className="py-16 bg-muted/30">
          <div className="container">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-primary" />
                <h2 className="text-2xl font-semibold text-foreground">Recently Verified</h2>
              </div>
              <Link to="/programs" className="text-sm font-medium text-primary hover:text-primary/80 flex items-center gap-1">
                View all programs <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recentPrograms.map((program) => (
                <ProgramCard key={program.slug} {...program} />
              ))}
            </div>
          </div>
        </section>

        {/* Popular Networks */}
        <section className="py-16">
          <div className="container">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-primary" />
                <h2 className="text-2xl font-semibold text-foreground">Popular CPA Networks</h2>
              </div>
              <Link to="/networks" className="text-sm font-medium text-primary hover:text-primary/80 flex items-center gap-1">
                View all networks <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {popularNetworks.map((network) => (
                <NetworkCard key={network.slug} {...network} />
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 bg-primary/5 border-y border-primary/10">
          <div className="container">
            <div className="max-w-2xl mx-auto text-center">
              <h2 className="text-2xl font-semibold text-foreground mb-4">
                Can't find what you're looking for?
              </h2>
              <p className="text-muted-foreground mb-6">
                Use our comparison tool to evaluate programs side-by-side, or suggest a program to add to our database.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-4">
                <Button asChild>
                  <Link to="/comparisons">Compare Programs</Link>
                </Button>
                <Button variant="outline" asChild>
                  <Link to="/about">Suggest a Program</Link>
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
