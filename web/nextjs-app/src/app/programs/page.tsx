import Link from "next/link";
import { Metadata } from "next";
import { Search, Filter, ChevronLeft, ChevronRight } from "lucide-react";
import { getPrograms, getStats } from "@/lib/api";
import { ProgramCard } from "@/components/program-card";

export const metadata: Metadata = {
  title: "Browse All Affiliate Programs",
  description:
    "Browse 36,000+ affiliate programs with commission rates, cookie durations, payout models, and direct signup links. Find the perfect program for your niche.",
  openGraph: {
    title: "Browse All Affiliate Programs",
    description: "Browse 36,000+ affiliate programs with commission rates and signup links.",
    url: "https://affiliateprograms.wiki/programs",
  },
  alternates: {
    canonical: "https://affiliateprograms.wiki/programs",
  },
};

export const revalidate = 300;

interface PageProps {
  searchParams: Promise<{ page?: string; q?: string }>;
}

export default async function ProgramsPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const page = Math.max(1, parseInt(params.page || "1", 10));
  const limit = 24;
  const offset = (page - 1) * limit;
  const query = params.q || "";

  const [programsData, stats] = await Promise.all([
    getPrograms({ limit, offset, q: query || undefined }),
    getStats(),
  ]);

  const totalPages = Math.ceil(programsData.total / limit);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Affiliate Programs</h1>
          <p className="text-gray-600 mt-1">
            {programsData.total.toLocaleString()} programs found
            {query && ` for "${query}"`}
          </p>
        </div>

        {/* Search Form */}
        <form action="/programs" method="GET" className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              name="q"
              defaultValue={query}
              placeholder="Search programs..."
              className="pl-10 pr-4 py-2 border rounded-lg w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Search
          </button>
        </form>
      </div>

      {/* Quick Stats */}
      <div className="flex flex-wrap gap-4 text-sm">
        <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full">
          {stats.programs.toLocaleString()} Total Programs
        </span>
        <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full">
          {stats.deep_researched.toLocaleString()} Deep Researched
        </span>
        <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full">
          {stats.categories} Categories
        </span>
        <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full">
          {stats.networks} Networks
        </span>
      </div>

      {/* Program Grid */}
      {programsData.items.length > 0 ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {programsData.items.map((program) => (
            <ProgramCard key={program.id} program={program} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg border">
          <Filter className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">No programs found</h2>
          <p className="text-gray-600 mt-2">
            Try adjusting your search or{" "}
            <Link href="/programs" className="text-blue-600 hover:underline">
              browse all programs
            </Link>
          </p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <nav className="flex items-center justify-center gap-2">
          {page > 1 ? (
            <Link
              href={`/programs?page=${page - 1}${query ? `&q=${encodeURIComponent(query)}` : ""}`}
              className="flex items-center gap-1 px-4 py-2 border rounded-lg hover:bg-gray-50 transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Link>
          ) : (
            <span className="flex items-center gap-1 px-4 py-2 border rounded-lg text-gray-400 cursor-not-allowed">
              <ChevronLeft className="h-4 w-4" />
              Previous
            </span>
          )}

          <span className="px-4 py-2 text-gray-600">
            Page {page} of {totalPages}
          </span>

          {page < totalPages ? (
            <Link
              href={`/programs?page=${page + 1}${query ? `&q=${encodeURIComponent(query)}` : ""}`}
              className="flex items-center gap-1 px-4 py-2 border rounded-lg hover:bg-gray-50 transition-colors"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Link>
          ) : (
            <span className="flex items-center gap-1 px-4 py-2 border rounded-lg text-gray-400 cursor-not-allowed">
              Next
              <ChevronRight className="h-4 w-4" />
            </span>
          )}
        </nav>
      )}
    </div>
  );
}
