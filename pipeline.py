#!/usr/bin/env python3
"""
L'Impressionnisme Vivant - Unified Pipeline Manager
A robust, modular orchestrator for managing the Monet Living Gallery archive:
- Status & telemetry dashboard (--status)
- Webpage & catalog builder (--build)
- Resolution metadata syncer (--sync-resolutions)
- Safe, anti-throttled wallpaper extractor (--extract)
- Full end-to-end sync (--sync)
- Local preview server (--serve)
"""

import os
import sys
import json
import argparse
import subprocess
from collections import Counter
from datetime import datetime

PLAYLIST_FILE = 'playlist_raw.json'
RESOLUTIONS_FILE = 'video_resolutions.json'
WALLPAPER_DIR = 'wallpapers'
METADATA_FILE = os.path.join(WALLPAPER_DIR, 'metadata.json')
TRACKER_FILE = os.path.join(WALLPAPER_DIR, 'batch_tracker.json')

def print_banner(text):
    print("\n" + "=" * 64)
    print(f"  {text}")
    print("=" * 64)

def get_status():
    print_banner("🎨 L'Impressionnisme Vivant - Pipeline Status")
    
    # 1. Videos
    if not os.path.exists(PLAYLIST_FILE):
        print(f"❌ Missing {PLAYLIST_FILE}")
        return
    with open(PLAYLIST_FILE, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    print(f"🎬 Total Catalog Videos:      {len(videos)}")
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                dm = json.load(f).get('metadata', {})
                if dm.get('alternateCutsCount'):
                    print(f"   De-cluttered Gallery:     {dm.get('declutteredVideosCount')} works ({dm.get('alternateCutsCount')} redundant cuts collapsed across {dm.get('totalDuplicateGroups')} clusters)")
        except Exception:
            pass

    # 2. Resolutions
    res_cache = {}
    if os.path.exists(RESOLUTIONS_FILE):
        try:
            with open(RESOLUTIONS_FILE, 'r', encoding='utf-8') as f:
                res_cache = json.load(f)
        except Exception:
            res_cache = {}

    catalog_ids = set(v.get('id') for v in videos if v.get('id'))
    indexed_in_catalog = sum(1 for vid in catalog_ids if vid in res_cache)

    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                dmeta = json.load(f).get('metadata', {})
                count_4k = dmeta.get('count4K', 0)
                count_fhd = dmeta.get('countFHD', 0)
        except Exception:
            count_4k = sum(1 for vid in catalog_ids if res_cache.get(vid, {}).get('is4K'))
            count_fhd = sum(1 for vid in catalog_ids if not res_cache.get(vid, {}).get('is4K') and res_cache.get(vid, {}).get('height', 0) >= 1080)
    else:
        count_4k = sum(1 for vid in catalog_ids if res_cache.get(vid, {}).get('is4K'))
        count_fhd = sum(1 for vid in catalog_ids if not res_cache.get(vid, {}).get('is4K') and res_cache.get(vid, {}).get('height', 0) >= 1080)

    count_other = len(videos) - (count_4k + count_fhd)
    print(f"📐 Resolution Breakdown:     {count_4k} in 4K UHD · {count_fhd} in 1080p FHD · {count_other} Other")
    print(f"   Resolution Cache Status:  {indexed_in_catalog} of {len(videos)} catalog titles indexed ({round(indexed_in_catalog/max(1, len(videos))*100, 1)}%)")

    # 3. Channels
    channel_counts = Counter(v.get('channel') or v.get('uploader') or 'Unknown' for v in videos)
    print(f"🏛️ Source Channels:           {len(channel_counts)} channels")
    top_channels = channel_counts.most_common(5)
    print("   Top Curators:")
    for ch, count in top_channels:
        print(f"     • {ch}: {count} videos")

    # 4. Wallpapers
    wp_list = []
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                wp_list = json.load(f)
        except Exception:
            wp_list = []

    desktop_wp = sum(1 for wp in wp_list if wp.get('formFactor') == 'desktop')
    mobile_wp = sum(1 for wp in wp_list if wp.get('formFactor') == 'mobile')
    covered_vids = len(set(wp.get('videoId') for wp in wp_list if wp.get('videoId') in catalog_ids))

    print(f"🖼️ Wallpaper Archive:         {len(wp_list)} snapshots ({desktop_wp} desktop widescreen, {mobile_wp} mobile portrait)")
    print(f"   Video Coverage:           {covered_vids} of {len(videos)} titles covered ({round(covered_vids/max(1, len(videos))*100, 1)}%)")

    # 5. Extraction Tracker
    if os.path.exists(TRACKER_FILE):
        try:
            with open(TRACKER_FILE, 'r', encoding='utf-8') as f:
                tracker = json.load(f)
            t_vids = tracker.get('videos', {})
            done = sum(1 for v in t_vids.values() if v.get('status') == 'completed')
            pending = sum(1 for v in t_vids.values() if v.get('status') == 'pending')
            failed = sum(1 for v in t_vids.values() if v.get('status') == 'failed')
            print(f"⚙️ Batch Extractor Tracker:   {done} completed · {pending} pending · {failed} failed")
        except Exception:
            pass
    print("=" * 64 + "\n")

def run_build():
    print("🔨 Running build_webpage.py...")
    res = subprocess.run([sys.executable, 'build_webpage.py'], capture_output=False)
    if os.path.exists('generate_report.py'):
        subprocess.run([sys.executable, 'generate_report.py'], capture_output=False)
    if res.returncode == 0:
        print("✅ Webpage assets (data.js and catalog CSV/Markdown) built successfully.")
    else:
        print("❌ build_webpage.py failed.")
    return res.returncode == 0

def run_sync_resolutions():
    print("📡 Running update_resolutions.py to probe missing video resolutions...")
    res = subprocess.run([sys.executable, 'update_resolutions.py'], capture_output=False)
    if res.returncode == 0:
        print("✅ Resolutions synchronized.")
        run_build()
    else:
        print("❌ update_resolutions.py failed.")
    return res.returncode == 0

def run_extract(batch_size=10, tier=None, delay=3.0, continuous=False, skip_copyright=False):
    cmd = [sys.executable, 'batch_wallpaper_extractor.py', '--batch-size', str(batch_size), '--delay', str(delay)]
    if tier:
        cmd.extend(['--tier', tier.lower()])
    if continuous:
        cmd.append('--continuous')
    if skip_copyright:
        cmd.append('--skip-copyright-restricted')
    print(f"🖼️ Running wallpaper extraction: {' '.join(cmd)}...")
    res = subprocess.run(cmd, capture_output=False)
    return res.returncode == 0

from core.playlist_engine import (
    load_gallery_config,
    get_active_playlists,
    ingest_all_configured_playlists,
    sync_and_save_raw_catalog
)

def get_configured_playlists():
    config = load_gallery_config()
    return [p['url'] for p in get_active_playlists(config)]

def run_pull_playlist(playlist_urls=None):
    if not playlist_urls:
        return sync_and_save_raw_catalog(PLAYLIST_FILE)
    elif isinstance(playlist_urls, str):
        if ',' in playlist_urls:
            playlist_urls = [u.strip() for u in playlist_urls.split(',') if u.strip()]
        else:
            playlist_urls = [playlist_urls.strip()]

    all_entries = []
    seen_ids = set()

    for p_url in playlist_urls:
        print(f"📥 Fetching playlist metadata via yt-dlp: {p_url} ...")
        cmd = ['yt-dlp', '--flat-playlist', '-J', p_url]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if proc.returncode == 0 and proc.stdout:
                data = json.loads(proc.stdout)
                entries = data.get('entries', [])
                new_added = 0
                for item in entries:
                    v_id = item.get('id')
                    if v_id and v_id not in seen_ids:
                        seen_ids.add(v_id)
                        all_entries.append(item)
                        new_added += 1
                print(f"   ✓ Added {new_added} unique items ({len(entries)} total in this playlist).")
            else:
                print(f"   ❌ yt-dlp failed for {p_url}: {proc.stderr[:200]}")
        except Exception as e:
            print(f"   ❌ Exception pulling {p_url}: {e}")

    if all_entries:
        with open(PLAYLIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_entries, f, indent=2, ensure_ascii=False)
        print(f"✅ Successfully written {len(all_entries)} combined catalog items to {PLAYLIST_FILE}.")
        return True
    return False

def run_serve(port=8000):
    print(f"🚀 Starting local gallery server on http://localhost:{port} ...")
    subprocess.run([sys.executable, '-m', 'http.server', str(port)])

def run_refresh(playlist_urls=None):
    print_banner("🔄 Refreshing Gallery from Source YouTube Playlist(s)")
    print("\nStep 1/3: Pulling latest playlist entries from YouTube...")
    success = run_pull_playlist(playlist_urls)
    if not success:
        print("⚠️ Could not pull fresh playlist. Retaining current catalog.")
    print("\nStep 2/3: Checking and probing video resolutions cache...")
    run_sync_resolutions()
    print("\nStep 3/3: Rebuilding web application assets (data.js, data.json, CSV)...")
    run_build()
    print("\n✨ Gallery refreshed and rebuilt successfully.")
    get_status()

def run_full_sync():
    print_banner("🔄 Running Full End-to-End Pipeline Sync")
    print("\nStep 1/4: Pulling latest playlist metadata from YouTube...")
    run_pull_playlist()
    print("\nStep 2/4: Checking and probing video resolutions cache...")
    run_sync_resolutions()
    print("\nStep 3/4: Running wallpaper extraction batch...")
    run_extract(batch_size=5, tier='fhd', delay=2.0)
    print("\nStep 4/4: Building web assets, data.js, data.json, and CSV catalogs...")
    run_build()
    print("\n✅ Full pipeline sync completed.")
    get_status()

def run_detect_duplicates():
    print_banner("🔍 Multi-Cut & Duplicate Segment Analysis")
    if not os.path.exists('data.json'):
        run_build()

    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    meta = data.get('metadata', {})
    groups = data.get('duplicateGroups', [])

    print("📊 Catalog Overview:")
    print(f"   • Total Catalog Videos:      {meta.get('totalVideos', 0)}")
    print(f"   • De-cluttered Gallery Size: {meta.get('declutteredVideosCount', 0)} works")
    print(f"   • Redundant Alternate Cuts:  {meta.get('alternateCutsCount', 0)} cuts across {meta.get('totalDuplicateGroups', 0)} clusters\n")

    if not groups:
        print("✅ No duplicate title clusters or multi-length cuts detected.")
        return

    for idx, g in enumerate(groups, 1):
        print(f"Cluster #{idx}: {g['canonicalStem'].title()} ({g['totalCuts']} cuts)")
        print(f"   🏛️ Channel: {g['channel']}")
        print(f"   🔑 Primary Video: {g['primaryVideoId']}")
        print("   🎞️ Available Cuts:")
        for c in g['cuts']:
            status_tag = "👑 PRIMARY CUT" if c.get('isPrimary') else "✂️ ALTERNATE"
            print(f"      • [{status_tag}] {c['id']} | {c['qualityLabel']} | {c['durationFormatted']} | {c['views']} views")
            print(f"        Title: \"{c['title']}\"")
        print("-" * 64)
    print("\n💡 Tip: In the Web Gallery, select 'De-clutter (Primary Cuts Only)' to collapse redundant segments,")
    print("   or click the '🎞️ Alternate Cuts' bar inside any video player lightbox to switch between cuts.\n")

def main():
    parser = argparse.ArgumentParser(
        description="L'Impressionnisme Vivant Unified Pipeline CLI",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('--status', action='store_true', help="Display comprehensive pipeline & catalog dashboard")
    parser.add_argument('--refresh', nargs='?', const='', help="One-command manual refresh: pull playlist(s), probe resolutions & rebuild site")
    parser.add_argument('--pull-playlist', nargs='?', const='', help="Fetch fresh playlist JSON (accepts URL, comma-separated URLs, or reads playlists.json)")
    parser.add_argument('--build', action='store_true', help="Rebuild data.js, data.json, and catalog CSV")
    parser.add_argument('--detect-duplicates', action='store_true', help="Detect duplicate titles, re-uploads, and multi-length segment cuts")
    parser.add_argument('--sync-resolutions', '--update-resolutions', dest='sync_resolutions', action='store_true', help="Probe missing resolutions from YouTube")
    parser.add_argument('--extract', action='store_true', help="Extract wallpaper scenes using batch_wallpaper_extractor.py")
    parser.add_argument('--continuous', action='store_true', help="Continuously extract all pending batches until 100% complete")
    parser.add_argument('--skip-copyright-restricted', action='store_true', help="Exclude titles/channels with copyright download restrictions")
    parser.add_argument('--batch-size', type=int, default=10, help="Batch size for wallpaper extraction (default: 10)")
    parser.add_argument('--tier', type=str.upper, choices=['4K', 'FHD', 'ALL'], default=None, help="Resolution tier filter for extraction")
    parser.add_argument('--delay', type=float, default=3.0, help="Anti-throttling delay in seconds between video extractions")
    parser.add_argument('--sync', action='store_true', help="Perform full automated end-to-end sync (with wallpaper extraction)")
    parser.add_argument('--serve', action='store_true', help="Start local preview web server")
    parser.add_argument('--port', type=int, default=8000, help="Port for local web server (default: 8000)")

    args = parser.parse_args()

    # Default to status if no arguments provided
    if len(sys.argv) == 1:
        get_status()
        parser.print_help()
        return

    if args.status:
        get_status()
    if args.detect_duplicates:
        run_detect_duplicates()
    if args.refresh is not None:
        target = args.refresh if args.refresh else None
        run_refresh(target)
    if args.pull_playlist is not None:
        target = args.pull_playlist if args.pull_playlist else None
        if run_pull_playlist(target):
            run_sync_resolutions()
    if args.sync_resolutions:
        run_sync_resolutions()
    if args.extract:
        run_extract(batch_size=args.batch_size, tier=args.tier, delay=args.delay, continuous=args.continuous, skip_copyright=args.skip_copyright_restricted)
    if args.build:
        run_build()
    if args.sync:
        run_full_sync()
    if args.serve:
        run_serve(port=args.port)

if __name__ == '__main__':
    main()
