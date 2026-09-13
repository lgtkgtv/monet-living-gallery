// L'Impressionnisme Vivant: App Logic, Resolutions, Device Adaptation & 4K Wallpaper Gallery

let currentViewMode = 'videos'; // 'videos' or 'wallpapers'
let currentVideos = [];
let currentWallpapers = [];
let currentModalVideoId = null;

document.addEventListener('DOMContentLoaded', () => {
    detectDeviceFormFactor();
    window.addEventListener('resize', detectDeviceFormFactor);

    initHeroStats();
    renderChannelCards();
    populateChannelFilter();
    initFiltersAndEvents();
    buildAllWallpapersList();

    // Default to 4K UHD Only as requested
    const resSelect = document.getElementById('resSelect');
    if (resSelect) {
        resSelect.value = '4K';
    }

    applyFilters();
});

// Device Form-Factor Detection (Mobile vs Desktop)
function detectDeviceFormFactor() {
    const isMobile = window.innerWidth <= 768 || 
                     /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    document.documentElement.classList.toggle('is-mobile-device', isMobile);
    document.documentElement.classList.toggle('is-desktop-device', !isMobile);

    return isMobile;
}

function formatViews(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1).replace(/\.0$/, '') + 'M views';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(0) + 'K views';
    }
    return num.toLocaleString() + ' views';
}

function formatHours(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hrs}h ${mins}m`;
}

function initHeroStats() {
    const meta = PLAYLIST_METADATA;
    if (document.getElementById('statTotalVideos')) {
        document.getElementById('statTotalVideos').textContent = meta.totalVideos;
    }
    if (document.getElementById('statTotalViews')) {
        document.getElementById('statTotalViews').textContent = (meta.totalViews / 1000000).toFixed(1) + 'M';
    }
    if (document.getElementById('statChannelCount')) {
        document.getElementById('statChannelCount').textContent = meta.channelCount;
    }
    if (document.getElementById('stat4kCount')) {
        document.getElementById('stat4kCount').textContent = `${meta.count4K} Works`;
    }
    if (document.getElementById('statWallpapersCount')) {
        document.getElementById('statWallpapersCount').textContent = `${meta.totalWallpapers}+`;
    }
}

function buildAllWallpapersList() {
    currentWallpapers = [];
    ALL_VIDEOS.forEach(v => {
        if (v.wallpapers && v.wallpapers.length > 0) {
            v.wallpapers.forEach(wp => {
                currentWallpapers.push({
                    ...wp,
                    videoTitle: v.title,
                    channel: v.channel,
                    videoUrl: v.url
                });
            });
        }
    });
}

function renderChannelCards() {
    const container = document.getElementById('channelsGrid');
    if (!container) return;
    container.innerHTML = '';

    const priorityOrder = [
        'LearnFromMasters',
        'Extraordinary Visual Art',
        'Muse Visual Art',
        'K A R O L A',
        'Painters Dream',
        'Cupid Studio'
    ];

    priorityOrder.forEach(key => {
        const profile = CHANNEL_PROFILES[key];
        const stats = CHANNEL_STATS.find(s => s.channel === key);
        if (!profile || !stats) return;

        const card = document.createElement('div');
        card.className = 'channel-card';
        card.innerHTML = `
            <div class="channel-card-top">
                <span class="channel-badge" style="background-color: ${profile.accent}15; color: ${profile.accent}">
                    ${profile.archetype}
                </span>
                <span class="channel-icon">${profile.icon}</span>
            </div>
            <h3 class="channel-name">${profile.name}</h3>
            <div class="channel-tagline">${profile.tagline}</div>
            <p class="channel-desc">${profile.characterization}</p>
            
            <div class="channel-theme-tags">
                ${profile.keyThemes.map(t => `<span class="theme-tag">${t}</span>`).join('')}
            </div>

            <div class="channel-stats-row">
                <div>
                    <span>Playlist Videos</span>
                    <strong>${stats.count}</strong>
                </div>
                <div>
                    <span>Total Views</span>
                    <strong>${formatViews(stats.total_views)}</strong>
                </div>
                <div>
                    <span>Avg / Video</span>
                    <strong>${formatViews(stats.avg_views)}</strong>
                </div>
            </div>

            <div class="channel-actions">
                <button class="btn-filter-channel" onclick="filterByChannel('${profile.name}')" style="width: 100%;">
                    🏛️ Explore ${stats.count} Curated Works
                </button>
            </div>
        `;
        container.appendChild(card);
    });
}

function populateChannelFilter() {
    const select = document.getElementById('channelSelect');
    if (!select) return;
    select.innerHTML = '<option value="ALL">All Source Channels (41)</option>';

    CHANNEL_STATS.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.channel;
        opt.textContent = `${s.channel} (${s.count} videos · ${formatViews(s.total_views)})`;
        select.appendChild(opt);
    });
}

function switchMainTab(tabKey) {
    const tabVideos = document.getElementById('tabBtnVideos');
    const tabWallpapers = document.getElementById('tabBtnWallpapers');
    const tabChannels = document.getElementById('tabBtnChannels');

    const explorerSection = document.getElementById('explorerSection');
    const channelsSection = document.getElementById('channelsSection');
    const gridVid = document.getElementById('videosGrid');
    const gridWp = document.getElementById('wallpapersGrid');
    const downloadBar = document.getElementById('wallpaperDownloadBar');
    const headerTitle = document.getElementById('sectionHeaderTitle');
    const headerDesc = document.getElementById('sectionHeaderDesc');

    // Update tab button states
    [
        { key: 'videos', btn: tabVideos },
        { key: 'wallpapers', btn: tabWallpapers },
        { key: 'channels', btn: tabChannels }
    ].forEach(({ key, btn }) => {
        if (!btn) return;
        const isActive = (key === tabKey);
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    if (tabKey === 'channels') {
        if (channelsSection) {
            channelsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        return;
    }

    currentViewMode = tabKey;

    if (tabKey === 'videos') {
        if (gridVid) gridVid.style.display = 'grid';
        if (gridWp) gridWp.style.display = 'none';
        if (downloadBar) downloadBar.style.display = 'none';
        if (headerTitle) headerTitle.textContent = '🎨 The Impressionist Video Explorer';
        if (headerDesc) headerDesc.innerHTML = 'Explore high-definition Impressionist masterworks, living canvas motion, and museum-grade reproductions.';
    } else if (tabKey === 'wallpapers') {
        if (gridVid) gridVid.style.display = 'none';
        if (gridWp) gridWp.style.display = 'grid';
        if (downloadBar) downloadBar.style.display = 'flex';
        if (headerTitle) headerTitle.textContent = '🖼️ The Impressionist Wallpaper Gallery';
        if (headerDesc) headerDesc.innerHTML = 'High-definition snapshots extracted from Impressionist masterworks. Instant artwork previews.';
    }

    applyFilters();

    if (explorerSection) {
        explorerSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function switchViewMode(mode) {
    switchMainTab(mode);
}

function renderCurrentView() {
    if (currentViewMode === 'videos') {
        renderVideos(currentVideos);
    } else {
        renderWallpapers(currentWallpapers);
    }
}

function renderVideos(videos) {
    const grid = document.getElementById('videosGrid');
    const countSpan = document.getElementById('resultsCount');
    if (!grid) return;

    if (countSpan) {
        countSpan.textContent = `Showing ${videos.length} of ${ALL_VIDEOS.length} works`;
    }

    if (videos.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: var(--text-muted);">
                <h3>No paintings or videos found</h3>
                <p>Try adjusting your search query, resolution filter, or channel selection.</p>
                <button class="btn btn-primary" style="margin-top: 16px;" onclick="resetFilters()">Reset All Filters</button>
            </div>
        `;
        return;
    }

    grid.innerHTML = '';
    videos.forEach(v => {
        const card = document.createElement('div');
        card.className = 'video-card';
        const resBadgeClass = v.is4K ? 'badge-4k' : (v.height >= 1080 ? 'badge-fhd' : 'badge-sd');
        let thumbSrc = v.thumb;
        if (v.channel === 'Cupid Studio' && v.wallpapers && v.wallpapers.length > 0) {
            thumbSrc = v.wallpapers[0].path;
        }
        
        card.innerHTML = `
            <div class="thumb-container" onclick="openVideoModal('${v.id}', '${escapeQuotes(v.title)}')">
                <img class="thumb-img" src="${thumbSrc}" alt="${escapeQuotes(v.title)}" loading="lazy" />
                <span class="thumb-badge-views">${formatViews(v.views)}</span>
                <span class="thumb-badge-res ${resBadgeClass}">${v.qualityLabel}</span>
                <span class="thumb-badge-duration">${v.durationFormatted}</span>
                <div class="play-overlay">
                    <div class="play-circle">▶</div>
                </div>
            </div>
            <div class="video-content">
                <div class="video-channel" onclick="filterByChannel('${escapeQuotes(v.channel)}')" style="cursor: pointer;" title="Click to view all from this channel">
                    ${v.channel}
                </div>
                <h4 class="video-title" onclick="openVideoModal('${v.id}', '${escapeQuotes(v.title)}')" style="cursor: pointer;" title="${escapeQuotes(v.title)}">
                    ${v.title}
                </h4>
                
                <div class="video-meta-pills">
                    <span class="pill-res-tag ${v.is4K ? 'tag-4k' : ''}">📐 ${v.resolution}</span>
                    <span style="color: var(--text-muted); font-size: 0.74rem;">· ⏱️ ${v.durationFormatted}</span>
                </div>

                <div class="video-actions">
                    <button class="btn-card-play" onclick="openVideoModal('${v.id}', '${escapeQuotes(v.title)}')" title="Watch in embedded gallery player">
                        ▶ Play Video
                    </button>
                    <button class="btn-card-wallpaper" onclick="openWallpaperModal('${v.id}')" title="View 4K wallpaper scene snapshots for this video">
                        🖼️ Wallpapers ${v.wallpaperCount > 0 ? `<span class="badge-count">${v.wallpaperCount}</span>` : ''}
                    </button>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}

function renderWallpapers(wallpapers) {
    const grid = document.getElementById('wallpapersGrid');
    const countSpan = document.getElementById('resultsCount');
    if (!grid) return;

    if (countSpan) {
        countSpan.textContent = `Showing ${wallpapers.length} wallpapers`;
    }

    if (wallpapers.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: var(--text-muted);">
                <h3>No wallpapers match your criteria</h3>
                <p>Try clearing your search or selecting a different channel or resolution.</p>
                <button class="btn btn-primary" style="margin-top: 16px;" onclick="resetFilters()">Reset All Filters</button>
            </div>
        `;
        return;
    }

    grid.innerHTML = '';
    wallpapers.forEach(wp => {
        const card = document.createElement('div');
        card.className = 'wallpaper-card';
        card.onclick = () => openWallpaperModal(wp.videoId, wp.snapshotIndex - 1);
        card.innerHTML = `
            <div class="wp-thumb-wrapper">
                <img class="wp-thumb-img" src="${wp.path}" alt="${escapeQuotes(wp.videoTitle)}" loading="lazy" />
                <span class="wp-pill-res">${wp.qualityLabel || '4K UHD'} (${wp.width}×${wp.height})</span>
                <span class="wp-pill-time">Scene at ${wp.timestampFormatted}</span>
            </div>
            <div class="wp-card-info">
                <span class="wp-card-channel">${wp.channel}</span>
                <h4 class="wp-card-title">${wp.videoTitle}</h4>
                <div class="wp-card-actions">
                    <button class="btn-wp-view">View & Download (${wp.width}×${wp.height})</button>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}

function escapeQuotes(str) {
    return (str || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function applyFilters() {
    const searchEl = document.getElementById('searchInput');
    const channelEl = document.getElementById('channelSelect');
    const resEl = document.getElementById('resSelect');
    const sortEl = document.getElementById('sortSelect');

    const query = searchEl ? searchEl.value.toLowerCase().trim() : '';
    const selectedChannel = channelEl ? channelEl.value : 'ALL';
    const selectedRes = resEl ? resEl.value : '1080P_PLUS';
    const sortBy = sortEl ? sortEl.value : 'views_desc';

    if (currentViewMode === 'videos') {
        let filtered = ALL_VIDEOS.filter(v => {
            const matchesQuery = !query || 
                v.title.toLowerCase().includes(query) || 
                v.channel.toLowerCase().includes(query);
            const matchesChannel = (selectedChannel === 'ALL') || (v.channel === selectedChannel);
            
            let matchesRes = true;
            if (selectedRes === '1080P_PLUS' || selectedRes === '1080P_OR_BETTER' || selectedRes === 'FHD_PLUS' || selectedRes === '1080P') {
                matchesRes = (v.is4K || v.height >= 1080);
            } else if (selectedRes === '1080P_EXACT' || selectedRes === 'FHD_EXACT' || selectedRes === '1080P_FHD' || selectedRes === 'FHD') {
                matchesRes = (!v.is4K && v.height === 1080);
            } else if (selectedRes === '4K') {
                matchesRes = v.is4K;
            } else if (selectedRes === 'OTHER') {
                matchesRes = (!v.is4K && v.height < 1080);
            }

            return matchesQuery && matchesChannel && matchesRes;
        });

        if (sortBy === 'views_desc') filtered.sort((a, b) => b.views - a.views);
        else if (sortBy === 'views_asc') filtered.sort((a, b) => a.views - b.views);
        else if (sortBy === 'res_desc') filtered.sort((a, b) => (b.width * b.height) - (a.width * a.height));
        else if (sortBy === 'duration_desc') filtered.sort((a, b) => b.durationSec - a.durationSec);
        else if (sortBy === 'duration_asc') filtered.sort((a, b) => a.durationSec - b.durationSec);
        else if (sortBy === 'title_asc') filtered.sort((a, b) => a.title.localeCompare(b.title));

        currentVideos = filtered;
        renderVideos(filtered);
        const downloadBar = document.getElementById('wallpaperDownloadBar');
        if (downloadBar) downloadBar.style.display = 'none';
    } else {
        let filteredWp = [];
        ALL_VIDEOS.forEach(v => {
            const matchesQuery = !query || 
                v.title.toLowerCase().includes(query) || 
                v.channel.toLowerCase().includes(query);
            const matchesChannel = (selectedChannel === 'ALL') || (v.channel === selectedChannel);
            
            let matchesRes = true;
            if (selectedRes === '1080P_PLUS' || selectedRes === '1080P_OR_BETTER' || selectedRes === 'FHD_PLUS' || selectedRes === '1080P') {
                matchesRes = (v.is4K || v.height >= 1080);
            } else if (selectedRes === '1080P_EXACT' || selectedRes === 'FHD_EXACT' || selectedRes === '1080P_FHD' || selectedRes === 'FHD') {
                matchesRes = (!v.is4K && v.height === 1080);
            } else if (selectedRes === '4K') {
                matchesRes = v.is4K;
            } else if (selectedRes === 'OTHER') {
                matchesRes = (!v.is4K && v.height < 1080);
            }

            if (matchesQuery && matchesChannel && matchesRes && v.wallpapers) {
                v.wallpapers.forEach(wp => {
                    filteredWp.push({
                        ...wp,
                        videoTitle: v.title,
                        channel: v.channel,
                        videoUrl: v.url
                    });
                });
            }
        });

        if (sortBy === 'res_desc') filteredWp.sort((a, b) => (b.width * b.height) - (a.width * a.height));

        currentWallpapers = filteredWp;
        renderWallpapers(filteredWp);
        updateWallpaperDownloadBar(filteredWp);
    }
}

function filterByChannel(channelName) {
    switchMainTab('videos');
    const channelSelect = document.getElementById('channelSelect');
    if (channelSelect) channelSelect.value = channelName;
    const searchInput = document.getElementById('searchInput');
    if (searchInput) searchInput.value = '';
    
    // Switch to all resolutions so channel videos aren't hidden
    const resSelect = document.getElementById('resSelect');
    if (resSelect) resSelect.value = 'ALL';

    const explorer = document.getElementById('explorerSection');
    if (explorer) explorer.scrollIntoView({ behavior: 'smooth' });
    applyFilters();
}

function selectPathway(pathwayKey) {
    document.querySelectorAll('.pathway-chip').forEach(c => c.classList.remove('active'));
    if (window.event && window.event.currentTarget) {
        window.event.currentTarget.classList.add('active');
    }

    const searchInput = document.getElementById('searchInput');
    const channelSelect = document.getElementById('channelSelect');
    const resSelect = document.getElementById('resSelect');

    if (pathwayKey === '1080p_plus' || pathwayKey === '1080p') {
        if (searchInput) searchInput.value = '';
        if (channelSelect) channelSelect.value = 'ALL';
        if (resSelect) resSelect.value = '1080P_PLUS';
    } else if (pathwayKey === '1080p_exact' || pathwayKey === '1080p_fhd' || pathwayKey === 'fhd') {
        if (searchInput) searchInput.value = '';
        if (channelSelect) channelSelect.value = 'ALL';
        if (resSelect) resSelect.value = '1080P_EXACT';
    } else if (pathwayKey === '4k') {
        if (searchInput) searchInput.value = '';
        if (channelSelect) channelSelect.value = 'ALL';
        if (resSelect) resSelect.value = '4K';
    } else if (pathwayKey === 'all') {
        if (searchInput) searchInput.value = '';
        if (channelSelect) channelSelect.value = 'ALL';
        if (resSelect) resSelect.value = 'ALL';
    } else if (pathwayKey === 'archives') {
        if (searchInput) searchInput.value = '';
        if (channelSelect) channelSelect.value = 'LearnFromMasters';
        if (resSelect) resSelect.value = 'ALL';
    } else if (pathwayKey === 'waterlilies') {
        if (channelSelect) channelSelect.value = 'ALL';
        if (searchInput) searchInput.value = 'water lilies';
        if (resSelect) resSelect.value = 'ALL';
    } else if (pathwayKey === 'immersion') {
        if (searchInput) searchInput.value = 'living';
        if (channelSelect) channelSelect.value = 'ALL';
        if (resSelect) resSelect.value = 'ALL';
    } else if (pathwayKey === 'masters') {
        if (channelSelect) channelSelect.value = 'K A R O L A';
        if (searchInput) searchInput.value = '';
        if (resSelect) resSelect.value = 'ALL';
    } else if (pathwayKey === 'romance') {
        if (channelSelect) channelSelect.value = 'Cupid Studio';
        if (searchInput) searchInput.value = '';
        if (resSelect) resSelect.value = 'ALL';
    }

    const explorer = document.getElementById('explorerSection');
    if (explorer) explorer.scrollIntoView({ behavior: 'smooth' });
    applyFilters();
}

function resetFilters() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) searchInput.value = '';
    const channelSelect = document.getElementById('channelSelect');
    if (channelSelect) channelSelect.value = 'ALL';
    const resSelect = document.getElementById('resSelect');
    if (resSelect) resSelect.value = '4K';
    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) sortSelect.value = 'views_desc';

    applyFilters();
}

function initFiltersAndEvents() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) searchInput.addEventListener('input', applyFilters);

    const channelSelect = document.getElementById('channelSelect');
    if (channelSelect) channelSelect.addEventListener('change', applyFilters);

    const resSelect = document.getElementById('resSelect');
    if (resSelect) resSelect.addEventListener('change', applyFilters);

    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) sortSelect.addEventListener('change', applyFilters);

    // Modal click-outside listeners
    const modalOverlay = document.getElementById('modalOverlay');
    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if (e.target.id === 'modalOverlay') closeVideoModal();
        });
    }

    const wallpaperModalOverlay = document.getElementById('wallpaperModalOverlay');
    if (wallpaperModalOverlay) {
        wallpaperModalOverlay.addEventListener('click', (e) => {
            if (e.target.id === 'wallpaperModalOverlay') closeWallpaperModal();
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeVideoModal();
            closeWallpaperModal();
        }
    });
}

// Modal 1: Video Player Lightbox
let currentModalTitle = '';
let currentModalStartSec = 0;

function loadPlayerIframe(videoId, title, startSec = 0) {
    const iframeWrapper = document.getElementById('playerFrameWrapper');
    if (!iframeWrapper || !videoId) return;

    const startParam = startSec > 0 ? `&start=${startSec}` : '';
    const originParam = (window.location.protocol.startsWith('http') && window.location.origin && window.location.origin !== 'null')
        ? `&origin=${encodeURIComponent(window.location.origin)}`
        : '';

    // Standard Privacy-Enhanced Mode (youtube-nocookie.com, modestbranding, rel=0, no tracking cookies)
    iframeWrapper.innerHTML = `
        <iframe 
            src="https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&enablejsapi=1&rel=0&modestbranding=1&iv_load_policy=3${startParam}${originParam}" 
            title="${escapeQuotes(title)}" 
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
            referrerpolicy="strict-origin-when-cross-origin"
            allowfullscreen>
        </iframe>
    `;
}

function openVideoModal(videoId, title, startSec = 0) {
    currentModalVideoId = videoId;
    currentModalTitle = title;
    currentModalStartSec = startSec;

    const video = ALL_VIDEOS.find(v => v.id === videoId);
    const modal = document.getElementById('modalOverlay');
    const titleEl = document.getElementById('modalTitle');
    const resEl = document.getElementById('modalVideoRes');
    const footerChannel = document.getElementById('modalFooterChannel');
    const footerQuality = document.getElementById('modalFooterQuality');
    const modalWpCount = document.getElementById('modalWpCount');
    const wpBtn = document.getElementById('modalViewWallpapersBtn');

    if (titleEl) titleEl.textContent = title;
    if (resEl && video) {
        resEl.textContent = video.is4K ? `👑 Native 4K UHD (${video.resolution})` : `Native Quality: ${video.qualityLabel} (${video.resolution})`;
    }

    if (footerChannel && video) {
        footerChannel.textContent = video.channel;
    }
    if (footerQuality && video) {
        footerQuality.textContent = video.is4K ? '👑 4K UHD Masterwork' : video.qualityLabel;
    }

    const wpCount = video ? (video.wallpaperCount || (video.wallpapers ? video.wallpapers.length : 0)) : 0;
    if (modalWpCount) modalWpCount.textContent = wpCount;
    if (wpBtn) wpBtn.style.display = wpCount > 0 ? 'inline-flex' : 'none';

    loadPlayerIframe(videoId, title, startSec);

    if (modal) modal.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function openWallpaperFromModal() {
    if (!currentModalVideoId) return;
    const vid = currentModalVideoId;
    closeVideoModal();
    openWallpaperModal(vid);
}

function closeVideoModal() {
    const modal = document.getElementById('modalOverlay');
    const iframeWrapper = document.getElementById('playerFrameWrapper');
    if (iframeWrapper) iframeWrapper.innerHTML = '';
    if (modal) modal.classList.remove('open');
    document.body.style.overflow = '';
}

// Modal 2: Wallpaper Gallery Lightbox
let activeWallpaperList = [];
let activeWallpaperIndex = 0;
let isDownloadingCurrent = false;
let isDownloadingAll = false;
const videoZipCache = new Map(); // Cache generated ZIP blobs per video to prevent duplicate downloads

function openWallpaperModal(videoId, initialIdx = 0) {
    const video = ALL_VIDEOS.find(v => v.id === videoId);
    if (!video) return;

    const modal = document.getElementById('wallpaperModalOverlay');
    const titleEl = document.getElementById('wpModalTitle');
    const subTitleEl = document.getElementById('wpModalSubtitle');
    const trayEl = document.getElementById('wpCarouselTray');

    if (titleEl) titleEl.textContent = video.title;
    if (subTitleEl) {
        subTitleEl.textContent = `${video.channel} · Native Quality: ${video.qualityLabel} (${video.resolution})`;
    }

    activeWallpaperList = [];
    if (video.wallpapers && video.wallpapers.length > 0) {
        activeWallpaperList = video.wallpapers.map(w => ({
            ...w,
            videoId: video.id,
            videoTitle: video.title
        }));
    } else {
        activeWallpaperList.push({
            path: video.maxresThumb,
            qualityLabel: `${video.qualityLabel} Master Cover`,
            timestampFormatted: 'Cover Masterwork',
            timestampSec: 0,
            width: video.width || 1920,
            height: video.height || 1080,
            videoId: video.id,
            videoTitle: video.title
        });
    }

    activeWallpaperIndex = Math.min(initialIdx, activeWallpaperList.length - 1);
    if (activeWallpaperIndex < 0) activeWallpaperIndex = 0;

    if (trayEl) {
        trayEl.innerHTML = '';
        activeWallpaperList.forEach((wp, idx) => {
            const thumb = document.createElement('img');
            thumb.src = wp.path;
            thumb.className = `wp-tray-thumb ${idx === activeWallpaperIndex ? 'active' : ''}`;
            thumb.title = `Scene at ${wp.timestampFormatted} (${wp.width}×${wp.height})`;
            thumb.onclick = () => selectWallpaperSnapshot(idx);
            trayEl.appendChild(thumb);
        });
    }

    displayActiveWallpaper();
    if (modal) modal.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function selectWallpaperSnapshot(idx) {
    activeWallpaperIndex = idx;
    const thumbs = document.querySelectorAll('.wp-tray-thumb');
    thumbs.forEach((t, i) => {
        t.classList.toggle('active', i === idx);
    });
    displayActiveWallpaper();
}

function displayActiveWallpaper() {
    const wp = activeWallpaperList[activeWallpaperIndex];
    if (!wp) return;

    const mainImg = document.getElementById('wpMainImage');
    const badgeRes = document.getElementById('wpBadgeResolution');
    const sceneNumEl = document.getElementById('wpCurrentSceneNum');
    const allCountEl = document.getElementById('wpAllCount');
    const jumpTimeEl = document.getElementById('wpJumpTimestamp');

    if (mainImg) mainImg.src = wp.path;
    const resText = `${wp.qualityLabel || '4K UHD'} · ${wp.width || 3840}×${wp.height || 2160}`;
    const timeText = wp.timestampFormatted ? ` · Scene at ${wp.timestampFormatted}` : '';
    if (badgeRes) badgeRes.textContent = `${resText}${timeText}`;

    if (sceneNumEl) {
        sceneNumEl.textContent = `Scene ${activeWallpaperIndex + 1}`;
    }
    if (allCountEl) {
        allCountEl.textContent = activeWallpaperList.length;
    }
    if (jumpTimeEl) {
        jumpTimeEl.textContent = wp.timestampFormatted || '00:00';
    }
}

// In-Page Scene Jump: seamlessly launches the in-page video player modal at exact scene timestamp
function jumpToSceneInPlayer() {
    const wp = activeWallpaperList[activeWallpaperIndex];
    if (!wp) return;

    const videoId = wp.videoId || currentModalVideoId;
    if (!videoId) return;

    const video = ALL_VIDEOS.find(v => v.id === videoId);
    const title = video ? video.title : 'Claude Monet Masterwork';
    const startSec = wp.timestampSec || 0;

    closeWallpaperModal();
    openVideoModal(videoId, title, startSec);
}

// Download currently viewed wallpaper snapshot with sanitized, descriptive title and timestamp
function downloadCurrentWallpaper() {
    const wp = activeWallpaperList[activeWallpaperIndex];
    if (!wp || isDownloadingCurrent) return;

    const video = ALL_VIDEOS.find(v => v.id === wp.videoId) || {};
    const rawTitle = wp.videoTitle || video.title || 'Monet_Impressionism';
    const safeTitle = rawTitle.replace(/[/\\?%*:|"<>]/g, '').replace(/\s+/g, '_').substring(0, 45);
    const sceneIdx = String(activeWallpaperIndex + 1).padStart(2, '0');
    const timeClean = (wp.timestampFormatted || '00m00s').replace(/[^a-zA-Z0-9]/g, '');
    const filename = `Monet_${safeTitle}_Scene_${sceneIdx}_${timeClean}_${wp.width || 3840}x${wp.height || 2160}.jpg`;

    isDownloadingCurrent = true;
    const btn = document.getElementById('wpDownloadCurrentBtn');
    const originalText = btn ? btn.innerHTML : '';

    if (btn) btn.innerHTML = '✓ Downloading...';

    const a = document.createElement('a');
    a.href = wp.path;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();

    setTimeout(() => {
        if (btn) btn.innerHTML = originalText;
        isDownloadingCurrent = false;
    }, 1200);
}

// Download all wallpapers for this video packaged cleanly into a single ZIP archive
async function downloadAllWallpapers() {
    if (isDownloadingAll) return;
    if (!activeWallpaperList || activeWallpaperList.length === 0) return;

    const btn = document.getElementById('wpDownloadAllBtn');
    const originalText = btn ? btn.innerHTML : '';

    const firstWp = activeWallpaperList[0];
    const videoId = firstWp.videoId || currentModalVideoId;
    const video = ALL_VIDEOS.find(v => v.id === videoId) || {};
    const rawTitle = firstWp.videoTitle || video.title || 'Monet_Impressionism';
    const safeTitle = rawTitle.replace(/[/\\?%*:|"<>]/g, '').replace(/\s+/g, '_').substring(0, 45);
    const zipFilename = `Monet_${safeTitle}_All_${activeWallpaperList.length}_Wallpapers.zip`;

    // 1. Return cached archive if already built during this session
    if (videoZipCache.has(videoId)) {
        const cachedBlob = videoZipCache.get(videoId);
        triggerBlobDownload(cachedBlob, zipFilename);
        if (btn) {
            btn.innerHTML = '✓ Downloaded!';
            setTimeout(() => { if (btn) btn.innerHTML = originalText; }, 1500);
        }
        return;
    }

    // 2. Check if JSZip library is available
    if (typeof JSZip === 'undefined') {
        alert('ZIP packaging library is loading. Downloading current wallpaper snapshot.');
        downloadCurrentWallpaper();
        return;
    }

    isDownloadingAll = true;
    try {
        const zip = new JSZip();
        const total = activeWallpaperList.length;

        for (let i = 0; i < total; i++) {
            const item = activeWallpaperList[i];
            if (btn) btn.innerHTML = `📦 Packaging ${i + 1}/${total}...`;

            const res = await fetch(item.path);
            if (!res.ok) throw new Error(`HTTP ${res.status} for ${item.path}`);
            const blob = await res.blob();

            const sceneIdx = String(i + 1).padStart(2, '0');
            const timeClean = (item.timestampFormatted || '').replace(/[^a-zA-Z0-9]/g, '');
            const itemFilename = `${safeTitle}_Scene_${sceneIdx}_${timeClean}_${item.width}x${item.height}.jpg`;

            zip.file(itemFilename, blob);
        }

        if (btn) btn.innerHTML = '📦 Compressing...';
        const zipBlob = await zip.generateAsync({
            type: 'blob',
            compression: 'STORE'
        });

        videoZipCache.set(videoId, zipBlob);
        triggerBlobDownload(zipBlob, zipFilename);

        if (btn) btn.innerHTML = '✓ Complete!';
        setTimeout(() => {
            if (btn) btn.innerHTML = originalText;
            isDownloadingAll = false;
        }, 1800);
    } catch (err) {
        console.error('Error packaging wallpapers zip:', err);
        if (btn) btn.innerHTML = '⚠️ Error. Try Single';
        setTimeout(() => {
            if (btn) btn.innerHTML = originalText;
            isDownloadingAll = false;
        }, 2000);
    }
}

function triggerBlobDownload(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
}

function closeWallpaperModal() {
    const modal = document.getElementById('wallpaperModalOverlay');
    if (modal) modal.classList.remove('open');
    document.body.style.overflow = '';
}

function updateWallpaperDownloadBar(filteredWp) {
    const downloadBar = document.getElementById('wallpaperDownloadBar');
    const countSpan = document.getElementById('wpDownloadFilteredCount');
    const titleEl = document.getElementById('wpDownloadFilterTitle');
    const subtitleEl = document.getElementById('wpDownloadFilterSubtitle');
    const btn = document.getElementById('wpDownloadFilteredBtn');

    if (!downloadBar) return;

    const channelEl = document.getElementById('channelSelect');
    const resEl = document.getElementById('resSelect');
    const channelText = (channelEl && channelEl.value !== 'ALL') ? channelEl.value : 'All Channels';
    const resText = resEl ? resEl.options[resEl.selectedIndex].text.replace(/^[^\w]+/, '').trim() : 'All Resolutions';

    const count = filteredWp ? filteredWp.length : 0;
    if (countSpan) countSpan.textContent = count;

    if (titleEl) {
        titleEl.textContent = `Download Filtered Wallpapers (${count} items)`;
    }
    if (subtitleEl) {
        subtitleEl.textContent = `Channel: ${channelText} · Resolution: ${resText} · Single ZIP Archive`;
    }

    if (btn) {
        if (count === 0) {
            btn.disabled = true;
            btn.innerHTML = '⚠️ No Wallpapers for Current Filter';
        } else {
            btn.disabled = false;
            btn.innerHTML = `📦 Download All (${count}) Wallpapers (ZIP)`;
        }
    }
}

let isDownloadingFiltered = false;
async function downloadAllFilteredWallpapers() {
    if (isDownloadingFiltered) return;
    if (!currentWallpapers || currentWallpapers.length === 0) {
        alert('No wallpapers match the current filter criteria.');
        return;
    }

    const btn = document.getElementById('wpDownloadFilteredBtn');
    const originalText = btn ? btn.innerHTML : '';

    if (typeof JSZip === 'undefined') {
        alert('ZIP packaging library is loading. Please try again in a moment.');
        return;
    }

    const channelEl = document.getElementById('channelSelect');
    const resEl = document.getElementById('resSelect');
    const channelName = (channelEl && channelEl.value !== 'ALL') 
        ? channelEl.value.replace(/[/\\?%*:|"<>]/g, '').replace(/\s+/g, '_') 
        : 'All_Channels';
    const resName = resEl ? resEl.value : 'Filtered';
    const total = currentWallpapers.length;
    const zipFilename = `Monet_Wallpapers_${channelName}_${resName}_(${total}_items).zip`;

    isDownloadingFiltered = true;
    if (btn) btn.disabled = true;

    try {
        const zip = new JSZip();
        let completed = 0;
        let successful = 0;

        // Download in parallel batches of 6 for high speed
        const batchSize = 6;
        for (let i = 0; i < total; i += batchSize) {
            const batch = currentWallpapers.slice(i, i + batchSize);
            await Promise.all(batch.map(async (wp, bIdx) => {
                const globalIdx = i + bIdx + 1;
                const safeTitle = (wp.videoTitle || 'Impressionism').replace(/[/\\?%*:|"<>]/g, '').replace(/\s+/g, '_').substring(0, 30);
                const safeChannel = (wp.channel || '').replace(/[/\\?%*:|"<>]/g, '').replace(/\s+/g, '_');
                const timeClean = (wp.timestampFormatted || '').replace(/[^a-zA-Z0-9]/g, '');
                const fileName = `${safeChannel}_${safeTitle}_scene${wp.snapshotIndex || globalIdx}_${timeClean}_${wp.width}x${wp.height}.jpg`;

                try {
                    const res = await fetch(wp.path);
                    if (res.ok) {
                        const blob = await res.blob();
                        zip.file(fileName, blob);
                        successful++;
                    }
                } catch (fetchErr) {
                    console.warn(`Could not load wallpaper ${wp.path}:`, fetchErr);
                }
                completed++;
            }));

            if (btn) btn.innerHTML = `📦 Packaging ${completed}/${total}...`;
        }

        if (successful === 0) {
            throw new Error('No wallpaper files could be loaded');
        }

        if (btn) btn.innerHTML = '📦 Compressing ZIP...';
        const zipBlob = await zip.generateAsync({
            type: 'blob',
            compression: 'STORE'
        });

        triggerBlobDownload(zipBlob, zipFilename);

        if (btn) btn.innerHTML = `✓ Downloaded ${successful} Wallpapers!`;
        setTimeout(() => {
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
            isDownloadingFiltered = false;
        }, 2500);
    } catch (err) {
        console.error('Error packaging filtered wallpapers:', err);
        if (btn) {
            btn.innerHTML = '⚠️ Download Error. Try Again';
            btn.disabled = false;
        }
        setTimeout(() => {
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
            isDownloadingFiltered = false;
        }, 3000);
    }
}
