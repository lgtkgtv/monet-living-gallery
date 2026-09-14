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

    # 2. Resolutions
    res_cache = {}
    if os.path.exists(RESOLUTIONS_FILE):
        try:
            with open(RESOLUTIONS_FILE, 'r', encoding='utf-8') as f:
                res_cache = json.load(f)
        except Exception:
            res_cache = {}
    
    count_4k = sum(1 for v in res_cache.values() if v.get('is4K'))
    count_fhd = sum(1 for v in res_cache.values() if not v.get('is4K') and v.get('height', 0) >= 1080)
    count_other = len(videos) - (count_4k + count_fhd)
    print(f"📐 Resolution Breakdown:     {count_4k} in 4K UHD · {count_fhd} in 1080p FHD · {count_other} Other")
    print(f"   Resolution Cache Status:  {len(res_cache)} of {len(videos)} indexed ({round(len(res_cache)/max(1, len(videos))*100, 1)}%)")

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
    covered_vids = len(set(wp.get('videoId') for wp in wp_list))
    
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
    if res.returncode == 0:
        print("✅ Webpage assets (data.js and catalog CSV) built successfully.")
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

def run_extract(batch_size=10, tier=None, delay=3.0):
    cmd = [sys.executable, 'batch_wallpaper_extractor.py', '--batch-size', str(batch_size), '--delay', str(delay)]
    if tier:
        cmd.extend(['--tier', tier])
    print(f"🖼️ Running wallpaper extraction: {' '.join(cmd)}...")
    res = subprocess.run(cmd, capture_output=False)
    return res.returncode == 0

def run_serve(port=8000):
    print(f"🚀 Starting local gallery server on http://localhost:{port} ...")
    subprocess.run([sys.executable, '-m', 'http.server', str(port)])

def run_full_sync():
    print_banner("🔄 Running Full End-to-End Pipeline Sync")
    print("\nStep 1/3: Checking resolutions cache...")
    run_sync_resolutions()
    print("\nStep 2/3: Checking wallpaper extraction batch (top 5 pending)...")
    run_extract(batch_size=5, tier='4K', delay=3.0)
    print("\nStep 3/3: Building web assets & updating data.js...")
    run_build()
    print("\n✅ Full pipeline sync completed.")
    get_status()

def main():
    parser = argparse.ArgumentParser(
        description="L'Impressionnisme Vivant Unified Pipeline CLI",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('--status', action='store_true', help="Display comprehensive pipeline & catalog dashboard")
    parser.add_argument('--build', action='store_true', help="Rebuild data.js and catalog CSV")
    parser.add_argument('--sync-resolutions', action='store_true', help="Probe missing resolutions from YouTube")
    parser.add_argument('--extract', action='store_true', help="Extract wallpaper scenes using batch_wallpaper_extractor.py")
    parser.add_argument('--batch-size', type=int, default=10, help="Batch size for wallpaper extraction (default: 10)")
    parser.add_argument('--tier', choices=['4K', 'FHD', 'ALL'], default=None, help="Resolution tier filter for extraction")
    parser.add_argument('--delay', type=float, default=3.0, help="Anti-throttling delay in seconds between video extractions")
    parser.add_argument('--sync', action='store_true', help="Perform full automated end-to-end sync")
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
    if args.sync_resolutions:
        run_sync_resolutions()
    if args.extract:
        run_extract(batch_size=args.batch_size, tier=args.tier, delay=args.delay)
    if args.build:
        run_build()
    if args.sync:
        run_full_sync()
    if args.serve:
        run_serve(port=args.port)

if __name__ == '__main__':
    main()
