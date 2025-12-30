# Affiliate Wiki Scripts

These scripts seed and maintain the `AffiliatePrograms.wiki` dataset.

## 1) Bootstrap a venv

```bash
bash affiliateprograms-wiki/scripts/affiliate_wiki/bootstrap_venv.sh
```

## 2) Export Skimlinks merchants (seed list)

```bash
affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python \
  affiliateprograms-wiki/scripts/affiliate_wiki/skimlinks_export.py
```

Outputs land in `affiliateprograms-wiki/data/affiliate_wiki/skimlinks/` by default.

## 3) Create schema in Postgres

```bash
export DATABASE_URL="postgresql://.../db?sslmode=require"
affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python \
  affiliateprograms-wiki/scripts/affiliate_wiki/setup_affiliate_wiki_db.py \
  --db-url "$DATABASE_URL"
```

## 4) Load exported merchants into Postgres

```bash
affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python \
  affiliateprograms-wiki/scripts/affiliate_wiki/skimlinks_export.py \
  --db-url "$DATABASE_URL"
```

## 5) Run first-pass research (Stage C/D-lite)

```bash
affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python \
  affiliateprograms-wiki/scripts/affiliate_wiki/research_runner.py \
  --db-url "$DATABASE_URL" \
  --limit 50
```

Tip: for a slower/deeper pass, increase `--timeout`, `--max-probes`, and `--max-link-probes`.

## 6) Initialize research queue

`research_runner.py` pulls from `affiliate_wiki.program_research` with `status='pending'`.
After loading seed programs, make sure the queue rows exist:

```bash
affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python \
  affiliateprograms-wiki/scripts/affiliate_wiki/init_research_queue.py \
  --db-url "$DATABASE_URL"
```

## 7) Seed CPA networks (starter list)

```bash
affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python \
  affiliateprograms-wiki/scripts/affiliate_wiki/seed_cpa_networks.py \
  --db-url "$DATABASE_URL"
```

## 8) Extract basic program fields (Stage E-lite)

This populates first-pass fields like cookie length and payout model from captured HTML snippets.

```bash
affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python \
  affiliateprograms-wiki/scripts/affiliate_wiki/extract_program_fields.py \
  --db-url "$DATABASE_URL" \
  --limit 200
```

## 9) Discover official pages via search (Stage C-lite)

This moves `needs_search` programs back to `pending` by finding a likely affiliate/partner URL.

```bash
affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python \
  affiliateprograms-wiki/scripts/affiliate_wiki/discover_program_pages_ddg.py \
  --db-url "$DATABASE_URL" \
  --limit 25
```

## 10) Overnight runner (keeps going)

This runs discovery → research → extraction in a loop with backoff.

Requirements:
- `BRAVE_API_KEY` available in `~/ai-shared/secrets/.env` (used for search/discovery)
- DB URL secret: `database_url_affiliate_wiki` (runner pulls it via gcloud in `scripts/run_overnight.sh`)

```bash
bash ~/affiliateprograms-wiki/scripts/run_overnight.sh
tail -f ~/affiliateprograms-wiki/logs/overnight-$(date +%F).log
```
