# Changelog

All notable changes to this project. The format follows [Keep a Changelog](https://keepachangelog.com/),
versioning follows [SemVer](https://semver.org/). The version lives in `__version__` in `youtube_cli.py`
and is printed by `youtube_cli.py --version`.

## [2.0.0] — 2026-08-18 — YouTube's new view counting + honest `--json` 📊

YouTube [unified how views are counted](https://support.google.com/youtube/thread/433409976) across
**all** formats on **2026-08-24**: a view is now counted the moment playback starts, with no minimum
watch time (Shorts have worked this way since 2025-03-31). The old, watch-time-gated number is gone
from the public Data API and survives only as **engaged views** in the Analytics API. This release
makes the CLI report both numbers and say which is which.

**Breaking change:** `analytics` without `--json` now prints an aligned table instead of raw JSON.
Scripts that parsed its output must add `--json` (the JSON shape itself is unchanged — it is still the
verbatim API `resultTable`).

### View counting
- **`engagedViews` added to the default `analytics` metrics** — every run now shows the new `views`
  next to the pre-2026-08-24 definition, so the methodology switch is visible instead of looking like
  a traffic spike. Verified live against the API: the metric already resolves today, and works with
  the `day`, `video`, `creatorContentType` and `insightTrafficSourceType` dimensions as well as with
  `--video-id`.
- **`stats --engaged`** — new flag fetching **lifetime** views + engaged views from the Analytics API
  for a channel (since its creation date) or a single video (since its publish date). Failure is
  non-fatal: a missing scope or a failed call warns on stderr and the Data API numbers still print.
- **Methodology note in human output** of `videos`, `video-get` and `stats`, explaining what `views`
  now counts and where the old definition went. Suppressed in `--json` output and when `--engaged`
  already prints both numbers.
- Legend under the `analytics` table whenever both `views` and `engagedViews` are present.

### Fixed
- **`--json` now returns valid JSON in `videos` and `playlists`.** Both printed a human summary line
  (`Showing 3 videos.` / `1 playlists found.`) *after* the JSON payload, so every consumer that parsed
  the output — script or agent — hit a decode error. The summary now prints only in human mode, and an
  empty result set returns `[]` instead of the prose `No videos found.`
- **`--sort -views` works.** The syntax documented in the command's own help died with
  `argument --sort: expected one argument`, because argparse reads a leading `-` as another flag.
  Values are now spliced into `--sort=-views` before parsing. `--sort` with a genuinely missing value
  still errors as before.
- **`analytics --dimensions` combinations that the docs advertised but the API refused.** The
  Analytics API only serves fixed dimension/metric combinations, so the documented
  `--dimensions insightTrafficSourceType` failed with `The query is not supported.` against the
  default metric set. The CLI now adapts what the user did not specify:
  - dimensions that only serve the core view metrics (`insightTrafficSourceType`,
    `insightPlaybackLocationType`, `deviceType`, `operatingSystem`, `subscribedStatus`) narrow the
    **default** metrics to `views,engagedViews,estimatedMinutesWatched` — an explicit `--metrics`
    always wins;
  - top-N dimensions (`video`, `playlist`, `insightTrafficSourceDetail`,
    `insightPlaybackLocationDetail`) get a default `--sort=-views` and `--max-results 25`, which the
    API requires — without them `--dimensions video` was rejected outright;
  - `--dimensions month` snaps both dates to the first of the month, which the API demands
    (`does not align to chosen date dimension`); with the default 28-day window it could never
    have worked.
  Every adjustment prints a note on **stderr**, so `--json` output stays clean.
- **Accurate error hints.** Analytics failures now suggest re-running `auth` only on 401/403, and
  point at the supported-combinations doc on `not supported` errors. The previous hint blamed the
  scope for any failure that mentioned `engagedViews`.

### Added
- **`--version`** flag and `__version__` in `youtube_cli.py`.
- **Human-readable `analytics` output** (aligned columns, thousands separators, floats to 2 decimals),
  which also makes `--json` mean something on this command for the first time — previously it was
  accepted and ignored.
- **`CHANGELOG.md`** (this file) and **`docs/api-notes.md`** — how the API actually behaves, incl.
  the live-verified gap between Data API `viewCount` and Analytics `views`.
- Hint on Analytics errors mentioning `engagedViews`: re-run `auth` to grant `yt-analytics.readonly`.
- `creatorContentType` documented as a dimension (splits Shorts from long-form).

### Docs
- README finally documents the `analytics` command (added in 1.1.0, never written up), the second
  API + scope it needs, and a section on the view counting change.

## [1.1.1] — 2026-07-04 — Thumbnail upload fix 🖼️

- **Fixed thumbnail upload** — the CLI sent `mimetype="image/*"`, which the API rejects. Now it uses
  `mimetypes.guess_type()` with a `image/jpeg` fallback, in both `upload` and `video-update`.

## [1.1.0] — 2026-06-20 — Analytics 📈

- **New `analytics` command** on the YouTube Analytics API v2: views, watch time, average view
  duration, **averageViewPercentage** (retention), traffic sources and subscriber changes, with
  `--days` / `--start-date` / `--end-date`, `--dimensions`, `--sort`, `--video-id`, `--max-results`.
- OAuth scope `yt-analytics.readonly` added (requires the YouTube Analytics API enabled in the Google
  Cloud project and a one-off `auth` re-run for tokens issued earlier).

## [1.0.0] — 2026-04-05 — Initial release 🚀

- YouTube Data API v3 CLI: `auth`, `videos`, `video-get`, `upload`, `video-update`, `video-delete`,
  `stats`, `playlists`.
- OAuth 2.0 installed-app flow with a refresh token stored outside the repo
  (`~/.youtube-cli-token.json`); credentials from `.env`.
- Resumable upload in ~12.5 MB chunks with exponential-backoff retry on 5xx.
- Safety defaults: uploads are **private**, `video-delete` requires `--confirm`.
- `--json` output on all commands for scripting and agent orchestration.
