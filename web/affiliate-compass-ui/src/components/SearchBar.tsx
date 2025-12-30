import { useState, useRef, useEffect } from "react";
import { Search, X, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { apiGet } from "@/lib/api";

interface SearchResult {
  type: "program" | "network" | "niche";
  name: string;
  slug: string;
  description?: string;
}

type SearchResponse = { items: SearchResult[] };

interface SearchBarProps {
  size?: "default" | "large";
  placeholder?: string;
  className?: string;
  value?: string;
  onValueChange?: (value: string) => void;
}

export function SearchBar({ size = "default", placeholder = "Search programs, networks, niches…", className, value, onValueChange }: SearchBarProps) {
  const [uncontrolledQuery, setUncontrolledQuery] = useState("");
  const query = value ?? uncontrolledQuery;
  const setQuery = (v: string) => {
    if (onValueChange) onValueChange(v);
    if (value === undefined) setUncontrolledQuery(v);
  };
  const [isOpen, setIsOpen] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    const ac = new AbortController();
    const t = setTimeout(async () => {
      try {
        const data = await apiGet<SearchResponse>("/search", { q, limit: 10 }, ac.signal);
        setResults(data.items || []);
        setIsOpen(true);
      } catch {
        setResults([]);
        setIsOpen(true);
      }
    }, 150);

    return () => {
      ac.abort();
      clearTimeout(t);
    };
  }, [query]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const getResultLink = (result: SearchResult) => {
    switch (result.type) {
      case "program": return `/programs/${result.slug}`;
      case "network": return `/networks/${result.slug}`;
      case "niche": return `/niches/${result.slug}`;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case "program": return "Program";
      case "network": return "Network";
      case "niche": return "Niche";
    }
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <div className={`relative ${size === "large" ? "text-lg" : ""}`}>
        <Search className={`absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground ${size === "large" ? "w-5 h-5" : "w-4 h-4"}`} />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className={`search-input ${size === "large" ? "pl-12 pr-12 py-4 text-lg" : "pl-10 pr-10 py-2.5"}`}
          onFocus={() => query.length >= 2 && setIsOpen(true)}
        />
        {query && (
          <button
            onClick={() => { setQuery(""); setIsOpen(false); }}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className={size === "large" ? "w-5 h-5" : "w-4 h-4"} />
          </button>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-card border border-border rounded-lg shadow-lg overflow-hidden z-50 animate-fade-in">
          {results.map((result, index) => (
            <Link
              key={`${result.type}-${result.slug}`}
              to={getResultLink(result)}
              className="flex items-center justify-between px-4 py-3 hover:bg-muted/50 transition-colors border-b border-border last:border-0"
              onClick={() => setIsOpen(false)}
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                    {getTypeLabel(result.type)}
                  </span>
                  <span className="font-medium text-foreground">{result.name}</span>
                </div>
                {result.description && (
                  <p className="text-sm text-muted-foreground mt-0.5">{result.description}</p>
                )}
              </div>
              <ArrowRight className="w-4 h-4 text-muted-foreground" />
            </Link>
          ))}
        </div>
      )}

      {isOpen && query.length >= 2 && results.length === 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-card border border-border rounded-lg shadow-lg p-6 text-center z-50 animate-fade-in">
          <p className="text-muted-foreground">No results found for "{query}"</p>
        </div>
      )}
    </div>
  );
}
