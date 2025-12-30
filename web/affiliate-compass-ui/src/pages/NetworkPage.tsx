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

type NetworkDetail = {
  id: number;
  name: string;
  slug: string;
  website: string | null;
  countries: string[] | null;
  research_status: string | null;
  last_success_at: string | null;
  last_attempt_at: string | null;
  extracted: Record<string, unknown> | null;
  evidence: unknown;
};

const tocItems = [
  { id: "overview", label: "Overview", level: 1 },
  { id: "sources", label: "Sources", level: 1 },
];

export default function NetworkPage() {
  const { slug } = useParams();
  const { data } = useQuery({
    queryKey: ["network", slug],
    queryFn: () => apiGet<NetworkDetail>(`/networks/${slug}`),
    enabled: Boolean(slug),
    staleTime: 30_000,
  });

  const verified = data?.last_success_at ? new Date(data.last_success_at).toLocaleDateString() : "—";
  const website = data?.website ?? "";

  const evidence = Array.isArray(data?.evidence) ? (data?.evidence as Array<Record<string, unknown>>) : [];
  const sources = evidence
    .filter((e) => typeof e?.final_url === "string" || typeof e?.url === "string")
    .slice(0, 25)
    .map((e, idx: number) => ({
      id: idx + 1,
      source: (e.final_url as string) || (e.url as string) || "evidence",
      url: (e.final_url as string) || (e.url as string) || "",
      date: data?.last_attempt_at ? new Date(data.last_attempt_at).toLocaleDateString() : "—",
    }));

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1 py-8">
        <div className="container">
          <Breadcrumbs items={[{ label: "CPA Networks", href: "/networks" }, { label: data?.name ?? "Network" }]} />

          <div className="grid lg:grid-cols-[1fr_280px] gap-8">
            <div className="min-w-0">
              <h1 className="text-3xl font-bold text-foreground mb-6">{data?.name ?? "Loading…"}</h1>

              <div className="lg:hidden mb-8">
                <Infobox
                  title={data?.name ?? "—"}
                  website={website}
                  verified={verified}
                  rows={[
                    { label: "Website", value: website ? <a className="wiki-link" href={website} target="_blank" rel="noopener noreferrer">{website}</a> : "—" },
                    { label: "Research Status", value: <Badge variant="secondary">{data?.research_status ?? "—"}</Badge> },
                    { label: "Countries", value: data?.countries?.length ? `${data.countries.length}` : "—" },
                  ]}
                />
              </div>

              <section id="overview" className="mb-10">
                <h2 className="wiki-heading text-xl">Overview</h2>
                <p className="text-muted-foreground leading-relaxed">
                  This network entry is currently a curated seed record. Detailed offer catalog, tracking specs, and policies will be added
                  during enrichment.
                </p>
                {website && (
                  <div className="mt-4">
                    <Button asChild>
                      <a href={website} target="_blank" rel="noopener noreferrer">
                        Visit Website <ExternalLink className="w-4 h-4 ml-2" />
                      </a>
                    </Button>
                  </div>
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
                  { label: "Website", value: website ? <a className="wiki-link" href={website} target="_blank" rel="noopener noreferrer">{website}</a> : "—" },
                  { label: "Research Status", value: <Badge variant="secondary">{data?.research_status ?? "—"}</Badge> },
                  { label: "Countries", value: data?.countries?.length ? `${data.countries.length}` : "—" },
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
