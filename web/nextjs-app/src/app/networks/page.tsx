import { Metadata } from "next";
import Link from "next/link";
import { Globe, ChevronRight, Building2 } from "lucide-react";
import { getNetworks } from "@/lib/api";
import type { Network } from "@/lib/api";

export const metadata: Metadata = {
  title: "Browse Affiliate Networks",
  description:
    "Browse affiliate networks including ShareASale, CJ Affiliate, Impact, Awin, and more. Find the best network for your affiliate marketing.",
  openGraph: {
    title: "Browse Affiliate Networks",
    description: "Browse affiliate networks and their programs.",
    url: "https://affiliateprograms.wiki/networks",
  },
  alternates: {
    canonical: "https://affiliateprograms.wiki/networks",
  },
};

export const revalidate = 300;

function NetworkCard({ network }: { network: Network }) {
  return (
    <Link
      href={`/networks/${network.slug}`}
      className="block bg-white rounded-lg border shadow-sm hover:shadow-md transition-shadow p-5"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 text-lg">{network.name}</h3>
          {network.website && (
            <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
              <Globe className="h-3.5 w-3.5" />
              {network.website.replace(/^https?:\/\//, "")}
            </p>
          )}
          {network.description && (
            <p className="text-gray-600 mt-2 text-sm line-clamp-2">{network.description}</p>
          )}
        </div>
        <ChevronRight className="h-5 w-5 text-gray-400 flex-shrink-0 mt-1" />
      </div>
      <div className="mt-4 pt-4 border-t flex items-center justify-between">
        <span className="text-sm font-medium text-blue-600">
          {network.program_count} programs
        </span>
        {network.countries && network.countries.length > 0 && (
          <span className="text-xs text-gray-500">
            {network.countries.length} countries
          </span>
        )}
      </div>
    </Link>
  );
}

export default async function NetworksPage() {
  const networksData = await getNetworks();

  // Sort by program count
  const networks = [...(networksData.items || [])].sort(
    (a, b) => (b.program_count || 0) - (a.program_count || 0)
  );

  // Calculate total programs across all networks
  const totalPrograms = networks.reduce((sum, n) => sum + (n.program_count || 0), 0);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Affiliate Networks</h1>
        <p className="text-gray-600 mt-1">
          {networks.length} affiliate networks with {totalPrograms.toLocaleString()} total programs
        </p>
      </div>

      {/* Networks Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {networks.map((network) => (
          <NetworkCard key={network.id} network={network} />
        ))}
      </div>

      {networks.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg border">
          <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">No networks found</h2>
          <p className="text-gray-600 mt-2">
            Check back soon for affiliate network listings.
          </p>
        </div>
      )}
    </div>
  );
}
