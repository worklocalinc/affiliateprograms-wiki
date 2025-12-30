import { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ChevronRight, Globe, ChevronLeft } from "lucide-react";
import { getCountryPrograms } from "@/lib/api";
import { generateCountryMetadata, generateBreadcrumbJsonLd } from "@/lib/seo";
import { ProgramCard } from "@/components/program-card";

interface PageProps {
  params: Promise<{ country: string }>;
  searchParams: Promise<{ page?: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { country } = await params;
  const decodedCountry = decodeURIComponent(country);
  const data = await getCountryPrograms(decodedCountry);
  if (!data) return {};
  return generateCountryMetadata(decodedCountry, data.total);
}

export const revalidate = 300;

export default async function CountryPage({ params, searchParams }: PageProps) {
  const { country } = await params;
  const { page } = await searchParams;
  const decodedCountry = decodeURIComponent(country);

  const currentPage = Math.max(1, parseInt(page || "1", 10));
  const limit = 24;
  const offset = (currentPage - 1) * limit;

  const data = await getCountryPrograms(decodedCountry, { limit, offset });

  if (!data) {
    notFound();
  }

  const totalPages = Math.ceil(data.total / limit);

  const breadcrumbs = [
    { name: "Home", url: "https://affiliateprograms.wiki" },
    { name: "Countries", url: "https://affiliateprograms.wiki/countries" },
    {
      name: decodedCountry,
      url: `https://affiliateprograms.wiki/countries/${encodeURIComponent(decodedCountry)}`,
    },
  ];

  return (
    <>
      {/* JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(generateBreadcrumbJsonLd(breadcrumbs)),
        }}
      />

      <div className="space-y-8">
        {/* Breadcrumbs */}
        <nav className="flex items-center gap-2 text-sm text-gray-500">
          <Link href="/" className="hover:text-blue-600">
            Home
          </Link>
          <ChevronRight className="h-4 w-4" />
          <Link href="/countries" className="hover:text-blue-600">
            Countries
          </Link>
          <ChevronRight className="h-4 w-4" />
          <span className="text-gray-900">{decodedCountry}</span>
        </nav>

        {/* Header */}
        <div className="bg-white rounded-xl border shadow-sm p-6 md:p-8">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
              <Globe className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {decodedCountry} Affiliate Programs
              </h1>
              <p className="text-gray-600 mt-1">
                {data.total} affiliate programs available in {decodedCountry}
              </p>
            </div>
          </div>
        </div>

        {/* Programs Grid */}
        {data.items.length > 0 ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.items.map((program) => (
              <ProgramCard key={program.id} program={program} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg border">
            <Globe className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900">No programs found</h2>
            <p className="text-gray-600 mt-2">
              Browse{" "}
              <Link href="/programs" className="text-blue-600 hover:underline">
                all programs
              </Link>
            </p>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <nav className="flex items-center justify-center gap-2">
            {currentPage > 1 ? (
              <Link
                href={`/countries/${encodeURIComponent(decodedCountry)}?page=${currentPage - 1}`}
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
              Page {currentPage} of {totalPages}
            </span>

            {currentPage < totalPages ? (
              <Link
                href={`/countries/${encodeURIComponent(decodedCountry)}?page=${currentPage + 1}`}
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
    </>
  );
}
