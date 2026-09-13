# 🎨 L'Impressionnisme Vivant
### *The Impressionist Video Explorer & 4K Wallpaper Archive*

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live%20Gallery-brightgreen?logo=github)](https://lgtkgtv.github.io/monet-living-gallery/)
[![4K UHD](https://img.shields.io/badge/Resolution-4K%20UHD%20(3840x2160)-gold)](https://lgtkgtv.github.io/monet-living-gallery/)
[![Curated Works](https://img.shields.io/badge/Works-199%20Paintings-blue)](https://lgtkgtv.github.io/monet-living-gallery/)
[![Views](https://img.shields.io/badge/Views-24.2M%20Total-red)](https://lgtkgtv.github.io/monet-living-gallery/)
[![Mobile First](https://img.shields.io/badge/Mobile-Optimized-purple)](https://lgtkgtv.github.io/monet-living-gallery/)

An interactive, curated digital guide and high-definition visual archive celebrating **Claude Monet** and the **Impressionist art movement**. Derived from the YouTube playlist **[sh_Monet inspired Visual Arts](https://www.youtube.com/playlist?list=PLeqGkucOU6lA)**, this project catalogs 199 masterworks across 41 distinct YouTube channels, featuring native resolution badges, detailed channel aesthetic characterizations, verified links, and a comprehensive 4K wallpaper archive.

🌐 **Live Web Application**: **[https://lgtkgtv.github.io/monet-living-gallery/](https://lgtkgtv.github.io/monet-living-gallery/)**

---

## 🌟 Key Features & Enhancements

### 1. 📱 Mobile-First Experience & Immediate Audio-Visual Engagement
- **4K UHD Masterworks First**: The application defaults on page load directly to the **👑 4K UHD Only** collection (45 native 4K works), giving visitors an immediate, stunning visual experience right above the fold.
- **Impressionist Video Explorer Front & Center**: The video explorer and wallpaper gallery are positioned immediately beneath the hero pathways bar so mobile visitors (iPhone, Android) never need to scroll past long text guides to find media.
- **Form-Factor Detection**: Automatically detects mobile vs desktop devices (`is-mobile-device` / `is-desktop-device`) to adapt button touch targets, drawer behaviors, and grid density.
- **Collapsible Curation Statistics**: Developer and catalog statistics (199 works, 24.2M views, 78h 15m) are neatly tucked into a clean collapsible drawer that visitors can expand on demand without cluttering the screen.
- **Curatorial Channel Guides**: Channel guides and scholar characterizations (LearnFromMasters, Extraordinary Visual Art, Muse Visual Art, etc.) are positioned following the media explorer, accessible via smooth quick-jump buttons.

### 2. 🎬 Streamlined Video Playback & Ad Mitigation
- **Clean Player Modal**: Safely removed all local environment Error 153 warnings. Replaced with an elegant dark toolbar showing the artist/channel, native resolution badge, quick button to jump into extracted wallpapers, and direct YouTube app launch.
- **Privacy-Enhanced Embeds (`youtube-nocookie.com`)**: Uses YouTube's official privacy-enhanced mode to eliminate behavioral tracking cookies, significantly reducing pre-roll ad auctions.
- **Ad-Free Wallpaper Previews**: Instant high-resolution 4K wallpaper lightbox allows users to admire paintings in uncompressed beauty without video ads or streaming buffering.

### 3. 🖼️ Multi-Day Batch Wallpaper Extraction Pipeline
- **Zero YouTube Data API Quota Usage**: Operates directly via `yt-dlp` stream inspection and `ffmpeg -q:v 1`, preserving the daily 10,000 unit YouTube Data API quota.
- **Anti-Throttling Safe Pacing**: Configurable delays and random jitter between extractions prevent YouTube IP rate-limiting (HTTP 429).
- **Persistent State Tracking (`wallpapers/batch_tracker.json`)**: Tracks every video title's processing status (`completed`, `pending`, `failed`), extracted scene paths, timestamps, and retry counts.
- **Resolution & Popularity Prioritization**:
  - **Tier 1**: 4K UHD videos, sorted by view count descending.
  - **Tier 2**: 1080p FHD videos, sorted by view count descending.
  - **Tier 3**: Remaining resolutions, sorted by view count descending.
- **Interactive CLI Dashboard**: View real-time progress of finished vs pending titles across resolution tiers:
  ```bash
  python3 batch_wallpaper_extractor.py --status
  ```

---

## 🚀 Running the Wallpaper Batch Pipeline

To extract wallpapers incrementally over several days without hitting rate limits:

```bash
# 1. Check current progress across 4K and 1080p tiers
python3 batch_wallpaper_extractor.py --status

# 2. Extract a batch of top 10 prioritized 4K UHD videos with polite pacing
python3 batch_wallpaper_extractor.py --batch-size 10 --tier 4k --delay 3.0

# 3. Process the next batch of 1080p videos
python3 batch_wallpaper_extractor.py --batch-size 10 --tier fhd --delay 3.0

# 4. Rebuild catalog and data.js from disk at any time
python3 batch_wallpaper_extractor.py --rebuild
```

---

## 💻 Local Development

```bash
# Start local HTTP server on port 8080
python3 start_server.py
```
Open **[http://localhost:8080](http://localhost:8080)** in your browser.

---

## 📁 Repository Structure

```
├── index.html                  # Main static web application ("L'Impressionnisme Vivant")
├── styles.css                  # Impressionist responsive mobile-first stylesheet
├── app.js                      # Explorer, 4K defaults, device detection & modal logic
├── batch_wallpaper_extractor.py # Safe multi-day batch wallpaper manager & status CLI
├── data.js                     # Unified dataset (199 videos with resolutions, wallpapers)
├── video_resolutions.json      # Complete native resolution cache (width, height, 4K flags)
├── playlist_raw.json           # Raw YouTube playlist metadata (199 videos)
├── monet_playlist_catalog.md   # Markdown catalog with resolutions and watch links
├── monet_playlist_by_channel.csv # Spreadsheet-ready CSV dataset with resolution columns
├── start_server.py             # One-click local HTTP server runner
├── extract_wallpapers.py       # Scenery-change 4K frame extractor (-q:v 1 quality)
├── build_webpage.py            # Automated site & metadata compiler
├── .nojekyll                   # Bypasses Jekyll processing on GitHub Pages
└── wallpapers/                 # Extracted 4K wallpaper archive
    ├── batch_tracker.json      # Persistent status tracker (completed vs pending titles)
    ├── metadata.json           # Wallpaper index, dimensions & timestamps
    └── <video_id>/             # Scenery snapshots (snapshot_1.jpg, snapshot_2.jpg...)
```

---
*Curated with devotion to Impressionist art and classical music.*
