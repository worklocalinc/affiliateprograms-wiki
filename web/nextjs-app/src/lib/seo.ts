/**
 * SEO Utilities
 *
 * Generate metadata, JSON-LD, and Open Graph tags.
 */

import type { Metadata } from "next";
import type { Program, Category, Network } from "./api";

const SITE_NAME = "AffiliatePrograms.wiki";
const SITE_URL = "https://affiliateprograms.wiki";

// ============================================
// Metadata Generators
// ============================================

export function generateProgramMetadata(program: Program): Metadata {
  const seo = program.seo_metadata || {};

  const title =
    seo.title ||
    `${program.name} Affiliate Program - ${program.commission_rate || "Commission"} | ${SITE_NAME}`;

  const description =
    seo.meta_description ||
    `Join the ${program.name} affiliate program. ${
      program.commission_rate ? `Earn ${program.commission_rate} commission.` : ""
    } ${program.cookie_duration_days ? `${program.cookie_duration_days}-day cookie.` : ""} ${
      program.tracking_platform ? `Powered by ${program.tracking_platform}.` : ""
    }`.trim();

  return {
    title,
    description,
    openGraph: {
      title: seo.og_title || program.name,
      description: seo.og_description || description,
      url: `${SITE_URL}/programs/${program.slug}`,
      siteName: SITE_NAME,
      type: "website",
      images: seo.og_image
        ? [{ url: seo.og_image }]
        : program.logo_url
          ? [{ url: program.logo_url }]
          : [],
    },
    twitter: {
      card: "summary",
      title: seo.og_title || program.name,
      description: seo.og_description || description,
    },
    alternates: {
      canonical: `${SITE_URL}/programs/${program.slug}`,
    },
  };
}

export function generateCategoryMetadata(
  category: Category,
  programCount: number
): Metadata {
  const title = `${category.name} Affiliate Programs (${programCount}) | ${SITE_NAME}`;
  const description =
    category.description ||
    `Browse ${programCount} affiliate programs in the ${category.name} category. Find the best ${category.name.toLowerCase()} affiliate programs with competitive commissions.`;

  return {
    title,
    description,
    openGraph: {
      title: category.name,
      description,
      url: `${SITE_URL}/categories/${category.slug}`,
      siteName: SITE_NAME,
      type: "website",
    },
    alternates: {
      canonical: `${SITE_URL}/categories/${category.slug}`,
    },
  };
}

export function generateNetworkMetadata(network: Network): Metadata {
  const title = `${network.name} - Affiliate Network | ${SITE_NAME}`;
  const description =
    network.description ||
    `${network.name} affiliate network with ${network.program_count} programs. ${
      network.website ? `Visit ${network.website}.` : ""
    }`.trim();

  return {
    title,
    description,
    openGraph: {
      title: network.name,
      description,
      url: `${SITE_URL}/networks/${network.slug}`,
      siteName: SITE_NAME,
      type: "website",
    },
    alternates: {
      canonical: `${SITE_URL}/networks/${network.slug}`,
    },
  };
}

export function generateCountryMetadata(
  country: string,
  programCount: number
): Metadata {
  const title = `${country} Affiliate Programs (${programCount}) | ${SITE_NAME}`;
  const description = `Browse ${programCount} affiliate programs available in ${country}. Find the best affiliate programs that accept affiliates from ${country}.`;

  return {
    title,
    description,
    openGraph: {
      title: `${country} Affiliate Programs`,
      description,
      url: `${SITE_URL}/countries/${encodeURIComponent(country)}`,
      siteName: SITE_NAME,
      type: "website",
    },
    alternates: {
      canonical: `${SITE_URL}/countries/${encodeURIComponent(country)}`,
    },
  };
}

// ============================================
// JSON-LD Generators
// ============================================

export function generateProgramJsonLd(program: Program): object {
  // Use stored JSON-LD if available from SEO editor
  if (program.seo_metadata?.json_ld) {
    return program.seo_metadata.json_ld;
  }

  // Generate Product schema
  return {
    "@context": "https://schema.org",
    "@type": "Product",
    name: `${program.name} Affiliate Program`,
    description: `Affiliate program for ${program.name}${
      program.commission_rate ? ` with ${program.commission_rate} commission` : ""
    }`,
    brand: {
      "@type": "Brand",
      name: program.name,
    },
    url: `https://affiliateprograms.wiki/programs/${program.slug}`,
    ...(program.logo_url && { image: program.logo_url }),
    offers: {
      "@type": "Offer",
      description: "Affiliate Partnership",
      ...(program.commission_rate && {
        priceSpecification: {
          "@type": "PriceSpecification",
          description: `Commission: ${program.commission_rate}`,
        },
      }),
    },
    ...(program.tracking_platform && {
      provider: {
        "@type": "Organization",
        name: program.tracking_platform,
      },
    }),
  };
}

export function generateCategoryJsonLd(
  category: Category,
  programs: Program[]
): object {
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: `${category.name} Affiliate Programs`,
    description:
      category.description ||
      `Collection of ${programs.length} affiliate programs in the ${category.name} category`,
    url: `https://affiliateprograms.wiki/categories/${category.slug}`,
    numberOfItems: programs.length,
    itemListElement: programs.slice(0, 10).map((p, i) => ({
      "@type": "ListItem",
      position: i + 1,
      item: {
        "@type": "Product",
        name: p.name,
        url: `https://affiliateprograms.wiki/programs/${p.slug}`,
      },
    })),
  };
}

export function generateNetworkJsonLd(network: Network): object {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: network.name,
    description:
      network.description ||
      `${network.name} affiliate network with ${network.program_count} programs`,
    url: network.website || `https://affiliateprograms.wiki/networks/${network.slug}`,
    numberOfEmployees: {
      "@type": "QuantitativeValue",
      description: "Affiliate Programs",
      value: network.program_count,
    },
  };
}

export function generateWebsiteJsonLd(): object {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: SITE_NAME,
    url: SITE_URL,
    description:
      "Directory of 36,000+ affiliate programs with commission rates, cookie durations, and signup links",
    potentialAction: {
      "@type": "SearchAction",
      target: {
        "@type": "EntryPoint",
        urlTemplate: `${SITE_URL}/search?q={search_term_string}`,
      },
      "query-input": "required name=search_term_string",
    },
  };
}

export function generateBreadcrumbJsonLd(
  items: { name: string; url: string }[]
): object {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: item.name,
      item: item.url,
    })),
  };
}
