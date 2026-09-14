#!/usr/bin/env python3
"""
create_youtube_playlist.py - YouTube Data API Playlist Management Utility

Automates creating, updating, and syncing playlists on a user's YouTube account.
Uses OAuth 2.0 Installed App Flow with credentials in ~/.config/gcloud/credentials.json.

Usage:
  # 1. First-time OAuth authentication & list existing playlists
  python3 create_youtube_playlist.py --list

  # 2. Create a new playlist
  python3 create_youtube_playlist.py --create "Impressionist Highlights" --description "Curated 4K Impressionist artworks" --privacy unlisted

  # 3. Add video IDs to a playlist
  python3 create_youtube_playlist.py --playlist-id <PLAYLIST_ID> --add-videos "dQw4w9WgXcQ,abc123xyz"
"""

import os
import sys
import json
import argparse

SCOPES = ["https://www.googleapis.com/auth/youtube"]
DEFAULT_CLIENT_SECRETS = os.path.expanduser("~/.config/gcloud/credentials.json")
TOKEN_STORAGE = os.path.expanduser("~/.config/gcloud/youtube_token.json")

def check_dependencies():
    missing = []
    try:
        import google_auth_oauthlib.flow
    except ImportError:
        missing.append("google-auth-oauthlib")
    try:
        import googleapiclient.discovery
    except ImportError:
        missing.append("google-api-python-client")
    
    if missing:
        print("❌ Required Google API client packages are missing.")
        print(f"   Please install them via:\n   pip install {' '.join(missing)}")
        return False
    return True

def get_authenticated_service(client_secrets_file=DEFAULT_CLIENT_SECRETS, token_file=TOKEN_STORAGE):
    if not check_dependencies():
        sys.exit(1)

    import google.oauth2.credentials
    import google_auth_oauthlib.flow
    import googleapiclient.discovery

    creds = None
    if os.path.exists(token_file):
        try:
            with open(token_file, "r") as token:
                token_data = json.load(token)
                creds = google.oauth2.credentials.Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            print(f"⚠️ Error reading existing token: {e}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            print("🔄 Refreshing expired OAuth token...")
            creds.refresh(Request())
        else:
            if not os.path.exists(client_secrets_file):
                print(f"❌ Client secrets file not found at: {client_secrets_file}")
                print("   Download your OAuth 2.0 Client Credentials JSON from Google Cloud Console")
                print("   and place it at ~/.config/gcloud/credentials.json")
                sys.exit(1)

            print("🔐 Launching OAuth 2.0 authorization flow...")
            print("   A browser window will open for you to sign in and grant YouTube playlist management access.")
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, SCOPES
            )
            try:
                creds = flow.run_local_server(port=8080, prompt="consent")
            except Exception:
                print("⚠️ Local server flow could not bind port 8080; falling back to console authorization.")
                creds = flow.run_console()

        # Save authorized user token for subsequent headless runs
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        with open(token_file, "w") as token:
            token.write(creds.to_json())
        print(f"✅ User OAuth credentials saved securely to {token_file}")

    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

def list_playlists(youtube):
    print("📋 Fetching your YouTube playlists...")
    request = youtube.playlists().list(
        part="snippet,contentDetails,status",
        mine=True,
        maxResults=50
    )
    response = request.execute()
    items = response.get("items", [])
    if not items:
        print("   No playlists found on this YouTube account.")
        return items

    print(f"\nFound {len(items)} playlists:")
    print("-" * 75)
    for p in items:
        p_id = p["id"]
        title = p["snippet"]["title"]
        count = p["contentDetails"]["itemCount"]
        privacy = p["status"]["privacyStatus"]
        print(f" • [{p_id}] {title} ({count} videos) - Privacy: {privacy}")
        print(f"   URL: https://www.youtube.com/playlist?list={p_id}")
    print("-" * 75)
    return items

def create_playlist(youtube, title, description="", privacy="unlisted"):
    print(f"✨ Creating YouTube playlist: '{title}' (privacy: {privacy})...")
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description
            },
            "status": {
                "privacyStatus": privacy
            }
        }
    )
    response = request.execute()
    playlist_id = response.get("id")
    print(f"🎉 Playlist created successfully!")
    print(f"   Playlist ID: {playlist_id}")
    print(f"   URL: https://www.youtube.com/playlist?list={playlist_id}")
    return playlist_id

def add_videos_to_playlist(youtube, playlist_id, video_ids):
    if isinstance(video_ids, str):
        video_ids = [vid.strip() for vid in video_ids.split(",") if vid.strip()]

    print(f"📥 Adding {len(video_ids)} video(s) to playlist {playlist_id}...")
    added = 0
    for idx, vid in enumerate(video_ids, 1):
        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": vid
                        }
                    }
                }
            ).execute()
            print(f"   [{idx}/{len(video_ids)}] Added video {vid}")
            added += 1
        except Exception as e:
            print(f"   [{idx}/{len(video_ids)}] ❌ Failed to add {vid}: {e}")

    print(f"✅ Added {added} video(s) to playlist.")

def main():
    parser = argparse.ArgumentParser(description="Manage YouTube playlists programmatically via YouTube Data API v3.")
    parser.add_argument("--list", action="store_true", help="List playlists on the authenticated YouTube channel")
    parser.add_argument("--create", type=str, metavar="TITLE", help="Create a new playlist with the specified title")
    parser.add_argument("--description", type=str, default="Curated Impressionist Masterworks collection", help="Description for newly created playlist")
    parser.add_argument("--privacy", type=str, choices=["public", "private", "unlisted"], default="unlisted", help="Privacy status (default: unlisted)")
    parser.add_argument("--playlist-id", type=str, help="Target playlist ID for adding videos")
    parser.add_argument("--add-videos", type=str, help="Comma-separated YouTube video IDs to add to the playlist")
    args = parser.parse_args()

    if not any([args.list, args.create, args.add_videos]):
        parser.print_help()
        sys.exit(0)

    youtube = get_authenticated_service()

    if args.create:
        pid = create_playlist(youtube, args.create, args.description, args.privacy)
        if args.add_videos:
            add_videos_to_playlist(youtube, pid, args.add_videos)
    elif args.add_videos:
        if not args.playlist_id:
            print("❌ --playlist-id is required when using --add-videos")
            sys.exit(1)
        add_videos_to_playlist(youtube, args.playlist_id, args.add_videos)

    if args.list:
        list_playlists(youtube)

if __name__ == "__main__":
    main()
