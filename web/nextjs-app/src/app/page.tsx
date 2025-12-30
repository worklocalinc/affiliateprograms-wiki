import Link from "next/link";
import { ArrowRight, TrendingUp, Globe, Layers, Building2 } from "lucide-react";
import { getStats, getPrograms, getCategories } from "@/lib/api";
import { ProgramCard } from "@/components/program-card";

export const revalidate = 300; // Revalidate every 5 minutes

export default async function HomePage() {
  const [stats, programsData, categories] = await Promise.all([
    getStats(),
    getPrograms({ limit: 6, has_deep_research: true }),
    getCategories(),
  ]);

  const topCategories = categories.slice(0, 8);

  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="text-center py-12">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
          Find the Perfect{" "}
          <span className="text-blue-600">Affiliate Program</span>
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
          Browse {stats.programs.toLocaleString()}+ affiliate programs with
          commission rates, cookie durations, and direct signup links.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/programs"
            className="inline-flex items-center justify-center px-6 py-3 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Browse Programs
            <ArrowRight className="ml-2 h-5 w-5" />
          </Link>
          <Link
            href="/categories"
            className="inline-flex items-center justify-center px-6 py-3 text-lg font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Explore Categories
          </Link>
        </div>
      </section>

      {/* Stats Section */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-6 border shadow-sm text-center">
          <TrendingUp className="h-8 w-8 text-blue-600 mx-auto mb-2" />
          <div className="text-3xl font-bold text-gray-900">
            {stats.programs.toLocaleString()}+
          </div>
          <div className="text-gray-500">Programs</div>
        </div>
        <div className="bg-white rounded-xl p-6 border shadow-sm text-center">
          <Globe className="h-8 w-8 text-green-600 mx-auto mb-2" />
          <div className="text-3xl font-bold text-gray-900">
            {stats.deep_researched.toLocaleString()}
          </div>
          <div className="text-gray-500">Deep Researched</div>
        </div>
        <div className="bg-white rounded-xl p-6 border shadow-sm text-center">
          <Layers className="h-8 w-8 text-purple-600 mx-auto mb-2" />
          <div className="text-3xl font-bold text-gray-900">
            {stats.categories}
          </div>
          <div className="text-gray-500">Categories</div>
        </div>
        <div className="bg-white rounded-xl p-6 border shadow-sm text-center">
          <Building2 className="h-8 w-8 text-orange-600 mx-auto mb-2" />
          <div className="text-3xl font-bold text-gray-900">
            {stats.networks}
          </div>
          <div className="text-gray-500">Networks</div>
        </div>
      </section>

      {/* Featured Programs */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">
            Recently Researched Programs
          </h2>
          <Link
            href="/programs"
            className="text-blue-600 hover:text-blue-700 font-medium inline-flex items-center"
          >
            View all
            <ArrowRight className="ml-1 h-4 w-4" />
          </Link>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {programsData.items.map((program) => (
            <ProgramCard key={program.id} program={program} />
          ))}
        </div>
      </section>

      {/* Categories */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">
            Browse by Category
          </h2>
          <Link
            href="/categories"
            className="text-blue-600 hover:text-blue-700 font-medium inline-flex items-center"
          >
            View all
            <ArrowRight className="ml-1 h-4 w-4" />
          </Link>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {topCategories.map((category) => (
            <Link
              key={category.id}
              href={`/categories/${category.slug}`}
              className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow"
            >
              <div className="text-2xl mb-2">{category.icon || "📁"}</div>
              <h3 className="font-semibold text-gray-900">{category.name}</h3>
              <p className="text-sm text-gray-500">
                {category.program_count} programs
              </p>
            </Link>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-blue-600 rounded-2xl p-8 md:p-12 text-center text-white">
        <h2 className="text-2xl md:text-3xl font-bold mb-4">
          Ready to Start Earning?
        </h2>
        <p className="text-blue-100 text-lg mb-6 max-w-2xl mx-auto">
          Find the perfect affiliate program for your niche. Our database is
          updated daily with the latest commission rates and program details.
        </p>
        <Link
          href="/programs"
          className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium text-blue-600 bg-white rounded-lg hover:bg-blue-50 transition-colors"
        >
          Get Started
          <ArrowRight className="ml-2 h-5 w-5" />
        </Link>
      </section>
    </div>
  );
}
