#!/usr/bin/env python3
"""
Core Reusable Playlist Engine for YouTube Living Gallery Applications
----------------------------------------------------------------------
This module provides a decoupled, reusable architectural pattern for turning
one or more YouTube Playlists into a searchable Video Explorer and Wallpaper Gallery.

Key Capabilities:
1. Multi-Playlist Configuration: Ingests N playlists defined in playlists.config.json.
2. Metadata Tagging: Attaches source playlist ID, title, and category to each video.
3. Cross-Playlist Deduplication: Ensures video IDs are unique while preserving all
   source playlist references (allows filtering by playlist in the UI).
4. Channel Copyright Policy Tracking: Configurable list of download-prohibited channels.
5. Headless Execution: Safe, polite yt-dlp flat-playlist metadata extraction (uses 0 YouTube Data API quota).
"""

import os
import sys
import json
import subprocess
from typing import Dict, List, Any, Optional, Set, Tuple

DEFAULT_CONFIG_PATH = 'playlists.config.json'
LEGACY_PLAYLIST_PATH = 'playlists.json'
RAW_PLAYLIST_OUTPUT = 'playlist_raw.json'
PLAYLIST_TRACKER_PATH = 'playlist_tracker.json'

def load_gallery_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """
    Loads gallery configuration from playlists.config.json, falling back
    gracefully to playlists.json or a sensible single-playlist default.
    """
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading {config_path}: {e}")

    # Fallback to legacy playlists.json
    if os.path.exists(LEGACY_PLAYLIST_PATH):
        try:
            with open(LEGACY_PLAYLIST_PATH, 'r', encoding='utf-8') as f:
                legacy_list = json.load(f)
                return {
                    "app": {
                        "title": "L'Impressionnisme Vivant",
                        "subtitle": "Step inside the living canvases of Claude Monet and the Impressionist masters.",
                        "curator": "sachin g",
                        "defaultResolutionFilter": "4K"
                    },
                    "playlists": legacy_list,
                    "prohibitedDownloadChannels": ["Living Art Moments"]
                }
        except Exception as e:
            print(f"⚠️ Error reading legacy {LEGACY_PLAYLIST_PATH}: {e}")

    # Ultimate fallback
    return {
        "app": {
            "title": "L'Impressionnisme Vivant",
            "subtitle": "Step inside the living canvases of Claude Monet and the Impressionist masters.",
            "curator": "sachin g",
            "defaultResolutionFilter": "4K"
        },
        "playlists": [
            {
                "id": "PLeqGkucOU6lA",
                "url": "https://www.youtube.com/playlist?list=PLeqGkucOU6lA",
                "title": "sh_Monet inspired Visual Arts",
                "category": "Impressionism & Masters",
                "enabled": True
            }
        ],
        "prohibitedDownloadChannels": ["Living Art Moments"]
    }

def get_active_playlists(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Returns all enabled playlists from the configuration."""
    playlists = config.get('playlists', [])
    return [p for p in playlists if p.get('enabled', True) and p.get('url')]

def load_playlist_tracker(path: str = PLAYLIST_TRACKER_PATH) -> Dict[str, Any]:
    """Loads stateful source playlist tracker recording modification dates and sync history."""
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "last_checked": None,
        "playlists": {}
    }

def save_playlist_tracker(tracker: Dict[str, Any], path: str = PLAYLIST_TRACKER_PATH) -> None:
    """Persists playlist sync and modification state to JSON."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(tracker, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Could not save {path}: {e}")

def probe_playlist_metadata(playlist_url: str, timeout_sec: int = 15) -> Dict[str, Any]:
    """
    Sub-second probe of YouTube playlist metadata (modified_date, playlist_count, top item ID)
    without downloading streams or incurring YouTube Data API quota.
    """
    cmd = ['yt-dlp', '--flat-playlist', '--playlist-items', '1', '-J', playlist_url]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        if proc.returncode == 0 and proc.stdout:
            data = json.loads(proc.stdout)
            entries = data.get('entries', [])
            mod_raw = data.get('modified_date')
            mod_fmt = f"{mod_raw[:4]}-{mod_raw[4:6]}-{mod_raw[6:8]}" if mod_raw and len(mod_raw) == 8 else mod_raw
            return {
                'id': data.get('id'),
                'title': data.get('title'),
                'uploader': data.get('uploader') or data.get('channel'),
                'modified_date_raw': mod_raw,
                'modified_date': mod_fmt,
                'playlist_count': data.get('playlist_count'),
                'top_video_id': entries[0].get('id') if entries else None,
                'url': playlist_url,
                'available': True,
                'error': None
            }
        else:
            return {'available': False, 'error': (proc.stderr or "Probe failed").strip()[:160], 'url': playlist_url}
    except Exception as e:
        return {'available': False, 'error': str(e)[:160], 'url': playlist_url}

def check_playlist_updates(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Compares live YouTube playlist modification dates and video counts
    against the last recorded sync in playlist_tracker.json.
    """
    from datetime import datetime
    if config is None:
        config = load_gallery_config()

    tracker = load_playlist_tracker()
    active_playlists = get_active_playlists(config)
    now_iso = datetime.now().isoformat()

    results = {
        'checked_at': now_iso,
        'has_updates': False,
        'playlists': []
    }

    for p in active_playlists:
        p_url = p.get('url')
        p_id = p.get('id')
        p_title = p.get('title', p_id or 'Playlist')

        probe = probe_playlist_metadata(p_url)
        saved = tracker.get('playlists', {}).get(p_id, {})

        is_modified = False
        reasons = []

        if probe.get('available'):
            live_mod = probe.get('modified_date')
            live_count = probe.get('playlist_count')
            live_top = probe.get('top_video_id')

            saved_mod = saved.get('last_known_modified_date')
            saved_count = saved.get('last_known_count')
            saved_top = saved.get('last_known_top_video_id')

            # 1. Check if count changed
            if saved_count is not None and live_count is not None and live_count != saved_count:
                is_modified = True
                reasons.append(f"Video count changed: {saved_count} -> {live_count} items")

            # 2. Check if modification date changed
            if saved_mod and live_mod and live_mod != saved_mod:
                is_modified = True
                reasons.append(f"YouTube modified date changed: {saved_mod} -> {live_mod}")

            # 3. Check if top video ID changed
            if saved_top and live_top and live_top != saved_top:
                is_modified = True
                reasons.append(f"Top video changed: {saved_top} -> {live_top}")

            # First time seeing playlist in tracker
            if not saved:
                is_modified = True
                reasons.append("New playlist not previously tracked in local state")

            results['playlists'].append({
                'id': p_id,
                'title': probe.get('title') or p_title,
                'url': p_url,
                'is_modified': is_modified,
                'reasons': reasons,
                'live_modified_date': live_mod,
                'live_count': live_count,
                'live_top_video_id': live_top,
                'saved_modified_date': saved_mod,
                'saved_count': saved_count,
                'last_synced_at': saved.get('last_synced_at')
            })

            if is_modified:
                results['has_updates'] = True
        else:
            results['playlists'].append({
                'id': p_id,
                'title': p_title,
                'url': p_url,
                'is_modified': False,
                'error': probe.get('error', 'Unreachable'),
                'reasons': [f"Probe failed: {probe.get('error')}"]
            })

    tracker['last_checked'] = now_iso
    save_playlist_tracker(tracker)
    return results

def fetch_single_playlist(playlist_url: str, timeout_sec: int = 120) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Uses yt-dlp flat-playlist extraction to safely pull video metadata
    without downloading streams or consuming YouTube Data API quota.
    """
    cmd = ['yt-dlp', '--flat-playlist', '-J', playlist_url]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        if proc.returncode == 0 and proc.stdout:
            data = json.loads(proc.stdout)
            entries = data.get('entries', [])
            mod_raw = data.get('modified_date')
            mod_fmt = f"{mod_raw[:4]}-{mod_raw[4:6]}-{mod_raw[6:8]}" if mod_raw and len(mod_raw) == 8 else mod_raw
            meta = {
                'id': data.get('id'),
                'title': data.get('title'),
                'uploader': data.get('uploader') or data.get('channel'),
                'view_count': data.get('view_count'),
                'url': playlist_url,
                'modified_date_raw': mod_raw,
                'modified_date': mod_fmt,
                'playlist_count': data.get('playlist_count') or len(entries),
                'top_video_id': entries[0].get('id') if entries else None
            }
            return entries, meta
        else:
            print(f"   ❌ yt-dlp error pulling {playlist_url}: {proc.stderr[:180]}")
    except Exception as e:
        print(f"   ❌ Exception pulling {playlist_url}: {e}")
    return [], {}

def ingest_all_configured_playlists(config: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Aggregates videos from all active playlists into a unified catalog:
    - Tags each video with playlistId, playlistTitle, playlistCategory.
    - Preserves all source playlist IDs if a video exists in multiple playlists.
    - Deduplicates by video ID.
    """
    if config is None:
        config = load_gallery_config()

    active_playlists = get_active_playlists(config)
    print(f"\n🏛️ Processing {len(active_playlists)} configured playlist(s)...")

    combined_entries: List[Dict[str, Any]] = []
    seen_videos: Dict[str, Dict[str, Any]] = {}
    playlist_summaries: List[Dict[str, Any]] = []

    for idx, p_cfg in enumerate(active_playlists, 1):
        p_url = p_cfg.get('url')
        p_title = p_cfg.get('title', f"Playlist #{idx}")
        p_id = p_cfg.get('id', '')
        p_cat = p_cfg.get('category', 'General')

        print(f"[{idx}/{len(active_playlists)}] 📥 Ingesting: {p_title} ({p_url})...")
        raw_entries, p_meta = fetch_single_playlist(p_url)

        valid_entries_count = 0
        new_unique_count = 0

        for item in raw_entries:
            v_id = item.get('id')
            if not v_id:
                continue

            valid_entries_count += 1

            if v_id in seen_videos:
                # Video already encountered in a previous playlist — append this playlist reference
                existing = seen_videos[v_id]
                source_pids = existing.setdefault('sourcePlaylistIds', [existing.get('playlistId')])
                if p_id and p_id not in source_pids:
                    source_pids.append(p_id)
            else:
                # First time seeing this video
                item['playlistId'] = p_id
                item['playlistTitle'] = p_title
                item['playlistCategory'] = p_cat
                item['sourcePlaylistIds'] = [p_id] if p_id else []
                seen_videos[v_id] = item
                combined_entries.append(item)
                new_unique_count += 1

        print(f"   ✓ Ingested {valid_entries_count} entries ({new_unique_count} new unique titles).")

        playlist_summaries.append({
            'id': p_id,
            'url': p_url,
            'title': p_meta.get('title') or p_title,
            'category': p_cat,
            'videoCount': valid_entries_count,
            'modifiedDate': p_meta.get('modified_date'),
            'playlistCount': p_meta.get('playlist_count', valid_entries_count),
            'topVideoId': p_meta.get('top_video_id')
        })

    return combined_entries, playlist_summaries

def sync_and_save_raw_catalog(output_file: str = RAW_PLAYLIST_OUTPUT) -> bool:
    """Convenience routine to ingest all playlists and write to playlist_raw.json."""
    config = load_gallery_config()
    entries, summaries = ingest_all_configured_playlists(config)
    if not entries:
        print("⚠️ No video entries found. Retaining existing catalog.")
        return False

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    # Persist updated modification dates & sync state into playlist_tracker.json
    from datetime import datetime
    tracker = load_playlist_tracker()
    now_iso = datetime.now().isoformat()
    for s in summaries:
        pid = s.get('id')
        if pid:
            tracker.setdefault('playlists', {})[pid] = {
                'id': pid,
                'url': s.get('url'),
                'title': s.get('title'),
                'last_known_modified_date': s.get('modifiedDate'),
                'last_known_count': s.get('playlistCount'),
                'last_known_top_video_id': s.get('topVideoId'),
                'last_synced_at': now_iso,
                'synced_video_count': s.get('videoCount')
            }
    tracker['last_synced'] = now_iso
    tracker['last_checked'] = now_iso
    save_playlist_tracker(tracker)

    print(f"\n✅ Successfully saved {len(entries)} aggregated unique titles across {len(summaries)} playlist(s) to {output_file}.")
    print(f"📡 Synchronized source playlist tracking state in {PLAYLIST_TRACKER_PATH}.")
    return True

if __name__ == '__main__':
    sync_and_save_raw_catalog()
