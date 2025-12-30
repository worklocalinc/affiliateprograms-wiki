import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const baseUrl = "https://affiliateprograms.wiki";

  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: [
          "/api/",        // API endpoints
          "/search?",     // Search queries (prevent crawl waste)
          "/*?page=",     // Pagination (optional - comment out if you want pagination indexed)
        ],
      },
      {
        userAgent: "GPTBot",
        disallow: ["/"], // Block OpenAI's crawler
      },
      {
        userAgent: "CCBot",
        disallow: ["/"], // Block Common Crawl
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
    host: baseUrl,
  };
}
