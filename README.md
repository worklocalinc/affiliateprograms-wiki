# AffiliatePrograms.wiki

**Domain**: affiliateprograms.wiki
**Platform**: Affiliate Business
**Status**: Setup

---

## Structure

```
affiliateprograms-wiki/
├── api/          # REST API
├── data/         # Program data, categories
├── scripts/      # Automation
├── templates/    # Page templates
├── generated/    # Built site output
└── docs/         # Documentation
```

## Links

- **Idea Doc**: `~/ai-shared/ideas/products/affiliateprograms-wiki.md`
- **Platform**: `~/ai-shared/ideas/platforms/affiliate-business.md`

## Tooling

- Dataset tooling lives in `affiliateprograms-wiki/scripts/affiliate_wiki/` (Skimlinks seed export + Postgres schema + first-pass research runner).

## UI (Design Reference)

- The Lovable/Vite + shadcn + Tailwind UI baseline (from `worklocalinc/affiliate-compass`) is vendored at `affiliateprograms-wiki/web/affiliate-compass-ui/`.
- Run it:
  - `cd ~/affiliateprograms-wiki/web/affiliate-compass-ui`
  - `npm i`
  - `npm run dev`

## API

- Local API lives in `affiliateprograms-wiki/api/server.py` (FastAPI over the `affiliate_wiki` Postgres schema).
- Quick start: `affiliateprograms-wiki/docs/run.md`
