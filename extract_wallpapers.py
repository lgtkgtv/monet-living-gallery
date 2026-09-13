#!/usr/bin/env python3
"""
Comprehensive 4K Wallpaper Snapshot Extractor with Scenery Change Sampling.
Extracts multiple high-definition (up to 4K 2160p) scene snapshots per video,
capturing visual transitions, different paintings, and changing landscapes.
Uses ffmpeg with -q:v 1 for pristine wallpaper image quality.
"""

import os
import sys
import json
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

WALLPAPER_DIR = "wallpapers"
METADATA_FILE = os.path.join(WALLPAPER_DIR, "metadata.json")
PLAYLIST_FILE = "playlist_raw.json"
RES_FILE = "video_resolutions.json"

def calculate_scenery_timestamps(duration_sec):
    """
    Generate timestamps that reflect changes of scenery across the video:
    - Short videos (< 4 mins): 5-6 scenes
    - Medium videos (4-15 mins): 7-8 scenes
    - Long anthologies (> 15 mins): 9-12 scenes
    """
    dur = int(duration_sec or 200)
    if dur <= 60:
        return [10, dur // 2, max(15, dur - 8)]
    
    if dur < 240: # 1 to 4 minutes
        num_scenes = 5
        start = max(10, int(dur * 0.08))
        end = min(dur - 8, int(dur * 0.92))
    elif dur < 900: # 4 to 15 minutes
        num_scenes = 7
        start = max(15, int(dur * 0.06))
        end = min(dur - 12, int(dur * 0.94))
    elif dur < 3600: # 15 to 60 minutes
        num_scenes = 9
        start = max(30, int(dur * 0.04))
        end = min(dur - 30, int(dur * 0.96))
    else: # > 1 hour
        num_scenes = 11
        start = 45
        end = min(dur - 60, int(dur * 0.95))

    step = (end - start) / (num_scenes - 1)
    return [int(start + i * step) for i in range(num_scenes)]

def format_timestamp(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def extract_for_video(entry, res_cache):
    vid = entry["id"]
    title = entry.get("title", "")
    channel = entry.get("channel") or entry.get("uploader") or "Unknown"
    duration = entry.get("duration") or 0
    
    vid_dir = os.path.join(WALLPAPER_DIR, vid)
    os.makedirs(vid_dir, exist_ok=True)

    timestamps = calculate_scenery_timestamps(duration)

    # Check if this video already has comprehensive extraction (at least len(timestamps) files)
    existing_files = [f for f in os.listdir(vid_dir) if f.startswith("snapshot_") and f.endswith(".jpg")]
    if len(existing_files) >= len(timestamps):
        return vid, "cached", []

    # Get highest available video stream up to 4K (2160p)
    yt_url = f"https://www.youtube.com/watch?v={vid}"
    cmd_stream = [
        "yt-dlp", "--no-warnings", "-g",
        "-f", "bestvideo[height<=2160][ext=mp4]/bestvideo[height<=2160]/bestvideo/best",
        yt_url
    ]
    try:
        proc = subprocess.run(cmd_stream, capture_output=True, text=True, timeout=20)
        if proc.returncode != 0 or not proc.stdout.strip():
            return vid, "failed_stream", []
        stream_url = proc.stdout.strip().split("\n")[0]
    except Exception as e:
        return vid, f"error_stream: {e}", []

    records = []

    for idx, ts in enumerate(timestamps, 1):
        out_path = os.path.join(vid_dir, f"snapshot_{idx}.jpg")
        ts_str = format_timestamp(ts)
        
        # -q:v 1 guarantees best possible JPEG compression quality
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-ss", ts_str, "-i", stream_url,
            "-vframes", "1", "-q:v", "1", out_path
        ]
        try:
            res = subprocess.run(ffmpeg_cmd, capture_output=True, timeout=20)
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
        except Exception:
            continue

    return vid, "success" if records else "empty", records

def main():
    os.makedirs(WALLPAPER_DIR, exist_ok=True)
    
    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        entries = json.load(f)

    # Sort videos by view count descending
    entries.sort(key=lambda x: x.get("view_count") or 0, reverse=True)

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(entries)
    target_entries = entries[:limit]

    res_cache = {}
    if os.path.exists(RES_FILE):
        try:
            with open(RES_FILE) as f:
                res_cache = json.load(f)
        except:
            pass

    print(f"Starting Comprehensive Scenery Extraction for {len(target_entries)} videos...")

    # Load existing metadata
    all_records = []
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                all_records = json.load(f)
        except:
            all_records = []

    # Map by id
    records_dict = {r["id"]: r for r in all_records}

    workers = 6
    success_count = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_entry = {executor.submit(extract_for_video, e, res_cache): e for e in target_entries}
        for future in as_completed(future_to_entry):
            entry = future_to_entry[future]
            vid = entry["id"]
            try:
                vid, status, records = future.result()
                if records:
                    success_count += 1
                    for r in records:
                        records_dict[r["id"]] = r
                    print(f"[{success_count}/{len(target_entries)}] ✓ {len(records)} scenes: {entry.get('title')[:45]}...")
                elif status == "cached":
                    success_count += 1
                    print(f"[{success_count}/{len(target_entries)}] ⚡ Cached: {entry.get('title')[:45]}...")
                else:
                    print(f"[!] {vid}: {status}")
            except Exception as e:
                print(f"[X] {vid}: {e}")

    updated_records = list(records_dict.values())
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_records, f, indent=2, ensure_ascii=False)

    print("=" * 60)
    print(f"Finished extraction! Total scenery snapshots in index: {len(updated_records)}")
    print(f"Elapsed time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
