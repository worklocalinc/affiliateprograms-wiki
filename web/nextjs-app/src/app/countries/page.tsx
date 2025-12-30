import { Metadata } from "next";
import Link from "next/link";
import { Globe, ChevronRight } from "lucide-react";
import { getCountries } from "@/lib/api";

export const metadata: Metadata = {
  title: "Browse by Country",
  description:
    "Browse affiliate programs by country. Find programs available in the United States, UK, Canada, Australia, and more.",
  openGraph: {
    title: "Browse Affiliate Programs by Country",
    description: "Browse affiliate programs available in your country.",
    url: "https://affiliateprograms.wiki/countries",
  },
  alternates: {
    canonical: "https://affiliateprograms.wiki/countries",
  },
};

export const revalidate = 300;

export default async function CountriesPage() {
  const countriesData = await getCountries();

  // Sort by program count
  const countries = [...countriesData.items].sort((a, b) => b.count - a.count);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Browse by Country</h1>
        <p className="text-gray-600 mt-1">
          Find affiliate programs available in your country
        </p>
      </div>

      {/* Countries Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {countries.map((item) => (
          <Link
            key={item.country}
            href={`/countries/${encodeURIComponent(item.country)}`}
            className="flex items-center justify-between p-4 bg-white rounded-lg border shadow-sm hover:shadow-md transition-shadow"
          >
            <span className="font-medium text-gray-900">{item.country}</span>
            <span className="text-sm text-gray-500">{item.count}</span>
          </Link>
        ))}
      </div>

      {countries.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg border">
          <Globe className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">No countries found</h2>
          <p className="text-gray-600 mt-2">
            Check back soon for country-specific listings.
          </p>
        </div>
      )}
    </div>
  );
}
