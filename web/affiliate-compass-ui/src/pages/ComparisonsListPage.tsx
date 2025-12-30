import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Button } from "@/components/ui/button";

const comparisons = [
  {
    title: "Notion vs Coda vs Airtable",
    slug: "notion-vs-coda-vs-airtable",
    description: "Compare the top productivity and workspace SaaS affiliate programs.",
    programs: ["Notion", "Coda", "Airtable"],
  },
  {
    title: "NordVPN vs ExpressVPN vs Surfshark",
    slug: "nordvpn-vs-expressvpn-vs-surfshark",
    description: "Compare the highest-paying VPN affiliate programs.",
    programs: ["NordVPN", "ExpressVPN", "Surfshark"],
  },
  {
    title: "Bluehost vs SiteGround vs HostGator",
    slug: "bluehost-vs-siteground-vs-hostgator",
    description: "Compare top web hosting affiliate programs.",
    programs: ["Bluehost", "SiteGround", "HostGator"],
  },
  {
    title: "CJ Affiliate vs ShareASale vs Impact",
    slug: "cj-vs-shareasale-vs-impact",
    description: "Compare the major affiliate networks.",
    programs: ["CJ Affiliate", "ShareASale", "Impact"],
  },
];

export default function ComparisonsListPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      
      <main className="flex-1 py-8">
        <div className="container">
          <Breadcrumbs items={[{ label: "Comparisons" }]} />

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-4">Comparisons</h1>
            <p className="text-lg text-muted-foreground">
              Side-by-side comparisons of affiliate programs and networks.
            </p>
          </div>

          {/* Comparison Cards */}
          <div className="grid md:grid-cols-2 gap-6 mb-10">
            {comparisons.map((comparison) => (
              <Link
                key={comparison.slug}
                to={`/comparisons/${comparison.slug}`}
                className="group block bg-card border border-border rounded-lg p-6 hover:shadow-md hover:border-primary/30 transition-all"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-semibold text-lg text-foreground group-hover:text-primary transition-colors mb-2">
                      {comparison.title}
                    </h3>
                    <p className="text-muted-foreground text-sm mb-4">{comparison.description}</p>
                    <div className="flex flex-wrap gap-2">
                      {comparison.programs.map((program) => (
                        <span key={program} className="text-xs bg-muted px-2 py-1 rounded">
                          {program}
                        </span>
                      ))}
                    </div>
                  </div>
                  <ArrowRight className="w-5 h-5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                </div>
              </Link>
            ))}
          </div>

          {/* CTA */}
          <div className="bg-primary/5 border border-primary/10 rounded-lg p-6 text-center">
            <h2 className="text-xl font-semibold text-foreground mb-2">Create Your Own Comparison</h2>
            <p className="text-muted-foreground mb-4">
              Select any programs to compare them side by side.
            </p>
            <Button>Build Comparison</Button>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
