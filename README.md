# 🎨 L'Impressionnisme Vivant
### *The Impressionist Video Explorer & 4K Wallpaper Archive*

An interactive, curated digital guide and high-definition visual archive dedicated to **Claude Monet** and the **Impressionist art movement**. Derived from the YouTube playlist **[sh_Monet inspired Visual Arts](https://www.youtube.com/playlist?list=PLeqGkucOU6lA)**, this project catalogs 199 masterworks across 41 distinct YouTube channels, featuring detailed channel aesthetic characterizations, verified links, embedded playback, and an extracted 4K wallpaper gallery.

---

## 🌟 Why is it called *"🎨 The Impressionist Video Explorer"*?

The name encapsulates three foundational dimensions of the project:

1. **The Impressionist Aesthetic**: The entire collection centers around Claude Monet and his French and international contemporaries (Renoir, Boudin, Sisley, Loiseau, Parreiras, Moras). Impressionism is uniquely defined by its obsession with *fleeting natural light, seasonal shifts, water reflections, and expressive brushwork*.
2. **The "Living" Video Medium**: Unlike static art books or traditional museum collections, these works exist as **cinematic and ambient videos**—reimagining classic canvases through 4K kinetic rendering, living animations of water and light, authentic nature ambiances (rain, birdsong, river breeze), and synchronized classical compositions (Debussy, Satie, Chopin).
3. **The "Explorer" Journey**: Rather than a flat list, the collection spans 41 distinct creators with contrasting philosophies—from academic museum catalogues to first-person immersion into Giverny's ponds. The interface functions as an *Explorer* where art lovers can navigate, filter, cross-reference, and journey through 78 hours of Impressionist art.

---

## 🏛️ The Curators & Channel Archetypes

The 41 channels in this playlist represent distinct artistic and curatorial approaches:

- **🏛️ LearnFromMasters** (*The Academic & Museum Archivist*): Complete, high-resolution monographic catalogues without kinetic effects, preserving scholarly museum fidelity. Features Monet (1,540 paintings, 3.8M views), Boudin, Sisley, and Levitan.
- **🎬 Extraordinary Visual Art** (*The Cinematic Immersionist*): High-concept 4K camera flights *inside* iconic canvases (*"Woman with a Parasol"*, *"Journey to the Water Lilies"*, *"Impression, Sunrise"*).
- **🌿 Muse Visual Art** (*The Nature & Atmospheric Sanctuary*): The playlist backbone (75 videos), focusing on meditative flora, water lily ponds, and gentle seasonal nature soundscapes paired with piano solos.
- **🎻 K A R O L A** (*The Classical Connoisseur*): Curatorial tributes rediscovering overlooked 19th/20th-century landscape masters (Antonio Parreiras, Walter Moras, Carl Spitzweg) strictly paired with credited classical recordings.
- **🎨 Painters Dream** (*The Masterwork Re-enactor*): Dramatic historical reconstructions of Impressionist life (Gare Saint-Lazare locomotives, domestic luncheons, winter snow).
- **💌 Cupid Studio** (*The Belle Époque Romantic*): Love stories, ballet, and Parisian nostalgia woven through Impressionist canvases.

---

## 🖼️ 4K Wallpaper Archive & Future AI Topic Clustering

This repository includes extracted, native high-definition / 4K snapshots sampled directly from the video streams:
- Located in `wallpapers/<video_id>/snapshot_<index>.jpg`
- Indexed in `wallpapers/metadata.json` and `data.js`
- Serves as:
  1. **Art Lover Wallpaper Gallery**: Downloadable 4K wallpapers for desktop and mobile displays with exact timestamp jump links.
  2. **Feature Resource for Topic Similarity**: Standardized image captures prepared for upcoming multi-modal visual clustering (categorizing works by botanical theme, marine/water, urban Paris, winter snow, and color palette uniqueness).

---

## 🚀 How to Host on GitHub Pages

This project is built with **zero external dependencies** and uses strictly relative paths, making it 100% ready for static hosting on **GitHub Pages**:

1. **Push to your GitHub repository**:
   ```bash
   git add .
   git commit -m "feat: Impressionist Video Explorer & 4K Wallpaper Gallery"
   git branch -M main
   git remote add origin https://github.com/<YOUR-USERNAME>/<YOUR-REPO-NAME>.git
   git push -u origin main
   ```
2. **Enable GitHub Pages**:
   - Go to your repository on GitHub: **Settings** → **Pages**
   - Under **Build and deployment** > **Source**, select **Deploy from a branch**
   - Branch: `main` / Folder: `/ (root)`
   - Click **Save**.
3. Your site will be live within seconds at:
   `https://<YOUR-USERNAME>.github.io/<YOUR-REPO-NAME>/`

---

## 💻 Running Locally

To run the explorer locally:
```bash
# Start local HTTP server on port 8080
python3 start_server.py
```
Open **[http://localhost:8080](http://localhost:8080)** in your browser. *(Running via HTTP provides a valid web origin, ensuring embedded YouTube player compatibility without Error 153).*

### Extracting Additional Wallpapers
To extract more 4K snapshots from the playlist:
```bash
# Extract wallpapers for the top N videos (or all 199)
python3 extract_wallpapers.py 50
python3 build_webpage.py
```

---

## 📁 Repository Structure

```
├── index.html                  # Main static web application
├── styles.css                  # Impressionist responsive design system
├── app.js                      # Explorer, filtering, search & wallpaper modal logic
├── data.js                     # Unified dataset (199 videos, channels, wallpapers)
├── playlist_raw.json           # Raw YouTube playlist metadata
├── monet_playlist_catalog.md   # Complete Markdown catalog of all 199 works
├── monet_playlist_by_channel.csv # Spreadsheet-ready CSV dataset
├── start_server.py             # One-click local HTTP server runner
├── extract_wallpapers.py       # Multi-threaded 4K stream frame extractor
├── build_webpage.py            # Automated site & metadata compiler
├── .nojekyll                   # Bypasses Jekyll processing on GitHub Pages
└── wallpapers/                 # 4K wallpaper archive by video ID
    ├── metadata.json           # Wallpaper index & dimensions
    └── <video_id>/             # High-res snapshots
```

---
*Curated with devotion to Impressionist art and classical music.*
