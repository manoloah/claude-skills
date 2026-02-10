# Meta (Facebook & Instagram) API setup for campaign-analytics

Use this checklist to get a token and Page ID so you can run `scripts/meta_content_fetcher.py` and then analyze results with campaign-analytics and social-media-analyzer.

---

## Getting an API key for Instagram Reels & Posts (mass stats)

If your goal is to **download mass stats on Reels and posts from Instagram** (and optionally Facebook), follow this process. You will get an **access token** (often called “API key” in practice) that allows the script to pull insights for all your recent media.

### Step 1: Create a Meta App

1. Go to [developers.facebook.com](https://developers.facebook.com/) and log in.
2. Click **My Apps** → **Create App**.
3. Select **Business** as the app type (required for Instagram and Page insights).
4. Name the app (e.g. “Instagram stats export”) and add your contact email → **Create App**.

### Step 2: Add the right products

1. In the app dashboard, open **App settings** → **Basic** and note your **App ID** and **App Secret** (you’ll need the secret for long‑lived tokens).
2. In the dashboard, click **Add Product**.
3. Add **Facebook Login** (needed to get a user token that can access your Pages).
4. Add **Instagram Graph API** (or ensure **Instagram** is available) so the app can read Instagram Business/Creator accounts linked to your Page.

### Step 3: Request permissions for Reels and posts

1. Go to **App Review** → **Permissions and Features**.
2. Find and request (or add for development) these permissions:

   **For Instagram (Reels + feed posts):**

   - **`instagram_basic`** – Read your Instagram account info and list of media (posts and Reels).
   - **`instagram_manage_insights`** – Read insights for each piece of media (likes, comments, reach, saves, shares, impressions).

   **For the Facebook Page that owns the Instagram account:**

   - **`pages_show_list`** – List Pages you manage.
   - **`pages_read_engagement`** – Read Page content.
   - **`read_insights`** – Read Page/post insights (optional if you only care about Instagram).

3. In **Development** mode you can use these permissions without App Review. For a **production** app (e.g. for other users), you must submit for App Review.

### Step 4: Get your access token (“API key”)

**Quick test (short‑lived token, ~1 hour):**

1. Open [Graph API Explorer](https://developers.facebook.com/tools/explorer/).
2. Select your app in the top dropdown.
3. Click **Generate Access Token**.
4. In the permission list, enable: `instagram_basic`, `instagram_manage_insights`, `pages_show_list`, `pages_read_engagement` (and `read_insights` if you want Facebook post stats).
5. Generate the token and approve the prompts. Copy the token — this is your **short‑lived access token**.

**For scripts / automation (long‑lived token, ~60 days):**

1. Get a short‑lived token from the Explorer as above.
2. Exchange it for a long‑lived token by opening this URL in your browser (replace placeholders):

   `https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_LIVED_TOKEN`

3. The response contains `access_token` — use this as your **long‑lived token** in the script.

**Optional – Page token (for Page‑only automation):**

1. With a User token that has the Page permissions, call in the Explorer: `me/accounts`.
2. From the response, copy the **`access_token`** of the Page that has the Instagram account linked. Use this as the token in the script.

### Step 5: Get your Facebook Page ID

Your Instagram Business/Creator account must be **linked to a Facebook Page**. The script uses the **Page ID** to find the linked Instagram account.

1. In [Graph API Explorer](https://developers.facebook.com/tools/explorer/), with your token, call: **`me/accounts`**.
2. In the response, find the Page that has Instagram connected and copy its **`id`** — that’s your **Page ID**.

Alternatively: open your Facebook Page → **About** → **Page ID**, or check Page **Settings** in Meta Business Suite.

### Step 6: Run the script and download stats (e.g. CSV)

Use the same script to pull all Reels and posts and download them as CSV (MVP):

```bash
export META_TOKEN="your_access_token"
export META_PAGE_ID="your_page_id"

# Download Instagram (and Facebook) stats to CSV (writes to results/ with dated filename)
python scripts/meta_content_fetcher.py --token "$META_TOKEN" --page-id "$META_PAGE_ID" --output csv

# Instagram only (no Facebook rows), fetch 100 posts
python scripts/meta_content_fetcher.py --token "$META_TOKEN" --page-id "$META_PAGE_ID" --output csv --instagram-only --limit 100

# Custom output path
python scripts/meta_content_fetcher.py --token "$META_TOKEN" --page-id "$META_PAGE_ID" --output csv -o my_export.csv
```

The CSV includes: `platform`, `post_id`, `media_type` (REELS, IMAGE, VIDEO, CAROUSEL_ALBUM), `content_type`, `posted_at`, `text` (caption/message), `likes`, `comments`, `shares`, `saves`, `reach`, `impressions`, `engagement_total`, `clicks`. You can open it in Excel or **import into Google Sheets** (File → Import → Upload and select the CSV).

---

## 1. Create a Meta App

1. Go to [developers.facebook.com](https://developers.facebook.com/) and sign in.
2. **My Apps** → **Create App** → choose **Business**.
3. Enter app name and contact email; create the app.

---

## 2. Add products and permissions

1. In the app dashboard, open **App Review** → **Permissions and Features**.
2. Request (or add for development) the following:

   **For Facebook Page content and insights:**
   - `pages_show_list` – list Pages you manage
   - `pages_read_engagement` – read Page content and engagement
   - `read_insights` – read Page and post insights

   **For Instagram (if your Page is linked to an Instagram Business/Creator account):**
   - `instagram_basic` – read Instagram account and media
   - `instagram_manage_insights` – read Instagram media insights

3. For **development**, you can use these permissions without App Review. For **production**, submit for App Review.

---

## 3. Get an access token

**Option A – Graph API Explorer (quick test)**

1. Open [Graph API Explorer](https://developers.facebook.com/tools/explorer/).
2. Select your app in the top dropdown.
3. Click **Generate Access Token** and approve the permissions above.
4. Copy the token. This is **short-lived** (about 1 hour).

**Option B – Long-lived User token**

1. Get a short-lived token (e.g. from Graph API Explorer).
2. Exchange it:  
   `https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=SHORT_LIVED_TOKEN`
3. Use the returned `access_token` as your long-lived token (about 60 days).

**Option C – Page token (good for automation)**

1. With a User token that has the Page permissions, call:  
   `GET /v21.0/me/accounts`
2. Find your Page in the response and copy its `access_token`. Use this for `meta_content_fetcher.py` with that Page.

---

## 4. Find your Page ID

- **From Meta Business Suite:** Page → **Settings** → **Page ID** (or in the Page’s **About** section).
- **From URL:** If your Page URL is `facebook.com/YourPageName`, use [Graph API Explorer](https://developers.facebook.com/tools/explorer/) with path `me/accounts` (with Page token or User token with `pages_show_list`) to see `id` for the Page.
- **From Page source:** View page source on your Facebook Page and search for `"page_id"`.

---

## 5. Run the fetcher

```bash
# Do not commit the token; use env vars or a local .env
export META_TOKEN="your_access_token"
export META_PAGE_ID="your_page_id"

cd campaign-analytics
python scripts/meta_content_fetcher.py --token "$META_TOKEN" --page-id "$META_PAGE_ID" --output all --format json > meta_export.json
```

- **Instagram:** Data is included only if the Page has a linked **Instagram Business** or **Creator** account (in Page **Settings** → **Instagram**).
- **Rate limits:** If you hit rate limits, reduce `--limit` or wait before re-running.
- **Output location:** With `--output csv`, files are **always** written to `results/` with a timestamp in the filename (e.g. `results/instagram_stats_2026-02-09_17-45.csv`). Use `-o cabo_seafaris` to customize the prefix: `results/cabo_seafaris_2026-02-09_17-45.csv`. The CSV also includes a `fetched_at` column with the script run time. The `results/` folder is gitignored.

---

## 6. If metrics show zeros

The script now follows the [Instagram Platform API reference](https://developers.facebook.com/docs/instagram-platform/reference/instagram-media) correctly:

- **Likes and comments** come from the media object’s `like_count` and `comments_count` (direct fields; no insights call).
- **Reach, saves, shares** come from the insights API.
- **Reels/video:** Uses the `views` metric instead of deprecated `impressions` for newer content.
- **media_product_type** (FEED vs REELS) is used to choose the correct insight metrics.

If zeros persist, verify `instagram_manage_insights` and `instagram_basic` are granted, and that the app has the **Instagram** product (not only Facebook Login). See [Instagram Platform docs](https://developers.facebook.com/docs/instagram-platform).

---

## 7. Security checklist

- [ ] Never commit `META_TOKEN` or put it in version control.
- [ ] Add `.env` to `.gitignore` if you store the token there.
- [ ] Prefer Page token or long-lived User token for scripts; rotate tokens periodically.
- [ ] For production, use App Review and minimal required permissions.
- [ ] The `results/` folder and `*_stats.csv` files are gitignored; do not remove them from `.gitignore`.

---

## 8. Next steps

- **Campaign ROI:**  
  `python scripts/campaign_roi_calculator.py meta_campaigns.json`  
  (Use `--output campaigns` and save to `meta_campaigns.json` if you only need ROI input.)
- **Per-post engagement:**  
  Use the `social_media` / `platforms.facebook` or `platforms.instagram` object from the fetcher output as input to the **social-media-analyzer** skill.
