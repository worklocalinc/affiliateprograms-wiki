import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Globe, Loader2 } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { ProgramCard } from "@/components/ProgramCard";
import { Badge } from "@/components/ui/badge";
import { apiGet } from "@/lib/api";

interface Program {
  id: number;
  name: string;
  slug: string;
  domain: string;
  countries: string[];
  commission_rate: string | null;
  cookie_duration_days: number | null;
  payout_model: string | null;
  tracking_platform: string | null;
  deep_researched_at: string | null;
}

interface CountryResponse {
  country: string;
  programs: Program[];
  total: number;
  limit: number;
  offset: number;
}

export default function CountryPage() {
  const { country } = useParams();
  const [data, setData] = useState<CountryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const limit = 24;

  useEffect(() => {
    async function loadCountry() {
      if (!country) return;
      setLoading(true);
      try {
        const result = await apiGet<CountryResponse>(
          `/countries/${encodeURIComponent(country)}`,
          { limit, offset }
        );
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load country");
      } finally {
        setLoading(false);
      }
    }
    loadCountry();
  }, [country, offset]);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </main>
        <Footer />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1 py-8">
          <div className="container">
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg">
              {error || "Country not found"}
            </div>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const { programs, total } = data;
  const decodedCountry = decodeURIComponent(country || "");

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1 py-8">
        <div className="container">
          <Breadcrumbs
            items={[
              { label: "Countries", href: "/countries" },
              { label: decodedCountry },
            ]}
          />

          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <Globe className="w-8 h-8 text-primary" />
              <h1 className="text-3xl font-bold text-foreground">{decodedCountry}</h1>
            </div>
            <Badge variant="secondary">{total.toLocaleString()} programs</Badge>
          </div>

          {programs.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No programs found for this country.
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Programs</h2>
                <span className="text-sm text-muted-foreground">
                  Showing {offset + 1}-{Math.min(offset + limit, total)} of {total.toLocaleString()}
                </span>
              </div>

              <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4 mb-6">
                {programs.map((program) => (
                  <ProgramCard
                    key={program.id}
                    name={program.name}
                    slug={program.slug}
                    description={program.domain}
                    payoutModel={program.payout_model || undefined}
                    commission={program.commission_rate || undefined}
                    cookieLength={
                      program.cookie_duration_days
                        ? `${program.cookie_duration_days} days`
                        : undefined
                    }
                    network={program.tracking_platform || undefined}
                    verified={
                      program.deep_researched_at
                        ? new Date(program.deep_researched_at).toLocaleDateString("en-US", {
                            month: "short",
                            year: "numeric",
                          })
                        : undefined
                    }
                  />
                ))}
              </div>

              {/* Pagination */}
              {total > limit && (
                <div className="flex justify-center gap-2">
                  <button
                    onClick={() => setOffset(Math.max(0, offset - limit))}
                    disabled={offset === 0}
                    className="px-4 py-2 bg-muted rounded hover:bg-muted/80 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setOffset(offset + limit)}
                    disabled={offset + limit >= total}
                    className="px-4 py-2 bg-muted rounded hover:bg-muted/80 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
