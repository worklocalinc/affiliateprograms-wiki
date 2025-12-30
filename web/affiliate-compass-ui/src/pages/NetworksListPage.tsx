import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { SearchBar } from "@/components/SearchBar";
import { NetworkCard } from "@/components/NetworkCard";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";

type NetworkSummary = {
  id: number;
  name: string;
  slug: string;
  website: string | null;
  research_status: string | null;
  last_success_at: string | null;
};

type NetworksResponse = { items: NetworkSummary[] };

export default function NetworksListPage() {
  const { data } = useQuery({
    queryKey: ["networks"],
    queryFn: () => apiGet<NetworksResponse>("/networks"),
    staleTime: 30_000,
  });

  const networks = data?.items ?? [];

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      
      <main className="flex-1 py-8">
        <div className="container">
          <Breadcrumbs items={[{ label: "CPA Networks" }]} />

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-4">CPA Networks</h1>
            <p className="text-lg text-muted-foreground">
              Compare affiliate networks, tracking platforms, and partnership ecosystems.
            </p>
          </div>

          {/* Search */}
          <div className="max-w-xl mb-8">
            <SearchBar placeholder="Search networks..." />
          </div>

          {/* Results */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {networks.map((network) => (
              <NetworkCard
                key={network.slug}
                name={network.name}
                slug={network.slug}
                description={network.website ?? "CPA network"}
                offerTypes={["—"]}
                payoutFrequency="—"
                verified={network.last_success_at ? new Date(network.last_success_at).toLocaleDateString() : "—"}
              />
            ))}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
