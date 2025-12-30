import { useParams } from "react-router-dom";
import { ExternalLink } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Infobox } from "@/components/Infobox";
import { TableOfContents } from "@/components/TableOfContents";
import { SourceList } from "@/components/Citation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiGet } from "@/lib/api";

type Evidence = { url?: string; final_url?: string; status?: number; ok?: boolean };

type ProgramDetail = {
  id: number;
  name: string;
  slug: string;
  domain: string | null;
  domains: string[] | null;
  countries: string[] | null;
  partner_type: string | null;
  verticals: unknown;
  metadata: unknown;
  research_status: string;
  last_success_at: string | null;
  last_attempt_at: string | null;
  // Deep research fields
  commission_rate: string | null;
  cookie_duration_days: number | null;
  payout_model: string | null;
  tracking_platform: string | null;
  minimum_payout: string | null;
  payment_methods: string[] | null;
  payment_frequency: string | null;
  requirements: string | null;
  restrictions: string[] | null;
  signup_url: string | null;
  notes: string | null;
  deep_researched_at: string | null;
  deep_research_model: string | null;
  extracted: Record<string, unknown> | null;
  evidence: Evidence[] | null;
};

const tocItems = [
  { id: "overview", label: "Overview", level: 1 },
  { id: "how-to-join", label: "How to Join", level: 1 },
  { id: "tracking", label: "Tracking & Attribution", level: 1 },
  { id: "sources", label: "Sources", level: 1 },
];

export default function ProgramPage() {
  const { slug } = useParams();
  const { data } = useQuery({
    queryKey: ["program", slug],
    queryFn: () => apiGet<ProgramDetail>(`/programs/${slug}`),
    enabled: Boolean(slug),
    staleTime: 30_000,
  });

  // Deep research fields (preferred)
  const signupUrl = data?.signup_url ?? null;
  const commissionRate = data?.commission_rate ?? null;
  const cookieDays = data?.cookie_duration_days ?? null;
  const payoutModel = data?.payout_model ?? null;
  const trackingPlatform = data?.tracking_platform ?? null;
  const minimumPayout = data?.minimum_payout ?? null;
  const paymentMethods = data?.payment_methods ?? [];
  const paymentFrequency = data?.payment_frequency ?? null;
  const requirements = data?.requirements ?? null;
  const restrictions = data?.restrictions ?? [];
  const notes = data?.notes ?? null;
  const deepResearchedAt = data?.deep_researched_at;

  // Legacy fallback
  const bestUrl = signupUrl || (data?.extracted && typeof data.extracted.best_url === "string" ? (data.extracted.best_url as string) : null);
  const fields = (data?.extracted?.fields ?? null) as Record<string, unknown> | null;
  const legacyCookieDays = fields && typeof fields.cookie_length_days === "number" ? (fields.cookie_length_days as number) : null;
  const legacyPayoutModels = fields && Array.isArray(fields.payout_models) ? (fields.payout_models as string[]) : [];
  const legacyCommission = fields && typeof fields.commission === "string" ? (fields.commission as string) : null;

  // Use deep research data if available, otherwise fall back to legacy
  const displayCommission = commissionRate ?? legacyCommission;
  const displayCookieDays = cookieDays ?? legacyCookieDays;
  const displayPayoutModel = payoutModel ?? (legacyPayoutModels.length ? legacyPayoutModels.join(" + ") : null);

  const verified = deepResearchedAt ? new Date(deepResearchedAt).toLocaleDateString() : (data?.last_success_at ? new Date(data.last_success_at).toLocaleDateString() : "—");
  const website = data?.domain ? `https://${data.domain}` : "";

  const sources =
    (data?.evidence || [])
      .filter((e) => e?.final_url || e?.url)
      .slice(0, 25)
      .map((e, idx) => ({
        id: idx + 1,
        source: e.final_url || e.url || "evidence",
        url: e.final_url || e.url || "",
        date: data?.last_attempt_at ? new Date(data.last_attempt_at).toLocaleDateString() : "—",
      })) || [];

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1 py-8">
        <div className="container">
          <Breadcrumbs
            items={[
              { label: "Programs", href: "/programs" },
              { label: data?.name ?? "Program" },
            ]}
          />

          <div className="grid lg:grid-cols-[1fr_280px] gap-8">
            <div className="min-w-0">
              <h1 className="text-3xl font-bold text-foreground mb-6">{data?.name ?? "Loading…"}</h1>

              <div className="lg:hidden mb-8">
                <Infobox
                  title={data?.name ?? "—"}
                  website={website}
                  verified={verified}
                  rows={[
                    { label: "Commission", value: displayCommission ?? "—" },
                    { label: "Cookie Length", value: displayCookieDays ? `${displayCookieDays} days` : "—" },
                    { label: "Payout Model", value: displayPayoutModel ?? "—" },
                    { label: "Tracking Platform", value: trackingPlatform ?? "—" },
                    { label: "Minimum Payout", value: minimumPayout ?? "—" },
                    { label: "Payment Methods", value: paymentMethods.length ? paymentMethods.join(", ") : "—" },
                    { label: "Payment Frequency", value: paymentFrequency ?? "—" },
                    { label: "Domain", value: data?.domain ?? "—" },
                    {
                      label: "Signup URL",
                      value: bestUrl ? (
                        <a className="wiki-link" href={bestUrl} target="_blank" rel="noopener noreferrer">
                          Apply Now
                        </a>
                      ) : (
                        "—"
                      ),
                    },
                  ]}
                />
              </div>

              <section id="overview" className="mb-10">
                <h2 className="wiki-heading text-xl">Overview</h2>
                {notes ? (
                  <p className="text-muted-foreground leading-relaxed">{notes}</p>
                ) : (
                  <p className="text-muted-foreground leading-relaxed">
                    {data?.name} offers an affiliate program allowing partners to earn commissions by promoting their products or services.
                    {displayCommission && ` Commission rates are ${displayCommission}.`}
                    {displayCookieDays && ` Cookies are tracked for ${displayCookieDays} days.`}
                  </p>
                )}
                {requirements && (
                  <div className="mt-4 bg-muted/50 rounded-lg p-4">
                    <h3 className="font-medium text-foreground mb-2">Requirements</h3>
                    <p className="text-sm text-muted-foreground">{requirements}</p>
                  </div>
                )}
                {restrictions.length > 0 && (
                  <div className="mt-4 bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
                    <h3 className="font-medium text-foreground mb-2">Restrictions</h3>
                    <ul className="text-sm text-muted-foreground list-disc list-inside">
                      {restrictions.map((r, i) => <li key={i}>{r}</li>)}
                    </ul>
                  </div>
                )}
              </section>

              <section id="how-to-join" className="mb-10">
                <h2 className="wiki-heading text-xl">How to Join</h2>
                <div className="bg-muted/50 rounded-lg p-4 mb-4">
                  <p className="text-sm text-muted-foreground">
                    Start at the program website and look for “Affiliate”, “Partner”, or “Referral” pages. Use the best candidate page below
                    if available.
                  </p>
                </div>
                <ol className="list-decimal list-inside space-y-2 text-muted-foreground mb-4">
                  <li>Visit the program’s main site</li>
                  <li>Find the official affiliate/partner page</li>
                  <li>Apply and follow onboarding</li>
                </ol>
                <div className="flex gap-3">
                  {bestUrl && (
                    <Button asChild>
                      <a href={bestUrl} target="_blank" rel="noopener noreferrer">
                        Best Candidate Page <ExternalLink className="w-4 h-4 ml-2" />
                      </a>
                    </Button>
                  )}
                  {website && (
                    <Button variant="outline" asChild>
                      <a href={website} target="_blank" rel="noopener noreferrer">
                        Website <ExternalLink className="w-4 h-4 ml-2" />
                      </a>
                    </Button>
                  )}
                </div>
              </section>

              <section id="tracking" className="mb-10">
                <h2 className="wiki-heading text-xl">Tracking & Attribution</h2>
                {trackingPlatform ? (
                  <div className="space-y-3">
                    <p className="text-muted-foreground">
                      This program uses <strong className="text-foreground">{trackingPlatform}</strong> for affiliate tracking.
                    </p>
                    {displayCookieDays && (
                      <p className="text-muted-foreground">
                        Cookie duration: <strong className="text-foreground">{displayCookieDays} days</strong>
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-muted-foreground">Tracking platform information not yet available.</p>
                )}
              </section>

              <section id="sources" className="mb-10">
                <h2 className="wiki-heading text-xl">Sources</h2>
                <SourceList sources={sources} />
              </section>
            </div>

            <aside className="hidden lg:block space-y-8">
              <Infobox
                title={data?.name ?? "—"}
                website={website}
                verified={verified}
                rows={[
                  { label: "Commission", value: displayCommission ?? "—" },
                  { label: "Cookie Length", value: displayCookieDays ? `${displayCookieDays} days` : "—" },
                  { label: "Payout Model", value: displayPayoutModel ?? "—" },
                  { label: "Tracking Platform", value: trackingPlatform ?? "—" },
                  { label: "Minimum Payout", value: minimumPayout ?? "—" },
                  { label: "Payment Methods", value: paymentMethods.length ? paymentMethods.join(", ") : "—" },
                  { label: "Payment Frequency", value: paymentFrequency ?? "—" },
                  { label: "Domain", value: data?.domain ?? "—" },
                  {
                    label: "Signup URL",
                    value: bestUrl ? (
                      <a className="wiki-link" href={bestUrl} target="_blank" rel="noopener noreferrer">
                        Apply Now
                      </a>
                    ) : (
                      "—"
                    ),
                  },
                ]}
              />
              <TableOfContents items={tocItems} />
            </aside>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
