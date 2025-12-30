/**
 * Client-side link rewriter for Next.js
 *
 * Applies affiliate link templates based on rules from the API.
 * Caches rules for performance.
 */

import { getLinkRules } from "./api";

interface LinkRule {
  id: number;
  match_domain: string;
  match_path_pattern: string | null;
  affiliate_template: string;
  network: string | null;
  default_tag: string | null;
  exception_paths: string[];
  priority: number;
}

let rulesCache: LinkRule[] | null = null;
let cacheTime = 0;
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

function domainMatches(domain: string, pattern: string): boolean {
  domain = domain.toLowerCase();
  pattern = pattern.toLowerCase();

  if (pattern.startsWith("*.")) {
    const suffix = pattern.slice(2);
    return domain.endsWith(suffix) || domain === suffix;
  }

  if (pattern.endsWith(".*")) {
    const prefix = pattern.slice(0, -2);
    return domain.startsWith(prefix + ".");
  }

  return (
    domain === pattern ||
    domain === `www.${pattern}` ||
    `www.${domain}` === pattern
  );
}

function pathMatches(path: string, pattern: string | null): boolean {
  if (!pattern) return true;

  // Simple glob matching
  const regex = new RegExp(
    "^" + pattern.replace(/\*/g, ".*").replace(/\?/g, ".") + "$"
  );
  return regex.test(path);
}

function isException(path: string, exceptions: string[]): boolean {
  return exceptions.some((exc) => pathMatches(path, exc));
}

export async function rewriteUrl(url: string): Promise<string> {
  if (!url) return url;

  try {
    const parsed = new URL(url);
    const domain = parsed.hostname;
    const path = parsed.pathname;

    // Load rules (with caching)
    const now = Date.now();
    if (!rulesCache || now - cacheTime > CACHE_TTL) {
      try {
        const data = await getLinkRules();
        rulesCache = data.rules;
        cacheTime = now;
      } catch {
        // If API fails, return original URL
        return url;
      }
    }

    // Find matching rule
    for (const rule of rulesCache) {
      if (!domainMatches(domain, rule.match_domain)) continue;
      if (!pathMatches(path, rule.match_path_pattern)) continue;
      if (isException(path, rule.exception_paths || [])) return url;

      // Apply template
      return rule.affiliate_template
        .replace("{url}", encodeURIComponent(url))
        .replace("{url_raw}", url)
        .replace("{tag}", rule.default_tag || "")
        .replace("{utm_source}", "affiliateprograms.wiki")
        .replace("{utm_medium}", "referral")
        .replace("{utm_campaign}", "");
    }

    return url;
  } catch {
    return url;
  }
}

// Synchronous version that uses cached rules
export function rewriteUrlSync(url: string): string {
  if (!url || !rulesCache) return url;

  try {
    const parsed = new URL(url);
    const domain = parsed.hostname;
    const path = parsed.pathname;

    for (const rule of rulesCache) {
      if (!domainMatches(domain, rule.match_domain)) continue;
      if (!pathMatches(path, rule.match_path_pattern)) continue;
      if (isException(path, rule.exception_paths || [])) return url;

      return rule.affiliate_template
        .replace("{url}", encodeURIComponent(url))
        .replace("{url_raw}", url)
        .replace("{tag}", rule.default_tag || "")
        .replace("{utm_source}", "affiliateprograms.wiki")
        .replace("{utm_medium}", "referral")
        .replace("{utm_campaign}", "");
    }

    return url;
  } catch {
    return url;
  }
}
