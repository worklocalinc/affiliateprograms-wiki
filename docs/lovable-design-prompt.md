# Lovable Design Prompt: AffiliatePrograms.wiki

Build a modern, fast, Wikipedia-style affiliate directory website called **AffiliatePrograms.wiki**.

## Product
- Public, SEO-first wiki of affiliate programs, CPA networks, and affiliate tools.
- Primary goal: help users discover programs by niche, compare terms, and find official signup/terms pages.
- Secondary goal: power internal automation (but the public site is the focus of this UI).

## Brand + Style
- Clean, neutral “reference site” aesthetic (Wikipedia meets modern product UI).
- Typography-forward, lots of whitespace, subtle borders, muted color palette.
- Accessible contrast, excellent readability, responsive layout, instant-feeling navigation.

## Information Architecture
Top nav:
- Programs
- CPA Networks
- Niches
- Comparisons
- Tools
- About
- Search

Homepage:
- Search-first hero (“Search programs, networks, niches…”)
- Featured niches
- Recently verified programs
- Popular CPA networks
- Stats strip (programs indexed, networks, last updated)

## Core Pages (must design)
1) Program page (Wikipedia-style)
Sections:
- Summary infobox (name, website, payout model, cookie length, network, geos, traffic allowed, last verified)
- Overview
- Commission & terms (structured table)
- How to join (official links)
- Tracking & attribution (subid params, postback/pixel support)
- Restrictions & compliance notes
- Alternatives / similar programs
- Sources / citations (with captured date)

2) CPA Network page
Sections:
- Infobox (signup, offer types, tracking methods, payout frequency, geos, last verified)
- Offer catalog access (public/private, API/docs)
- Tracking specs (postback templates, click IDs)
- Policies (incent, email, brand bidding, etc.)
- Notable verticals and examples

3) Niche page
- Definition + intent
- Top programs for niche
- Related niches
- Content ideas + “best pages to read next”

4) Comparison page
- Side-by-side table (cookie, payout model, geos, traffic rules, tracking)
- “Who is it for?” section

## UX Requirements
- Extremely fast search (typeahead) and filtering (geo, payout model, network, traffic type).
- Clear “Last verified” badges and confidence indicators.
- Citations visible and scannable (inline markers + Sources section).
- Sticky table-of-contents on long pages.
- Mobile: collapsible TOC, sticky search, readable tables (horizontal scroll with hints).

## Components
- Search bar with autocomplete (programs, networks, niches)
- Filter drawer (multi-select)
- Infobox component
- Data table component
- Citation/source list component
- “Verified” badge component
- Breadcrumbs and related-entities cards

## SEO
- Clean URLs (e.g., `/programs/brand-name`, `/networks/cpa-network`, `/niches/pickleball`)
- Schema.org structured data where appropriate
- Internal linking blocks on every page

Deliverables:
- High-fidelity homepage + Program page + CPA Network page + Niche page + Comparison page designs
- Component library for the above components

