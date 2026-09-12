#!/usr/bin/env python3
"""
High-Definition / 4K Wallpaper Snapshot Extractor for Monet Impressionist Playlist.
Extracts wallpaper-grade frames directly from video streams at representative timestamps.
Saves images to wallpapers/<video_id>/ and indexes them in wallpapers/metadata.json.
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

WALLPAPER_DIR = "wallpapers"
METADATA_FILE = os.path.join(WALLPAPER_DIR, "metadata.json")
PLAYLIST_FILE = "playlist_raw.json"

def get_timestamps(duration):
    """Calculate 3 representative timestamps keeping them early enough for fast network seeks."""
    if not duration or duration <= 0:
        return [20, 60, 100]
    dur = int(duration)
    if dur < 60:
        return [10, max(15, dur // 2), max(20, dur - 5)]
    elif dur < 180:
        return [20, 60, 110]
    elif dur < 600:
        return [30, 120, 240]
    else:
        # For longer compilations: 30s, 120s, 300s (avoids long network stream seeking)
        return [30, 120, 300]

def format_timestamp(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def extract_for_video(entry):
    vid = entry["id"]
    title = entry.get("title", "")
    channel = entry.get("channel") or entry.get("uploader") or "Unknown"
    duration = entry.get("duration") or 0
    
    vid_dir = os.path.join(WALLPAPER_DIR, vid)
    os.makedirs(vid_dir, exist_ok=True)
    
    # Check if snapshots already exist
    expected_files = [os.path.join(vid_dir, f"snapshot_{i}.jpg") for i in (1, 2, 3)]
    if all(os.path.exists(f) and os.path.getsize(f) > 10000 for f in expected_files):
        return vid, "cached", []

    # Get stream URL via yt-dlp (best video up to 4K 2160p)
    yt_url = f"https://www.youtube.com/watch?v={vid}"
    cmd_stream = [
        "yt-dlp", "--no-warnings", "-g",
        "-f", "bestvideo[height<=2160]/bestvideo/best",
        yt_url
    ]
    try:
        proc = subprocess.run(cmd_stream, capture_output=True, text=True, timeout=20)
        if proc.returncode != 0 or not proc.stdout.strip():
            return vid, "failed_stream", []
        stream_url = proc.stdout.strip().split("\n")[0]
    except Exception as e:
        return vid, f"error_stream: {e}", []

    timestamps = get_timestamps(duration)
    records = []

    for idx, ts in enumerate(timestamps, 1):
        out_path = os.path.join(vid_dir, f"snapshot_{idx}.jpg")
        ts_str = format_timestamp(ts)
        
        # Placing -ss AFTER -i handles HLS m3u8 playlists cleanly
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", stream_url,
            "-ss", ts_str, "-vframes", "1", "-q:v", "2", out_path
        ]
        try:
            res = subprocess.run(ffmpeg_cmd, capture_output=True, timeout=25)
            if res.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
                # Probe resolution
                probe = subprocess.run(
                    ["ffprobe", "-v", "error", "-select_streams", "v:0",
                     "-show_entries", "stream=width,height", "-of", "json", out_path],
                    capture_output=True, text=True, timeout=10
                )
                width, height = 1920, 1080
                try:
                    pdata = json.loads(probe.stdout)
                    width = pdata["streams"][0]["width"]
                    height = pdata["streams"][0]["height"]
                except:
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
                    "fileSizeKB": file_size_kb,
                    "tags": [],
                    "primaryPalette": []
                })
        except Exception as e:
            continue

    return vid, "success" if records else "empty", records

def main():
    os.makedirs(WALLPAPER_DIR, exist_ok=True)
    
    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        entries = json.load(f)

    # Sort videos by popularity descending
    entries.sort(key=lambda x: x.get("view_count") or 0, reverse=True)

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(entries)
    target_entries = entries[:limit]
    
    print(f"Starting Wallpaper Extraction for {len(target_entries)} videos...")

    all_records = []
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                all_records = json.load(f)
        except:
            all_records = []

    existing_ids = {r["id"] for r in all_records}

    workers = 5
    success_count = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_entry = {executor.submit(extract_for_video, e): e for e in target_entries}
        for future in as_completed(future_to_entry):
            entry = future_to_entry[future]
            vid = entry["id"]
            try:
                vid, status, records = future.result()
                if records:
                    success_count += 1
                    for r in records:
                        if r["id"] not in existing_ids:
                            all_records.append(r)
                            existing_ids.add(r["id"])
                    print(f"[{success_count}/{len(target_entries)}] ✓ {entry.get('title')[:45]}...")
                elif status == "cached":
                    success_count += 1
                    print(f"[{success_count}/{len(target_entries)}] ⚡ Cached: {entry.get('title')[:45]}...")
                else:
                    print(f"[!] Warning for {vid}: {status}")
            except Exception as e:
                print(f"[X] Exception processing {vid}: {e}")

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)

    print("=" * 60)
    print(f"Finished extraction! Total snapshots in index: {len(all_records)}")
    print(f"Elapsed time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
