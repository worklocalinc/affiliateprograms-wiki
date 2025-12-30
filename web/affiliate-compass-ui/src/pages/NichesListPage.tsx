import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, Folder, FolderOpen, Loader2 } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { apiGet } from "@/lib/api";

interface Category {
  id: number;
  name: string;
  slug: string;
  path: string;
  depth: number;
  program_count: number;
  children: Category[];
}

interface CategoriesResponse {
  items: Category[];
  total: number;
}

function CategoryItem({ category, expanded, onToggle }: {
  category: Category;
  expanded: Set<number>;
  onToggle: (id: number) => void;
}) {
  const hasChildren = category.children && category.children.length > 0;
  const isExpanded = expanded.has(category.id);

  return (
    <div className="select-none">
      <div className="flex items-center gap-2 py-1.5 px-2 rounded hover:bg-muted/50 group">
        {hasChildren ? (
          <button
            onClick={() => onToggle(category.id)}
            className="p-0.5 hover:bg-muted rounded"
          >
            {isExpanded ? (
              <FolderOpen className="w-4 h-4 text-primary" />
            ) : (
              <Folder className="w-4 h-4 text-muted-foreground" />
            )}
          </button>
        ) : (
          <span className="w-5" />
        )}
        <Link
          to={`/niches/${category.slug}`}
          className="flex-1 flex items-center justify-between gap-2 text-foreground hover:text-primary transition-colors"
        >
          <span className="font-medium">{category.name}</span>
          <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
            {category.program_count}
          </span>
        </Link>
        <ChevronRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>

      {hasChildren && isExpanded && (
        <div className="ml-6 border-l border-border pl-2">
          {category.children.map((child) => (
            <CategoryItem
              key={child.id}
              category={child}
              expanded={expanded}
              onToggle={onToggle}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function NichesListPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  useEffect(() => {
    async function loadCategories() {
      try {
        const data = await apiGet<CategoriesResponse>("/categories");
        setCategories(data.items);
        // Auto-expand top-level categories
        setExpanded(new Set(data.items.map(c => c.id)));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load categories");
      } finally {
        setLoading(false);
      }
    }
    loadCategories();
  }, []);

  const toggleExpanded = (id: number) => {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const expandAll = () => {
    const allIds = new Set<number>();
    const collectIds = (cats: Category[]) => {
      cats.forEach(c => {
        allIds.add(c.id);
        if (c.children) collectIds(c.children);
      });
    };
    collectIds(categories);
    setExpanded(allIds);
  };

  const collapseAll = () => setExpanded(new Set());

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1 py-8">
        <div className="container">
          <Breadcrumbs items={[{ label: "Categories" }]} />

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-4">Browse Categories</h1>
            <p className="text-lg text-muted-foreground">
              Explore affiliate programs organized by industry and vertical. Click a category to see all programs.
            </p>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : error ? (
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg">
              {error}
            </div>
          ) : (
            <>
              <div className="flex gap-4 mb-6">
                <button
                  onClick={expandAll}
                  className="text-sm text-primary hover:underline"
                >
                  Expand All
                </button>
                <button
                  onClick={collapseAll}
                  className="text-sm text-primary hover:underline"
                >
                  Collapse All
                </button>
              </div>

              <div className="grid lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {categories.map((category) => (
                  <div key={category.id} className="bg-card border border-border rounded-lg p-4">
                    <CategoryItem
                      category={category}
                      expanded={expanded}
                      onToggle={toggleExpanded}
                    />
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
