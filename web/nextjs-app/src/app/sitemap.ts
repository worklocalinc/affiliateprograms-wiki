import { MetadataRoute } from "next";
import { getProgramSlugs, getCategorySlugs, getNetworkSlugs, getCountries } from "@/lib/api";

const BASE_URL = "https://affiliateprograms.wiki";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // Fetch all slugs in parallel
  const [programSlugs, categorySlugs, networkSlugs, countriesData] = await Promise.all([
    getProgramSlugs().catch(() => []),
    getCategorySlugs().catch(() => []),
    getNetworkSlugs().catch(() => []),
    getCountries().catch(() => ({ items: [] })),
  ]);

  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    {
      url: BASE_URL,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 1,
    },
    {
      url: `${BASE_URL}/programs`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.9,
    },
    {
      url: `${BASE_URL}/categories`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${BASE_URL}/networks`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/countries`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.8,
    },
  ];

  // Program pages (highest priority - main content)
  const programPages: MetadataRoute.Sitemap = programSlugs.map((slug) => ({
    url: `${BASE_URL}/programs/${slug}`,
    lastModified: new Date(),
    changeFrequency: "weekly" as const,
    priority: 0.7,
  }));

  // Category pages
  const categoryPages: MetadataRoute.Sitemap = categorySlugs.map((slug) => ({
    url: `${BASE_URL}/categories/${slug}`,
    lastModified: new Date(),
    changeFrequency: "weekly" as const,
    priority: 0.8,
  }));

  // Network pages
  const networkPages: MetadataRoute.Sitemap = networkSlugs.map((slug) => ({
    url: `${BASE_URL}/networks/${slug}`,
    lastModified: new Date(),
    changeFrequency: "monthly" as const,
    priority: 0.6,
  }));

  // Country pages
  const countryPages: MetadataRoute.Sitemap = countriesData.items.map((item) => ({
    url: `${BASE_URL}/countries/${encodeURIComponent(item.country)}`,
    lastModified: new Date(),
    changeFrequency: "weekly" as const,
    priority: 0.6,
  }));

  return [
    ...staticPages,
    ...programPages,
    ...categoryPages,
    ...networkPages,
    ...countryPages,
  ];
}
