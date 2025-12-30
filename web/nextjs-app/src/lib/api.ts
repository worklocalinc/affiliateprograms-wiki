/**
 * API Client for AffiliatePrograms.wiki
 *
 * Server-side fetching for Next.js SSR pages.
 */

const API_BASE = process.env.API_URL || "http://localhost:8120";

// ============================================
// Types
// ============================================

export interface Program {
  id: number;
  name: string;
  slug: string;
  domain: string | null;
  logo_url: string | null;
  commission_rate: string | null;
  cookie_duration_days: number | null;
  payout_model: string | null;
  tracking_platform: string | null;
  signup_url: string | null;
  minimum_payout: string | null;
  payment_methods: string[] | null;
  payment_frequency: string | null;
  requirements: string | null;
  restrictions: string | null;
  languages: string[] | null;
  countries: string[] | null;
  categories: string[];
  deep_researched_at: string | null;
  seo_metadata?: {
    title?: string;
    meta_description?: string;
    og_title?: string;
    og_description?: string;
    og_image?: string;
    json_ld?: Record<string, unknown>;
  };
}

export interface Network {
  id: number;
  name: string;
  slug: string;
  website: string | null;
  description: string | null;
  program_count: number;
  countries: string[] | null;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  path: string;
  depth: number;
  description: string | null;
  icon: string | null;
  program_count: number;
  children?: Category[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Stats {
  programs: number;
  deep_researched: number;
  networks: number;
  categories: number;
}

// ============================================
// API Functions
// ============================================

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;

  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    // Cache for 5 minutes by default
    next: { revalidate: 300 },
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

// Programs
export async function getPrograms(params?: {
  limit?: number;
  offset?: number;
  q?: string;
  has_deep_research?: boolean;
}): Promise<PaginatedResponse<Program>> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  if (params?.q) searchParams.set("q", params.q);
  if (params?.has_deep_research) searchParams.set("has_deep_research", "true");

  const query = searchParams.toString();
  return fetchAPI(`/programs${query ? `?${query}` : ""}`);
}

export async function getProgram(slug: string): Promise<Program | null> {
  try {
    return await fetchAPI(`/programs/${slug}`);
  } catch {
    return null;
  }
}

export async function getProgramSlugs(): Promise<string[]> {
  const data = await fetchAPI<PaginatedResponse<{ slug: string }>>(
    "/programs?limit=50000&has_deep_research=true"
  );
  return data.items.map((p) => p.slug);
}

// Networks
export async function getNetworks(): Promise<PaginatedResponse<Network>> {
  return fetchAPI("/networks");
}

export async function getNetwork(slug: string): Promise<Network | null> {
  try {
    return await fetchAPI(`/networks/${slug}`);
  } catch {
    return null;
  }
}

export async function getNetworkSlugs(): Promise<string[]> {
  const data = await getNetworks();
  return data.items.map((n) => n.slug);
}

// Categories
export async function getCategories(): Promise<Category[]> {
  const data = await fetchAPI<{ categories: Category[] }>("/categories");
  return data.categories;
}

export async function getCategory(slug: string): Promise<{
  category: Category;
  programs: Program[];
  breadcrumbs: Category[];
} | null> {
  try {
    return await fetchAPI(`/categories/${slug}`);
  } catch {
    return null;
  }
}

export async function getCategorySlugs(): Promise<string[]> {
  const categories = await getCategories();

  function collectSlugs(cats: Category[]): string[] {
    return cats.flatMap((c) => [c.slug, ...collectSlugs(c.children || [])]);
  }

  return collectSlugs(categories);
}

// Countries
export async function getCountries(): Promise<
  PaginatedResponse<{ country: string; count: number }>
> {
  return fetchAPI("/countries");
}

export async function getCountryPrograms(
  country: string,
  params?: { limit?: number; offset?: number }
): Promise<PaginatedResponse<Program> | null> {
  try {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.offset) searchParams.set("offset", String(params.offset));
    const query = searchParams.toString();
    return await fetchAPI(`/countries/${encodeURIComponent(country)}${query ? `?${query}` : ""}`);
  } catch {
    return null;
  }
}

// Browse (combined filters)
export async function browse(params: {
  country?: string;
  category?: string;
  network?: string;
  language?: string;
  q?: string;
  limit?: number;
  offset?: number;
}): Promise<PaginatedResponse<Program> & { filters: Record<string, string | null> }> {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.set(key, String(value));
    }
  });
  return fetchAPI(`/browse?${searchParams.toString()}`);
}

// Stats
export async function getStats(): Promise<Stats> {
  return fetchAPI("/stats");
}

// Search
export async function search(
  q: string,
  limit = 20
): Promise<PaginatedResponse<Program>> {
  return fetchAPI(`/search?q=${encodeURIComponent(q)}&limit=${limit}`);
}

// Link rules for affiliate rewriting
export async function getLinkRules(): Promise<{
  rules: Array<{
    id: number;
    match_domain: string;
    match_path_pattern: string | null;
    affiliate_template: string;
    network: string | null;
    default_tag: string | null;
    exception_paths: string[];
    priority: number;
  }>;
}> {
  return fetchAPI("/editorial/link-rules");
}
