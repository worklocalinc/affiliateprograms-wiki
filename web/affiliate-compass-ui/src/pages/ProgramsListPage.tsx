import { useMemo, useState } from "react";
import { Filter, SortAsc } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { SearchBar } from "@/components/SearchBar";
import { ProgramCard } from "@/components/ProgramCard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";

type ProgramSummary = {
  id: number;
  name: string;
  slug: string;
  domain: string | null;
  partner_type: string | null;
  research_status: string;
  last_success_at: string | null;
  // Deep research fields
  commission_rate?: string | null;
  cookie_duration_days?: number | null;
  payout_model?: string | null;
  tracking_platform?: string | null;
  minimum_payout?: string | null;
  signup_url?: string | null;
  deep_researched_at?: string | null;
  // Legacy fallback
  commission?: string | null;
  cookie_length_days?: string | null;
  payout_models?: unknown;
};

type ProgramsResponse = {
  items: ProgramSummary[];
  total: number;
  limit: number;
  offset: number;
};

const filterOptions = {
  payoutModel: ["CPA", "Recurring", "CPA + Recurring", "RevShare"],
  network: ["Direct", "CJ", "Impact", "ShareASale", "Awin"],
  cookieLength: ["24 hours", "7 days", "30 days", "60 days", "90+ days"],
};

export default function ProgramsListPage() {
  const [activeFilters, setActiveFilters] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [query, setQuery] = useState("");

  const { data } = useQuery({
    queryKey: ["programs", query],
    queryFn: () => apiGet<ProgramsResponse>("/programs", { q: query, limit: 60, offset: 0 }),
    staleTime: 10_000,
  });

  const programs = useMemo(() => data?.items ?? [], [data]);

  const toggleFilter = (filter: string) => {
    setActiveFilters(prev => 
      prev.includes(filter) 
        ? prev.filter(f => f !== filter)
        : [...prev, filter]
    );
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      
      <main className="flex-1 py-8">
        <div className="container">
          <Breadcrumbs items={[{ label: "Programs" }]} />

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-4">Affiliate Programs</h1>
            <p className="text-lg text-muted-foreground">
              Browse and compare {data?.total?.toLocaleString() ?? "—"} affiliate programs across all niches.
            </p>
          </div>

          {/* Search and Filters */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="flex-1">
              <SearchBar placeholder="Search programs..." value={query} onValueChange={setQuery} />
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                onClick={() => setShowFilters(!showFilters)}
                className="gap-2"
              >
                <Filter className="w-4 h-4" />
                Filters
                {activeFilters.length > 0 && (
                  <Badge variant="default" className="ml-1">{activeFilters.length}</Badge>
                )}
              </Button>
              <Button variant="outline" className="gap-2">
                <SortAsc className="w-4 h-4" />
                Sort
              </Button>
            </div>
          </div>

          {/* Filter Panel */}
          {showFilters && (
            <div className="bg-card border border-border rounded-lg p-4 mb-6 animate-fade-in">
              <div className="grid sm:grid-cols-3 gap-6">
                <div>
                  <h4 className="font-medium text-foreground mb-2 text-sm">Payout Model</h4>
                  <div className="flex flex-wrap gap-2">
                    {filterOptions.payoutModel.map((option) => (
                      <Badge
                        key={option}
                        variant={activeFilters.includes(option) ? "default" : "outline"}
                        className="cursor-pointer"
                        onClick={() => toggleFilter(option)}
                      >
                        {option}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="font-medium text-foreground mb-2 text-sm">Network</h4>
                  <div className="flex flex-wrap gap-2">
                    {filterOptions.network.map((option) => (
                      <Badge
                        key={option}
                        variant={activeFilters.includes(option) ? "default" : "outline"}
                        className="cursor-pointer"
                        onClick={() => toggleFilter(option)}
                      >
                        {option}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="font-medium text-foreground mb-2 text-sm">Cookie Length</h4>
                  <div className="flex flex-wrap gap-2">
                    {filterOptions.cookieLength.map((option) => (
                      <Badge
                        key={option}
                        variant={activeFilters.includes(option) ? "default" : "outline"}
                        className="cursor-pointer"
                        onClick={() => toggleFilter(option)}
                      >
                        {option}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
              {activeFilters.length > 0 && (
                <div className="mt-4 pt-4 border-t border-border">
                  <Button variant="ghost" size="sm" onClick={() => setActiveFilters([])}>
                    Clear all filters
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Results */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {programs.map((program) => (
              <ProgramCard
                key={program.slug}
                name={program.name}
                slug={program.slug}
                description={program.domain ? `Website: ${program.domain}` : "Seeded program record"}
                payoutModel={program.payout_model ?? (Array.isArray(program.payout_models) ? (program.payout_models as string[]).join(" + ") : "—")}
                commission={program.commission_rate ?? program.commission ?? "—"}
                cookieLength={program.cookie_duration_days ? `${program.cookie_duration_days} days` : (program.cookie_length_days ? `${program.cookie_length_days} days` : "—")}
                network={program.tracking_platform ?? program.partner_type ?? "—"}
                verified={program.deep_researched_at ? new Date(program.deep_researched_at).toLocaleDateString() : (program.last_success_at ? new Date(program.last_success_at).toLocaleDateString() : "—")}
              />
            ))}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
