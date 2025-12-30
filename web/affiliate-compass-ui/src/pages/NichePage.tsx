import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowRight, ChevronRight, Loader2 } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { ProgramCard } from "@/components/ProgramCard";
import { Badge } from "@/components/ui/badge";
import { apiGet } from "@/lib/api";

interface Program {
  id: number;
  name: string;
  slug: string;
  domain: string;
  relevance_score: number;
  is_primary: boolean;
  commission_rate: string | null;
  cookie_duration_days: number | null;
  payout_model: string | null;
  tracking_platform: string | null;
  deep_researched_at: string | null;
}

interface CategoryInfo {
  id: number;
  name: string;
  slug: string;
  path: string;
  depth: number;
  parent_id: number | null;
  program_count: number;
  parent_name: string | null;
  parent_slug: string | null;
}

interface Subcategory {
  id: number;
  name: string;
  slug: string;
  program_count: number;
}

interface BreadcrumbItem {
  name: string;
  slug: string;
}

interface CategoryResponse {
  category: CategoryInfo;
  subcategories: Subcategory[];
  breadcrumbs: BreadcrumbItem[];
  programs: Program[];
  total: number;
  limit: number;
  offset: number;
}

export default function NichePage() {
  const { slug } = useParams();
  const [data, setData] = useState<CategoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const limit = 24;

  useEffect(() => {
    async function loadCategory() {
      if (!slug) return;
      setLoading(true);
      try {
        const result = await apiGet<CategoryResponse>(`/categories/${slug}`, { limit, offset });
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load category");
      } finally {
        setLoading(false);
      }
    }
    loadCategory();
  }, [slug, offset]);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </main>
        <Footer />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1 py-8">
          <div className="container">
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg">
              {error || "Category not found"}
            </div>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const { category, subcategories, breadcrumbs, programs, total } = data;

  const breadcrumbItems = [
    { label: "Categories", href: "/niches" },
    ...breadcrumbs.slice(0, -1).map(bc => ({
      label: bc.name,
      href: `/niches/${bc.slug}`,
    })),
    { label: category.name },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1 py-8">
        <div className="container">
          <Breadcrumbs items={breadcrumbItems} />

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">{category.name}</h1>
            <p className="text-muted-foreground">{category.path}</p>
            <Badge variant="secondary" className="mt-2">
              {total} programs
            </Badge>
          </div>

          {/* Subcategories */}
          {subcategories.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold mb-4">Subcategories</h2>
              <div className="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {subcategories.map((sub) => (
                  <Link
                    key={sub.id}
                    to={`/niches/${sub.slug}`}
                    className="flex items-center justify-between p-3 bg-card border border-border rounded-lg hover:border-primary/50 hover:shadow-sm transition-all group"
                  >
                    <span className="font-medium group-hover:text-primary transition-colors">
                      {sub.name}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {sub.program_count}
                    </span>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* Programs */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Programs</h2>
              {total > 0 && (
                <span className="text-sm text-muted-foreground">
                  Showing {offset + 1}-{Math.min(offset + limit, total)} of {total}
                </span>
              )}
            </div>

            {programs.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                No programs in this category yet.
                {subcategories.length > 0 && (
                  <p className="mt-2">Try browsing the subcategories above.</p>
                )}
              </div>
            ) : (
              <>
                <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4 mb-6">
                  {programs.map((program) => (
                    <ProgramCard
                      key={program.id}
                      name={program.name}
                      slug={program.slug}
                      description={program.domain}
                      payoutModel={program.payout_model || undefined}
                      commission={program.commission_rate || undefined}
                      cookieLength={program.cookie_duration_days ? `${program.cookie_duration_days} days` : undefined}
                      network={program.tracking_platform || undefined}
                      verified={program.deep_researched_at ? new Date(program.deep_researched_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : undefined}
                    />
                  ))}
                </div>

                {/* Pagination */}
                {total > limit && (
                  <div className="flex justify-center gap-2">
                    <button
                      onClick={() => setOffset(Math.max(0, offset - limit))}
                      disabled={offset === 0}
                      className="px-4 py-2 bg-muted rounded hover:bg-muted/80 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setOffset(offset + limit)}
                      disabled={offset + limit >= total}
                      className="px-4 py-2 bg-muted rounded hover:bg-muted/80 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            )}
          </section>

          {/* Parent category link */}
          {category.parent_slug && (
            <div className="mt-10 pt-6 border-t border-border">
              <Link
                to={`/niches/${category.parent_slug}`}
                className="inline-flex items-center gap-2 text-primary hover:underline"
              >
                <ArrowRight className="w-4 h-4 rotate-180" />
                Back to {category.parent_name}
              </Link>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
