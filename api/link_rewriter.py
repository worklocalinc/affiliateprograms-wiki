#!/usr/bin/env python3
"""
Deterministic Link Rewriting Engine

Applies affiliate link templates based on configurable rules.
NOT LLM-based - fully deterministic and testable.

Used in:
- Next.js server components (at render time)
- API response layer (optional)
- Markdown renderer (for editorial content)
"""
from __future__ import annotations

import os
import re
import subprocess
from fnmatch import fnmatch
from functools import lru_cache
from typing import Any
from urllib.parse import quote, urlparse

import psycopg


def _get_db_url() -> str:
    """Get database URL from environment or gcloud."""
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url

    try:
        result = subprocess.run(
            ["/home/skynet/google-cloud-sdk/bin/gcloud", "secrets", "versions", "access",
             "latest", "--secret=database_url_affiliate_wiki", "--project=superapp-466313"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"Failed to get DB URL from gcloud: {e}")

    raise RuntimeError("DATABASE_URL not set")


class LinkRewriter:
    """
    Deterministic link rewriting - NOT LLM-based.

    Applies affiliate templates to URLs based on matching rules.

    Usage:
        rewriter = LinkRewriter()
        affiliate_url = rewriter.rewrite("https://amazon.com/product/123")
    """

    def __init__(self, db_url: str | None = None, cache_ttl: int = 300):
        """
        Initialize the link rewriter.

        Args:
            db_url: Database connection URL. If None, fetches from gcloud.
            cache_ttl: Time in seconds to cache rules (default 5 min)
        """
        self.db_url = db_url or _get_db_url()
        self.cache_ttl = cache_ttl
        self._rules_cache: list[dict] | None = None
        self._cache_time: float = 0

    def _load_rules(self) -> list[dict]:
        """Load active link rules from database, sorted by priority."""
        import time

        # Check cache
        now = time.time()
        if self._rules_cache is not None and (now - self._cache_time) < self.cache_ttl:
            return self._rules_cache

        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        id, match_domain, match_path_pattern,
                        affiliate_template, network, default_tag,
                        utm_source, utm_medium, utm_campaign,
                        exception_paths, priority
                    FROM affiliate_wiki.link_rules
                    WHERE is_enabled = TRUE
                    ORDER BY priority DESC
                """)
                cols = [d.name for d in cur.description]
                rules = [dict(zip(cols, row)) for row in cur.fetchall()]

        self._rules_cache = rules
        self._cache_time = now
        return rules

    def _domain_matches(self, domain: str, pattern: str) -> bool:
        """
        Check if domain matches a pattern.

        Patterns:
        - 'amazon.com' - exact match
        - '*.amazon.com' - wildcard subdomain
        - 'amazon.*' - wildcard TLD
        """
        domain = domain.lower()
        pattern = pattern.lower()

        if pattern.startswith("*."):
            # Wildcard subdomain: *.amazon.com matches sub.amazon.com
            suffix = pattern[2:]
            return domain.endswith(suffix) or domain == suffix

        if pattern.endswith(".*"):
            # Wildcard TLD: amazon.* matches amazon.com, amazon.co.uk
            prefix = pattern[:-2]
            return domain.startswith(prefix + ".")

        # Exact match
        return domain == pattern or domain == f"www.{pattern}" or f"www.{domain}" == pattern

    def _path_matches(self, path: str, pattern: str | None) -> bool:
        """Check if path matches a glob pattern."""
        if not pattern:
            return True  # No pattern = match all paths
        return fnmatch(path, pattern)

    def _is_exception(self, path: str, exception_paths: list[str] | None) -> bool:
        """Check if path is in exception list."""
        if not exception_paths:
            return False
        return any(fnmatch(path, exc) for exc in exception_paths)

    def _apply_template(self, url: str, rule: dict) -> str:
        """
        Apply affiliate template to URL.

        Template variables:
        - {url} - Original URL (URL encoded)
        - {url_raw} - Original URL (not encoded)
        - {tag} - Affiliate tag
        - {utm_source} - UTM source
        - {utm_medium} - UTM medium
        - {utm_campaign} - UTM campaign
        """
        template = rule["affiliate_template"]

        return template.format(
            url=quote(url, safe=''),
            url_raw=url,
            tag=rule.get("default_tag") or "",
            utm_source=rule.get("utm_source") or "affiliateprograms.wiki",
            utm_medium=rule.get("utm_medium") or "referral",
            utm_campaign=rule.get("utm_campaign") or ""
        )

    def rewrite(self, url: str) -> str:
        """
        Apply affiliate rewriting rules to URL.

        Returns original URL if:
        - No rule matches
        - URL path is in exception list
        - URL is malformed

        Args:
            url: The URL to potentially rewrite

        Returns:
            The rewritten URL with affiliate tracking, or original URL
        """
        if not url:
            return url

        try:
            parsed = urlparse(url)
        except Exception:
            return url

        domain = parsed.netloc
        path = parsed.path

        if not domain:
            return url

        rules = self._load_rules()

        for rule in rules:
            # Check domain match
            if not self._domain_matches(domain, rule["match_domain"]):
                continue

            # Check path pattern match
            if not self._path_matches(path, rule.get("match_path_pattern")):
                continue

            # Check exceptions
            if self._is_exception(path, rule.get("exception_paths")):
                return url  # Don't rewrite exception paths

            # Apply template
            return self._apply_template(url, rule)

        # No rule matched
        return url

    def rewrite_all(self, urls: list[str]) -> list[str]:
        """Rewrite multiple URLs."""
        return [self.rewrite(url) for url in urls]

    def add_rule(
        self,
        match_domain: str,
        affiliate_template: str,
        match_path_pattern: str | None = None,
        network: str | None = None,
        default_tag: str | None = None,
        exception_paths: list[str] | None = None,
        priority: int = 100
    ) -> int:
        """
        Add a new link rewriting rule.

        Returns the rule ID.
        """
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO affiliate_wiki.link_rules (
                        match_domain, match_path_pattern, affiliate_template,
                        network, default_tag, exception_paths, priority
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    match_domain,
                    match_path_pattern,
                    affiliate_template,
                    network,
                    default_tag,
                    exception_paths,
                    priority
                ))
                result = cur.fetchone()
                conn.commit()

        # Clear cache
        self._rules_cache = None
        return result[0]


# Convenience function for simple usage
@lru_cache(maxsize=1)
def get_rewriter() -> LinkRewriter:
    """Get a singleton LinkRewriter instance."""
    return LinkRewriter()


def rewrite_url(url: str) -> str:
    """Convenience function to rewrite a single URL."""
    return get_rewriter().rewrite(url)


# CLI for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python link_rewriter.py <url>")
        print("       python link_rewriter.py --add-rule <domain> <template>")
        print("       python link_rewriter.py --list-rules")
        sys.exit(1)

    rewriter = LinkRewriter()

    if sys.argv[1] == "--list-rules":
        rules = rewriter._load_rules()
        print(f"Found {len(rules)} active rules:\n")
        for rule in rules:
            print(f"  [{rule['priority']}] {rule['match_domain']}")
            if rule.get('match_path_pattern'):
                print(f"       path: {rule['match_path_pattern']}")
            print(f"       template: {rule['affiliate_template'][:50]}...")
            if rule.get('exception_paths'):
                print(f"       exceptions: {rule['exception_paths']}")
            print()

    elif sys.argv[1] == "--add-rule" and len(sys.argv) >= 4:
        domain = sys.argv[2]
        template = sys.argv[3]
        rule_id = rewriter.add_rule(domain, template)
        print(f"Added rule {rule_id} for {domain}")

    else:
        url = sys.argv[1]
        result = rewriter.rewrite(url)
        print(f"Input:  {url}")
        print(f"Output: {result}")
        if result != url:
            print("  → URL was rewritten")
        else:
            print("  → No rule matched (URL unchanged)")
