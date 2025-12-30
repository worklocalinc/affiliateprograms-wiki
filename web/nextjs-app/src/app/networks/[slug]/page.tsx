import { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ChevronRight, Globe, ExternalLink, Building2 } from "lucide-react";
import { getNetwork, browse } from "@/lib/api";
import { generateNetworkMetadata, generateNetworkJsonLd, generateBreadcrumbJsonLd } from "@/lib/seo";
import { ProgramCard } from "@/components/program-card";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const network = await getNetwork(slug);
  if (!network) return {};
  return generateNetworkMetadata(network);
}

export const revalidate = 300;

export default async function NetworkPage({ params }: PageProps) {
  const { slug } = await params;
  const network = await getNetwork(slug);

  if (!network) {
    notFound();
  }

  // Get programs from this network
  const programsData = await browse({ network: network.name, limit: 50 });

  const breadcrumbs = [
    { name: "Home", url: "https://affiliateprograms.wiki" },
    { name: "Networks", url: "https://affiliateprograms.wiki/networks" },
    { name: network.name, url: `https://affiliateprograms.wiki/networks/${network.slug}` },
  ];

  return (
    <>
      {/* JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(generateNetworkJsonLd(network)),
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(generateBreadcrumbJsonLd(breadcrumbs)),
        }}
      />

      <div className="max-w-4xl mx-auto space-y-8">
        {/* Breadcrumbs */}
        <nav className="flex items-center gap-2 text-sm text-gray-500">
          <Link href="/" className="hover:text-blue-600">
            Home
          </Link>
          <ChevronRight className="h-4 w-4" />
          <Link href="/networks" className="hover:text-blue-600">
            Networks
          </Link>
          <ChevronRight className="h-4 w-4" />
          <span className="text-gray-900">{network.name}</span>
        </nav>

        {/* Header */}
        <div className="bg-white rounded-xl border shadow-sm p-6 md:p-8">
          <div className="flex flex-col md:flex-row md:items-start gap-6">
            {/* Icon */}
            <div className="flex-shrink-0 w-16 h-16 bg-blue-100 rounded-xl flex items-center justify-center">
              <Building2 className="h-8 w-8 text-blue-600" />
            </div>

            {/* Info */}
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900">{network.name}</h1>
              {network.website && (
                <a
                  href={network.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline flex items-center gap-1 mt-1"
                >
                  <Globe className="h-4 w-4" />
                  {network.website.replace(/^https?:\/\//, "")}
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
              {network.description && (
                <p className="mt-4 text-gray-700">{network.description}</p>
              )}

              {/* Stats */}
              <div className="mt-4 flex flex-wrap gap-4">
                <span className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded-full font-medium">
                  {network.program_count} Programs
                </span>
                {network.countries && network.countries.length > 0 && (
                  <span className="px-3 py-1.5 bg-green-100 text-green-700 rounded-full font-medium">
                    {network.countries.length} Countries
                  </span>
                )}
              </div>
            </div>

            {/* CTA */}
            {network.website && (
              <div className="flex-shrink-0">
                <a
                  href={network.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Visit Network
                  <ExternalLink className="h-4 w-4" />
                </a>
              </div>
            )}
          </div>
        </div>

        {/* Countries */}
        {network.countries && network.countries.length > 0 && (
          <div className="bg-white rounded-xl border shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Available Countries</h2>
            <div className="flex flex-wrap gap-2">
              {network.countries.slice(0, 20).map((country) => (
                <Link
                  key={country}
                  href={`/countries/${encodeURIComponent(country)}`}
                  className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200 transition-colors"
                >
                  {country}
                </Link>
              ))}
              {network.countries.length > 20 && (
                <span className="px-3 py-1 bg-gray-100 text-gray-500 rounded-full text-sm">
                  +{network.countries.length - 20} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Programs */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Programs on {network.name}
          </h2>
          {programsData.items.length > 0 ? (
            <div className="grid md:grid-cols-2 gap-4">
              {programsData.items.map((program) => (
                <ProgramCard key={program.id} program={program} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-lg border">
              <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900">No programs listed yet</h3>
              <p className="text-gray-600 mt-2">
                Browse{" "}
                <Link href="/programs" className="text-blue-600 hover:underline">
                  all programs
                </Link>
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
