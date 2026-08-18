# API notes — how the YouTube APIs actually behave

Field notes for this CLI: the quirks that cost debugging time, verified live against the API where
noted. Last reviewed **2026-08-18**.

## Two APIs, two quotas, two scopes

| | Data API v3 | Analytics API v2 |
|---|---|---|
| Used by | `videos`, `video-get`, `upload`, `video-update`, `video-delete`, `stats`, `playlists` | `analytics`, `stats --engaged` |
| Scope | `https://www.googleapis.com/auth/youtube` | `https://www.googleapis.com/auth/yt-analytics.readonly` |
| Must be enabled in GCP | YouTube Data API v3 | YouTube Analytics API |
| Quota | 10,000 units/day (read 1, write 50, upload ~1,600) | separate quota, not shared with the Data API |
| Access | public data for any channel | **owned channels only** (`ids=channel==MINE`) |

Both scopes are requested by `auth`. A token minted before a scope was added does **not** gain it —
re-run `auth` once. That is why Analytics failures print a hint instead of just the raw error.

## View counting (the 2026-08-24 change)

YouTube changed what a "view" means, in two steps:

| Date | Scope of change |
|---|---|
| 2025-03-31 | **Shorts**: a view = a Short starts to play or replay, no minimum watch time |
| **2026-08-24** | **All formats** — long-form and live streams included — same definition |

What this means per surface:

- **Data API `statistics.viewCount`** — from 2026-08-24 it reports the new count for all content.
  The old definition is **not available anywhere in the public Data API**.
- **Analytics API `views`** — same new definition.
- **Analytics API `engagedViews`** — the *old* definition ("viewed past the initial seconds"). This
  is the metric to use for like-for-like comparisons with pre-August-2026 numbers. It is a **core
  metric** (subject to the deprecation policy) and works with `day`, `video`, `creatorContentType`
  and `insightTrafficSourceType` dimensions, and with a `video==ID` filter — all verified live.
- **Bulk Reporting API** — the same metric is called `engaged_views` (snake case).

Practical consequence: **a jump in `views` around 2026-08-24 is not growth.** Compare `engagedViews`
across that boundary, or you will read a definition change as a traffic spike. Channels with no
Shorts saw `views == engagedViews` before the switch (verified on this channel: 400 vs 400 over 28
days on 2026-08-18), so the two series only diverge going forward.

Sources: [Data API `statistics.viewCount`](https://developers.google.com/youtube/v3/docs/videos#statistics.viewCount),
[Analytics view metrics](https://developers.google.com/youtube/analytics/metrics#View_Metrics),
[Reporting metrics](https://developers.google.com/youtube/reporting/v1/reports/metrics#View_Metrics),
[announcement](https://support.google.com/youtube/thread/433409976).

## Data API `viewCount` ≠ Analytics `views`

They are different numbers and always have been — do not expect them to reconcile:

- Analytics is **despammed and processed**; the Data API count is the public-facing one.
- Analytics is bounded by the date range you ask for; `viewCount` is lifetime.
- Analytics data lags by roughly a day or two.

Live example (2026-08-18, this channel): Data API `viewCount` = 10,526 lifetime, Analytics `views`
since channel creation = 11,095. Both correct, neither is a bug. `stats --engaged` prints them side
by side and labels which is which.

## Analytics query gotchas

- **`--sort -views` and argparse.** A value starting with `-` looks like a flag to argparse, so the
  documented syntax used to fail with `argument --sort: expected one argument`. The CLI now rewrites
  `--sort -views` into `--sort=-views` before parsing (`_splice_negative_values`). Worth remembering
  if you add another flag whose value can start with a minus.
- **Unknown metric names fail the whole query** with HTTP 400 `Unknown identifier (X) given in field
  parameters.metrics` — there is no partial result, so a typo costs the entire call.
- **`maxResults` only makes sense with `dimensions`**; a totals query returns exactly one row.
- **Empty result sets are normal** for narrow date ranges (`rows` is simply absent, not empty).

### Dimensions only serve fixed metric combinations

The API does not compose dimensions and metrics freely — it serves a fixed catalogue of
[available reports](https://developers.google.com/youtube/analytics/v2/available_reports). Anything
outside it fails the *whole* query with `The query is not supported.` Measured live on 2026-08-18
against this CLI's default metric set (`views, engagedViews, estimatedMinutesWatched,
averageViewDuration, averageViewPercentage, subscribersGained, subscribersLost, likes, comments,
shares`):

| Dimension | Behaviour |
|---|---|
| `day`, `country`, `creatorContentType` | full default metric set works |
| `insightTrafficSourceType`, `insightPlaybackLocationType`, `deviceType`, `operatingSystem`, `subscribedStatus` | **core view metrics only** (`views, engagedViews, estimatedMinutesWatched`) |
| `video`, `playlist`, `insightTrafficSourceDetail`, `insightPlaybackLocationDetail` | top-N reports: **both** `sort` and `maxResults` are mandatory; with them, the full metric set works for `video` |
| `month` | both `startDate` and `endDate` must be the **first day of a month** (`2026-07-31` is rejected as "does not align to chosen date dimension") |
| `sharingService`, `insightTrafficSourceDetail` | need a matching filter (e.g. `insightTrafficSourceType==X`) — still refused otherwise |

The CLI fills in these requirements automatically when the user did not specify them (narrowing
default metrics, defaulting `--sort=-views --max-results 25` for top-N dimensions, snapping `month`
dates), and prints what it changed on stderr. Explicit flags always win.

## Data API gotchas

- **Thumbnails**: `mimetype="image/*"` is rejected — pass a concrete type
  (`mimetypes.guess_type()`, falling back to `image/jpeg`). Custom thumbnails also require a
  phone-verified YouTube account. Thumbnail failures are treated as non-fatal by this CLI: the video
  is already uploaded at that point, and failing the command would hide the video ID.
- **`videos.update` needs the full `snippet`** — sending only the changed fields wipes the rest. The
  CLI reads the current video first and merges, which costs an extra read unit per update.
- **`publishAt` requires `privacyStatus: private`**; the CLI forces it when `--publish-at` is set.
- **`search.list(forMine=True)`** costs **100 units** (not 1) and returns at most 50 results per page.
  `videos` therefore spends ~101 units per run: one search plus one batched `videos.list`.
- **`statistics.dislikeCount`** is owner-only since 2021-12-13; `favoriteCount` has been hardcoded
  to `0` since 2015.
- **Uploads are ~1,600 units** — the daily quota allows roughly 6 uploads plus normal traffic. Quota
  errors surface as `quotaExceeded` and reset at midnight Pacific time.

## OAuth notes

- The refresh token lives in `~/.youtube-cli-token.json`, deliberately outside the repo.
- In OAuth "Testing" mode refresh tokens expire after **7 days**. Publishing the consent screen
  (still without Google verification, for personal use) makes them long-lived.
- A revoked or expired refresh token surfaces as `invalid_grant`; the CLI detects it and tells you to
  re-run `auth` rather than dumping a raw traceback.
