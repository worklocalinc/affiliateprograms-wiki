import { Link } from "react-router-dom";
import { CheckCircle2, XCircle, Minus } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const comparisonData = {
  title: "Notion vs Coda vs Airtable",
  description: "Compare the top productivity and workspace SaaS affiliate programs side by side.",
  programs: [
    {
      name: "Notion",
      slug: "notion",
      commission: "50%",
      payoutModel: "Recurring (12 mo)",
      cookieLength: "90 days",
      network: "PartnerStack",
      minPayout: "$50",
      payoutFrequency: "Monthly",
      geos: "Worldwide",
      trafficAllowed: ["Content", "Email", "Social"],
      trafficRestricted: ["PPC Brand", "Incentive"],
      postbackSupport: true,
      apiAccess: false,
    },
    {
      name: "Coda",
      slug: "coda",
      commission: "50%",
      payoutModel: "Recurring (12 mo)",
      cookieLength: "60 days",
      network: "PartnerStack",
      minPayout: "$50",
      payoutFrequency: "Monthly",
      geos: "Worldwide",
      trafficAllowed: ["Content", "Email", "Social", "YouTube"],
      trafficRestricted: ["PPC Brand"],
      postbackSupport: true,
      apiAccess: false,
    },
    {
      name: "Airtable",
      slug: "airtable",
      commission: "$50-200",
      payoutModel: "CPA",
      cookieLength: "30 days",
      network: "Impact",
      minPayout: "$10",
      payoutFrequency: "Net 30",
      geos: "US, UK, EU",
      trafficAllowed: ["Content", "Email", "Social", "Podcast"],
      trafficRestricted: ["PPC Brand", "Coupon"],
      postbackSupport: true,
      apiAccess: true,
    },
  ],
  whoIsItFor: [
    {
      program: "Notion",
      audience: "Best for content creators targeting productivity enthusiasts, small teams, and students. The 50% recurring commission is excellent for building passive income.",
    },
    {
      program: "Coda",
      audience: "Ideal for affiliates with tech-savvy audiences who need powerful document automation. Similar commission structure to Notion with slightly shorter cookie.",
    },
    {
      program: "Airtable",
      audience: "Great for B2B affiliates targeting operations teams and project managers. CPA model means immediate payouts but no recurring revenue.",
    },
  ],
};

const RenderValue = ({ value }: { value: boolean | string | string[] }) => {
  if (typeof value === "boolean") {
    return value ? (
      <CheckCircle2 className="w-5 h-5 text-verified" />
    ) : (
      <XCircle className="w-5 h-5 text-muted-foreground" />
    );
  }
  if (Array.isArray(value)) {
    return (
      <div className="flex flex-wrap gap-1">
        {value.map((v) => (
          <Badge key={v} variant="secondary" className="text-xs">{v}</Badge>
        ))}
      </div>
    );
  }
  return <span>{value}</span>;
};

type ComparisonProgram = (typeof comparisonData.programs)[number];

const comparisonRows: Array<{ label: string; key: keyof ComparisonProgram }> = [
  { label: "Commission", key: "commission" },
  { label: "Payout Model", key: "payoutModel" },
  { label: "Cookie Length", key: "cookieLength" },
  { label: "Network", key: "network" },
  { label: "Min. Payout", key: "minPayout" },
  { label: "Payout Frequency", key: "payoutFrequency" },
  { label: "Geos", key: "geos" },
  { label: "Allowed Traffic", key: "trafficAllowed" },
  { label: "Restricted Traffic", key: "trafficRestricted" },
  { label: "Postback Support", key: "postbackSupport" },
  { label: "API Access", key: "apiAccess" },
];

export default function ComparisonPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      
      <main className="flex-1 py-8">
        <div className="container">
          <Breadcrumbs items={[
            { label: "Comparisons", href: "/comparisons" },
            { label: comparisonData.title },
          ]} />

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-4">{comparisonData.title}</h1>
            <p className="text-lg text-muted-foreground">{comparisonData.description}</p>
          </div>

          {/* Comparison Table */}
          <div className="overflow-x-auto -mx-4 px-4 mb-10">
            <table className="w-full border-collapse min-w-[640px]">
              <thead>
                <tr>
                  <th className="text-left font-medium text-muted-foreground bg-muted/50 px-4 py-3 border-b border-border w-40"></th>
                  {comparisonData.programs.map((program) => (
                    <th key={program.slug} className="text-left font-semibold text-foreground bg-muted/50 px-4 py-3 border-b border-border">
                      <Link to={`/programs/${program.slug}`} className="wiki-link">
                        {program.name}
                      </Link>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {comparisonRows.map((row) => (
                  <tr key={row.key} className="hover:bg-muted/30">
                    <td className="px-4 py-3 border-b border-border font-medium text-muted-foreground">
                      {row.label}
                    </td>
                    {comparisonData.programs.map((program) => (
                      <td key={`${program.slug}-${row.key}`} className="px-4 py-3 border-b border-border">
                        <RenderValue value={program[row.key]} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Who Is It For */}
          <section className="mb-10">
            <h2 className="wiki-heading text-xl">Who Is It For?</h2>
            <div className="grid md:grid-cols-3 gap-6">
              {comparisonData.whoIsItFor.map((item) => (
                <div key={item.program} className="infobox">
                  <h3 className="font-semibold text-foreground mb-2">{item.program}</h3>
                  <p className="text-sm text-muted-foreground">{item.audience}</p>
                  <Button variant="outline" size="sm" className="mt-4" asChild>
                    <Link to={`/programs/${item.program.toLowerCase()}`}>View Program</Link>
                  </Button>
                </div>
              ))}
            </div>
          </section>

          {/* CTA */}
          <section className="bg-primary/5 border border-primary/10 rounded-lg p-6 text-center">
            <h2 className="text-xl font-semibold text-foreground mb-2">Create Your Own Comparison</h2>
            <p className="text-muted-foreground mb-4">
              Select any programs to compare them side by side.
            </p>
            <Button asChild>
              <Link to="/comparisons/new">Build Comparison</Link>
            </Button>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
