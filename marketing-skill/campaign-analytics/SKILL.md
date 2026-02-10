---
name: campaign-analytics
description: Analyzes campaign performance with multi-touch attribution, funnel conversion, and ROI calculation for marketing optimization
license: MIT
metadata:
  version: 1.0.0
  author: Alireza Rezvani
  category: marketing
  domain: campaign-analytics
  updated: 2026-02-06
  python-tools: attribution_analyzer.py, funnel_analyzer.py, campaign_roi_calculator.py, meta_content_fetcher.py
  tech-stack: marketing-analytics, attribution-modeling
---

# Campaign Analytics

Production-grade campaign performance analysis with multi-touch attribution modeling, funnel conversion analysis, and ROI calculation. Three Python CLI tools provide deterministic, repeatable analytics using standard library only -- no external dependencies, no API calls, no ML models.

---

## Table of Contents

- [Capabilities](#capabilities)
- [Input Requirements](#input-requirements)
- [Output Formats](#output-formats)
- [How to Use](#how-to-use)
- [Scripts](#scripts)
- [Reference Guides](#reference-guides)
- [Connecting Meta (Facebook & Instagram)](#connecting-meta-facebook--instagram)
- [Best Practices](#best-practices)
- [Limitations](#limitations)

---

## Capabilities

- **Multi-Touch Attribution**: Five attribution models (first-touch, last-touch, linear, time-decay, position-based) with configurable parameters
- **Funnel Conversion Analysis**: Stage-by-stage conversion rates, drop-off identification, bottleneck detection, and segment comparison
- **Campaign ROI Calculation**: ROI, ROAS, CPA, CPL, CAC metrics with industry benchmarking and underperformance flagging
- **A/B Test Support**: Templates for structured A/B test documentation and analysis
- **Channel Comparison**: Cross-channel performance comparison with normalized metrics
- **Executive Reporting**: Ready-to-use templates for campaign performance reports

---

## Input Requirements

All scripts accept a JSON file as positional input argument. See `assets/sample_campaign_data.json` for complete examples.

### Attribution Analyzer

```json
{
  "journeys": [
    {
      "journey_id": "j1",
      "touchpoints": [
        {"channel": "organic_search", "timestamp": "2025-10-01T10:00:00", "interaction": "click"},
        {"channel": "email", "timestamp": "2025-10-05T14:30:00", "interaction": "open"},
        {"channel": "paid_search", "timestamp": "2025-10-08T09:15:00", "interaction": "click"}
      ],
      "converted": true,
      "revenue": 500.00
    }
  ]
}
```

### Funnel Analyzer

```json
{
  "funnel": {
    "stages": ["Awareness", "Interest", "Consideration", "Intent", "Purchase"],
    "counts": [10000, 5200, 2800, 1400, 420]
  }
}
```

### Campaign ROI Calculator

```json
{
  "campaigns": [
    {
      "name": "Spring Email Campaign",
      "channel": "email",
      "spend": 5000.00,
      "revenue": 25000.00,
      "impressions": 50000,
      "clicks": 2500,
      "leads": 300,
      "customers": 45
    }
  ]
}
```

---

## Output Formats

All scripts support two output formats via the `--format` flag:

- `--format text` (default): Human-readable tables and summaries for review
- `--format json`: Machine-readable JSON for integrations and pipelines

---

## How to Use

### Attribution Analysis

```bash
# Run all 5 attribution models
python scripts/attribution_analyzer.py campaign_data.json

# Run a specific model
python scripts/attribution_analyzer.py campaign_data.json --model time-decay

# JSON output for pipeline integration
python scripts/attribution_analyzer.py campaign_data.json --format json

# Custom time-decay half-life (default: 7 days)
python scripts/attribution_analyzer.py campaign_data.json --model time-decay --half-life 14
```

### Funnel Analysis

```bash
# Basic funnel analysis
python scripts/funnel_analyzer.py funnel_data.json

# JSON output
python scripts/funnel_analyzer.py funnel_data.json --format json
```

### Campaign ROI Calculation

```bash
# Calculate ROI metrics for all campaigns
python scripts/campaign_roi_calculator.py campaign_data.json

# JSON output
python scripts/campaign_roi_calculator.py campaign_data.json --format json
```

---

## Connecting Meta (Facebook & Instagram)

To **download content stats** from your Facebook Page and linked Instagram Business account and run campaign-analytics (and optional social-media-analyzer), use the Meta Graph API fetcher.

### 1. Get API access

1. Go to [Meta for Developers](https://developers.facebook.com/) → Create App → Business type.
2. Add **Facebook Login** and **Instagram Graph API** (or **Marketing API** if you need Ads later).
3. Under **App Review**, request these permissions (or use Graph API Explorer for testing):
   - **Facebook Page:** `pages_show_list`, `pages_read_engagement`, `read_insights`
   - **Instagram (linked to Page):** `instagram_basic`, `instagram_manage_insights`
4. Generate a **User** or **Page** access token with those permissions. For a long-lived token, use [Access Token Tool](https://developers.facebook.com/tools/accesstoken/) or exchange a short-lived token for a long-lived one.
5. Find your **Page ID**: Page → About → scroll to "Page ID", or from the Page’s URL (`facebook.com/PAGE_ID`).

### 2. Fetch content and stats

From the `campaign-analytics` directory (or with paths adjusted):

```bash
# Required: your token and Facebook Page ID
export META_TOKEN="your_access_token"
export META_PAGE_ID="your_page_id"

# Download all content stats (Facebook + Instagram) and get both output formats
python scripts/meta_content_fetcher.py --token "$META_TOKEN" --page-id "$META_PAGE_ID" --output all --format json > meta_export.json

# Or only campaigns format (for ROI calculator)
python scripts/meta_content_fetcher.py --token "$META_TOKEN" --page-id "$META_PAGE_ID" --output campaigns --format json > meta_campaigns.json

# Or only social_media format (for social-media-analyzer: use .platforms.facebook or .platforms.instagram)
python scripts/meta_content_fetcher.py --token "$META_TOKEN" --page-id "$META_PAGE_ID" --output social_media --format json > meta_social.json

# Download as CSV (MVP): always writes to results/ with timestamp (e.g. results/cabo_seafaris_2026-02-09_17-45.csv)
python scripts/meta_content_fetcher.py --token "$META_TOKEN" --page-id "$META_PAGE_ID" --output csv
python scripts/meta_content_fetcher.py --token "$META_TOKEN" --page-id "$META_PAGE_ID" --output csv -o cabo_seafaris
```

- **Limit:** `--limit 50` (default 25) to fetch more posts per platform.
- **Instagram:** Only included if the Page has a linked Instagram Business/Creator account.
- **API key (token) for mass Instagram/Reels stats:** See **assets/meta_api_setup.md** → “Getting an API key for Instagram Reels & Posts (mass stats)” for the full process (create app, permissions, token, Page ID).
- **CSV → Google Sheets:** After generating the CSV, use File → Import → Upload in Google Sheets to load it (MVP); a future option may push directly to a GSheet.

### 3. Run analysis

**Campaign ROI (organic aggregate):**

```bash
# Use the "campaigns" part of the export (or meta_campaigns.json)
python scripts/campaign_roi_calculator.py meta_campaigns.json
python scripts/campaign_roi_calculator.py meta_campaigns.json --format json
```

**Social media (per-post engagement):**  
Use the `social_media` object from `meta_export.json`, or `platforms.facebook` / `platforms.instagram` from `meta_social.json`, as input to the **social-media-analyzer** skill (each platform has `platform`, `posts[]`, `total_spend`).

### 4. Security

- Never commit tokens. Use environment variables or a local `.env` (and add `.env` to `.gitignore`).
- Prefer short-lived tokens for testing; long-lived or Page tokens for automation.
- See `assets/meta_api_setup.md` for a step-by-step token and permission checklist.

---

## Scripts

### 1. attribution_analyzer.py

Implements five industry-standard attribution models to allocate conversion credit across marketing channels:

| Model | Description | Best For |
|-------|-------------|----------|
| First-Touch | 100% credit to first interaction | Brand awareness campaigns |
| Last-Touch | 100% credit to last interaction | Direct response campaigns |
| Linear | Equal credit to all touchpoints | Balanced multi-channel evaluation |
| Time-Decay | More credit to recent touchpoints | Short sales cycles |
| Position-Based | 40/20/40 split (first/middle/last) | Full-funnel marketing |

### 2. funnel_analyzer.py

Analyzes conversion funnels to identify bottlenecks and optimization opportunities:

- Stage-to-stage conversion rates and drop-off percentages
- Automatic bottleneck identification (largest absolute and relative drops)
- Overall funnel conversion rate
- Segment comparison when multiple segments are provided

### 3. campaign_roi_calculator.py

Calculates comprehensive ROI metrics with industry benchmarking:

- **ROI**: Return on investment percentage
- **ROAS**: Return on ad spend ratio
- **CPA**: Cost per acquisition
- **CPL**: Cost per lead
- **CAC**: Customer acquisition cost
- **CTR**: Click-through rate
- **CVR**: Conversion rate (leads to customers)
- Flags underperforming campaigns against industry benchmarks

### 4. meta_content_fetcher.py

Fetches content and insights from a Facebook Page and its linked Instagram Business account via the Meta Graph API (no pip dependencies; uses `urllib` only):

- **Facebook:** Page posts and post insights (impressions, engaged users, clicks).
- **Instagram:** Media list and media insights for **Reels and posts** (reach, likes, comments, saves, shares, impressions).
- **Outputs:** JSON (`social_media`, `campaigns`) and **CSV** (MVP: one file with all Reels/posts stats, GSheet-ready).

Use `--output csv -o file.csv` to download stats to CSV (optionally `--instagram-only`, `--limit N`). For how to get the API token for mass Instagram/Reels stats, see **assets/meta_api_setup.md** → “Getting an API key for Instagram Reels & Posts (mass stats)”.

Requires a Page or User access token with `pages_show_list`, `pages_read_engagement`, `read_insights`, and for Instagram: `instagram_basic`, `instagram_manage_insights`. See [Connecting Meta](#connecting-meta-facebook--instagram) and `assets/meta_api_setup.md`.

---

## Reference Guides

| Guide | Location | Purpose |
|-------|----------|---------|
| Attribution Models Guide | `references/attribution-models-guide.md` | Deep dive into 5 models with formulas, pros/cons, selection criteria |
| Campaign Metrics Benchmarks | `references/campaign-metrics-benchmarks.md` | Industry benchmarks by channel and vertical for CTR, CPC, CPM, CPA, ROAS |
| Funnel Optimization Framework | `references/funnel-optimization-framework.md` | Stage-by-stage optimization strategies, common bottlenecks, best practices |

---

## Best Practices

1. **Use multiple attribution models** -- No single model tells the full story. Compare at least 3 models to triangulate channel value.
2. **Set appropriate lookback windows** -- Match your time-decay half-life to your average sales cycle length.
3. **Segment your funnels** -- Always compare segments (channel, cohort, geography) to identify what drives best performance.
4. **Benchmark against your own history first** -- Industry benchmarks provide context, but your own historical data is the most relevant comparison.
5. **Run ROI analysis at regular intervals** -- Weekly for active campaigns, monthly for strategic review.
6. **Include all costs** -- Factor in creative, tooling, and labor costs alongside media spend for accurate ROI.
7. **Document A/B tests rigorously** -- Use the provided template to ensure statistical validity and clear decision criteria.

---

## Limitations

- **No statistical significance testing** -- A/B test analysis requires external tools for p-value calculations. Scripts provide descriptive metrics only.
- **Standard library only** -- No advanced statistical or data processing libraries. Suitable for most campaign sizes but not optimized for datasets exceeding 100K journeys.
- **Offline analysis** -- Core scripts (attribution, funnel, ROI) analyze static JSON. Use `meta_content_fetcher.py` to pull Facebook/Instagram content stats from the Meta Graph API into that pipeline.
- **Single-currency** -- All monetary values assumed to be in the same currency. No currency conversion support.
- **Simplified time-decay** -- Uses exponential decay based on configurable half-life. Does not account for weekday/weekend or seasonal patterns.
- **No cross-device tracking** -- Attribution operates on provided journey data as-is. Cross-device identity resolution must be handled upstream.
