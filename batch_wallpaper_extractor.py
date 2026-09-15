#!/usr/bin/env python3
"""
Batch Wallpaper Extractor & Pipeline Manager for Impressionist Art Archive.

Features:
- Prioritization engine: 4K UHD first (by view count desc), then 1080p FHD (by views desc), then others.
- Multi-day batch execution with state tracking (wallpapers/batch_tracker.json).
- Zero YouTube API quota consumption (uses yt-dlp + ffmpeg directly).
- Anti-throttling / safe pacing (configurable delays + random jitter to prevent HTTP 429).
- CLI Dashboard (--status) showing finished vs pending titles across resolution tiers.
- Automatic metadata sync with wallpapers/metadata.json and data.js.
"""

import os
import sys
import json
import time
import random
import argparse
import subprocess
from datetime import datetime

WALLPAPER_DIR = "wallpapers"
TRACKER_FILE = os.path.join(WALLPAPER_DIR, "batch_tracker.json")
METADATA_FILE = os.path.join(WALLPAPER_DIR, "metadata.json")
PLAYLIST_FILE = "playlist_raw.json"
RES_FILE = "video_resolutions.json"

def calculate_scenery_timestamps(duration_sec):
    """
    Generate diverse scenery timestamps across the video:
    - Short (<4m): 7 scenes
    - Medium (4-15m): 9 scenes
    - Long (15-60m): 12 scenes
    - Anthologies & Screensavers (>60m): 16 scenes
    """
    dur = int(duration_sec or 240)
    if dur <= 60:
        return [10, max(15, dur // 2), max(20, dur - 8)]
    if dur < 240:
        num = 7
        start, end = max(10, int(dur * 0.08)), min(dur - 8, int(dur * 0.92))
    elif dur < 900:
        num = 9
        start, end = max(15, int(dur * 0.06)), min(dur - 12, int(dur * 0.94))
    elif dur < 3600:
        num = 12
        start, end = max(30, int(dur * 0.04)), min(dur - 30, int(dur * 0.96))
    else:
        num = 16
        start, end = 45, min(dur - 60, int(dur * 0.95))

    step = (end - start) / max(1, num - 1)
    return [int(start + i * step) for i in range(num)]

def format_timestamp(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def detect_form_factor(image_path, width=None, height=None):
    """
    Detect whether an extracted wallpaper is desktop widescreen or mobile/pillarboxed portrait.
    Returns 'mobile' if height > width or if black pillarbox bars are detected on left/right edges.
    Otherwise returns 'desktop'.
    """
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            w, h = img.size
            if h > w:
                return "mobile"
            # Sample left/right margins to check for black pillarbox bars
            rgb = img.convert("RGB")
            left_sample = rgb.crop((int(w * 0.02), int(h * 0.2), int(w * 0.06), int(h * 0.8)))
            right_sample = rgb.crop((int(w * 0.94), int(h * 0.2), int(w * 0.98), int(h * 0.8)))
            
            if hasattr(left_sample, 'get_flattened_data'):
                left_raw = left_sample.get_flattened_data()
                right_raw = right_sample.get_flattened_data()
                left_lums = [left_raw[i] * 0.299 + left_raw[i+1] * 0.587 + left_raw[i+2] * 0.114 for i in range(0, len(left_raw), 3)]
                right_lums = [right_raw[i] * 0.299 + right_raw[i+1] * 0.587 + right_raw[i+2] * 0.114 for i in range(0, len(right_raw), 3)]
            else:
                left_lums = [p[0] * 0.299 + p[1] * 0.587 + p[2] * 0.114 for p in left_sample.getdata()]
                right_lums = [p[0] * 0.299 + p[1] * 0.587 + p[2] * 0.114 for p in right_sample.getdata()]
            avg_l = sum(left_lums) / max(len(left_lums), 1)
            avg_r = sum(right_lums) / max(len(right_lums), 1)
            if avg_l < 18 and avg_r < 18:
                return "mobile"
    except Exception:
        if height and width and height > width:
            return "mobile"
    return "desktop"

def load_playlist_and_resolutions():
    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        playlist = json.load(f)
    
    res_cache = {}
    if os.path.exists(RES_FILE):
        try:
            with open(RES_FILE, "r", encoding="utf-8") as f:
                res_cache = json.load(f)
        except Exception:
            res_cache = {}
    return playlist, res_cache

def load_or_init_tracker(playlist, res_cache):
    os.makedirs(WALLPAPER_DIR, exist_ok=True)
    existing_meta = []
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                existing_meta = json.load(f)
        except Exception:
            existing_meta = []

    # Map existing files by videoId
    existing_by_video = {}
    for r in existing_meta:
        vid = r.get("videoId")
        if vid:
            existing_by_video.setdefault(vid, []).append(r)

    MIN_REQUIRED_SCENES = 3

    # Check disk for actual image files
    disk_completed = set()
    for vid_entry in os.listdir(WALLPAPER_DIR):
        vdir = os.path.join(WALLPAPER_DIR, vid_entry)
        if os.path.isdir(vdir):
            jpgs = [f for f in os.listdir(vdir) if f.startswith("snapshot_") and f.endswith(".jpg")]
            if len(jpgs) >= MIN_REQUIRED_SCENES:
                disk_completed.add(vid_entry)

    tracker = {}
    if os.path.exists(TRACKER_FILE):
        try:
            with open(TRACKER_FILE, "r", encoding="utf-8") as f:
                tracker = json.load(f)
        except Exception:
            tracker = {}

    videos_map = tracker.get("videos", {})

    # Build or update video records
    for item in playlist:
        vid = item["id"]
        res_info = res_cache.get(vid, {})
        is_4k = res_info.get("is4K", False)
        height = res_info.get("height", 1080)
        views = item.get("view_count") or 0

        # Determine Tier
        if is_4k:
            tier = "Tier 1: 4K UHD"
            tier_rank = 1
        elif height >= 1080:
            tier = "Tier 2: 1080p FHD"
            tier_rank = 2
        else:
            tier = "Tier 3: 720p/Other"
            tier_rank = 3

        existing_records = existing_by_video.get(vid, [])
        is_done = (len(existing_records) >= MIN_REQUIRED_SCENES) and (vid in disk_completed)

        if vid not in videos_map:
            videos_map[vid] = {
                "id": vid,
                "title": item.get("title", "Unknown"),
                "channel": item.get("channel") or item.get("uploader") or "Unknown",
                "views": views,
                "tier": tier,
                "tier_rank": tier_rank,
                "is_4k": is_4k,
                "height": height,
                "duration": item.get("duration") or 0,
                "status": "completed" if is_done else "pending",
                "extracted_count": len(existing_records),
                "last_attempt": datetime.now().isoformat() if is_done else None,
                "error": None,
                "retry_count": 0
            }
        else:
            # Refresh views / tier info if needed
            videos_map[vid]["views"] = views
            videos_map[vid]["is_4k"] = is_4k
            videos_map[vid]["tier"] = tier
            videos_map[vid]["tier_rank"] = tier_rank
            if not is_done:
                videos_map[vid]["status"] = "pending"
                videos_map[vid]["retry_count"] = 0
                videos_map[vid]["error"] = None
            elif videos_map[vid]["status"] != "completed":
                videos_map[vid]["status"] = "completed"
                videos_map[vid]["extracted_count"] = max(videos_map[vid].get("extracted_count", 0), len(existing_records))

    playlist_ids = {item["id"] for item in playlist}
    videos_map = {vid: v for vid, v in videos_map.items() if vid in playlist_ids}

    tracker["videos"] = videos_map
    tracker["last_updated"] = datetime.now().isoformat()
    save_tracker(tracker)
    return tracker

def save_tracker(tracker):
    tracker["last_updated"] = datetime.now().isoformat()
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(tracker, f, indent=2, ensure_ascii=False)

def print_status(tracker):
    vids = list(tracker.get("videos", {}).values())
    total = len(vids)
    completed = [v for v in vids if v["status"] == "completed"]
    pending = [v for v in vids if v["status"] == "pending"]
    failed = [v for v in vids if v["status"] == "failed"]

    k4_total = [v for v in vids if v.get("is_4k")]
    k4_done = [v for v in k4_total if v["status"] == "completed"]

    fhd_total = [v for v in vids if not v.get("is_4k") and v.get("height", 0) >= 1080]
    fhd_done = [v for v in fhd_total if v["status"] == "completed"]

    # Count total wallpapers in metadata
    total_wp_count = 0
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                total_wp_count = len(json.load(f))
        except Exception:
            pass

    print("\n" + "=" * 68)
    print(" 🎨  IMPRESSIONIST ARCHIVE - WALLPAPER BATCH EXTRACTION STATUS")
    print("=" * 68)
    print(f" Total Playlist Videos:         {total}")
    print(f" Fully Processed Titles:        {len(completed)} ({(len(completed)/total*100):.1f}%)")
    print(f" Pending Titles in Queue:       {len(pending)}")
    print(f" Failed / Blocked Titles:       {len(failed)}")
    print(f" Total Wallpapers in Gallery:   {total_wp_count}")
    print("-" * 68)
    print(" Breakdown by Quality Tier:")
    print(f"  👑 Tier 1 (4K UHD):           {len(k4_done)} / {len(k4_total)} completed ({(len(k4_done)/max(1,len(k4_total))*100):.1f}%)")
    print(f"  💎 Tier 2 (1080p FHD):        {len(fhd_done)} / {len(fhd_total)} completed ({(len(fhd_done)/max(1,len(fhd_total))*100):.1f}%)")
    print("-" * 68)

    # Show next 5 priority queue items
    pending_sorted = sorted(pending, key=lambda x: (x.get("tier_rank", 9), -x.get("views", 0)))
    print(" Next Up in Priority Queue (4K UHD & High Popularity First):")
    for i, v in enumerate(pending_sorted[:6], 1):
        tier_label = "4K UHD" if v.get("is_4k") else f"{v.get('height')}p"
        print(f"  {i}. [{tier_label:7s}] {v.get('views', 0):>8,d} views | {v.get('channel')[:16]:16s} | {v.get('title')[:34]}")
    print("=" * 68 + "\n")

def extract_video_wallpapers(entry, cookies_browser=None, cookies_file=None):
    vid = entry["id"]
    title = entry.get("title", "")
    channel = entry.get("channel", "Unknown")
    duration = entry.get("duration", 0)

    vid_dir = os.path.join(WALLPAPER_DIR, vid)
    os.makedirs(vid_dir, exist_ok=True)

    timestamps = calculate_scenery_timestamps(duration)

    cookie_args = []
    if cookies_browser:
        cookie_args.extend(["--cookies-from-browser", cookies_browser])
    if cookies_file:
        cookie_args.extend(["--cookies", cookies_file])

    # 1. Obtain stream URL with yt-dlp (up to 4K 2160p)
    yt_url = f"https://www.youtube.com/watch?v={vid}"
    cmd_stream = [
        "yt-dlp", "--no-warnings", "-g",
        *cookie_args,
        "-f", "bestvideo[height<=2160][protocol=https]/bestvideo[height<=2160]/best",
        yt_url
    ]
    try:
        proc = subprocess.run(cmd_stream, capture_output=True, text=True, timeout=25)
        if proc.returncode != 0 or not proc.stdout.strip():
            # Fallback retry with android player client (bypasses bot challenges and SABR restrictions)
            cmd_fallback = [
                "yt-dlp", "--no-warnings", "-g",
                *cookie_args,
                "--extractor-args", "youtube:player_client=android",
                "-f", "bestvideo[height<=2160][protocol=https]/bestvideo[height<=2160]/best",
                yt_url
            ]
            proc = subprocess.run(cmd_fallback, capture_output=True, text=True, timeout=25)
            if proc.returncode != 0 or not proc.stdout.strip():
                err_msg = (proc.stderr or proc.stdout or "stream_not_found").strip()[:100]
                return False, f"yt-dlp error: {err_msg}", []
        stream_url = proc.stdout.strip().split("\n")[0]
    except Exception as e:
        return False, f"yt-dlp exception: {str(e)[:100]}", []

    records = []
    for idx, ts in enumerate(timestamps, 1):
        out_path = os.path.join(vid_dir, f"snapshot_{idx}.jpg")
        ts_str = format_timestamp(ts)

        ffmpeg_cmd = [
            "ffmpeg", "-y", "-ss", ts_str, "-i", stream_url,
            "-frames:v", "1", "-update", "1", "-q:v", "1", out_path
        ]
        try:
            res = subprocess.run(ffmpeg_cmd, capture_output=True, timeout=35)
            if res.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
                # Probe exact resolution
                probe = subprocess.run(
                    ["ffprobe", "-v", "error", "-select_streams", "v:0",
                     "-show_entries", "stream=width,height", "-of", "json", out_path],
                    capture_output=True, text=True, timeout=8
                )
                width, height = 1920, 1080
                try:
                    pdata = json.loads(probe.stdout)
                    width = pdata["streams"][0]["width"]
                    height = pdata["streams"][0]["height"]
                except Exception:
                    pass

                file_size_kb = round(os.path.getsize(out_path) / 1024, 1)
                is_4k = width >= 3840 or height >= 2160
                quality_label = "4K UHD" if is_4k else ("1440p QHD" if height >= 1440 else ("1080p FHD" if height >= 1080 else f"{height}p"))

                records.append({
                    "id": f"{vid}_{idx}",
                    "videoId": vid,
                    "videoTitle": title,
                    "channel": channel,
                    "snapshotIndex": idx,
                    "timestampSec": ts,
                    "timestampFormatted": ts_str,
                    "path": f"wallpapers/{vid}/snapshot_{idx}.jpg",
                    "width": width,
                    "height": height,
                    "qualityLabel": quality_label,
                    "is4K": is_4k,
                    "formFactor": detect_form_factor(out_path, width, height),
                    "fileSizeKB": file_size_kb,
                    "tags": [],
                    "primaryPalette": []
                })
        except Exception:
            continue

    if not records:
        # Fallback single frame attempt at 15s
        fallback_ts = "00:00:15"
        out_path = os.path.join(vid_dir, "snapshot_1.jpg")
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-ss", fallback_ts, "-i", stream_url,
            "-frames:v", "1", "-update", "1", "-q:v", "1", out_path
        ]
        try:
            res = subprocess.run(ffmpeg_cmd, capture_output=True, timeout=35)
            if res.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
                width, height = 3840, 2160
                probe = subprocess.run(
                    ["ffprobe", "-v", "error", "-select_streams", "v:0",
                     "-show_entries", "stream=width,height", "-of", "json", out_path],
                    capture_output=True, text=True, timeout=8
                )
                try:
                    pdata = json.loads(probe.stdout)
                    width = pdata["streams"][0]["width"]
                    height = pdata["streams"][0]["height"]
                except Exception:
                    pass
                file_size_kb = round(os.path.getsize(out_path) / 1024, 1)
                is_4k = width >= 3840 or height >= 2160
                quality_label = "4K UHD" if is_4k else ("1440p QHD" if height >= 1440 else ("1080p FHD" if height >= 1080 else f"{height}p"))
                records.append({
                    "id": f"{vid}_1",
                    "videoId": vid,
                    "videoTitle": title,
                    "channel": channel,
                    "snapshotIndex": 1,
                    "timestampSec": 15,
                    "timestampFormatted": fallback_ts,
                    "path": f"wallpapers/{vid}/snapshot_1.jpg",
                    "width": width,
                    "height": height,
                    "qualityLabel": quality_label,
                    "is4K": is_4k,
                    "formFactor": detect_form_factor(out_path, width, height),
                    "fileSizeKB": file_size_kb,
                    "tags": [],
                    "primaryPalette": []
                })
        except Exception:
            pass

    if records:
        return True, "ok", records
    return False, "no_snapshots_extracted", []

def sync_metadata_and_rebuild(new_records):
    # Load existing metadata
    all_records = []
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                all_records = json.load(f)
        except Exception:
            all_records = []

    records_dict = {r["id"]: r for r in all_records}
    for r in new_records:
        records_dict[r["id"]] = r

    final_records = list(records_dict.values())
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(final_records, f, indent=2, ensure_ascii=False)

    print(f"✨ Synchronized {METADATA_FILE}: Total {len(final_records)} wallpapers.")

    # Re-build data.js & csv
    try:
        res = subprocess.run(["python3", "build_webpage.py"], capture_output=True, text=True, timeout=30)
        if res.returncode == 0:
            print("🚀 Rebuilt data.js and catalog successfully.")
        else:
            print(f"⚠️ build_webpage.py error: {res.stderr[:200]}")
    except Exception as e:
        print(f"⚠️ Could not run build_webpage.py: {e}")

def run_batch(batch_size=10, tier_filter=None, delay=3.0, max_retries=3, skip_copyright=False, cookies_browser=None, cookies_file=None, retry_failed=False):
    playlist, res_cache = load_playlist_and_resolutions()
    tracker = load_or_init_tracker(playlist, res_cache)

    vids = list(tracker["videos"].values())

    if retry_failed:
        for v in vids:
            if v.get("status") == "failed":
                v["status"] = "pending"
                v["retry_count"] = 0
        save_tracker(tracker)

    if skip_copyright:
        try:
            from core.playlist_engine import load_gallery_config
            cfg = load_gallery_config()
            prohibited = set(cfg.get('prohibitedDownloadChannels', ['Living Art Moments']))
            vids = [v for v in vids if v.get('channel') not in prohibited]
        except Exception:
            pass

    # Filter by tier if specified
    if tier_filter == "4k":
        candidates = [v for v in vids if v.get("is_4k")]
    elif tier_filter == "fhd":
        candidates = [v for v in vids if not v.get("is_4k") and v.get("height", 0) >= 1080]
    else:
        candidates = vids

    # Select candidates that are pending or failed with retries left
    queue = [
        v for v in candidates
        if v["status"] == "pending" or (v["status"] == "failed" and v.get("retry_count", 0) < max_retries)
    ]

    # Prioritize: Tier 1 (4K) first, then by view count descending!
    queue.sort(key=lambda x: (x.get("tier_rank", 9), -x.get("views", 0)))

    selected = queue[:batch_size]
    if not selected:
        print("✅ No videos matching criteria require extraction! All prioritized titles are up to date.")
        return

    print(f"\n🚀 Launching Safe Batch Extraction for {len(selected)} prioritized videos...")
    print(f"⏱️ Safe pacing delay: {delay:.1f}s (prevents YouTube IP rate-limiting; uses 0 YouTube Data API units)")
    print("-" * 68)

    all_new_records = []
    success_count = 0

    for idx, v in enumerate(selected, 1):
        vid = v["id"]
        tier_label = "4K UHD" if v.get("is_4k") else f"{v.get('height')}p"
        print(f"[{idx}/{len(selected)}] Processing [{tier_label}] ({v.get('views', 0):,d} views): {v.get('title')[:45]}...")

        v["status"] = "in_progress"
        v["last_attempt"] = datetime.now().isoformat()
        save_tracker(tracker)

        ok, msg, records = extract_video_wallpapers(v, cookies_browser=cookies_browser, cookies_file=cookies_file)

        if ok and records:
            success_count += 1
            v["status"] = "completed"
            v["extracted_count"] = len(records)
            v["error"] = None
            all_new_records.extend(records)
            print(f"   ✓ Extracted {len(records)} pristine {records[0]['qualityLabel']} wallpapers! ({records[0]['width']}x{records[0]['height']})")
        else:
            v["status"] = "failed"
            v["retry_count"] = v.get("retry_count", 0) + 1
            v["error"] = msg
            print(f"   ✗ Extraction failed: {msg}")

        save_tracker(tracker)

        # Polite delay with random jitter to prevent YouTube rate-limiting
        if idx < len(selected):
            sleep_time = delay + random.uniform(0.5, 2.0)
            time.sleep(sleep_time)

    if all_new_records:
        sync_metadata_and_rebuild(all_new_records)

    print("\n" + "=" * 68)
    print(f"🏁 Batch complete: {success_count}/{len(selected)} videos successfully extracted.")
    print_status(tracker)

def main():
    parser = argparse.ArgumentParser(description="Impressionist Archive - Wallpaper Batch Extractor & Manager")
    parser.add_argument("--status", action="store_true", help="Display current tracking dashboard and queue status")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of videos to process in this run (default: 10)")
    parser.add_argument("--tier", choices=["all", "4k", "fhd"], default="all", help="Resolution tier to prioritize (default: all)")
    parser.add_argument("--delay", type=float, default=3.0, help="Polite delay between extractions in seconds (default: 3.0)")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild metadata and data.js from disk")
    parser.add_argument("--continuous", action="store_true", help="Continuously process all remaining batches until 100% complete")
    parser.add_argument("--skip-copyright-restricted", action="store_true", help="Exclude titles/channels with copyright download restrictions")
    parser.add_argument("--cookies-from-browser", default=None, help="Extract cookies from browser (e.g. chrome, edge, firefox)")
    parser.add_argument("--cookies", default=None, help="Path to Netscape-format cookies.txt file")
    parser.add_argument("--retry-failed", action="store_true", help="Reset failed video statuses to pending to re-attempt extraction")

    args = parser.parse_args()

    playlist, res_cache = load_playlist_and_resolutions()
    tracker = load_or_init_tracker(playlist, res_cache)

    if args.status:
        print_status(tracker)
        return

    if args.rebuild:
        # Re-scan disk and rebuild
        print("Re-scanning wallpaper directory and rebuilding...")
        sync_metadata_and_rebuild([])
        print_status(tracker)
        return

    tier_filter = None if args.tier == "all" else args.tier

    if args.continuous:
        print(f"\n🔄 Starting Continuous Wallpaper Extraction (Tier: {args.tier.upper()}, Batch Size: {args.batch_size}, Delay: {args.delay}s)...")
        if args.skip_copyright_restricted:
            print("🛡️ Copyright Filter: Skipping channels with download restrictions.")
        batch_num = 1
        while True:
            playlist, res_cache = load_playlist_and_resolutions()
            tracker = load_or_init_tracker(playlist, res_cache)
            vids = list(tracker["videos"].values())
            if args.skip_copyright_restricted:
                try:
                    from core.playlist_engine import load_gallery_config
                    cfg = load_gallery_config()
                    prohibited = set(cfg.get('prohibitedDownloadChannels', ['Living Art Moments']))
                    vids = [v for v in vids if v.get('channel') not in prohibited]
                except Exception:
                    pass
            if tier_filter == "4k":
                candidates = [v for v in vids if v.get("is_4k")]
            elif tier_filter == "fhd":
                candidates = [v for v in vids if not v.get("is_4k") and v.get("height", 0) >= 1080]
            else:
                candidates = vids
            queue = [
                v for v in candidates
                if v["status"] == "pending" or (v["status"] == "failed" and v.get("retry_count", 0) < 3)
            ]
            if not queue:
                print(f"\n🎉 100% COMPLETE! All {len(candidates)} {args.tier.upper()} titles have been successfully processed!")
                break
            print(f"\n📦 === Running Batch #{batch_num} ({min(args.batch_size, len(queue))} of {len(queue)} remaining) ===")
            run_batch(batch_size=args.batch_size, tier_filter=tier_filter, delay=args.delay, skip_copyright=args.skip_copyright_restricted, cookies_browser=args.cookies_from_browser, cookies_file=args.cookies, retry_failed=args.retry_failed)
            batch_num += 1
        return

    run_batch(batch_size=args.batch_size, tier_filter=tier_filter, delay=args.delay, skip_copyright=args.skip_copyright_restricted, cookies_browser=args.cookies_from_browser, cookies_file=args.cookies, retry_failed=args.retry_failed)

if __name__ == "__main__":
    main()
