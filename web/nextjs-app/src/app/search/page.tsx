import { Metadata } from "next";
import Link from "next/link";
import { Search as SearchIcon } from "lucide-react";
import { search } from "@/lib/api";
import { ProgramCard } from "@/components/program-card";

export const metadata: Metadata = {
  title: "Search Affiliate Programs",
  description: "Search our database of 36,000+ affiliate programs.",
  robots: {
    index: false, // Don't index search results
    follow: true,
  },
};

interface PageProps {
  searchParams: Promise<{ q?: string }>;
}

export default async function SearchPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const query = params.q || "";

  const results = query ? await search(query, 50) : { items: [], total: 0 };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Search Form */}
      <div className="bg-white rounded-xl border shadow-sm p-6 md:p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Search Programs</h1>
        <form action="/search" method="GET" className="flex gap-2">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              name="q"
              defaultValue={query}
              placeholder="Search by name, domain, or category..."
              className="w-full pl-12 pr-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
              autoFocus
            />
          </div>
          <button
            type="submit"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Search
          </button>
        </form>
      </div>

      {/* Results */}
      {query && (
        <div>
          <p className="text-gray-600 mb-4">
            {results.total > 0
              ? `Found ${results.total} programs for "${query}"`
              : `No results for "${query}"`}
          </p>

          {results.items.length > 0 ? (
            <div className="grid md:grid-cols-2 gap-4">
              {results.items.map((program) => (
                <ProgramCard key={program.id} program={program} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-lg border">
              <SearchIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-900">No results found</h2>
              <p className="text-gray-600 mt-2">
                Try different keywords or{" "}
                <Link href="/programs" className="text-blue-600 hover:underline">
                  browse all programs
                </Link>
              </p>
            </div>
          )}
        </div>
      )}

      {/* Popular searches when no query */}
      {!query && (
        <div className="bg-white rounded-xl border shadow-sm p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Popular Searches</h2>
          <div className="flex flex-wrap gap-2">
            {[
              "amazon",
              "shopify",
              "hosting",
              "vpn",
              "saas",
              "finance",
              "health",
              "travel",
            ].map((term) => (
              <Link
                key={term}
                href={`/search?q=${encodeURIComponent(term)}`}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                {term}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
