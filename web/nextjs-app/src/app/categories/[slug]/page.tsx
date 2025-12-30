import { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ChevronRight, Folder } from "lucide-react";
import { getCategory } from "@/lib/api";
import { generateCategoryMetadata, generateCategoryJsonLd, generateBreadcrumbJsonLd } from "@/lib/seo";
import { ProgramCard } from "@/components/program-card";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const data = await getCategory(slug);
  if (!data) return {};
  return generateCategoryMetadata(data.category, data.programs.length);
}

export const revalidate = 300;

export default async function CategoryPage({ params }: PageProps) {
  const { slug } = await params;
  const data = await getCategory(slug);

  if (!data) {
    notFound();
  }

  const { category, programs, breadcrumbs } = data;

  const breadcrumbItems = [
    { name: "Home", url: "https://affiliateprograms.wiki" },
    { name: "Categories", url: "https://affiliateprograms.wiki/categories" },
    ...breadcrumbs.map((b) => ({
      name: b.name,
      url: `https://affiliateprograms.wiki/categories/${b.slug}`,
    })),
  ];

  return (
    <>
      {/* JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(generateCategoryJsonLd(category, programs)),
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(generateBreadcrumbJsonLd(breadcrumbItems)),
        }}
      />

      <div className="space-y-8">
        {/* Breadcrumbs */}
        <nav className="flex items-center gap-2 text-sm text-gray-500 flex-wrap">
          <Link href="/" className="hover:text-blue-600">
            Home
          </Link>
          <ChevronRight className="h-4 w-4" />
          <Link href="/categories" className="hover:text-blue-600">
            Categories
          </Link>
          {breadcrumbs.map((b) => (
            <span key={b.id} className="flex items-center gap-2">
              <ChevronRight className="h-4 w-4" />
              {b.slug === slug ? (
                <span className="text-gray-900">{b.name}</span>
              ) : (
                <Link href={`/categories/${b.slug}`} className="hover:text-blue-600">
                  {b.name}
                </Link>
              )}
            </span>
          ))}
        </nav>

        {/* Header */}
        <div className="bg-white rounded-xl border shadow-sm p-6 md:p-8">
          <div className="flex items-center gap-4">
            <span className="text-4xl">{category.icon || "📁"}</span>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{category.name}</h1>
              <p className="text-gray-600 mt-1">
                {programs.length} affiliate programs
              </p>
            </div>
          </div>
          {category.description && (
            <p className="mt-4 text-gray-700">{category.description}</p>
          )}
        </div>

        {/* Subcategories */}
        {category.children && category.children.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Subcategories</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {category.children.map((child) => (
                <Link
                  key={child.id}
                  href={`/categories/${child.slug}`}
                  className="flex items-center gap-2 p-3 bg-white rounded-lg border hover:shadow-md transition-shadow"
                >
                  <span>{child.icon || "📁"}</span>
                  <div className="min-w-0">
                    <p className="font-medium text-gray-900 truncate">{child.name}</p>
                    <p className="text-xs text-gray-500">{child.program_count} programs</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Programs */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Programs in {category.name}
          </h2>
          {programs.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {programs.map((program) => (
                <ProgramCard key={program.id} program={program} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-lg border">
              <Folder className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900">No programs yet</h3>
              <p className="text-gray-600 mt-2">
                Check subcategories or browse{" "}
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
