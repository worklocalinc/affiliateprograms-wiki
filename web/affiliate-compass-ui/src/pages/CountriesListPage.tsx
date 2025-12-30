import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Globe, Loader2 } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { apiGet } from "@/lib/api";

interface Country {
  country: string;
  program_count: number;
}

interface CountriesResponse {
  items: Country[];
  total: number;
}

export default function CountriesListPage() {
  const [countries, setCountries] = useState<Country[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadCountries() {
      try {
        const data = await apiGet<CountriesResponse>("/countries");
        setCountries(data.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load countries");
      } finally {
        setLoading(false);
      }
    }
    loadCountries();
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1 py-8">
        <div className="container">
          <Breadcrumbs items={[{ label: "Countries" }]} />

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-4">Browse by Country</h1>
            <p className="text-lg text-muted-foreground">
              Find affiliate programs available in your country or target market.
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
            <div className="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
              {countries.map((c) => (
                <Link
                  key={c.country}
                  to={`/countries/${encodeURIComponent(c.country)}`}
                  className="flex items-center justify-between p-4 bg-card border border-border rounded-lg hover:border-primary/50 hover:shadow-sm transition-all group"
                >
                  <div className="flex items-center gap-3">
                    <Globe className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
                    <span className="font-medium group-hover:text-primary transition-colors">
                      {c.country}
                    </span>
                  </div>
                  <span className="text-sm text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                    {c.program_count.toLocaleString()}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
