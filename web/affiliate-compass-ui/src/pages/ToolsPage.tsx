import { Link } from "react-router-dom";
import { Calculator, GitCompare, Search, Link2, BarChart3, FileText } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Breadcrumbs } from "@/components/Breadcrumbs";

const tools = [
  {
    icon: GitCompare,
    title: "Program Comparison",
    description: "Compare affiliate programs side by side. Evaluate commission rates, cookie lengths, and terms at a glance.",
    href: "/comparisons",
    status: "available",
  },
  {
    icon: Calculator,
    title: "Commission Calculator",
    description: "Estimate your potential earnings based on traffic, conversion rates, and commission structures.",
    href: "/tools/calculator",
    status: "coming-soon",
  },
  {
    icon: Search,
    title: "Program Finder",
    description: "Answer a few questions about your niche and audience to get personalized program recommendations.",
    href: "/tools/finder",
    status: "coming-soon",
  },
  {
    icon: Link2,
    title: "Link Builder",
    description: "Generate properly formatted affiliate links with tracking parameters and deep links.",
    href: "/tools/link-builder",
    status: "coming-soon",
  },
  {
    icon: BarChart3,
    title: "Niche Analyzer",
    description: "Explore niches with data on average commissions, competition, and top-performing programs.",
    href: "/tools/niche-analyzer",
    status: "coming-soon",
  },
  {
    icon: FileText,
    title: "Disclosure Generator",
    description: "Generate compliant affiliate disclosure text for your website, blog, or social media.",
    href: "/tools/disclosure-generator",
    status: "coming-soon",
  },
];

export default function ToolsPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      
      <main className="flex-1 py-8">
        <div className="container">
          <Breadcrumbs items={[{ label: "Tools" }]} />

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-4">Affiliate Tools</h1>
            <p className="text-lg text-muted-foreground">
              Free tools to help you research, compare, and optimize your affiliate marketing.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {tools.map((tool) => (
              <div
                key={tool.title}
                className={`bg-card border border-border rounded-lg p-6 ${
                  tool.status === "available" 
                    ? "hover:shadow-md hover:border-primary/30 transition-all" 
                    : "opacity-70"
                }`}
              >
                <div className="flex items-start justify-between mb-4">
                  <tool.icon className="w-8 h-8 text-primary" />
                  {tool.status === "coming-soon" && (
                    <span className="text-xs font-medium text-muted-foreground bg-muted px-2 py-1 rounded">
                      Coming Soon
                    </span>
                  )}
                </div>
                <h3 className="font-semibold text-lg text-foreground mb-2">{tool.title}</h3>
                <p className="text-sm text-muted-foreground mb-4">{tool.description}</p>
                {tool.status === "available" ? (
                  <Link to={tool.href} className="text-sm font-medium text-primary hover:text-primary/80">
                    Use Tool →
                  </Link>
                ) : (
                  <span className="text-sm text-muted-foreground">Notify me when available</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
