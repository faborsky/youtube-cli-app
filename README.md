# YouTube CLI

**🇬🇧 English** · [🇨🇿 Čeština](README.cs.md) · [🇪🇸 Español](i18n/README.es.md) · [🇧🇷 Português](i18n/README.pt-BR.md) · [🇩🇪 Deutsch](i18n/README.de.md) · [🇫🇷 Français](i18n/README.fr.md) · [🇨🇳 简体中文](i18n/README.zh-CN.md) · [🇯🇵 日本語](i18n/README.ja.md) · [🇸🇪 Svenska](i18n/README.sv.md) · [🇳🇴 Norsk](i18n/README.nb.md) · [🇩🇰 Dansk](i18n/README.da.md)

A Python command-line tool for managing videos on [YouTube](https://www.youtube.com/) through the YouTube Data API v3 and for reading channel performance through the YouTube Analytics API v2. It's for anyone who publishes on YouTube regularly and is tired of clicking through YouTube Studio. Uploads, metadata, thumbnails, playlists, stats, watch time and retention, all from the terminal. Built so that [Claude Code](https://docs.anthropic.com/en/docs/claude-code) or another AI agent can drive it.

Author: [Jindřich Fáborský](https://www.faborsky.com)

**v2.0.0** · [Changelog](CHANGELOG.md) · [API notes](docs/api-notes.md)

> [!TIP]
> **The app is free and it's yours.** Clone it, use it, rebuild it your way.
>
> Want to build tools like this for your own marketing? That's what I teach: **[faborsky.com](https://www.faborsky.com)**.

> **📊 Views are counted differently since August 24, 2026.** YouTube now counts a view as soon as playback starts, with no minimum watch time, for **all** formats (Shorts have worked this way since March 31, 2025). The old definition is gone from the public Data API and survives as **engaged views** in the Analytics API. This CLI shows both, see [View counting](#view-counting-since-august-24-2026).

## Why this exists

Publishing a video on YouTube involves a lot of repetitive manual work: upload the file through the web interface, fill in the title and description, set privacy, add a thumbnail, put it in a playlist. This CLI automates those steps so you can script them or chain them with other tools.

Here's what a podcast release driven by Claude Code can look like:

1. **Transcribe** the audio with [whisper-cz-en](https://github.com/faborsky/whisper-cz-en)
2. **Generate metadata** (title, description, chapters) from the transcript
3. **Upload the audio** to Podbean with [podbean-app](https://github.com/faborsky/podbean-app)
4. **Upload the video** to YouTube with this CLI
5. **Set the thumbnail** and add it to a playlist, automatically

All in one conversation.

## What you need

- **Python 3.9+**
- **A YouTube channel** linked to a Google account
- **A Google Cloud project** with the YouTube Data API v3 enabled and OAuth 2.0 credentials
- For the `analytics` command: the **YouTube Analytics API** enabled in the same project

## Google Cloud setup

Before using the CLI, you need a Google Cloud project and OAuth credentials. You only do this once.

### 1. Create a Google Cloud project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown (top bar) → **New Project**
3. Name it (e.g. `youtube-cli`) → **Create**
4. Select the new project in the dropdown

### 2. Enable the APIs

1. Go to **APIs & Services → Library** ([direct link](https://console.cloud.google.com/apis/library))
2. Search for **YouTube Data API v3** → click it → **Enable**
3. Search for **YouTube Analytics API** → click it → **Enable** (needed for the `analytics` command and for `stats --engaged`; skip it if you only publish videos)

### 3. Configure the OAuth consent screen

1. Go to **APIs & Services → OAuth consent screen**
2. Choose the **External** user type → **Create**
3. Fill in the required fields:
   - **App name:** any name (e.g. `Video Manager CLI`)
   - **User support email:** your email
   - **Developer contact:** your email
4. Click **Save and Continue**
5. On the **Scopes** page → **Add or Remove Scopes** → add `https://www.googleapis.com/auth/youtube` and `https://www.googleapis.com/auth/yt-analytics.readonly` → **Save and Continue**
6. On the **Test users** page → **Add Users** → add the Gmail address that owns your channel → **Save and Continue**

> **Watch out for token expiry:** In "Testing" mode, OAuth refresh tokens expire after **7 days**. To get long-lived tokens, click **Publish App** on the OAuth consent screen page. For personal-use apps where only your own account signs in, Google usually doesn't require any further verification.

### 4. Create OAuth credentials

1. Go to **APIs & Services → Credentials** ([direct link](https://console.cloud.google.com/apis/credentials))
2. Click **Create Credentials → OAuth client ID**
3. Application type: **Desktop app**
4. Name: anything (e.g. `YouTube CLI`)
5. Click **Create**
6. Copy the **Client ID** and **Client Secret**

The Client ID looks like `123456789-abc.apps.googleusercontent.com`; the Client Secret is a short alphanumeric string.

## Installation

```bash
git clone https://github.com/faborsky/youtube-cli-app.git
cd youtube-cli-app

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your Google Cloud OAuth credentials
```

## Configuration

Put the OAuth credentials from the Google Cloud setup into `.env`:

```
YOUTUBE_CLIENT_ID=your-client-id-here
YOUTUBE_CLIENT_SECRET=your-client-secret-here
```

Then sign in once (a browser window opens):

```bash
python youtube_cli.py auth
```

This saves a long-lived refresh token to `~/.youtube-cli-token.json`. All other commands pick it up automatically, no browser needed.

## Usage

Always activate the virtual environment first:

```bash
source venv/bin/activate
```

### List videos

```bash
python youtube_cli.py videos
python youtube_cli.py videos --limit 10 --json
```

### Video details

```bash
python youtube_cli.py video-get --video-id VIDEO_ID
python youtube_cli.py video-get --video-id VIDEO_ID --json
```

### Upload a video

Videos are uploaded as **private** by default, to be safe.

```bash
# Basic upload (private)
python youtube_cli.py upload \
  --file /path/to/video.mp4 \
  --title "My Video Title"

# Upload with all metadata
python youtube_cli.py upload \
  --file /path/to/video.mp4 \
  --title "My Video Title" \
  --description "Video description with details" \
  --tags "tag1,tag2,tag3" \
  --category 22 \
  --privacy private \
  --thumbnail /path/to/thumbnail.jpg \
  --playlist PLAYLIST_ID \
  --language en \
  --json

# Scheduled publishing
python youtube_cli.py upload \
  --file /path/to/video.mp4 \
  --title "Scheduled Video" \
  --publish-at "2026-04-10T15:00:00Z"
```

Uploads use resumable transfer in chunks of about 12.5&nbsp;MB and retry automatically with exponential backoff on server errors.

### Update video metadata

Only the fields you pass are changed; everything else stays as it was:

```bash
python youtube_cli.py video-update --video-id VIDEO_ID --title "New Title"
python youtube_cli.py video-update --video-id VIDEO_ID --privacy public
python youtube_cli.py video-update --video-id VIDEO_ID --thumbnail /path/to/new-thumb.jpg
python youtube_cli.py video-update --video-id VIDEO_ID \
  --title "Updated" \
  --description "New description" \
  --tags "new,tags" \
  --json
```

### Delete a video

Requires the `--confirm` flag as a safety measure:

```bash
python youtube_cli.py video-delete --video-id VIDEO_ID --confirm
```

### Channel and video stats

```bash
# Channel overview
python youtube_cli.py stats

# Stats for a specific video
python youtube_cli.py stats --video-id VIDEO_ID
python youtube_cli.py stats --video-id VIDEO_ID --json

# Add lifetime engaged views (the view definition used until August 24, 2026)
python youtube_cli.py stats --engaged
python youtube_cli.py stats --video-id VIDEO_ID --engaged
```

### Analytics

Watch time, retention and traffic sources via the YouTube Analytics API, for your own channel only.
Requires the YouTube Analytics API to be enabled and the `yt-analytics.readonly` scope (if you
granted access before enabling the API, run `auth` again).

```bash
# Channel summary for the last 28 days
python youtube_cli.py analytics --days 28

# Daily trend
python youtube_cli.py analytics --days 28 --dimensions day --sort day

# Most-watched videos
python youtube_cli.py analytics --dimensions video --sort -views --max-results 10

# Where views come from
python youtube_cli.py analytics --dimensions insightTrafficSourceType --sort -views

# Shorts vs. long-form
python youtube_cli.py analytics --days 90 --dimensions creatorContentType

# One video, a specific date range, raw JSON from the API
python youtube_cli.py analytics --video-id VIDEO_ID \
  --start-date 2026-07-01 --end-date 2026-07-31 --json
```

Default metrics: `views`, `engagedViews`, `estimatedMinutesWatched`, `averageViewDuration`,
`averageViewPercentage` (retention), `subscribersGained`, `subscribersLost`, `likes`, `comments`,
`shares`. Change them with `--metrics` ([full list](https://developers.google.com/youtube/analytics/metrics)).

The Analytics API only serves [fixed combinations of dimensions and metrics](https://developers.google.com/youtube/analytics/v2/available_reports), so the CLI fills in what you leave out: for dimensions that only support view metrics (traffic source, device, subscription status…) it narrows the default metric set, for top-N dimensions (`video`, `playlist` and others) it adds the required sort and result limit, and for `--dimensions month` it aligns dates to whole months. Every adjustment is printed to stderr, so `--json` output stays clean. Anything you set yourself takes precedence.

### View counting since August 24, 2026

On **August 24, 2026**, YouTube [unified view counting](https://support.google.com/youtube/thread/433409976)
across all formats: a view counts as soon as playback starts, with no minimum watch time.
Shorts have worked this way since March 31, 2025.

| Metric | Where | What it counts |
|--------|-------|----------------|
| `viewCount` | Data API (`stats`, `videos`, `video-get`) | New definition, every playback start |
| `views` | Analytics API (`analytics`) | New definition |
| `engagedViews` | Analytics API (`analytics`, `stats --engaged`) | **Old** definition, views past the first few seconds |

The old number is no longer available anywhere in the public Data API, and only the channel owner can read `engagedViews`.
**The jump in views around August 24, 2026 comes from the definition change.** To compare across that
date, use `engagedViews`. More detail in [docs/api-notes.md](docs/api-notes.md).

### List playlists

```bash
python youtube_cli.py playlists
python youtube_cli.py playlists --json
```

### JSON output

Every command supports `--json` for machine-readable output, useful for scripting and for AI agents. In JSON mode only the data goes to stdout; notes and warnings for humans go to stderr:

```bash
python youtube_cli.py videos --json
python youtube_cli.py analytics --days 28 --json    # the API's resultTable, verbatim
```

## Command reference

| Command | What it does | Main flags |
|---------|--------------|------------|
| `auth` | One-time OAuth setup (opens a browser) | none |
| `videos` | List recent videos | `--limit`, `--json` |
| `video-get` | Video details | `--video-id` (required), `--json` |
| `upload` | Upload a video with metadata | `--file`, `--title` (required), `--description`, `--tags`, `--category`, `--privacy`, `--thumbnail`, `--playlist`, `--language`, `--publish-at`, `--json` |
| `video-update` | Update an existing video | `--video-id` (required), `--title`, `--description`, `--tags`, `--category`, `--privacy`, `--thumbnail`, `--json` |
| `video-delete` | Delete a video | `--video-id` (required), `--confirm` (required) |
| `stats` | View statistics | `--video-id` (optional), `--engaged`, `--json` |
| `analytics` | Watch time, retention, traffic sources (Analytics API) | `--days`, `--start-date`, `--end-date`, `--metrics`, `--dimensions`, `--sort`, `--video-id`, `--max-results`, `--json` |
| `playlists` | List playlists | `--json` |

`python youtube_cli.py --version` prints the installed version.

## Upload flags

| Flag | Required | Default | What it does |
|------|----------|---------|--------------|
| `--file` | yes | none | Path to the video file (MP4, MOV and others) |
| `--title` | yes | none | Video title |
| `--description` | no | empty | Video description |
| `--tags` | no | none | Comma-separated tags |
| `--category` | no | `22` | YouTube [category ID](https://developers.google.com/youtube/v3/docs/videoCategories/list) (22 = People & Blogs) |
| `--privacy` | no | `private` | `private`, `unlisted` or `public` |
| `--thumbnail` | no | none | Path to a thumbnail image (JPG/PNG) |
| `--playlist` | no | none | ID of the playlist to add the video to |
| `--language` | no | none | Language code (e.g. `en`, `cs`, `de`) |
| `--publish-at` | no | none | Scheduled publishing (ISO 8601, forces privacy to `private`) |

## Safety

- **Private by default.** Uploaded videos are `private`. You make them public yourself, either with `--privacy public` or later with `video-update`.
- **Deleting requires confirmation.** The `--confirm` flag is mandatory for `video-delete`.
- **Credentials stay with you.** `.env` is gitignored, and the OAuth token lives in your home directory (`~/.youtube-cli-token.json`).
- **No keys in the code.** All credentials come from environment variables.

## Troubleshooting

**"Not authenticated" error:**
Run `python youtube_cli.py auth` and complete the OAuth sign-in.

**"Token has been expired or revoked" error:**
Your refresh token expired (in "Testing" mode this happens after 7 days). Run `auth` again. To prevent it, publish the app in the Google Cloud Console.

**"YouTube API quota exceeded" error:**
The default quota is 10,000 units per day, and one video upload costs about 1,600 units. Check usage in [Google Cloud Quotas](https://console.cloud.google.com/iam-admin/quotas).

**"Google hasn't verified this app" warning:**
Normal for personal-use apps. Click **Continue**.

**Thumbnail upload fails:**
Custom thumbnails require a [verified YouTube account](https://support.google.com/youtube/answer/171664) (phone verification).

**`analytics` reports a scope or permission error:**
Enable the **YouTube Analytics API** in your Google Cloud project, then run `python youtube_cli.py auth` once. An existing token won't pick up the new scope on its own. Analytics only works for channels you own.

**Views suddenly jumped:**
It may not be growth. Since August 24, 2026, a view counts from the start of playback, with no minimum watch time. To compare like with like, look at `engagedViews` (the `analytics` command or `stats --engaged`).

## Project structure

```
youtube_cli.py        # Main CLI (single file)
.env.example          # Template for OAuth credentials
.env                  # Your credentials (gitignored)
requirements.txt      # Python dependencies
CLAUDE.md             # Instructions for Claude Code
CHANGELOG.md          # Version history (Keep a Changelog, SemVer)
docs/api-notes.md     # How the YouTube APIs actually behave
```

## Automation chain

This CLI is one link in a content pipeline driven by AI:

| Step | Tool | What it does |
|------|------|--------------|
| Transcription | [whisper-cz-en](https://github.com/faborsky/whisper-cz-en) | Local transcription with Whisper Large V3 |
| Episode notes | Claude Code | Generates titles, descriptions, chapters |
| Cover | [nanobanana-app](https://github.com/faborsky/nanobanana-app) | Generates artwork with AI |
| Audio publishing | [podbean-app](https://github.com/faborsky/podbean-app) | Uploads podcast audio |
| Video publishing | **youtube-cli-app** (this repo) | Uploads videos to YouTube |

## License

MIT, see [LICENSE](LICENSE).

## Author

[Jindřich Fáborský](https://www.faborsky.com), marketer and educator from Prague. I teach marketers to build their own tools with AI.

YouTube CLI started as part of my content automation toolkit, and I use it in production to run a Czech podcast's YouTube channel.
