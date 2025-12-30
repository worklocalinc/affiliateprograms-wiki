import { BookOpen, Users, RefreshCw, Shield } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Breadcrumbs } from "@/components/Breadcrumbs";

const values = [
  {
    icon: BookOpen,
    title: "Open Knowledge",
    description: "All information is freely accessible. No paywalls, no gatekeeping. Just comprehensive, accurate affiliate program data.",
  },
  {
    icon: RefreshCw,
    title: "Always Current",
    description: "We verify and update program information regularly. Every entry shows its last verification date for transparency.",
  },
  {
    icon: Shield,
    title: "Trustworthy Sources",
    description: "Every data point is cited with its source. We prioritize official program pages and documentation.",
  },
  {
    icon: Users,
    title: "Community-Driven",
    description: "Suggest corrections, additions, and new programs. Together we build the most complete affiliate resource.",
  },
];

export default function AboutPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      
      <main className="flex-1 py-8">
        <div className="container">
          <Breadcrumbs items={[{ label: "About" }]} />

          <div className="max-w-3xl">
            <h1 className="text-3xl font-bold text-foreground mb-6">About AffiliatePrograms.wiki</h1>
            
            <section className="mb-10">
              <p className="text-lg text-muted-foreground mb-4">
                AffiliatePrograms.wiki is a free, open reference site for affiliate marketers. Our mission is to provide accurate, comprehensive, and up-to-date information about affiliate programs, CPA networks, and performance marketing resources.
              </p>
              <p className="text-lg text-muted-foreground">
                Think of it as Wikipedia for affiliate marketing—a neutral, community-verified resource that helps you discover programs, compare terms, and make informed decisions about your affiliate partnerships.
              </p>
            </section>

            <section className="mb-10">
              <h2 className="wiki-heading text-xl">Our Values</h2>
              <div className="grid sm:grid-cols-2 gap-6">
                {values.map((value) => (
                  <div key={value.title} className="infobox">
                    <value.icon className="w-8 h-8 text-primary mb-3" />
                    <h3 className="font-semibold text-foreground mb-2">{value.title}</h3>
                    <p className="text-sm text-muted-foreground">{value.description}</p>
                  </div>
                ))}
              </div>
            </section>

            <section className="mb-10">
              <h2 className="wiki-heading text-xl">How We Verify Information</h2>
              <ol className="list-decimal list-inside space-y-3 text-muted-foreground">
                <li>We start with official program documentation and terms pages</li>
                <li>We cross-reference with network dashboards and public materials</li>
                <li>We note the verification date on every entry</li>
                <li>We encourage community corrections and updates</li>
                <li>We clearly mark when information may be outdated</li>
              </ol>
            </section>

            <section className="mb-10">
              <h2 className="wiki-heading text-xl">Suggest a Program</h2>
              <p className="text-muted-foreground mb-4">
                Know of an affiliate program we should add? Found an error in our data? We welcome all contributions.
              </p>
              <p className="text-muted-foreground">
                Email us at <a href="mailto:hello@affiliateprograms.wiki" className="wiki-link">hello@affiliateprograms.wiki</a> or submit a suggestion through our contribution form.
              </p>
            </section>

            <section>
              <h2 className="wiki-heading text-xl">Disclosure</h2>
              <p className="text-muted-foreground">
                AffiliatePrograms.wiki is an independent resource. We may participate in some affiliate programs featured on this site, but this does not influence our editorial decisions. All program information is presented objectively based on publicly available data.
              </p>
            </section>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
