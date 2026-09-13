import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

RES_FILE = 'video_resolutions.json'

def get_res(entry):
    vid = entry['id']
    url = f"https://www.youtube.com/watch?v={vid}"
    cmd = ['yt-dlp', '--no-warnings', '--print', '%(width)s %(height)s', url]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        if proc.returncode == 0 and proc.stdout.strip():
            parts = proc.stdout.strip().split()
            if len(parts) >= 2:
                w, h = int(parts[0]), int(parts[1])
                is_4k = w >= 3840 or h >= 2160
                label = "4K UHD" if is_4k else ("1440p QHD" if h >= 1440 else ("1080p FHD" if h >= 1080 else f"{h}p"))
                return vid, w, h, label
    except Exception as e:
        pass
    
    # Fallback heuristic from title
    title = entry.get('title', '').upper()
    if '4K' in title or '2160' in title:
        return vid, 3840, 2160, "4K UHD"
    elif '8K' in title:
        return vid, 3840, 2160, "4K UHD"
    elif '1080' in title or 'HD' in title:
        return vid, 1920, 1080, "1080p FHD"
    return vid, 1920, 1080, "1080p FHD"

def main():
    with open('playlist_raw.json') as f:
        entries = json.load(f)

    cache = {}
    if os.path.exists(RES_FILE):
        try:
            with open(RES_FILE) as f:
                cache = json.load(f)
        except:
            cache = {}

    to_fetch = [e for e in entries if e['id'] not in cache]
    print(f"Resolutions cached: {len(cache)}. To fetch: {len(to_fetch)}")

    if to_fetch:
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_entry = {executor.submit(get_res, e): e for e in to_fetch}
            for future in as_completed(future_to_entry):
                vid, w, h, label = future.result()
                cache[vid] = {
                    'width': w,
                    'height': h,
                    'resolution': f"{w}x{h}",
                    'qualityLabel': label,
                    'is4K': (w >= 3840 or h >= 2160)
                }

        with open(RES_FILE, 'w') as f:
            json.dump(cache, f, indent=2)

    print(f"Total resolutions indexed: {len(cache)}")

if __name__ == '__main__':
    main()
