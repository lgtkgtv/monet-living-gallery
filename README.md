# 🎨 L'Impressionnisme Vivant
### *The Impressionist Video Explorer & 4K Wallpaper Archive*

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live%20Gallery-brightgreen?logo=github)](https://lgtkgtv.github.io/monet-living-gallery/)
[![4K UHD](https://img.shields.io/badge/Resolution-4K%20UHD%20(3840x2160)-gold)](https://lgtkgtv.github.io/monet-living-gallery/)
[![Curated Works](https://img.shields.io/badge/Works-198%20Masterworks-blue)](https://lgtkgtv.github.io/monet-living-gallery/)
[![Wallpapers](https://img.shields.io/badge/Wallpapers-366%20Snapshots-purple)](https://lgtkgtv.github.io/monet-living-gallery/)
[![Views](https://img.shields.io/badge/Views-24.2M%20Total-red)](https://lgtkgtv.github.io/monet-living-gallery/)
[![Mobile First](https://img.shields.io/badge/Mobile-Optimized-success)](https://lgtkgtv.github.io/monet-living-gallery/)

An interactive, curated digital museum and high-definition visual archive celebrating **Claude Monet** and the **Impressionist art movement**. Derived from the YouTube playlist **[sh_Monet inspired Visual Arts](https://www.youtube.com/playlist?list=PLeqGkucOU6lA)**, this project catalogs 198 masterworks across 39 distinct YouTube channels, featuring native resolution tags, dynamic channel aesthetic characterizations, verified links, instant bulk zip downloads, and a device-appropriate fullscreen wallpaper slideshow.

🌐 **Live Web Application**: **[https://lgtkgtv.github.io/monet-living-gallery/](https://lgtkgtv.github.io/monet-living-gallery/)**

---

## 🌟 Key Features & Architecture

### 1. 📱 Device-Appropriate Fullscreen Wallpaper Slideshow
- **Automatic Form Factor Adaptation**: Automatically categorizes extracted snapshots into desktop widescreen (16:9) vs mobile/pillarboxed portrait using luminosity margin sampling.
- **Smart Aspect Ratio Filtering**: When launching the fullscreen slideshow, desktop users automatically view widescreen-optimized masterworks, while mobile users receive portrait scenes (or toggle between Desktop, Mobile, and All formats).
- **Presentation Controls**: Fullscreen mode, automatic looping with play/pause, selectable transition delays (3s, 5s, 8s, 12s), fit vs cover mode, and keyboard navigation (`Space`, `ArrowLeft`, `ArrowRight`, `Esc`).

### 2. ⚡ Progressive Batch DOM Rendering
- **Instant Paint**: Initial grid render loads the first 24 cards in milliseconds using `DocumentFragment`.
- **Infinite Scrolling Sentinel**: Uses an `IntersectionObserver` sentinel (with 400px margin) to smoothly append subsequent batches of 24 as the user scrolls, paired with a styled manual "Load More" trigger.
- **Ultra-Low Memory Footprint**: Scalable to thousands of titles without lag or browser freezing.

### 3. 📦 Instant Bulk Wallpaper Downloader
- **In-Browser Zip Packaging**: Uses `JSZip` to bundle filtered wallpapers directly in the browser with no server load.
- **Contextual Selection**: Users can filter by artist, channel, or resolution tier (e.g. "Download all 293 4K wallpapers for LearnFromMasters") with a single click.

### 4. 🎨 Dynamic Curatorial Grid & Automated Channel Profiles
- **Dynamic Extensibility**: Channels are dynamically profiled from catalog metrics. Hand-curated channels (e.g. *LearnFromMasters*, *Extraordinary Visual Art*, *Muse Visual Art*, *Cupid Studio*, *Beautiful Living Art*) are highlighted, while newly discovered channels receive automatic archetypes and metrics.
- **Live Search Guide Chips**: Pre-curated artist chips (*Claude Monet*, *Renoir*, *Sisley*, *Boudin*, *Levitan*) and theme chips (*Water Lilies*, *Garden Sanctuaries*, *Winter & Snow*, *Venice*, *Paris*) dynamically compute and display current matching catalog counts.

### 5. 🎬 Streamlined Ad-Free Previews & Playback
- **Privacy-Enhanced Embeds (`youtube-nocookie.com`)**: Eliminates third-party tracking cookies to minimize ad pre-rolls.
- **Ad-Free Wallpaper Previews**: Full resolution 4K wallpapers enable uncompressed contemplation without streaming buffering or commercials.

---

## 🛠️ Unified Pipeline CLI (`pipeline.py`)

A single command-line interface orchestrates the entire archive, metadata extraction, and deployment:

```bash
# 1. View real-time telemetry dashboard (videos, resolutions, channels, wallpapers)
./pipeline.py --status

# 2. Rebuild data.js, channel profiles, and CSV catalog instantly
./pipeline.py --build

# 3. Pull fresh playlist metadata directly from YouTube via yt-dlp
./pipeline.py --pull-playlist

# 4. Probe and cache missing video resolutions from YouTube
./pipeline.py --sync-resolutions

# 5. Extract 4K wallpapers with anti-throttling delay (e.g., batch of 10)
./pipeline.py --extract --batch-size 10 --tier 4K --delay 3.0

# 6. Full automated end-to-end sync (resolutions -> extraction -> build -> status)
./pipeline.py --sync

# 7. Start local gallery preview server
./pipeline.py --serve --port 8000
```

---

## 📁 Repository Structure

```
├── index.html                  # Responsive mobile-first gallery application
├── styles.css                  # Impressionist typography, colors, animations & media queries
├── app.js                      # Dynamic search guide, progressive renderer, slideshow & downloader
├── pipeline.py                 # Unified CLI orchestrator (--status, --build, --extract, --sync)
├── batch_wallpaper_extractor.py # Anti-throttled wallpaper extractor with form factor detection
├── build_webpage.py            # Site data & CSV catalog compiler
├── data.js                     # Static optimized dataset (198 videos, 366 wallpapers, profiles)
├── video_resolutions.json      # Complete native resolution cache (100% indexed)
├── playlist_raw.json           # Raw playlist JSON dump
├── monet_playlist_by_channel.csv # Spreadsheet-ready catalog with resolution columns
├── monet_playlist_catalog.md   # Markdown catalog with resolution tags and watch links
├── jszip.min.js                # Client-side zip bundling for bulk downloads
├── .nojekyll                   # Bypasses Jekyll processing on GitHub Pages
└── wallpapers/                 # Extracted 4K & FHD wallpaper scene archive
    ├── batch_tracker.json      # Extraction progress tracker (completed vs pending)
    ├── metadata.json           # Wallpaper index, dimensions, timestamps, and formFactor
    └── <video_id>/             # Scenery snapshots (snapshot_1.jpg, snapshot_2.jpg...)
```

---
*Curated by sachin g · [lgtkgtv@gmail.com](mailto:lgtkgtv@gmail.com)*
