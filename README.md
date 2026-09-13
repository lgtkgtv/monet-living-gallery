# 🎨 L'Impressionnisme Vivant
### *The Impressionist Video Explorer & 4K Wallpaper Archive*

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live%20Gallery-brightgreen?logo=github)](https://lgtkgtv.github.io/monet-living-gallery/)
[![4K UHD](https://img.shields.io/badge/Resolution-4K%20UHD%20(3840x2160)-gold)](https://lgtkgtv.github.io/monet-living-gallery/)
[![Curated Works](https://img.shields.io/badge/Works-199%20Paintings-blue)](https://lgtkgtv.github.io/monet-living-gallery/)
[![Views](https://img.shields.io/badge/Views-24.2M%20Total-red)](https://lgtkgtv.github.io/monet-living-gallery/)

An interactive, curated digital guide and high-definition visual archive dedicated to **Claude Monet** and the **Impressionist art movement**. Derived from the YouTube playlist **[sh_Monet inspired Visual Arts](https://www.youtube.com/playlist?list=PLeqGkucOU6lA)**, this project catalogs 199 masterworks across 41 distinct YouTube channels, featuring native resolution badges, detailed channel aesthetic characterizations, verified links, and a comprehensive 4K wallpaper archive.

🌐 **Live Web Application**: **[https://lgtkgtv.github.io/monet-living-gallery/](https://lgtkgtv.github.io/monet-living-gallery/)**

---

## 🌟 Key Features & Enhancements

1. **Native Resolution Badges & Filters**:
   - Every video and wallpaper displays its exact native resolution:
     - **45 Native 4K UHD Masterworks (3840×2160)**
     - **145 Full HD Masterworks (1920×1080)**
     - **2 Quad HD Works (2560×1440)**
   - Interactive dropdown filters allow viewing **4K UHD Only**, **1080p FHD**, or sorting by highest resolution.

2. **Comprehensive Scenery Change Wallpaper Archive**:
   - High-definition wallpaper snapshots extracted directly from video streams at representative scene changes across the video runtime.
   - Built with `ffmpeg` using `-q:v 1` for **pristine, lossless/near-lossless image quality** without compression artifacts.
   - Adaptive scene sampling:
     - **5-6 distinct scenery captures** for short visual poems
     - **7-8 distinct scenery captures** for medium videos
     - **9-12 distinct paintings** for long museum anthologies
   - Fullscreen lightbox viewer with exact resolution metrics, one-click **Download Full-Res Wallpaper**, and timestamped scene jumps to the YouTube video (`&t=...`).

3. **Curated Channel Archetypes**:
   - Deep characterizations of the 41 contributing creators:
     - **🏛️ LearnFromMasters**: The Academic & Museum Archivist (complete 1540-painting catalogues)
     - **🎬 Extraordinary Visual Art**: The Cinematic Masterpiece Immersionist (4K camera flights inside iconic canvases)
     - **🌿 Muse Visual Art**: The Impressionist Nature Sanctuary (75 videos of meditative gardens, water lilies, and ambient piano)
     - **🎻 K A R O L A**: The Classical Connoisseur (rediscovering overlooked 19th/20th-century landscape masters with classical scores)
     - **🎨 Painters Dream**: The Masterwork Re-enactor (steam trains at Gare Saint-Lazare, domestic Impressionist scenes)
     - **💌 Cupid Studio**: The Belle Époque Romantic Storyteller (Parisian ballet, opera, and Venice love stories)

4. **Preparation for AI Art Topic Similarity & Categorization**:
   - Standardized visual frames indexed in `wallpapers/metadata.json` ready for visual embeddings (CLIP, ResNet, Gemini Multimodal).
   - Structured schema with `tags`, `primaryPalette`, `timestampSec`, and `qualityLabel` fields.

---

## 🚀 Deployment & Local Running

This website is statically deployed to **GitHub Pages** with zero build steps or server dependencies.

### Local Development
```bash
# Start local HTTP server on port 8080 (ensures YouTube embed compatibility)
python3 start_server.py
```
Open **[http://localhost:8080](http://localhost:8080)** in your browser.

### Scenery Extraction Script
To extract additional wallpaper scenes:
```bash
# Run comprehensive scenery extractor (samples scene changes across runtime at -q:v 1)
python3 extract_wallpapers.py 30
python3 build_webpage.py
```

---

## 📁 Repository Structure

```
├── index.html                  # Main static web application ("L'Impressionnisme Vivant")
├── styles.css                  # Impressionist responsive design system
├── app.js                      # Explorer, filtering, resolution badges & wallpaper modal
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
    ├── metadata.json           # Wallpaper index, dimensions & timestamps
    └── <video_id>/             # Scenery snapshots (snapshot_1.jpg, snapshot_2.jpg...)
```

---
*Curated with devotion to Impressionist art and classical music.*
