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

    // Default to 4K UHD Only as requested for immediate high-end visual impact
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

    const badge = document.getElementById('heroDeviceBadge');
    if (badge) {
        if (isMobile) {
            badge.textContent = '📱 Mobile Optimized View';
            badge.title = 'Layout adapted for one-hand browsing, quick audio-visual streaming, and touch interaction.';
        } else {
            badge.textContent = '🖥️ Desktop Gallery View';
            badge.title = 'Full-width cinematic view with high-definition wallpaper inspection.';
        }
    }

    return isMobile;
}

function toggleHeroStats() {
    const drawer = document.getElementById('heroStatsDrawer');
    const icon = document.getElementById('statsToggleIcon');
    const btn = document.getElementById('statsToggleBtn');
    if (!drawer) return;

    const isOpen = drawer.classList.contains('open');
    if (isOpen) {
        drawer.classList.remove('open');
        if (icon) icon.textContent = '▼';
        if (btn) btn.setAttribute('aria-expanded', 'false');
    } else {
        drawer.classList.add('open');
        if (icon) icon.textContent = '▲';
        if (btn) btn.setAttribute('aria-expanded', 'true');
    }
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
    if (document.getElementById('statTotalRuntime')) {
        document.getElementById('statTotalRuntime').textContent = formatHours(meta.totalDurationSec);
    }
    if (document.getElementById('statChannelCount')) {
        document.getElementById('statChannelCount').textContent = meta.channelCount;
    }
    if (document.getElementById('stat4kCount')) {
        document.getElementById('stat4kCount').textContent = `${meta.count4K} Works`;
    }
    if (document.getElementById('hero4kBtnCount')) {
        document.getElementById('hero4kBtnCount').textContent = meta.count4K;
    }
    if (document.getElementById('statWallpapersCount')) {
        document.getElementById('statWallpapersCount').textContent = `${meta.totalWallpapers}+`;
    }
    if (document.getElementById('heroWpBtnCount')) {
        document.getElementById('heroWpBtnCount').textContent = `${meta.totalWallpapers}+`;
    }
    if (document.getElementById('toggleVideosCount')) {
        document.getElementById('toggleVideosCount').textContent = meta.totalVideos;
    }
    if (document.getElementById('toggleWallpapersCount')) {
        document.getElementById('toggleWallpapersCount').textContent = meta.totalWallpapers;
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
                <button class="btn-filter-channel" onclick="filterByChannel('${profile.name}')">
                    Explore ${stats.count} Videos
                </button>
                <a href="${stats.channel_url}" target="_blank" rel="noopener noreferrer" class="btn-visit-channel" title="Open Channel on YouTube">
                    Visit Channel ↗
                </a>
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

function switchViewMode(mode) {
    currentViewMode = mode;
    const btnVid = document.getElementById('toggleBtnVideos');
    const btnWp = document.getElementById('toggleBtnWallpapers');
    const gridVid = document.getElementById('videosGrid');
    const gridWp = document.getElementById('wallpapersGrid');
    const headerTitle = document.getElementById('sectionHeaderTitle');
    const headerDesc = document.getElementById('sectionHeaderDesc');

    if (mode === 'videos') {
        if (btnVid) btnVid.classList.add('active');
        if (btnWp) btnWp.classList.remove('active');
        if (gridVid) gridVid.style.display = 'grid';
        if (gridWp) gridWp.style.display = 'none';
        if (headerTitle) headerTitle.textContent = '🎨 The Impressionist Video Explorer';
        if (headerDesc) headerDesc.innerHTML = 'Currently showcasing <strong>4K Ultra-HD Masterworks</strong> first. Native resolutions, verified links, and extracted scene snapshots.';
    } else {
        if (btnWp) btnWp.classList.add('active');
        if (btnVid) btnVid.classList.remove('active');
        if (gridVid) gridVid.style.display = 'none';
        if (gridWp) gridWp.style.display = 'grid';
        if (headerTitle) headerTitle.textContent = '🖼️ The 4K Impressionist Wallpaper Gallery';
        if (headerDesc) headerDesc.innerHTML = 'High-definition 4K snapshots extracted from Impressionist masterworks. Completely ad-free, instant artwork previews.';
    }

    applyFilters();
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
        
        card.innerHTML = `
            <div class="thumb-container" onclick="openVideoModal('${v.id}', '${escapeQuotes(v.title)}')">
                <img class="thumb-img" src="${v.thumb}" alt="${escapeQuotes(v.title)}" loading="lazy" />
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
                    <button class="btn-card-play" onclick="openVideoModal('${v.id}', '${escapeQuotes(v.title)}')" title="Preview in embedded modal player">
                        ▶ Play Video
                    </button>
                    <button class="btn-card-wallpaper" onclick="openWallpaperModal('${v.id}')" title="View 4K wallpaper scene snapshots for this video">
                        🖼️ Wallpapers ${v.wallpaperCount > 0 ? `<span class="badge-count">${v.wallpaperCount}</span>` : ''}
                    </button>
                    <a href="${v.url}" target="_blank" rel="noopener noreferrer" class="btn-card-yt" title="Watch full quality on YouTube">
                        YouTube ↗
                    </a>
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
        countSpan.textContent = `Showing ${wallpapers.length} 4K wallpapers`;
    }

    if (wallpapers.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: var(--text-muted);">
                <h3>No wallpapers match your criteria</h3>
                <p>Try clearing your search or selecting a different channel.</p>
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
    const selectedRes = resEl ? resEl.value : '4K';
    const sortBy = sortEl ? sortEl.value : 'views_desc';

    if (currentViewMode === 'videos') {
        let filtered = ALL_VIDEOS.filter(v => {
            const matchesQuery = !query || 
                v.title.toLowerCase().includes(query) || 
                v.channel.toLowerCase().includes(query);
            const matchesChannel = (selectedChannel === 'ALL') || (v.channel === selectedChannel);
            
            let matchesRes = true;
            if (selectedRes === '4K') matchesRes = v.is4K;
            else if (selectedRes === 'FHD') matchesRes = (!v.is4K && v.height >= 1080);
            else if (selectedRes === 'OTHER') matchesRes = (v.height < 1080 || v.height === 1440);

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
    } else {
        let filteredWp = [];
        ALL_VIDEOS.forEach(v => {
            const matchesQuery = !query || 
                v.title.toLowerCase().includes(query) || 
                v.channel.toLowerCase().includes(query);
            const matchesChannel = (selectedChannel === 'ALL') || (v.channel === selectedChannel);
            
            let matchesRes = true;
            if (selectedRes === '4K') matchesRes = v.is4K;
            else if (selectedRes === 'FHD') matchesRes = (!v.is4K && v.height >= 1080);
            else if (selectedRes === 'OTHER') matchesRes = (v.height < 1080 || v.height === 1440);

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
    }
}

function filterByChannel(channelName) {
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
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('active');
    }

    const searchInput = document.getElementById('searchInput');
    const channelSelect = document.getElementById('channelSelect');
    const resSelect = document.getElementById('resSelect');

    if (pathwayKey === '4k') {
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

    document.querySelectorAll('.pathway-chip').forEach(c => c.classList.remove('active'));
    const firstChip = document.querySelector('.pathway-chip');
    if (firstChip) firstChip.classList.add('active');

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
function openVideoModal(videoId, title) {
    currentModalVideoId = videoId;
    const video = ALL_VIDEOS.find(v => v.id === videoId);
    const modal = document.getElementById('modalOverlay');
    const titleEl = document.getElementById('modalTitle');
    const resEl = document.getElementById('modalVideoRes');
    const iframeWrapper = document.getElementById('playerFrameWrapper');
    const directBtn = document.getElementById('modalYtDirectBtn');
    const directBtn2 = document.getElementById('modalYtDirectBtn2');
    const footerChannel = document.getElementById('modalFooterChannel');
    const footerQuality = document.getElementById('modalFooterQuality');

    const ytUrl = `https://www.youtube.com/watch?v=${videoId}`;
    if (titleEl) titleEl.textContent = title;
    if (resEl && video) {
        resEl.textContent = video.is4K ? `👑 Native 4K UHD (${video.resolution})` : `Native Quality: ${video.qualityLabel} (${video.resolution})`;
    }
    if (directBtn) directBtn.href = ytUrl;
    if (directBtn2) directBtn2.href = ytUrl;

    if (footerChannel && video) {
        footerChannel.textContent = video.channel;
    }
    if (footerQuality && video) {
        footerQuality.textContent = video.is4K ? '👑 4K UHD Masterwork' : video.qualityLabel;
    }

    const originParam = (window.location.protocol.startsWith('http') && window.location.origin && window.location.origin !== 'null')
        ? `&origin=${encodeURIComponent(window.location.origin)}`
        : '';

    // Use Privacy-Enhanced mode (youtube-nocookie.com) + modestbranding + rel=0 to minimize ad annoyance
    if (iframeWrapper) {
        iframeWrapper.innerHTML = `
            <iframe 
                src="https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&enablejsapi=1&rel=0&modestbranding=1&iv_load_policy=3${originParam}" 
                title="${escapeQuotes(title)}" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                referrerpolicy="strict-origin-when-cross-origin"
                allowfullscreen>
            </iframe>
        `;
    }

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
        activeWallpaperList = [...video.wallpapers];
    } else {
        // High-definition YouTube master cover fallback
        activeWallpaperList.push({
            path: video.maxresThumb,
            qualityLabel: `${video.qualityLabel} Master Cover`,
            timestampFormatted: 'Cover Masterwork',
            timestampSec: 0,
            width: video.width || 1920,
            height: video.height || 1080,
            videoId: video.id
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
    const downloadBtn = document.getElementById('wpDownloadBtn');
    const jumpBtn = document.getElementById('wpJumpVideoBtn');

    if (mainImg) mainImg.src = wp.path;
    const resText = `${wp.qualityLabel || '4K UHD'} · ${wp.width || 3840}×${wp.height || 2160}`;
    const timeText = wp.timestampFormatted ? ` · Scene at ${wp.timestampFormatted}` : '';
    if (badgeRes) badgeRes.textContent = `${resText}${timeText}`;
    
    if (downloadBtn) {
        downloadBtn.href = wp.path;
        downloadBtn.download = `Impressionism_Wallpaper_${wp.videoId || 'artwork'}_${activeWallpaperIndex + 1}.jpg`;
    }

    if (jumpBtn) {
        const tsParam = wp.timestampSec ? `&t=${wp.timestampSec}s` : '';
        jumpBtn.href = `https://www.youtube.com/watch?v=${wp.videoId}${tsParam}`;
        jumpBtn.textContent = wp.timestampSec ? `Jump to Scene (${wp.timestampFormatted}) ↗` : `Watch Video ↗`;
    }
}

function closeWallpaperModal() {
    const modal = document.getElementById('wallpaperModalOverlay');
    if (modal) modal.classList.remove('open');
    document.body.style.overflow = '';
}
