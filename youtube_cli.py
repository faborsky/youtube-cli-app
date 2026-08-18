#!/usr/bin/env python3
"""YouTube CLI — manage videos, playlists, uploads, and stats.

SAFETY: Videos are uploaded as PRIVATE by default.
Delete requires --confirm flag.
"""

from __future__ import annotations

import argparse
import datetime
import http.client
import json
import os
import mimetypes
import random
import sys
import time

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
TOKEN_FILE = os.path.expanduser("~/.youtube-cli-token.json")
SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

__version__ = "2.0.0"

MAX_RETRIES = 10
RETRIABLE_STATUS_CODES = (500, 502, 503, 504)
CHUNK_SIZE = 256 * 1024 * 50  # ~12.5 MB

# On 2026-08-24 YouTube unified view counting across all formats (Shorts had it
# since 2025-03-31): a view is counted the moment playback starts, with no
# minimum watch time. The old, watch-time-gated number is no longer in the
# public Data API — it survives as `engagedViews` in the Analytics API.
VIEWS_METHODOLOGY_DATE = "2026-08-24"

# Analytics default metric set, and the subset that narrow dimensions accept. The
# Analytics API only serves the fixed combinations listed in its "available reports"
# — asking for subscriber/engagement metrics alongside e.g. insightTrafficSourceType
# fails the whole query with "The query is not supported."
ANALYTICS_DEFAULT_METRICS = (
    "views,engagedViews,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,"
    "subscribersGained,subscribersLost,likes,comments,shares"
)
ANALYTICS_CORE_METRICS = "views,engagedViews,estimatedMinutesWatched"
# Verified live 2026-08-18: these reject the full default set but serve the core one.
CORE_ONLY_DIMENSIONS = {
    "insightTrafficSourceType",
    "insightPlaybackLocationType",
    "deviceType",
    "operatingSystem",
    "subscribedStatus",
}
# Top-N reports: the API requires both sort and maxResults, otherwise it refuses the query.
TOP_N_DIMENSIONS = {"video", "playlist", "insightTrafficSourceDetail", "insightPlaybackLocationDetail"}
VIEWS_NOTE = (
    f"Note: since {VIEWS_METHODOLOGY_DATE} a view counts as soon as playback starts (no minimum watch\n"
    "      time), for every format. The previous definition lives on as `engagedViews`\n"
    "      in the Analytics API — see `analytics` or `stats --engaged`."
)


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _check_config() -> None:
    if not CLIENT_ID or CLIENT_ID == "your-client-id-here":
        print("ERROR: YOUTUBE_CLIENT_ID not set. Copy .env.example to .env and add your credentials.", file=sys.stderr)
        sys.exit(1)
    if not CLIENT_SECRET or CLIENT_SECRET == "your-client-secret-here":
        print("ERROR: YOUTUBE_CLIENT_SECRET not set.", file=sys.stderr)
        sys.exit(1)


def _get_client_config() -> dict:
    return {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def _load_credentials() -> Credentials | None:
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        return creds
    except Exception:
        return None


def _save_credentials(creds: Credentials) -> None:
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())


def _get_credentials() -> Credentials | None:
    creds = _load_credentials()
    if creds is None:
        return None

    if creds.valid:
        return creds

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_credentials(creds)
            return creds
        except Exception as e:
            err = str(e).lower()
            if "revoked" in err or "expired" in err or "invalid_grant" in err:
                print("ERROR: Token has been expired or revoked. Run 'auth' command to re-authenticate.", file=sys.stderr)
                sys.exit(1)
            raise

    return None


def _get_youtube_service():
    creds = _get_credentials()
    if creds is None:
        print("ERROR: Not authenticated. Run 'auth' command first.", file=sys.stderr)
        sys.exit(1)
    return build("youtube", "v3", credentials=creds)


def _get_analytics_service():
    """YouTube Analytics API v2 (watch time, retention, traffic sources). Needs yt-analytics.readonly scope."""
    creds = _get_credentials()
    if creds is None:
        return None
    return build("youtubeAnalytics", "v2", credentials=creds)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _handle_api_error(e: HttpError) -> None:
    try:
        error_body = json.loads(e.content.decode("utf-8"))
        errors = error_body.get("error", {}).get("errors", [])
        reason = errors[0].get("reason", "") if errors else ""
        message = error_body.get("error", {}).get("message", str(e))
    except Exception:
        reason = ""
        message = str(e)

    if reason == "quotaExceeded":
        print(f"ERROR: YouTube API quota exceeded. Check your quota at https://console.cloud.google.com/iam-admin/quotas", file=sys.stderr)
    elif reason == "youtubeSignupRequired":
        print(f"ERROR: The authenticated account has no YouTube channel.", file=sys.stderr)
    else:
        print(f"ERROR: YouTube API error ({e.resp.status}): {message}", file=sys.stderr)
    sys.exit(1)


def _resumable_upload(insert_request) -> dict:
    response = None
    error = None
    retry = 0

    while response is None:
        try:
            status, response = insert_request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"  Upload progress: {pct}%", file=sys.stderr)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"  Retriable HTTP error {e.resp.status}: {e.content.decode('utf-8', errors='replace')}"
            else:
                raise
        except (http.client.HTTPException, OSError) as e:
            error = f"  Retriable error: {e}"

        if error is not None:
            print(error, file=sys.stderr)
            retry += 1
            if retry > MAX_RETRIES:
                print("ERROR: Max retries exceeded.", file=sys.stderr)
                sys.exit(1)
            sleep_seconds = random.random() * (2 ** retry)
            print(f"  Sleeping {sleep_seconds:.1f}s before retry {retry}/{MAX_RETRIES}...", file=sys.stderr)
            time.sleep(sleep_seconds)
            error = None

    return response


def _engaged_views(start_date: str, video_id: str | None = None) -> dict | None:
    """Lifetime views + engagedViews from the Analytics API (the pre-2026-08-24 metric).

    Returns None (with a warning on stderr) when the Analytics API is unavailable —
    callers treat it as optional enrichment, never as a hard failure.
    """
    analytics = _get_analytics_service()
    if analytics is None:
        print("WARNING: not authenticated for Analytics — skipping engaged views.", file=sys.stderr)
        return None

    query = {
        "ids": "channel==MINE",
        "startDate": start_date,
        "endDate": datetime.date.today().isoformat(),
        "metrics": "views,engagedViews",
    }
    if video_id:
        query["filters"] = f"video=={video_id}"

    try:
        resp = analytics.reports().query(**query).execute()
    except HttpError as e:
        print(
            f"WARNING: engaged views unavailable ({e.resp.status}). If this is a scope error, "
            "run `auth` once to grant yt-analytics.readonly.",
            file=sys.stderr,
        )
        return None

    rows = resp.get("rows", [])
    if not rows:
        return None
    return {"analytics_views": rows[0][0], "engaged_views": rows[0][1], "since": start_date}


def _print_analytics_table(resp: dict) -> None:
    """Render an Analytics resultTable as aligned columns."""
    headers = [h.get("name", "") for h in resp.get("columnHeaders", [])]
    types = [h.get("dataType", "") for h in resp.get("columnHeaders", [])]
    rows = resp.get("rows", [])

    if not rows:
        print("No data for this query and date range.")
        return

    def fmt(value, dtype: str) -> str:
        if isinstance(value, float) or dtype == "FLOAT":
            return f"{value:,.2f}"
        if isinstance(value, int):
            return f"{value:,}"
        return str(value)

    table = [[fmt(v, types[i] if i < len(types) else "") for i, v in enumerate(row)] for row in rows]
    widths = [max(len(headers[i]), max((len(r[i]) for r in table), default=0)) for i in range(len(headers))]

    print("  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    print("-" * (sum(widths) + 2 * (len(widths) - 1)))
    for r in table:
        print("  ".join(c.ljust(widths[i]) for i, c in enumerate(r)))
    print(f"\n{len(rows)} row(s).")

    if "views" in headers and "engagedViews" in headers:
        print(f"\nviews        = all playback starts (unified across formats on {VIEWS_METHODOLOGY_DATE})")
        print(f"engagedViews = views past the initial seconds (the pre-{VIEWS_METHODOLOGY_DATE} definition)")


# ---------------------------------------------------------------------------
# Commands — Auth
# ---------------------------------------------------------------------------

def cmd_auth(_args: argparse.Namespace) -> None:
    """One-time OAuth setup. Opens browser for consent."""
    flow = InstalledAppFlow.from_client_config(_get_client_config(), SCOPES)
    print("Opening browser for YouTube authorization...", file=sys.stderr)
    print("If the browser doesn't open, copy the URL from below.", file=sys.stderr)
    creds = flow.run_local_server(port=8080, prompt="consent", access_type="offline")
    _save_credentials(creds)
    print(f"\nAuthentication successful. Token saved to {TOKEN_FILE}")
    print("You can now use all YouTube CLI commands.")


# ---------------------------------------------------------------------------
# Commands — Read-only
# ---------------------------------------------------------------------------

def cmd_videos(args: argparse.Namespace) -> None:
    """List recent videos from the channel."""
    youtube = _get_youtube_service()

    try:
        # Use search to find own videos ordered by date
        search_resp = youtube.search().list(
            part="snippet",
            forMine=True,
            type="video",
            maxResults=args.limit,
            order="date",
        ).execute()
    except HttpError as e:
        _handle_api_error(e)

    items = search_resp.get("items", [])
    if not items:
        print("[]" if args.json else "No videos found.")
        return

    # Fetch full details for all videos in one call
    video_ids = [item["id"]["videoId"] for item in items]
    try:
        details_resp = youtube.videos().list(
            part="snippet,contentDetails,statistics,status",
            id=",".join(video_ids),
        ).execute()
    except HttpError as e:
        _handle_api_error(e)

    videos = details_resp.get("items", [])

    if args.json:
        output = []
        for v in videos:
            snippet = v.get("snippet", {})
            stats = v.get("statistics", {})
            status = v.get("status", {})
            cd = v.get("contentDetails", {})
            output.append({
                "video_id": v["id"],
                "title": snippet.get("title", ""),
                "published_at": snippet.get("publishedAt", ""),
                "privacy": status.get("privacyStatus", ""),
                "duration": cd.get("duration", ""),
                "view_count": stats.get("viewCount", "0"),
                "like_count": stats.get("likeCount", "0"),
                "comment_count": stats.get("commentCount", "0"),
                "url": f"https://youtu.be/{v['id']}",
            })
        print(json.dumps(output, indent=2))
    else:
        print(f"{'Title':<55} {'Privacy':<10} {'Views':<8} {'Published':<12} {'ID'}")
        print("-" * 115)
        for v in videos:
            snippet = v.get("snippet", {})
            stats = v.get("statistics", {})
            status = v.get("status", {})
            title = snippet.get("title", "")
            if len(title) > 53:
                title = title[:51] + ".."
            pub = snippet.get("publishedAt", "")[:10]
            views = stats.get("viewCount", "0")
            privacy = status.get("privacyStatus", "")
            print(f"{title:<55} {privacy:<10} {views:<8} {pub:<12} {v['id']}")

        print(f"\nShowing {len(videos)} videos.")
        print(f"\n{VIEWS_NOTE}")


def cmd_video_get(args: argparse.Namespace) -> None:
    """Get details of a single video."""
    youtube = _get_youtube_service()

    try:
        resp = youtube.videos().list(
            part="snippet,contentDetails,statistics,status",
            id=args.video_id,
        ).execute()
    except HttpError as e:
        _handle_api_error(e)

    items = resp.get("items", [])
    if not items:
        print(f"ERROR: Video '{args.video_id}' not found.", file=sys.stderr)
        sys.exit(1)

    v = items[0]
    snippet = v.get("snippet", {})
    stats = v.get("statistics", {})
    status = v.get("status", {})
    cd = v.get("contentDetails", {})

    if args.json:
        print(json.dumps(v, indent=2))
    else:
        print(f"Title:        {snippet.get('title', '')}")
        print(f"Video ID:     {v['id']}")
        print(f"URL:          https://youtu.be/{v['id']}")
        print(f"Channel:      {snippet.get('channelTitle', '')}")
        print(f"Published:    {snippet.get('publishedAt', '')}")
        print(f"Privacy:      {status.get('privacyStatus', '')}")
        print(f"Duration:     {cd.get('duration', '')}")
        print(f"Category:     {snippet.get('categoryId', '')}")
        print(f"Language:     {snippet.get('defaultLanguage', snippet.get('defaultAudioLanguage', ''))}")
        print(f"Views:        {stats.get('viewCount', '0')}")
        print(f"Likes:        {stats.get('likeCount', '0')}")
        print(f"Comments:     {stats.get('commentCount', '0')}")
        tags = snippet.get("tags", [])
        if tags:
            print(f"Tags:         {', '.join(tags)}")
        desc = snippet.get("description", "")
        if desc:
            if len(desc) > 300:
                desc = desc[:300] + "..."
            print(f"Description:  {desc}")
        print(f"\n{VIEWS_NOTE}")


def cmd_stats(args: argparse.Namespace) -> None:
    """View channel or video statistics."""
    youtube = _get_youtube_service()

    if args.video_id:
        # Video-specific stats
        try:
            resp = youtube.videos().list(
                part="snippet,statistics",
                id=args.video_id,
            ).execute()
        except HttpError as e:
            _handle_api_error(e)

        items = resp.get("items", [])
        if not items:
            print(f"ERROR: Video '{args.video_id}' not found.", file=sys.stderr)
            sys.exit(1)

        v = items[0]
        snippet = v.get("snippet", {})
        stats = v.get("statistics", {})

        engaged = None
        if args.engaged:
            published = snippet.get("publishedAt", "")[:10]
            if published:
                engaged = _engaged_views(published, video_id=v["id"])

        if args.json:
            payload = {"video_id": v["id"], "title": snippet.get("title", ""), **stats}
            if engaged:
                payload.update(engaged)
            print(json.dumps(payload, indent=2))
        else:
            print(f"Video:     {snippet.get('title', '')}")
            print(f"Video ID:  {v['id']}")
            print(f"Views:     {stats.get('viewCount', '0')}")
            if engaged:
                print(f"  Analytics views:  {engaged['analytics_views']:,} (since {engaged['since']})")
                print(f"  Engaged views:    {engaged['engaged_views']:,} (pre-{VIEWS_METHODOLOGY_DATE} definition)")
            print(f"Likes:     {stats.get('likeCount', '0')}")
            print(f"Comments:  {stats.get('commentCount', '0')}")
            print(f"Favorites: {stats.get('favoriteCount', '0')}")
            if not engaged:
                print(f"\n{VIEWS_NOTE}")
    else:
        # Channel stats
        try:
            resp = youtube.channels().list(
                part="snippet,statistics",
                mine=True,
            ).execute()
        except HttpError as e:
            _handle_api_error(e)

        items = resp.get("items", [])
        if not items:
            print("ERROR: No channel found for this account.", file=sys.stderr)
            sys.exit(1)

        ch = items[0]
        snippet = ch.get("snippet", {})
        stats = ch.get("statistics", {})

        engaged = None
        if args.engaged:
            published = snippet.get("publishedAt", "")[:10]
            if published:
                engaged = _engaged_views(published)

        if args.json:
            payload = {"channel_id": ch["id"], "title": snippet.get("title", ""), **stats}
            if engaged:
                payload.update(engaged)
            print(json.dumps(payload, indent=2))
        else:
            print(f"Channel:      {snippet.get('title', '')}")
            print(f"Channel ID:   {ch['id']}")
            print(f"Subscribers:  {stats.get('subscriberCount', '0')}")
            print(f"Total views:  {stats.get('viewCount', '0')}")
            if engaged:
                print(f"  Analytics views:  {engaged['analytics_views']:,} (since {engaged['since']})")
                print(f"  Engaged views:    {engaged['engaged_views']:,} (pre-{VIEWS_METHODOLOGY_DATE} definition)")
            print(f"Total videos: {stats.get('videoCount', '0')}")
            if not engaged:
                print(f"\n{VIEWS_NOTE}")


def cmd_playlists(args: argparse.Namespace) -> None:
    """List playlists for the channel."""
    youtube = _get_youtube_service()

    try:
        resp = youtube.playlists().list(
            part="snippet,contentDetails",
            mine=True,
            maxResults=50,
        ).execute()
    except HttpError as e:
        _handle_api_error(e)

    items = resp.get("items", [])
    if not items:
        print("[]" if args.json else "No playlists found.")
        return

    if args.json:
        output = []
        for pl in items:
            snippet = pl.get("snippet", {})
            cd = pl.get("contentDetails", {})
            output.append({
                "playlist_id": pl["id"],
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "video_count": cd.get("itemCount", 0),
                "published_at": snippet.get("publishedAt", ""),
            })
        print(json.dumps(output, indent=2))
    else:
        print(f"{'Title':<50} {'Videos':<8} {'Playlist ID'}")
        print("-" * 90)
        for pl in items:
            snippet = pl.get("snippet", {})
            cd = pl.get("contentDetails", {})
            title = snippet.get("title", "")
            if len(title) > 48:
                title = title[:46] + ".."
            print(f"{title:<50} {cd.get('itemCount', 0):<8} {pl['id']}")

        print(f"\n{len(items)} playlists found.")


# ---------------------------------------------------------------------------
# Commands — Write
# ---------------------------------------------------------------------------

def cmd_upload(args: argparse.Namespace) -> None:
    """Upload video with metadata, optional thumbnail and playlist."""
    filepath = os.path.expanduser(args.file)
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    file_size = os.path.getsize(filepath)
    filename = os.path.basename(filepath)
    youtube = _get_youtube_service()

    # Build video body
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    body: dict = {
        "snippet": {
            "title": args.title,
            "description": args.description or "",
            "tags": tags,
            "categoryId": str(args.category),
            **({"defaultLanguage": args.language, "defaultAudioLanguage": args.language} if args.language else {}),
        },
        "status": {
            "privacyStatus": args.privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    # Scheduled publish: must be private
    if args.publish_at:
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = args.publish_at

    print(f"Uploading: {filename} ({file_size / 1024 / 1024:.1f} MB)", file=sys.stderr)
    print(f"  Title:   {args.title}", file=sys.stderr)
    print(f"  Privacy: {body['status']['privacyStatus']}", file=sys.stderr)

    media = MediaFileUpload(filepath, mimetype="video/*", resumable=True, chunksize=CHUNK_SIZE)

    try:
        insert_request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )
        response = _resumable_upload(insert_request)
    except HttpError as e:
        _handle_api_error(e)

    video_id = response.get("id", "")
    video_url = f"https://youtu.be/{video_id}"

    print(f"  Video uploaded: {video_url}", file=sys.stderr)

    # Upload thumbnail if provided
    if args.thumbnail:
        thumb_path = os.path.expanduser(args.thumbnail)
        if not os.path.exists(thumb_path):
            print(f"WARNING: Thumbnail file not found: {thumb_path}", file=sys.stderr)
        else:
            print(f"  Uploading thumbnail: {os.path.basename(thumb_path)}...", file=sys.stderr)
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumb_path, mimetype=mimetypes.guess_type(thumb_path)[0] or "image/jpeg"),
                ).execute()
                print("  Thumbnail set.", file=sys.stderr)
            except HttpError as e:
                # Thumbnail errors are non-fatal
                print(f"  WARNING: Thumbnail upload failed: {e}", file=sys.stderr)

    # Add to playlist if provided
    if args.playlist:
        print(f"  Adding to playlist {args.playlist}...", file=sys.stderr)
        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": args.playlist,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id,
                        },
                    },
                },
            ).execute()
            print("  Added to playlist.", file=sys.stderr)
        except HttpError as e:
            print(f"  WARNING: Failed to add to playlist: {e}", file=sys.stderr)

    output = {
        "video_id": video_id,
        "title": args.title,
        "privacy": body["status"]["privacyStatus"],
        "url": video_url,
    }

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"\nVideo uploaded successfully.")
        print(f"  Video ID: {video_id}")
        print(f"  Title:    {args.title}")
        print(f"  Privacy:  {body['status']['privacyStatus']}")
        print(f"  URL:      {video_url}")


def cmd_video_update(args: argparse.Namespace) -> None:
    """Update video metadata. Fetches current data first, merges changes."""
    youtube = _get_youtube_service()

    # Fetch current video data (required — YouTube API needs full snippet on update)
    try:
        resp = youtube.videos().list(
            part="snippet,status",
            id=args.video_id,
        ).execute()
    except HttpError as e:
        _handle_api_error(e)

    items = resp.get("items", [])
    if not items:
        print(f"ERROR: Video '{args.video_id}' not found.", file=sys.stderr)
        sys.exit(1)

    video = items[0]
    snippet = video["snippet"]
    status = video["status"]

    # Merge user changes
    if args.title is not None:
        snippet["title"] = args.title
    if args.description is not None:
        snippet["description"] = args.description
    if args.tags is not None:
        snippet["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]
    if args.category is not None:
        snippet["categoryId"] = str(args.category)
    if args.privacy is not None:
        status["privacyStatus"] = args.privacy

    body = {
        "id": args.video_id,
        "snippet": snippet,
        "status": status,
    }

    try:
        result = youtube.videos().update(
            part="snippet,status",
            body=body,
        ).execute()
    except HttpError as e:
        _handle_api_error(e)

    # Upload thumbnail if provided
    if args.thumbnail:
        thumb_path = os.path.expanduser(args.thumbnail)
        if not os.path.exists(thumb_path):
            print(f"WARNING: Thumbnail file not found: {thumb_path}", file=sys.stderr)
        else:
            print(f"Uploading thumbnail: {os.path.basename(thumb_path)}...", file=sys.stderr)
            try:
                youtube.thumbnails().set(
                    videoId=args.video_id,
                    media_body=MediaFileUpload(thumb_path, mimetype=mimetypes.guess_type(thumb_path)[0] or "image/jpeg"),
                ).execute()
                print("Thumbnail set.", file=sys.stderr)
            except HttpError as e:
                print(f"WARNING: Thumbnail upload failed: {e}", file=sys.stderr)

    updated_snippet = result.get("snippet", {})
    updated_status = result.get("status", {})

    output = {
        "video_id": args.video_id,
        "title": updated_snippet.get("title", ""),
        "privacy": updated_status.get("privacyStatus", ""),
        "updated": True,
    }

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"Video updated successfully.")
        print(f"  Video ID: {args.video_id}")
        print(f"  Title:    {updated_snippet.get('title', '')}")
        print(f"  Privacy:  {updated_status.get('privacyStatus', '')}")


def cmd_video_delete(args: argparse.Namespace) -> None:
    """Delete a video (requires --confirm)."""
    if not args.confirm:
        print("ERROR: Delete requires --confirm flag for safety.", file=sys.stderr)
        print("  Usage: video-delete --video-id ID --confirm", file=sys.stderr)
        sys.exit(1)

    youtube = _get_youtube_service()

    try:
        youtube.videos().delete(id=args.video_id).execute()
    except HttpError as e:
        _handle_api_error(e)

    output = {
        "video_id": args.video_id,
        "deleted": True,
    }

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"Video deleted successfully.")
        print(f"  Video ID: {args.video_id}")


# ---------------------------------------------------------------------------
# CLI setup
# ---------------------------------------------------------------------------

def cmd_analytics(args: argparse.Namespace) -> None:
    """Channel analytics over a date range — views, watch time, retention, traffic, subs (YouTube Analytics API).

    Needs the yt-analytics.readonly scope: if the saved token predates it, run `auth` once to re-grant.
    Examples:
      analytics --days 28                              # channel totals, last 28 days
      analytics --days 28 --dimensions day --sort day  # daily trend
      analytics --dimensions video --sort -views --max-results 10   # top videos
      analytics --dimensions insightTrafficSourceType  # where views come from
    """
    analytics = _get_analytics_service()
    if analytics is None:
        print("ERROR: Not authenticated. Run `auth` to (re-)grant the analytics scope.", file=sys.stderr)
        sys.exit(1)
    end = args.end_date or datetime.date.today().isoformat()
    start = args.start_date or (datetime.date.today() - datetime.timedelta(days=args.days)).isoformat()

    # Adapt the defaults to what the requested dimension actually serves. Explicit
    # --metrics / --sort / --max-results always win — we only fill in the blanks.
    metrics = args.metrics
    sort = args.sort
    max_results = args.max_results
    if args.dimensions:
        if metrics is None and args.dimensions in CORE_ONLY_DIMENSIONS:
            metrics = ANALYTICS_CORE_METRICS
            print(f"Note: `{args.dimensions}` only serves {ANALYTICS_CORE_METRICS} — using those.",
                  file=sys.stderr)
        if args.dimensions in TOP_N_DIMENSIONS:
            if not sort:
                sort = "-views"
            if not max_results:
                max_results = 25
        if args.dimensions == "month":
            # Both dates must be the first of a month, or the API rejects the query
            # ("does not align to chosen date dimension") — verified live 2026-08-18.
            aligned_start, aligned_end = start[:7] + "-01", end[:7] + "-01"
            if (aligned_start, aligned_end) != (start, end):
                print(f"Note: `month` needs month-aligned dates — using {aligned_start} → {aligned_end}.",
                      file=sys.stderr)
                start, end = aligned_start, aligned_end
    if metrics is None:
        metrics = ANALYTICS_DEFAULT_METRICS

    query = {
        "ids": "channel==MINE",
        "startDate": start,
        "endDate": end,
        "metrics": metrics,
    }
    if args.dimensions:
        query["dimensions"] = args.dimensions
    if sort:
        query["sort"] = sort
    if args.video_id:
        query["filters"] = f"video=={args.video_id}"
    if max_results:
        query["maxResults"] = max_results
    try:
        resp = analytics.reports().query(**query).execute()
    except HttpError as e:
        print(f"ERROR: YouTube Analytics: {e}", file=sys.stderr)
        detail = str(e)
        if e.resp.status in (401, 403):
            print("HINT: this looks like an auth/scope problem — run `auth` once to grant "
                  "yt-analytics.readonly, and check the YouTube Analytics API is enabled.",
                  file=sys.stderr)
        elif "not supported" in detail:
            print(f"HINT: the API only serves fixed dimension/metric combinations. Retry with "
                  f"--metrics {ANALYTICS_CORE_METRICS}, and note that some dimensions need a filter "
                  "(insightTrafficSourceDetail) or aligned dates (month). Supported combinations: "
                  "https://developers.google.com/youtube/analytics/v2/available_reports",
                  file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(resp, ensure_ascii=False, indent=2))
    else:
        print(f"Channel analytics: {start} → {end}")
        if args.video_id:
            print(f"Filtered to video: {args.video_id}")
        print()
        _print_analytics_table(resp)


def _splice_negative_values(argv: list[str]) -> list[str]:
    """Let `--sort -views` work.

    argparse parses a leading `-` as another flag, so the documented
    `--sort -views` dies with "expected one argument". Rewrite it to
    `--sort=-views` before parsing. `--sort --json` is left alone so a genuinely
    missing value still errors out.
    """
    out: list[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token == "--sort" and i + 1 < len(argv):
            nxt = argv[i + 1]
            if nxt.startswith("-") and not nxt.startswith("--"):
                out.append(f"--sort={nxt}")
                i += 2
                continue
        out.append(token)
        i += 1
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="YouTube CLI — manage videos, playlists, uploads, and stats.",
    )
    parser.add_argument("--version", action="version", version=f"youtube-cli {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    json_kwargs: dict = {"action": "store_true", "help": "Output as JSON"}

    # --- auth ---
    subparsers.add_parser("auth", help="One-time OAuth setup (opens browser)")

    # --- videos ---
    p_videos = subparsers.add_parser("videos", help="List recent videos")
    p_videos.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")
    p_videos.add_argument("--json", **json_kwargs)

    # --- video-get ---
    p_vget = subparsers.add_parser("video-get", help="Get video details")
    p_vget.add_argument("--video-id", required=True, help="YouTube video ID")
    p_vget.add_argument("--json", **json_kwargs)

    # --- upload ---
    p_upload = subparsers.add_parser("upload", help="Upload video")
    p_upload.add_argument("--file", required=True, help="Path to video file")
    p_upload.add_argument("--title", required=True, help="Video title")
    p_upload.add_argument("--description", type=str, default="", help="Video description")
    p_upload.add_argument("--tags", type=str, default="", help="Comma-separated tags")
    p_upload.add_argument("--category", type=int, default=22, help="Category ID (default: 22 = People & Blogs)")
    p_upload.add_argument("--privacy", type=str, default="private", choices=["private", "unlisted", "public"], help="Privacy status (default: private)")
    p_upload.add_argument("--thumbnail", type=str, help="Path to thumbnail image")
    p_upload.add_argument("--playlist", type=str, help="Playlist ID to add video to")
    p_upload.add_argument("--language", type=str, help="Language code (e.g. en, cs, de)")
    p_upload.add_argument("--publish-at", type=str, help="Scheduled publish time (ISO 8601, e.g. 2026-04-10T15:00:00Z)")
    p_upload.add_argument("--json", **json_kwargs)

    # --- video-update ---
    p_vupd = subparsers.add_parser("video-update", help="Update video metadata")
    p_vupd.add_argument("--video-id", required=True, help="YouTube video ID")
    p_vupd.add_argument("--title", type=str, help="New title")
    p_vupd.add_argument("--description", type=str, help="New description")
    p_vupd.add_argument("--tags", type=str, help="New tags (comma-separated)")
    p_vupd.add_argument("--category", type=int, help="New category ID")
    p_vupd.add_argument("--privacy", type=str, choices=["private", "unlisted", "public"], help="New privacy status")
    p_vupd.add_argument("--thumbnail", type=str, help="Path to new thumbnail image")
    p_vupd.add_argument("--json", **json_kwargs)

    # --- video-delete ---
    p_vdel = subparsers.add_parser("video-delete", help="Delete a video")
    p_vdel.add_argument("--video-id", required=True, help="YouTube video ID")
    p_vdel.add_argument("--confirm", action="store_true", help="Required to confirm deletion")
    p_vdel.add_argument("--json", **json_kwargs)

    # --- stats ---
    p_stats = subparsers.add_parser("stats", help="View channel or video statistics")
    p_stats.add_argument("--video-id", type=str, help="Video ID (omit for channel stats)")
    p_stats.add_argument("--engaged", action="store_true",
                         help=f"Also fetch lifetime engaged views (the pre-{VIEWS_METHODOLOGY_DATE} "
                              "view definition) from the Analytics API")
    p_stats.add_argument("--json", **json_kwargs)

    # --- analytics ---
    p_an = subparsers.add_parser("analytics",
                                 help="Channel analytics (watch time, retention, traffic) — may need re-auth")
    p_an.add_argument("--days", type=int, default=28, help="Lookback window in days (default 28)")
    p_an.add_argument("--start-date", help="YYYY-MM-DD (overrides --days)")
    p_an.add_argument("--end-date", help="YYYY-MM-DD (default today)")
    p_an.add_argument(
        "--metrics",
        default=None,
        help=f"Comma-separated YouTube Analytics metrics (default: {ANALYTICS_DEFAULT_METRICS}, "
             "narrowed automatically for dimensions that only serve the core view metrics)")
    p_an.add_argument("--dimensions", help="e.g. day | video | insightTrafficSourceType | creatorContentType")
    p_an.add_argument("--sort", help="e.g. -views | day (a leading minus sorts descending)")
    p_an.add_argument("--video-id", help="Filter to a single video")
    p_an.add_argument("--max-results", type=int, help="Row cap (with dimensions)")
    p_an.add_argument("--json", **json_kwargs)

    # --- playlists ---
    p_pl = subparsers.add_parser("playlists", help="List playlists")
    p_pl.add_argument("--json", **json_kwargs)

    args = parser.parse_args(_splice_negative_values(sys.argv[1:]))

    # Auth command doesn't need existing credentials
    if args.command == "auth":
        _check_config()
        cmd_auth(args)
        return

    _check_config()

    commands = {
        "videos": cmd_videos,
        "video-get": cmd_video_get,
        "upload": cmd_upload,
        "video-update": cmd_video_update,
        "video-delete": cmd_video_delete,
        "stats": cmd_stats,
        "analytics": cmd_analytics,
        "playlists": cmd_playlists,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
