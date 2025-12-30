#!/usr/bin/env python3
"""
Asset Pipeline

Captures and stores visual assets for affiliate programs:
- Screenshots of program signup pages
- Logos from merchant sites
- Creative assets from affiliate networks

Assets are stored locally with metadata in PostgreSQL.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import psycopg
import requests


# ============================================
# Configuration
# ============================================

ASSETS_DIR = Path(os.environ.get("ASSETS_DIR", "/home/skynet/affiliateprograms-wiki/assets"))
SCREENSHOT_WIDTH = 1280
SCREENSHOT_HEIGHT = 800
SCREENSHOT_TIMEOUT = 30


@dataclass
class Asset:
    """Represents a stored asset."""
    id: int | None
    program_id: int | None
    category_id: int | None
    asset_type: str  # logo, screenshot, creative
    storage_path: str
    file_hash: str
    mime_type: str
    file_size_bytes: int
    width: int | None
    height: int | None
    title: str | None
    alt_text: str | None
    source_url: str | None


class AssetPipeline:
    """
    Pipeline for capturing and storing visual assets.

    Usage:
        pipeline = AssetPipeline(db_url)

        # Capture screenshot
        asset = pipeline.capture_screenshot(program_id=123, url="https://example.com/affiliate")

        # Fetch logo
        asset = pipeline.fetch_logo(program_id=123, url="https://example.com/logo.png")

        # Get assets for program
        assets = pipeline.get_assets(program_id=123)
    """

    def __init__(self, db_url: str | None = None):
        self.db_url = db_url or os.environ.get("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL not set")

        # Create assets directory
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        (ASSETS_DIR / "screenshots").mkdir(exist_ok=True)
        (ASSETS_DIR / "logos").mkdir(exist_ok=True)
        (ASSETS_DIR / "creatives").mkdir(exist_ok=True)

    def capture_screenshot(
        self,
        program_id: int,
        url: str,
        title: str | None = None
    ) -> Asset | None:
        """
        Capture screenshot of a URL using Chrome headless.

        Returns Asset object or None if capture failed.
        """
        print(f"Capturing screenshot: {url}")

        try:
            # Generate output path
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            filename = f"prog_{program_id}_{url_hash}.png"
            output_path = ASSETS_DIR / "screenshots" / filename

            # Use Chrome headless via puppeteer or playwright
            # Fallback to cutycapt or wkhtmltoimage if available
            success = self._capture_with_chrome(url, output_path)

            if not success or not output_path.exists():
                print(f"  Failed to capture screenshot")
                return None

            # Calculate file hash
            file_hash = self._hash_file(output_path)

            # Get dimensions
            width, height = self._get_image_dimensions(output_path)

            # Store in database
            asset = Asset(
                id=None,
                program_id=program_id,
                category_id=None,
                asset_type="screenshot",
                storage_path=str(output_path.relative_to(ASSETS_DIR)),
                file_hash=file_hash,
                mime_type="image/png",
                file_size_bytes=output_path.stat().st_size,
                width=width,
                height=height,
                title=title or f"Screenshot of {urlparse(url).netloc}",
                alt_text=f"Screenshot of affiliate signup page",
                source_url=url
            )

            asset_id = self._save_asset(asset)
            asset.id = asset_id

            print(f"  ✓ Saved screenshot: {filename}")
            return asset

        except Exception as e:
            print(f"  Error capturing screenshot: {e}")
            return None

    def fetch_logo(
        self,
        program_id: int,
        url: str,
        program_name: str | None = None
    ) -> Asset | None:
        """
        Fetch and store a logo from URL.

        Returns Asset object or None if fetch failed.
        """
        print(f"Fetching logo: {url}")

        try:
            # Download logo
            resp = requests.get(url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (compatible; AffiliateBot/1.0)"
            })
            resp.raise_for_status()

            # Detect mime type
            content_type = resp.headers.get("content-type", "").split(";")[0].strip()
            if not content_type.startswith("image/"):
                print(f"  Not an image: {content_type}")
                return None

            # Get extension
            ext_map = {
                "image/png": "png",
                "image/jpeg": "jpg",
                "image/gif": "gif",
                "image/webp": "webp",
                "image/svg+xml": "svg",
                "image/x-icon": "ico",
            }
            ext = ext_map.get(content_type, "png")

            # Calculate hash for deduplication
            content_hash = hashlib.sha256(resp.content).hexdigest()[:16]

            # Generate filename
            filename = f"logo_{program_id}_{content_hash}.{ext}"
            output_path = ASSETS_DIR / "logos" / filename

            # Check for duplicate
            existing = self._find_by_hash(content_hash)
            if existing:
                print(f"  Duplicate logo, reusing: {existing['storage_path']}")
                return None

            # Save file
            output_path.write_bytes(resp.content)

            # Get dimensions
            width, height = self._get_image_dimensions(output_path)

            # Store in database
            asset = Asset(
                id=None,
                program_id=program_id,
                category_id=None,
                asset_type="logo",
                storage_path=str(output_path.relative_to(ASSETS_DIR)),
                file_hash=content_hash,
                mime_type=content_type,
                file_size_bytes=len(resp.content),
                width=width,
                height=height,
                title=f"{program_name or 'Program'} Logo",
                alt_text=f"Logo for {program_name or 'affiliate program'}",
                source_url=url
            )

            asset_id = self._save_asset(asset)
            asset.id = asset_id

            print(f"  ✓ Saved logo: {filename}")
            return asset

        except Exception as e:
            print(f"  Error fetching logo: {e}")
            return None

    def get_assets(
        self,
        program_id: int | None = None,
        category_id: int | None = None,
        asset_type: str | None = None
    ) -> list[Asset]:
        """Get assets matching criteria."""
        conditions = []
        params = []

        if program_id is not None:
            conditions.append("program_id = %s")
            params.append(program_id)
        if category_id is not None:
            conditions.append("category_id = %s")
            params.append(category_id)
        if asset_type is not None:
            conditions.append("asset_type = %s")
            params.append(asset_type)

        where = " AND ".join(conditions) if conditions else "1=1"

        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT id, program_id, category_id, asset_type, storage_path,
                           file_hash, mime_type, file_size_bytes, width, height,
                           title, alt_text, source_url
                    FROM affiliate_wiki.assets
                    WHERE {where}
                    ORDER BY created_at DESC
                """, tuple(params))

                return [
                    Asset(
                        id=row[0],
                        program_id=row[1],
                        category_id=row[2],
                        asset_type=row[3],
                        storage_path=row[4],
                        file_hash=row[5],
                        mime_type=row[6],
                        file_size_bytes=row[7],
                        width=row[8],
                        height=row[9],
                        title=row[10],
                        alt_text=row[11],
                        source_url=row[12]
                    )
                    for row in cur.fetchall()
                ]

    def bulk_fetch_logos(self, programs: list[dict], max_workers: int = 5) -> int:
        """
        Fetch logos for multiple programs.

        programs: list of {id, name, logo_url}
        Returns count of successfully fetched logos.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        success = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self.fetch_logo,
                    p["id"],
                    p["logo_url"],
                    p.get("name")
                ): p
                for p in programs
                if p.get("logo_url")
            }

            for future in as_completed(futures):
                if future.result() is not None:
                    success += 1

        return success

    def _capture_with_chrome(self, url: str, output_path: Path) -> bool:
        """Capture screenshot using Chrome headless."""
        try:
            # Try using puppeteer via Node.js script
            script = f"""
            const puppeteer = require('puppeteer');
            (async () => {{
                const browser = await puppeteer.launch({{
                    headless: 'new',
                    args: ['--no-sandbox', '--disable-setuid-sandbox']
                }});
                const page = await browser.newPage();
                await page.setViewport({{ width: {SCREENSHOT_WIDTH}, height: {SCREENSHOT_HEIGHT} }});
                await page.goto('{url}', {{ waitUntil: 'networkidle2', timeout: {SCREENSHOT_TIMEOUT * 1000} }});
                await page.screenshot({{ path: '{output_path}', fullPage: false }});
                await browser.close();
            }})();
            """

            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(script)
                script_path = f.name

            result = subprocess.run(
                ['node', script_path],
                capture_output=True,
                timeout=SCREENSHOT_TIMEOUT + 10
            )

            os.unlink(script_path)
            return result.returncode == 0 and output_path.exists()

        except Exception as e:
            print(f"    Chrome capture failed: {e}")
            return False

    def _hash_file(self, path: Path) -> str:
        """Calculate SHA256 hash of file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()[:16]

    def _get_image_dimensions(self, path: Path) -> tuple[int | None, int | None]:
        """Get image dimensions."""
        try:
            from PIL import Image
            with Image.open(path) as img:
                return img.size
        except ImportError:
            # PIL not installed
            return None, None
        except Exception:
            return None, None

    def _save_asset(self, asset: Asset) -> int:
        """Save asset to database, return ID."""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO affiliate_wiki.assets (
                        program_id, category_id, asset_type, storage_path,
                        file_hash, mime_type, file_size_bytes, width, height,
                        title, alt_text, source_url, captured_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    asset.program_id, asset.category_id, asset.asset_type,
                    asset.storage_path, asset.file_hash, asset.mime_type,
                    asset.file_size_bytes, asset.width, asset.height,
                    asset.title, asset.alt_text, asset.source_url,
                    datetime.now(timezone.utc)
                ))
                return cur.fetchone()[0]

    def _find_by_hash(self, file_hash: str) -> dict | None:
        """Find existing asset by file hash."""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, storage_path FROM affiliate_wiki.assets
                    WHERE file_hash = %s LIMIT 1
                """, (file_hash,))
                row = cur.fetchone()
                if row:
                    return {"id": row[0], "storage_path": row[1]}
                return None


# ============================================
# CLI
# ============================================

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Asset Pipeline")
    parser.add_argument("--action", choices=["screenshot", "logo", "bulk-logos"], required=True)
    parser.add_argument("--program-id", type=int)
    parser.add_argument("--url")
    parser.add_argument("--name")
    parser.add_argument("--limit", type=int, default=100)

    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set")
        exit(1)

    pipeline = AssetPipeline(db_url)

    if args.action == "screenshot":
        if not args.program_id or not args.url:
            print("--program-id and --url required for screenshot")
            exit(1)
        pipeline.capture_screenshot(args.program_id, args.url, args.name)

    elif args.action == "logo":
        if not args.program_id or not args.url:
            print("--program-id and --url required for logo")
            exit(1)
        pipeline.fetch_logo(args.program_id, args.url, args.name)

    elif args.action == "bulk-logos":
        # Fetch logos for programs that have logo_url but no stored asset
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.id, p.name, pr.extracted->>'logo_url' as logo_url
                    FROM affiliate_wiki.programs p
                    JOIN affiliate_wiki.program_research pr ON p.id = pr.program_id
                    WHERE pr.extracted->>'logo_url' IS NOT NULL
                      AND pr.extracted->>'logo_url' != ''
                      AND NOT EXISTS (
                          SELECT 1 FROM affiliate_wiki.assets a
                          WHERE a.program_id = p.id AND a.asset_type = 'logo'
                      )
                    ORDER BY p.id
                    LIMIT %s
                """, (args.limit,))
                programs = [
                    {"id": row[0], "name": row[1], "logo_url": row[2]}
                    for row in cur.fetchall()
                ]

        print(f"Found {len(programs)} programs without stored logos")
        count = pipeline.bulk_fetch_logos(programs)
        print(f"Successfully fetched {count} logos")
