# Marketing Network Fundamentals

## Core Definition

**A marketing network is a risk-allocation and measurement system that coordinates strangers by defining which user behaviors trigger payment and who absorbs uncertainty between attention and revenue.**

## Why Networks Exist

Networks are **economic coordination layers** that solve three fundamental problems at scale:

### 1. Trust
Strangers want to exchange value without getting cheated. Without a trusted intermediary, every transaction requires bilateral verification.

### 2. Measurement
Everyone needs agreement on what happened and who caused it. Attribution is the foundation of fair payment.

### 3. Risk Allocation
Someone must absorb uncertainty: "Will this traffic actually do anything valuable?"

**Key insight**: Marketing networks exist because bilateral trust does not scale.

Without networks, every advertiser would need:
- Custom contracts with every publisher
- Custom tracking systems
- Custom fraud detection
- Custom payout infrastructure

Networks compress all this complexity into shared infrastructure.

---

## The Four Core Entities

Every marketing network has the same four roles:

| Entity | Role | Core Need |
|--------|------|-----------|
| **Advertiser** | Wants outcomes (attention, clicks, leads, sales, installs) | Predictable customer acquisition costs |
| **Publisher/Affiliate** | Controls traffic (users, audiences, distribution) | Monetization of attention |
| **User** | The human whose behavior creates value | Solutions to their problems |
| **Network** | Enforces rules, measures reality, moves money | Transaction volume (fees) |

Everything else is a variation on **what outcome is paid for** and **who carries risk**.

---

## Payment Models: Risk Spectrum

The payment trigger defines the network type. Each model moves the payment line closer to or farther from actual business value.

### CPM (Cost Per Mille) — Pay for Potential Attention
- **Trigger**: Ad is shown (impression)
- **Signal quality**: Extremely weak
- **Risk allocation**: Almost entirely on advertiser
- **Use case**: Brand awareness, reach campaigns
- **Economics**: Buying possibility, not performance

### CPC (Cost Per Click) — Pay for Expressed Interest
- **Trigger**: User clicks
- **Signal quality**: Weak to medium
- **Risk allocation**: Mostly on advertiser
- **Use case**: Traffic generation, initial engagement
- **Economics**: A click proves curiosity, not intent

### CPL (Cost Per Lead) — Pay for Contact Information
- **Trigger**: Lead form submitted
- **Signal quality**: Medium
- **Risk allocation**: Shared between parties
- **Use case**: B2B, high-value services, insurance, education
- **Economics**: Leads are promises—some mature, many rot

### CPA (Cost Per Action) — Pay for Defined Action
- **Trigger**: Advertiser-defined event (signup, trial, install)
- **Signal quality**: Strong
- **Risk allocation**: Mostly on publisher
- **Use case**: Apps, SaaS trials, registrations
- **Economics**: Actions are closer to value but still may not equal revenue

### CPS/Affiliate (Cost Per Sale) — Pay for Revenue
- **Trigger**: Completed purchase
- **Signal quality**: Very strong
- **Risk allocation**: Heavily on publisher
- **Use case**: E-commerce, retail, subscription services
- **Economics**: Outcome-aligned—money only flows after money flows

### RevShare (Revenue Share) — Pay for Ongoing Value
- **Trigger**: Ongoing revenue over time
- **Signal quality**: Strongest
- **Risk allocation**: Shared long-term
- **Use case**: SaaS, subscriptions, recurring services
- **Economics**: Aligns incentives across lifetime value, not moments

---

## Affiliate Networks (Deep Analysis)

Affiliate Networks are **optimized for value realization**, not just user behavior.

### Key Characteristics
- Payment tied to **revenue events** (actual sales)
- **Attribution** matters deeply (who influenced the sale)
- Fraud is rarer but disputes are harder
- Cash flow timing is slower (often 30-60 day delays)
- Higher commissions due to risk transfer

### Why They Work
Affiliates act like **external sales forces** who:
- Choose their own promotional methods
- Are only paid if the sale happens
- Absorb most experimentation and traffic risk

### Traffic Characteristics
Affiliate traffic tends to be:
- **Content-heavy** (reviews, comparisons, guides)
- **Intent-focused** (users actively researching purchases)
- **Trust-dependent** (affiliates build audience relationships)

### Major Affiliate Networks
| Network | Strength | Typical Verticals |
|---------|----------|-------------------|
| **ShareASale** | Mid-market merchants | Fashion, home, lifestyle |
| **CJ (Commission Junction)** | Enterprise brands | Retail, travel, finance |
| **Awin** | Global reach | Retail, telecom, travel |
| **Impact** | Technology-first | SaaS, DTC brands |
| **Rakuten** | Premium brands | Luxury, electronics |
| **PartnerStack** | B2B/SaaS focus | Software, services |

---

## CPA Networks (Deep Analysis)

CPA Networks are **optimized for behavior extraction**, not full value capture.

### Core Insight
**A CPA network offer is defined by the action required, not the product itself. The product is often incidental; the behavior is the commodity.**

CPA networks don't sell products—they sell **actions**. The advertiser buys a specific user behavior (signup, install, form fill), and the product behind it is just the context that makes that action possible.

### What CPA Networks Actually Sell

| What They Appear to Sell | What They Actually Sell |
|-------------------------|------------------------|
| App installs | User device access |
| Lead forms | Contact information |
| Trial signups | Time-limited engagement |
| Sweepstakes entries | Email/phone capture |
| Content unlocks | User commitment signals |

### Key Characteristics
- Payment tied to **intermediate actions** (not final revenue)
- Actions are **proxies** for value
- Higher volume, faster optimization cycles
- Higher fraud risk (actions easier to fake than sales)
- Faster payouts (often weekly)

### Why They Exist
CPA networks thrive where:
- Sales cycles are long (can't wait for conversion)
- Attribution is murky (multi-touch journeys)
- Advertisers want **predictable costs** (fixed CPA vs variable CPS)

**Key tradeoff**: CPA networks trade certainty of payment for uncertainty of eventual revenue.

### Offer-Market Equilibrium

CPA markets naturally tend toward equilibrium based on:

1. **Traffic supply constraints**
   - Limited high-quality traffic sources
   - Geographic/demographic targeting limits
   - Platform policy restrictions

2. **Payout floor dynamics**
   - Minimum viable payout for publishers to engage
   - Competition raises payouts until margins compress

3. **Quality-volume tradeoff**
   - Higher payouts attract more traffic
   - More traffic often means lower average quality
   - Advertisers adjust caps and payouts to find balance

4. **Fraud pressure**
   - As payouts rise, fraud becomes more attractive
   - Networks must invest in detection
   - Detection costs compress margins

The equilibrium price for an action = `(Advertiser's expected LTV from action × acceptable margin) - (network fee + fraud loss buffer)`

---

## Incentive Offers (Deep Analysis)

### Definition

**An incentive offer is a performance contract where the user's motivation is external to the advertiser's product, trading intent quality for speed and volume.**

An incentive offer is a CPA or affiliate offer where the user is explicitly rewarded for completing the required action. The reward does not come from the advertiser's product—it comes from the publisher or platform promoting the offer.

The real exchange: **"Do this action, and I'll give you something."**

That "something" might be:
- Cash or micropayments
- Gift cards
- Points/rewards
- Virtual currency
- Sweepstakes entries
- In-game rewards

The incentive is the primary motivation, not interest in the product.

### Why Incentive Offers Exist

Incentive offers exist to **lower friction to near zero**.

Humans are loss-averse, impatient primates. Incentives bypass curiosity, intent, and trust-building entirely.

**Excellent at:**
- Generating volume fast
- Clearing caps quickly
- Stress-testing funnels
- Bootstrapping data sets
- Geographic penetration testing

**Dangerous because:**
- Intent quality drops dramatically
- Retention collapses
- Fraud risk spikes
- Advertisers get angry if expectations aren't aligned

### Incentive vs Non-Incentive

| Aspect | Non-Incentive | Incentive |
|--------|---------------|-----------|
| User motivation | Wants the product | Wants the reward |
| Intent quality | High | Low |
| User retention | Normal | Very low |
| Fraud risk | Baseline | Elevated |
| Conversion speed | Variable | Very fast |
| LTV correlation | Strong | Weak/none |

**Key insight**: Incentive traffic is **behavior-for-rent**, not demand.

### Common Incentive Offer Types

Incentives typically attach to low-friction CPA actions:
- Email submit offers
- App installs
- Survey completions
- Trial signups
- Sweepstakes entries

Rarely effective for:
- High-ticket purchases
- Long-form applications
- Regulated financial products
- Subscription commitments

**Rule**: The harder the action, the weaker the incentive effect.

### Advertiser Restrictions

Many advertisers explicitly forbid incentivized traffic because:
- Users churn immediately
- Compliance rules are violated
- Metrics become meaningless
- LTV models are poisoned

CPA networks label offers as:
- **"Incent allowed"** — incentive traffic accepted
- **"Non-incent only"** — incentive traffic forbidden
- **"Incent with restrictions"** — specific conditions apply

**Warning**: Violating incent restrictions gets accounts terminated without ceremony.

### Incentive Platforms (Natural Habitat)

Incentive offers live on platforms like:
- Reward apps (Swagbucks, InboxDollars)
- "Get paid to" sites
- Mobile reward walls (Tapjoy, ironSource)
- Loyalty programs
- GPT (Get-Paid-To) networks

Users expect transactional behavior on these platforms. Advertisers tolerate it when they want raw volume, not engaged customers.

### When Incentive Makes Sense

**Rational uses:**
- QA and testing
- Early funnel validation
- Geographic/device testing
- Cap clearing for volume bonuses
- Competitor intelligence

**Self-sabotage uses:**
- Long-term growth modeling
- LTV calculations
- Brand building
- Customer acquisition cost baselines

### AI Reasoning Framework

For incentive offer detection and handling:

1. **Flag incentive-compatible offers** based on:
   - Low friction actions (email, install)
   - Platform type (reward app, GPT site)
   - Advertiser restrictions

2. **Discount conversion value** when incentive traffic suspected:
   - Typical discount: 60-90% vs organic intent

3. **Isolate incentive traffic** in analytics:
   - Never mix with non-incent for LTV modeling
   - Separate cohorts for retention analysis

4. **Avoid poisoning models**:
   - Exclude incent cohorts from CAC calculations
   - Flag blended metrics as unreliable

---

### Major CPA Networks
| Network | Focus | Typical Offers |
|---------|-------|----------------|
| **MaxBounty** | General CPA | Sweeps, trials, finance |
| **ClickDealer** | Mobile/global | Apps, utilities |
| **CrakRevenue** | Adult/dating | Subscriptions |
| **CPAlead** | Content locking | Mobile content |
| **PeerFly** | Performance | Mixed verticals |

---

## Influencer & Creator Networks (Modern Evolution)

A new category emerging that blends affiliate economics with social distribution.

### Key Characteristics
- **Trust is personal** (tied to individual creators)
- **Content is native** (not traditional ads)
- Attribution through unique links/codes
- Higher engagement, smaller scale per creator

### Major Platforms
| Platform | Model | Focus |
|----------|-------|-------|
| **TikTok Shop** | Hybrid (CPS + creator tools) | Social commerce |
| **LTK (rewardStyle)** | CPS | Fashion/lifestyle |
| **ShopMy** | CPS | Multi-retailer |
| **Amazon Influencer** | CPS | Product storefronts |
| **CreatorIQ** | Campaign-based | Brand partnerships |

---

## Network Economics

### How Networks Make Money
1. **Transaction fees**: Percentage of each payment (typically 20-30% of affiliate commission)
2. **Float**: Interest on held funds during payment delay
3. **Data**: Aggregate insights sold to advertisers
4. **Tools**: Premium features, API access, analytics

### The Trust Premium
Networks command fees because they provide:
- **Standardized contracts** (no custom legal work)
- **Unified tracking** (one pixel/link across merchants)
- **Fraud detection** (shared intelligence)
- **Payment guarantee** (network pays even if advertiser defaults)

---

## Decision Framework for AI Reasoning

For any network or offer, analyze:

1. **What behavior triggers payment?**
   - Impression, click, lead, action, or sale?

2. **How close is that behavior to real economic value?**
   - Is it a proxy or the actual revenue event?

3. **Who absorbs uncertainty?**
   - If the user never becomes profitable, who loses?

4. **What incentives does this create?**
   - Upstream (publisher optimization)
   - Downstream (advertiser expectations)

5. **Where does fraud most likely occur?**
   - What's the easiest thing to fake in this model?

---

## Deep Linking

### Definition

**Deep linking is the ability to create affiliate links that point to specific pages within a merchant's site, rather than just the homepage.**

Without deep linking: `https://merchant.com?ref=affiliate123` → Homepage only

With deep linking: `https://merchant.com/products/blue-widget?ref=affiliate123` → Specific product

### Why Deep Linking Matters

Deep links dramatically improve conversion because:

1. **Reduced friction** - User lands exactly where they want
2. **Intent preservation** - No navigation required after click
3. **Content alignment** - Affiliate content matches destination
4. **Higher relevance** - Product reviews link to that product

**Conversion impact**: Deep links typically convert 2-5x better than homepage links.

### Deep Link Structures

Different networks handle deep linking differently:

| Network | Deep Link Format |
|---------|------------------|
| **ShareASale** | `shareasale.com/r.cfm?u=AFFID&m=MERCHANTID&urllink=merchant.com/product` |
| **CJ** | `anrdoezrs.net/links/AFFID/type/dlg/https://merchant.com/product` |
| **Impact** | `MERCHANT.sjv.io/c/AFFID/CAMPAIGNID/URL` |
| **Awin** | `awin1.com/cread.php?awinmid=MERCHANTID&awinaffid=AFFID&ued=https://merchant.com/product` |
| **Rakuten** | `click.linksynergy.com/deeplink?id=AFFID&mid=MERCHANTID&murl=https://merchant.com/product` |

### Deep Link Generators

Most networks provide tools to create deep links:

1. **Bookmarklet** - Browser tool that generates link for current page
2. **API endpoint** - Programmatic link generation
3. **Dashboard tool** - Manual URL input in network interface
4. **Link builder plugins** - WordPress/browser extensions

### Deep Linking Restrictions

Some merchants restrict deep linking:

- **No deep links** - Homepage only (rare, usually brand protection)
- **Approved pages only** - Whitelist of allowed destinations
- **No product pages** - Category pages only
- **No sale/clearance** - Full-price items only

### Sub-ID Tracking with Deep Links

Deep links often include sub-ID parameters for tracking:

```
https://merchant.com/product?ref=aff123&subid=blogpost-review&subid2=sidebar
```

Sub-IDs help affiliates track:
- Which content drove the sale
- Which placement performed best
- A/B test results
- Traffic source attribution

### Technical Considerations

**URL Encoding**: Deep link URLs must be properly encoded
```
Original: https://merchant.com/products?color=blue&size=large
Encoded:  https%3A%2F%2Fmerchant.com%2Fproducts%3Fcolor%3Dblue%26size%3Dlarge
```

**Redirect chains**: Deep links often create multiple redirects:
```
Affiliate link → Network tracking → Merchant landing page
```
Each redirect adds latency. Best networks minimize hops.

**Mobile deep linking**: Links to app content (not just web)
- iOS Universal Links
- Android App Links
- Deferred deep linking (installs app first, then opens content)

### Deep Linking for Different Content Types

| Content Type | Deep Link Strategy |
|--------------|-------------------|
| **Product reviews** | Link to exact product |
| **Comparison posts** | Link to each compared product |
| **Category guides** | Link to category pages |
| **Deal posts** | Link to sale/coupon pages |
| **Brand content** | Homepage may be appropriate |

### AI Considerations

When building affiliate content, the AI should:

1. **Always prefer deep links** over homepage links
2. **Match link destination to content context**
3. **Verify deep linking is allowed** for the merchant
4. **Include sub-IDs** for tracking performance
5. **Test links** before publishing (redirects can break)

---

## Taxonomy for Database

### Network Types
```
affiliate        - Sale-based commission
cpa              - Action-based payment
cpc              - Click-based payment
cpl              - Lead-based payment
influencer       - Creator-focused platforms
hybrid           - Multiple models supported
in-house         - Merchant-run programs
sub-network      - Aggregates other networks
```

### Payout Models
```
cps              - Cost per sale (percentage)
cpa              - Cost per action (flat fee)
cpl              - Cost per lead (flat fee)
revshare         - Revenue share (ongoing %)
hybrid           - Multiple models
tiered           - Performance-based tiers
recurring        - Ongoing commissions
```

### Risk Profile (who bears more risk)
```
advertiser_heavy - CPM, CPC models
balanced         - CPL, some CPA
publisher_heavy  - CPS, RevShare
```

---

## Implications for AffiliatePrograms.wiki

### Data Model Enhancements
- Track **payout_model** for each program
- Categorize networks by **type** (affiliate, cpa, influencer, etc.)
- Store **risk_profile** indicator
- Track **payment_terms** (NET30, weekly, etc.)

### User Value
Help users find programs that match their:
- Traffic type (content vs. paid vs. social)
- Risk tolerance (CPA vs CPS)
- Cash flow needs (fast payout vs. higher commission)

### AI Integration Points
- Recommend programs based on traffic characteristics
- Estimate potential earnings by model type
- Flag programs with misaligned incentives
- Detect arbitrage opportunities across networks
