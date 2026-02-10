#!/usr/bin/env python3
"""
Meta (Facebook + Instagram) content stats fetcher for campaign-analytics.

Fetches content and insights from a Facebook Page and its linked Instagram
Business account via the Meta Graph API. Outputs JSON suitable for:
  - social-media-analyzer (per-post engagement)
  - campaign_roi_calculator (aggregate campaigns: organic_facebook, organic_instagram)

Requires: Page Access Token with pages_read_engagement, pages_show_list,
          instagram_basic, instagram_manage_insights (for Instagram).
Uses: urllib only (no pip dependencies).

Usage:
    python meta_content_fetcher.py --token YOUR_TOKEN --page-id PAGE_ID [--limit 50]
    python meta_content_fetcher.py --token YOUR_TOKEN --page-id PAGE_ID --output social_media
    python meta_content_fetcher.py --token YOUR_TOKEN --page-id PAGE_ID --output campaigns
    python meta_content_fetcher.py --token YOUR_TOKEN --page-id PAGE_ID --output csv -o instagram_stats.csv
    python meta_content_fetcher.py --token YOUR_TOKEN --page-id PAGE_ID --output csv -o stats.csv --instagram-only --limit 100
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

GRAPH_API_BASE = "https://graph.facebook.com"
DEFAULT_API_VERSION = "v21.0"

# Default output dir (relative to campaign-analytics); gitignored
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CAMPAIGN_ANALYTICS_DIR = os.path.dirname(_SCRIPT_DIR)
DEFAULT_RESULTS_DIR = os.path.join(_CAMPAIGN_ANALYTICS_DIR, "results")


def _load_dotenv() -> None:
    """Load .env into os.environ (stdlib only). Looks in campaign-analytics dir, then cwd."""
    for base in (_CAMPAIGN_ANALYTICS_DIR, os.getcwd()):
        path = os.path.join(base, ".env")
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, val = line.partition("=")
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        if key:
                            os.environ.setdefault(key, val)
            break


def api_get(access_token: str, path: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """GET a Meta Graph API endpoint. path is e.g. /v21.0/PAGE_ID/posts."""
    params = dict(params or {})
    params["access_token"] = access_token
    url = f"{GRAPH_API_BASE}{path}?{urlencode(params)}"
    req = Request(url, method="GET")
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        body = e.read().decode() if e.fp else ""
        try:
            err = json.loads(body)
            raise RuntimeError(err.get("error", {}).get("message", body) or str(e))
        except json.JSONDecodeError:
            raise RuntimeError(body or str(e))
    except URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")


def get_page_posts(access_token: str, page_id: str, limit: int, api_version: str) -> List[Dict[str, Any]]:
    """Fetch recent Page posts (id, message, created_time)."""
    path = f"/{api_version}/{page_id}/posts"
    params = {"fields": "id,message,created_time,full_picture", "limit": str(limit)}
    data = api_get(access_token, path, params)
    return data.get("data", [])


def get_post_insights(access_token: str, post_id: str, api_version: str) -> Dict[str, int]:
    """Fetch insights for a single Page post. Returns dict of metric -> value."""
    path = f"/{api_version}/{post_id}/insights"
    # post_impressions, post_engaged_users, post_clicks (link clicks when available)
    params = {"metric": "post_impressions,post_engaged_users,post_clicks"}
    data = api_get(access_token, path, params)
    result: Dict[str, int] = {}
    for item in data.get("data", []):
        name = item.get("name")
        values = item.get("values", [])
        if name and values:
            # Use latest value (lifetime or last period)
            result[name] = int(values[-1].get("value", 0))
    return result


def fetch_facebook_content(
    access_token: str, page_id: str, limit: int, api_version: str
) -> List[Dict[str, Any]]:
    """Fetch Facebook Page posts and their insights."""
    posts = get_page_posts(access_token, page_id, limit, api_version)
    out = []
    for p in posts:
        pid = p.get("id", "")
        created = p.get("created_time", "")
        insights = get_post_insights(access_token, pid, api_version)
        impressions = insights.get("post_impressions", 0)
        engaged = insights.get("post_engaged_users", 0)
        clicks = insights.get("post_clicks", 0)
        out.append({
            "post_id": pid,
            "content_type": "video" if p.get("full_picture") else "image",
            "message": (p.get("message") or "")[:200],
            "likes": 0,  # Page post insights don't give likes in simple metrics; use engaged as proxy
            "comments": 0,
            "shares": 0,
            "saves": 0,
            "reach": engaged,  # use engaged_users as reach proxy when reach not in standard metrics
            "impressions": impressions,
            "clicks": clicks,
            "engagement_proxy": engaged,
            "posted_at": created,
        })
    return out


def get_instagram_business_id(access_token: str, page_id: str, api_version: str) -> Optional[str]:
    """Get Instagram Business Account ID linked to the Page."""
    path = f"/{api_version}/{page_id}"
    params = {"fields": "instagram_business_account"}
    data = api_get(access_token, path, params)
    ig = data.get("instagram_business_account")
    if ig is None:
        return None
    return ig.get("id") if isinstance(ig, dict) else str(ig)


def get_instagram_media_list(
    access_token: str, ig_user_id: str, limit: int, api_version: str
) -> List[Dict[str, Any]]:
    """Fetch Instagram media (feed + reels) IDs and basic fields.
    Includes like_count and comments_count (direct fields, no insights needed).
    media_product_type distinguishes FEED vs REELS for correct insights metrics."""
    path = f"/{api_version}/{ig_user_id}/media"
    params = {
        "fields": "id,media_type,media_product_type,caption,timestamp,like_count,comments_count",
        "limit": str(limit),
    }
    data = api_get(access_token, path, params)
    return data.get("data", [])


def get_instagram_media_insights(
    access_token: str,
    media_id: str,
    media_type: str,
    media_product_type: str,
    api_version: str,
) -> Dict[str, int]:
    """Fetch insights for one Instagram media.
    Per Meta docs: use views for REELS/video (impressions deprecated for new Reels).
    media_product_type: FEED, REELS, or STORY - determines which metrics are valid."""
    path = f"/{api_version}/{media_id}/insights"
    product = (media_product_type or "FEED").upper()
    # reach, saved, shares available for FEED and REELS
    # views: for video/reels (impressions deprecated for new Reels per Meta changelog)
    # Avoid impressions for REELS - can cause empty/error response for media after July 2024
    metrics = "reach,saved,shares"
    if product == "REELS" or media_type.upper() == "VIDEO":
        metrics += ",views"  # views replaces impressions for Reels/video
    else:
        metrics += ",impressions"  # OK for FEED images/carousels
    params = {"metric": metrics, "period": "lifetime"}
    try:
        data = api_get(access_token, path, params)
    except RuntimeError:
        return {}
    result: Dict[str, int] = {}
    for item in data.get("data", []):
        name = item.get("name")
        values = item.get("values", [])
        if name and values:
            result[name] = int(values[-1].get("value", 0))
    return result


def fetch_instagram_content(
    access_token: str, ig_user_id: str, limit: int, api_version: str
) -> List[Dict[str, Any]]:
    """Fetch Instagram media and their insights."""
    media_list = get_instagram_media_list(access_token, ig_user_id, limit, api_version)
    out = []
    for m in media_list:
        mid = m.get("id", "")
        media_type = m.get("media_type", "IMAGE")
        media_product_type = m.get("media_product_type", "FEED")
        ts = m.get("timestamp", "")
        # like_count and comments_count are direct media fields (no insights needed)
        likes = m.get("like_count", 0) or 0
        comments = m.get("comments_count", 0) or 0
        insights = get_instagram_media_insights(
            access_token, mid, media_type, media_product_type, api_version
        )
        reach = insights.get("reach", 0)
        views = insights.get("views", 0)
        impressions = insights.get("impressions", 0) or views or reach
        saved = insights.get("saved", 0)
        shares = insights.get("shares", 0)
        content_type = "video" if media_type in ("VIDEO", "REELS") else "carousel" if media_type == "CAROUSEL_ALBUM" else "image"
        caption = (m.get("caption") or "")[:500]
        out.append({
            "post_id": mid,
            "media_type": media_type,
            "content_type": content_type,
            "caption": caption,
            "media_product_type": media_product_type,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": saved,
            "reach": reach,
            "impressions": impressions,
            "views": views,
            "clicks": 0,  # not in standard media insights
            "posted_at": ts,
        })
    return out


def build_social_media_output(
    facebook_posts: List[Dict[str, Any]], instagram_posts: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build output compatible with social-media-analyzer (per platform)."""
    return {
        "meta_fetched_at": datetime.utcnow().isoformat() + "Z",
        "platforms": {
            "facebook": {
                "platform": "facebook",
                "total_spend": 0,
                "posts": facebook_posts,
            },
            "instagram": {
                "platform": "instagram",
                "total_spend": 0,
                "posts": instagram_posts,
            },
        },
    }


def build_campaigns_output(
    facebook_posts: List[Dict[str, Any]], instagram_posts: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build campaigns array for campaign_roi_calculator (aggregate organic)."""
    def agg(posts: List[Dict[str, Any]], name: str, channel: str) -> Dict[str, Any]:
        impressions = sum(p.get("impressions", 0) for p in posts)
        clicks = sum(p.get("clicks", 0) for p in posts)
        engagement = sum(
            p.get("engagement_proxy", 0) or p.get("likes", 0) + p.get("comments", 0) + p.get("shares", 0)
            for p in posts
        )
        return {
            "name": name,
            "channel": "organic_social",
            "spend": 0.0,
            "revenue": 0.0,
            "impressions": impressions,
            "clicks": clicks if clicks > 0 else engagement,
            "leads": 0,
            "customers": 0,
        }

    campaigns = []
    if facebook_posts:
        campaigns.append(agg(facebook_posts, "Facebook Page (organic)", "organic_social"))
    if instagram_posts:
        campaigns.append(agg(instagram_posts, "Instagram (organic)", "organic_social"))

    return {"campaigns": campaigns, "meta_fetched_at": datetime.utcnow().isoformat() + "Z"}


# Combined CSV columns for Instagram (reels + posts) and Facebook; safe for GSheet import
CSV_COLUMNS = [
    "platform", "post_id", "media_type", "media_product_type", "content_type", "posted_at", "text",
    "likes", "comments", "shares", "saves", "reach", "impressions", "views", "engagement_total",
    "engagement_rate_pct", "clicks", "fetched_at",
]


def _row_to_csv_row(platform: str, r: Dict[str, Any], text_key: str) -> Dict[str, Any]:
    text = (r.get(text_key) or "").replace("\n", " ").replace("\r", "")
    engagement = (
        r.get("likes", 0) + r.get("comments", 0) + r.get("shares", 0) + r.get("saves", 0)
        if platform == "instagram"
        else r.get("engagement_proxy", 0)
    )
    views = r.get("views", 0) or r.get("impressions", 0)
    engagement_rate = round(100 * engagement / views, 2) if views > 0 else 0.0
    return {
        "platform": platform,
        "post_id": r.get("post_id", ""),
        "media_type": r.get("media_type", ""),
        "media_product_type": r.get("media_product_type", ""),
        "content_type": r.get("content_type", ""),
        "posted_at": r.get("posted_at", ""),
        "text": text,
        "likes": r.get("likes", 0),
        "comments": r.get("comments", 0),
        "shares": r.get("shares", 0),
        "saves": r.get("saves", 0),
        "reach": r.get("reach", 0) if platform == "instagram" else r.get("engagement_proxy", 0),
        "impressions": r.get("impressions", 0),
        "views": r.get("views", 0),
        "engagement_total": engagement,
        "engagement_rate_pct": engagement_rate,
        "clicks": r.get("clicks", 0),
        "fetched_at": "",  # filled by write_csv
    }


def write_csv(
    instagram_posts: List[Dict[str, Any]],
    facebook_posts: List[Dict[str, Any]],
    path: str,
    instagram_only: bool = False,
) -> None:
    """Write Instagram reels/posts and optionally Facebook stats to one CSV (MVP; GSheet-ready)."""
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in instagram_posts:
            row = _row_to_csv_row("instagram", r, "caption")
            row["fetched_at"] = fetched_at
            w.writerow(row)
        if not instagram_only and facebook_posts:
            for r in facebook_posts:
                row = _row_to_csv_row("facebook", r, "message")
                row["fetched_at"] = fetched_at
                w.writerow(row)


def main() -> int:
    _load_dotenv()
    parser = argparse.ArgumentParser(
        description="Fetch Facebook Page and Instagram content stats from Meta Graph API."
    )
    parser.add_argument("--token", default=os.environ.get("META_TOKEN"), help="Meta Page or User access token (or set META_TOKEN in .env)")
    parser.add_argument("--page-id", default=os.environ.get("META_PAGE_ID"), help="Facebook Page ID (or set META_PAGE_ID in .env)")
    parser.add_argument("--limit", type=int, default=25, help="Max posts per platform (default 25)")
    parser.add_argument(
        "--output",
        choices=["all", "social_media", "campaigns", "csv"],
        default="all",
        help="Output: all, social_media, campaigns, or csv (download to file)",
    )
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format (ignored if --output csv)")
    parser.add_argument("-o", "--out-file", dest="out_file", help="For --output csv: filename prefix (output always goes to results/ with timestamp, e.g. results/prefix_YYYY-MM-DD_HHMM.csv)")
    parser.add_argument("--instagram-only", action="store_true", help="With --output csv: write only Instagram rows (no Facebook)")
    parser.add_argument("--api-version", default=DEFAULT_API_VERSION, help="Graph API version")
    args = parser.parse_args()

    if not args.token or not args.page_id:
        print("Error: --token and --page-id are required (or set META_TOKEN and META_PAGE_ID in .env).", file=sys.stderr)
        return 1

    try:
        fb_posts = fetch_facebook_content(
            args.token, args.page_id, args.limit, args.api_version
        )
    except RuntimeError as e:
        print(f"Facebook fetch error: {e}", file=sys.stderr)
        return 1

    ig_user_id = get_instagram_business_id(args.token, args.page_id, args.api_version)
    ig_posts: List[Dict[str, Any]] = []
    if ig_user_id:
        try:
            ig_posts = fetch_instagram_content(
                args.token, ig_user_id, args.limit, args.api_version
            )
        except RuntimeError as e:
            print(f"Instagram fetch warning: {e}", file=sys.stderr)
    else:
        print("No Instagram Business account linked to this Page.", file=sys.stderr)

    if args.output == "csv":
        os.makedirs(DEFAULT_RESULTS_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        prefix = (args.out_file or "instagram_stats").strip()
        if prefix.endswith(".csv"):
            prefix = prefix[:-4]
        out_path = os.path.join(DEFAULT_RESULTS_DIR, f"{prefix}_{timestamp}.csv")
        write_csv(ig_posts, fb_posts, out_path, instagram_only=args.instagram_only)
        print(f"Wrote {len(ig_posts)} Instagram + {0 if args.instagram_only else len(fb_posts)} Facebook rows to {out_path}", file=sys.stderr)
        return 0

    if args.format != "json":
        print("Facebook posts:", len(fb_posts))
        print("Instagram posts:", len(ig_posts))
        print("Use --format json to get full data.")
        return 0

    if args.output == "social_media":
        out = build_social_media_output(fb_posts, ig_posts)
    elif args.output == "campaigns":
        out = build_campaigns_output(fb_posts, ig_posts)
    else:
        out = {
            "social_media": build_social_media_output(fb_posts, ig_posts),
            "campaigns": build_campaigns_output(fb_posts, ig_posts),
        }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
