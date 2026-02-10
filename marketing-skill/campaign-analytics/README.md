# Campaign Analytics

Campaign performance analysis with multi-touch attribution, funnel conversion, ROI calculation, and Meta (Facebook/Instagram) content stats export.

---

## How to Run

### Attribution, Funnel, and ROI (JSON input)

From this directory:

```bash
# Attribution analysis (journey data)
python scripts/attribution_analyzer.py assets/sample_campaign_data.json

# Funnel analysis (stage counts)
python scripts/funnel_analyzer.py assets/sample_campaign_data.json

# Campaign ROI calculation
python scripts/campaign_roi_calculator.py assets/sample_campaign_data.json
```

Use `--format json` for machine-readable output.

### Meta (Facebook & Instagram) content stats → CSV

Download Reels and posts stats from your Facebook Page and linked Instagram account:

```bash
# 1. Set credentials (use a Page Access Token and your Page ID)
export META_TOKEN="your_access_token"
export META_PAGE_ID="your_page_id"

# 2. Run (output goes to results/ with timestamp, e.g. results/instagram_stats_2026-02-09_17-45.csv)
python scripts/meta_content_fetcher.py --token "$META_TOKEN" --page-id "$META_PAGE_ID" --output csv

# Custom filename prefix
python scripts/meta_content_fetcher.py --token "$META_TOKEN" --page-id "$META_PAGE_ID" --output csv -o cabo_seafaris

# Instagram only, fetch more posts
python scripts/meta_content_fetcher.py --token "$META_TOKEN" --page-id "$META_PAGE_ID" --output csv --instagram-only --limit 100
```

**First-time setup:** See [assets/meta_api_setup.md](assets/meta_api_setup.md) for creating a Meta app, permissions, and getting your token and Page ID.

---

## Documentation

| Doc | Description |
|-----|-------------|
| [SKILL.md](SKILL.md) | Full skill documentation, input formats, reference guides |
| [assets/meta_api_setup.md](assets/meta_api_setup.md) | Meta API setup: app creation, permissions, token, Page ID |
| [assets/sample_campaign_data.json](assets/sample_campaign_data.json) | Example input for attribution, funnel, and ROI scripts |
