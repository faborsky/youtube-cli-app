# YouTube CLI

A Python command-line tool for managing [YouTube](https://www.youtube.com/) videos via the YouTube Data API v3. Upload videos, manage metadata, set thumbnails, organize playlists, and view stats — all from the terminal. Built to be orchestrated by [Claude Code](https://docs.anthropic.com/en/docs/claude-code) or any AI coding agent.

## Why This Exists

Publishing video content on YouTube involves repetitive manual work: uploading files through the web UI, typing titles and descriptions, setting privacy, adding thumbnails, organizing playlists. This CLI automates those operations so they can be scripted or chained with other tools.

For example, a podcast publishing workflow orchestrated by Claude Code:

1. **Transcribe** audio with [whisper-cz-en](https://github.com/faborsky/whisper-cz-en)
2. **Generate metadata** (title, description, chapters) from the transcript
3. **Upload audio** to Podbean with [podbean-app](https://github.com/faborsky/podbean-app)
4. **Upload video** to YouTube with this CLI
5. **Set thumbnail** and add to playlist — automatically

All in a single conversation. You create content, AI does the admin.

## Prerequisites

- **Python 3.9+**
- **YouTube channel** linked to a Google account
- **Google Cloud project** with YouTube Data API v3 enabled and OAuth 2.0 credentials

## Google Cloud Setup

Before using the CLI, you need to set up a Google Cloud project with OAuth credentials. This is a one-time process.

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown (top bar) → **New Project**
3. Name it (e.g. `youtube-cli`) → **Create**
4. Select the new project from the dropdown

### 2. Enable YouTube Data API v3

1. Go to **APIs & Services → Library** ([direct link](https://console.cloud.google.com/apis/library))
2. Search for **YouTube Data API v3**
3. Click on it → **Enable**

### 3. Configure OAuth Consent Screen

1. Go to **APIs & Services → OAuth consent screen**
2. Select **External** user type → **Create**
3. Fill in required fields:
   - **App name:** any name (e.g. `Video Manager CLI`)
   - **User support email:** your email
   - **Developer contact:** your email
4. Click **Save and Continue**
5. On the **Scopes** page → **Add or Remove Scopes** → find and add `https://www.googleapis.com/auth/youtube` → **Save and Continue**
6. On the **Test users** page → **Add Users** → add your Gmail address → **Save and Continue**

> **Token expiry note:** In "Testing" mode, OAuth refresh tokens expire after **7 days**. To get long-lived tokens, click **Publish App** on the OAuth consent screen page. For personal-use apps with only your own account, Google typically doesn't require additional verification.

### 4. Create OAuth Credentials

1. Go to **APIs & Services → Credentials** ([direct link](https://console.cloud.google.com/apis/credentials))
2. Click **Create Credentials → OAuth client ID**
3. Application type: **Desktop app**
4. Name: any name (e.g. `YouTube CLI`)
5. Click **Create**
6. Copy the **Client ID** and **Client Secret**

You now have everything needed. The Client ID looks like `123456789-abc.apps.googleusercontent.com` and the Client Secret is a short alphanumeric string.

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

Edit `.env` with your OAuth credentials from the Google Cloud setup:

```
YOUTUBE_CLIENT_ID=your-client-id-here
YOUTUBE_CLIENT_SECRET=your-client-secret-here
```

Then authenticate (one-time — opens your browser):

```bash
python youtube_cli.py auth
```

This saves a long-lived refresh token to `~/.youtube-cli-token.json`. Subsequent commands use it automatically — no browser needed.

## Usage

Always activate the virtual environment first:

```bash
source venv/bin/activate
```

### List Videos

```bash
python youtube_cli.py videos
python youtube_cli.py videos --limit 10 --json
```

### Get Video Details

```bash
python youtube_cli.py video-get --video-id VIDEO_ID
python youtube_cli.py video-get --video-id VIDEO_ID --json
```

### Upload Video

Videos are uploaded as **private** by default for safety.

```bash
# Basic upload (private)
python youtube_cli.py upload \
  --file /path/to/video.mp4 \
  --title "My Video Title"

# Full upload with all metadata
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

# Scheduled publish
python youtube_cli.py upload \
  --file /path/to/video.mp4 \
  --title "Scheduled Video" \
  --publish-at "2026-04-10T15:00:00Z"
```

Upload uses resumable transfer with ~12.5 MB chunks and automatic retry with exponential backoff on server errors.

### Update Video Metadata

Only the specified fields are changed — everything else stays as-is:

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

### Delete Video

Requires `--confirm` flag for safety:

```bash
python youtube_cli.py video-delete --video-id VIDEO_ID --confirm
```

### Channel & Video Statistics

```bash
# Channel overview
python youtube_cli.py stats

# Specific video stats
python youtube_cli.py stats --video-id VIDEO_ID
python youtube_cli.py stats --video-id VIDEO_ID --json
```

### List Playlists

```bash
python youtube_cli.py playlists
python youtube_cli.py playlists --json
```

### JSON Output

All commands support `--json` for machine-readable output, useful for scripting and AI agent orchestration:

```bash
python youtube_cli.py videos --json
```

## Command Reference

| Command | Description | Key Flags |
|---------|-------------|-----------|
| `auth` | One-time OAuth setup (opens browser) | — |
| `videos` | List recent videos | `--limit`, `--json` |
| `video-get` | Get video details | `--video-id` (required), `--json` |
| `upload` | Upload video with metadata | `--file`, `--title` (required), `--description`, `--tags`, `--category`, `--privacy`, `--thumbnail`, `--playlist`, `--language`, `--publish-at`, `--json` |
| `video-update` | Update existing video | `--video-id` (required), `--title`, `--description`, `--tags`, `--category`, `--privacy`, `--thumbnail`, `--json` |
| `video-delete` | Delete a video | `--video-id` (required), `--confirm` (required) |
| `stats` | View statistics | `--video-id` (optional), `--json` |
| `playlists` | List playlists | `--json` |

## Upload Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--file` | Yes | — | Path to video file (MP4, MOV, etc.) |
| `--title` | Yes | — | Video title |
| `--description` | No | empty | Video description |
| `--tags` | No | none | Comma-separated tags |
| `--category` | No | `22` | YouTube [category ID](https://developers.google.com/youtube/v3/docs/videoCategories/list) (22 = People & Blogs) |
| `--privacy` | No | `private` | `private`, `unlisted`, or `public` |
| `--thumbnail` | No | none | Path to thumbnail image (JPG/PNG) |
| `--playlist` | No | none | Playlist ID to add the video to |
| `--language` | No | none | Language code (e.g. `en`, `cs`, `de`) |
| `--publish-at` | No | none | Schedule publish (ISO 8601, forces privacy to `private`) |

## Safety

- **Private by default** — uploaded videos are set to `private`. You must explicitly use `--privacy public` or update later with `video-update`.
- **Delete requires confirmation** — the `--confirm` flag is mandatory for `video-delete`.
- **Credentials stay local** — `.env` is git-ignored, OAuth token is stored in your home directory (`~/.youtube-cli-token.json`).
- **No secrets in code** — all credentials come from environment variables.

## Troubleshooting

**"Not authenticated" error:**
Run `python youtube_cli.py auth` to complete the OAuth flow.

**"Token has been expired or revoked":**
Your refresh token expired (happens in "Testing" mode after 7 days). Run `auth` again. To avoid this, publish your app in Google Cloud Console.

**"YouTube API quota exceeded":**
Default quota is 10,000 units/day. A video upload costs ~1,600 units. Check usage at [Google Cloud Quotas](https://console.cloud.google.com/iam-admin/quotas).

**"Google hasn't verified this app" warning:**
Normal for personal-use apps. Click **Continue** to proceed.

**Thumbnail upload fails:**
Custom thumbnails require a [verified YouTube account](https://support.google.com/youtube/answer/171664) (phone number verification).

## Project Structure

```
youtube_cli.py        # Main CLI (single file)
.env.example          # Template for OAuth credentials
.env                  # Your credentials (git-ignored)
requirements.txt      # Python dependencies
CLAUDE.md             # Instructions for Claude Code
```

## Automation Chain

This CLI is designed to work as part of a larger AI-powered content pipeline:

| Step | Tool | What It Does |
|------|------|-------------|
| Transcription | [whisper-cz-en](https://github.com/faborsky/whisper-cz-en) | Local transcription with Whisper Large V3 |
| Show notes | Claude Code | Generate titles, descriptions, chapters |
| Cover art | [nanobanana-agent](https://github.com/faborsky/nanobonana-agent-public) | Generate artwork with AI |
| Audio publishing | [podbean-app](https://github.com/faborsky/podbean-app) | Upload audio podcasts |
| Video publishing | **youtube-cli-app** (this repo) | Upload videos to YouTube |

## About

Built by [Jindrich Faborsky](https://github.com/faborsky) as part of the content automation toolkit. Used in production for managing a Czech podcast on YouTube.

This project is part of the curriculum for:
- **[Vibe Coding for Marketers](https://vibecodingformarketers.com)** — an international course teaching marketers to build tools with AI
- **[AI First](https://www.aifirst.cz)** — a Czech course on AI-first thinking for entrepreneurs and marketers

---

## Česky

### Co to je

CLI nástroj pro správu YouTube videí přes YouTube Data API v3. Nahrávání videí, správa metadat, thumbnailů, playlistů a statistik — vše z terminálu. Navržený tak, aby ho mohl ovládat Claude Code nebo jiný AI agent.

### Proč to existuje

Publikování videa na YouTube zahrnuje spoustu opakující se práce: nahrávání přes webové rozhraní, vyplňování titulků a popisků, nastavování soukromí, přidávání thumbnailů. Tohle CLI to automatizuje a dá se řetězit s dalšími nástroji do kompletního publikačního workflow.

### Instalace

```bash
git clone https://github.com/faborsky/youtube-cli-app.git
cd youtube-cli-app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Upravte .env a vložte své Google Cloud OAuth credentials
```

### Nastavení Google Cloud

1. Vytvořte projekt na [Google Cloud Console](https://console.cloud.google.com/)
2. Povolte **YouTube Data API v3** (APIs & Services → Library)
3. Nastavte **OAuth consent screen** (External, přidejte svůj email jako test user)
4. Vytvořte **OAuth client ID** (typ: Desktop app)
5. Zkopírujte Client ID a Client Secret do `.env`
6. Spusťte `python youtube_cli.py auth` — otevře se prohlížeč pro jednorázové přihlášení

Podrobný návod v angličtině výše v sekci [Google Cloud Setup](#google-cloud-setup).

### Bezpečnost

- Videa se nahrávají jako **private** (soukromá) — musíte explicitně zveřejnit
- Smazání vyžaduje `--confirm` flag
- Credentials jsou v `.env` (nikdy se necommitují do gitu)

### Kde se to učí

- **[Vibe Coding for Marketers](https://vibecodingformarketers.com)** — mezinárodní kurz (EN), kde se marketéři učí stavět nástroje s AI
- **[AI First](https://www.aifirst.cz)** — český kurz o AI-first přístupu pro podnikatele a marketéry

---

## License

MIT
