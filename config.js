/**
 * L'Impressionnisme Vivant - Central Configuration & Legal Compliance Flags
 * 
 * This module establishes a clean separation between the YouTube playlist ingestion
 * and the viewing/downloading features. Toggling any flag cleanly enables or disables
 * the corresponding capability across all cards, modals, toolbars, and slideshows
 * without breaking application flow or layout integrity.
 */
const GALLERY_CONFIG = {
    // 1. Copyright & Distribution Feature Flags
    // Set to false to instantly disable all wallpaper downloading functionality
    ENABLE_WALLPAPER_DOWNLOADS: true,

    // Set to false to disable bulk ZIP packaging (e.g. to save client CPU/bandwidth or ToS compliance)
    ENABLE_BULK_ZIP_DOWNLOADS: true,

    // Set to false to hide direct external links to YouTube
    ENABLE_DIRECT_YOUTUBE_LINKS: true,

    // Set to false to hide channel attribution links
    SHOW_CHANNEL_ATTRIBUTION: true,

    // Show Public Domain, DMCA takedown & Fair Use educational disclosure in footer
    SHOW_LEGAL_DISCLAIMER: true,

    // 2. Playback & Soundtrack Separation
    // Controls the ambient classical music suite (Debussy, Satie, Ravel)
    ENABLE_AMBIENT_AUDIO: true,

    // Strict audio separation: guarantee ambient audio pauses whenever a video is playing
    // so the video title's original soundtrack is the only audio playing
    STRICT_VIDEO_AUDIO_ISOLATION: true,

    // 3. Performance & Rendering
    // Prefer loading compact data.json asynchronously if available
    PREFER_ASYNC_JSON: true,

    // Progressive rendering batch size
    BATCH_PAGE_SIZE: 24,

    // 4. Source Playlist Registry
    PLAYLIST_SOURCES: [
        {
            id: "PLeqGkucOU6lA",
            title: "sh_Monet inspired Visual Arts",
            url: "https://www.youtube.com/playlist?list=PLeqGkucOU6lA",
            category: "Claude Monet & Impressionist Masters"
        }
    ]
};

// Apply config flags to UI dynamically on load
function applyConfigFlags() {
    // If wallpaper downloads are disabled, hide all single and bulk download buttons
    if (!GALLERY_CONFIG.ENABLE_WALLPAPER_DOWNLOADS) {
        document.documentElement.classList.add('config-downloads-disabled');
        const dlCur = document.getElementById('wpDownloadCurrentBtn');
        const dlAll = document.getElementById('wpDownloadAllBtn');
        const dlFilter = document.getElementById('wpDownloadFilteredBtn');
        const ssDl = document.getElementById('slideshowDownloadBtn');
        if (dlCur) dlCur.style.display = 'none';
        if (dlAll) dlAll.style.display = 'none';
        if (dlFilter) dlFilter.style.display = 'none';
        if (ssDl) ssDl.style.display = 'none';
    }

    if (!GALLERY_CONFIG.ENABLE_BULK_ZIP_DOWNLOADS) {
        const dlAll = document.getElementById('wpDownloadAllBtn');
        const dlFilter = document.getElementById('wpDownloadFilteredBtn');
        if (dlAll) dlAll.style.display = 'none';
        if (dlFilter) dlFilter.style.display = 'none';
    }

    if (!GALLERY_CONFIG.ENABLE_AMBIENT_AUDIO) {
        const audioPill = document.getElementById('globalAudioPill');
        const ssAudio = document.querySelector('.slideshow-audio-control');
        if (audioPill) audioPill.style.display = 'none';
        if (ssAudio) ssAudio.style.display = 'none';
    }

    if (!GALLERY_CONFIG.ENABLE_DIRECT_YOUTUBE_LINKS) {
        const ytLink = document.getElementById('modalYtDirectLink');
        if (ytLink) ytLink.style.display = 'none';
    }
}

if (typeof window !== 'undefined') {
    window.GALLERY_CONFIG = GALLERY_CONFIG;
    window.applyConfigFlags = applyConfigFlags;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { GALLERY_CONFIG, applyConfigFlags };
}
