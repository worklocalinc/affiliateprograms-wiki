import { Metadata } from "next";
import Link from "next/link";
import { Folder, ChevronRight } from "lucide-react";
import { getCategories } from "@/lib/api";
import type { Category } from "@/lib/api";

export const metadata: Metadata = {
  title: "Browse Categories",
  description:
    "Browse affiliate programs by category. Find programs in e-commerce, software, finance, health, and more.",
  openGraph: {
    title: "Browse Affiliate Program Categories",
    description: "Browse affiliate programs by category.",
    url: "https://affiliateprograms.wiki/categories",
  },
  alternates: {
    canonical: "https://affiliateprograms.wiki/categories",
  },
};

export const revalidate = 300;

function CategoryCard({ category }: { category: Category }) {
  return (
    <Link
      href={`/categories/${category.slug}`}
      className="block bg-white rounded-lg border shadow-sm hover:shadow-md transition-shadow p-4"
    >
      <div className="flex items-center gap-3">
        <span className="text-2xl">{category.icon || "📁"}</span>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 truncate">{category.name}</h3>
          <p className="text-sm text-gray-500">{category.program_count} programs</p>
        </div>
        <ChevronRight className="h-5 w-5 text-gray-400" />
      </div>
      {category.children && category.children.length > 0 && (
        <div className="mt-3 pt-3 border-t">
          <p className="text-xs text-gray-500 mb-2">
            {category.children.length} subcategories
          </p>
          <div className="flex flex-wrap gap-1">
            {category.children.slice(0, 3).map((child) => (
              <span
                key={child.id}
                className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded"
              >
                {child.name}
              </span>
            ))}
            {category.children.length > 3 && (
              <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded">
                +{category.children.length - 3}
              </span>
            )}
          </div>
        </div>
      )}
    </Link>
  );
}

export default async function CategoriesPage() {
  const categories = await getCategories();

  // Get top-level categories
  const topLevel = categories.filter((c) => c.depth === 0);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Browse by Category</h1>
        <p className="text-gray-600 mt-1">
          Find affiliate programs organized by industry and niche
        </p>
      </div>

      {/* Categories Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {topLevel.map((category) => (
          <CategoryCard key={category.id} category={category} />
        ))}
      </div>

      {topLevel.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg border">
          <Folder className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">No categories found</h2>
          <p className="text-gray-600 mt-2">
            Check back soon for organized categories.
          </p>
        </div>
      )}
    </div>
  );
}
