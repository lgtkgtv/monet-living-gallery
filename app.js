// L'Impressionnisme Vivant: App Logic, Resolutions & Wallpaper Gallery

let currentViewMode = 'videos'; // 'videos' or 'wallpapers'
let currentVideos = [...ALL_VIDEOS];
let currentWallpapers = [];

document.addEventListener('DOMContentLoaded', () => {
    checkProtocolNotice();
    initHeroStats();
    renderChannelCards();
    populateChannelFilter();
    initFiltersAndEvents();
    buildAllWallpapersList();
    renderCurrentView();
});

function checkProtocolNotice() {
    if (window.location.protocol === 'file:') {
        const notice = document.getElementById('protocolNotice');
        if (notice) notice.style.display = 'block';
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
    document.getElementById('statTotalVideos').textContent = meta.totalVideos;
    document.getElementById('statTotalViews').textContent = (meta.totalViews / 1000000).toFixed(1) + 'M';
    document.getElementById('statTotalRuntime').textContent = formatHours(meta.totalDurationSec);
    document.getElementById('statChannelCount').textContent = meta.channelCount;
    if (document.getElementById('stat4kCount')) {
        document.getElementById('stat4kCount').textContent = `${meta.count4K} Works`;
    }
    if (document.getElementById('statWallpapersCount')) {
        document.getElementById('statWallpapersCount').textContent = `${meta.totalWallpapers}+`;
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
        btnVid.classList.add('active');
        btnWp.classList.remove('active');
        gridVid.style.display = 'grid';
        gridWp.style.display = 'none';
        headerTitle.textContent = '🎨 The Impressionist Video Explorer';
        headerDesc.textContent = 'Browse all 199 paintings and visual poems with native resolution badges, verified YouTube links, and 4K wallpaper scene snapshots.';
    } else {
        btnWp.classList.add('active');
        btnVid.classList.remove('active');
        gridVid.style.display = 'none';
        gridWp.style.display = 'grid';
        headerTitle.textContent = '🖼️ The 4K Impressionist Wallpaper Gallery';
        headerDesc.textContent = 'High-definition 4K snapshots extracted from Impressionist masterworks, perfect for desktop wallpapers and topic similarity analysis.';
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
    countSpan.textContent = `Showing ${videos.length} of ${ALL_VIDEOS.length} works`;

    if (videos.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: var(--text-muted);">
                <h3>No paintings or videos found</h3>
                <p>Try adjusting your search query, resolution, or channel filter.</p>
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
                <div class="video-channel" onclick="filterByChannel('${v.channel}')" style="cursor: pointer;" title="Click to view all from this channel">
                    ${v.channel}
                </div>
                <h4 class="video-title" title="${escapeQuotes(v.title)}">${v.title}</h4>
                
                <div class="video-meta-pills">
                    <span class="pill-res-tag ${v.is4K ? 'tag-4k' : ''}">📐 ${v.resolution}</span>
                    <span style="color: var(--text-muted); font-size: 0.74rem;">· ⏱️ ${v.durationFormatted}</span>
                </div>

                <div class="video-actions">
                    <a href="${v.url}" target="_blank" rel="noopener noreferrer" class="btn-card-yt" title="Watch full quality on YouTube">
                        Watch on YouTube ↗
                    </a>
                    <button class="btn-card-wallpaper" onclick="openWallpaperModal('${v.id}')" title="View 4K wallpaper scene snapshots for this video">
                        🖼️ Wallpapers ${v.wallpaperCount > 0 ? `<span class="badge-count">${v.wallpaperCount}</span>` : ''}
                    </button>
                    <button class="btn-card-play" onclick="openVideoModal('${v.id}', '${escapeQuotes(v.title)}')" title="Preview in embedded modal player">
                        ▶ In-Page
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
    countSpan.textContent = `Showing ${wallpapers.length} 4K wallpapers`;

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
    const query = document.getElementById('searchInput').value.toLowerCase().trim();
    const selectedChannel = document.getElementById('channelSelect').value;
    const selectedRes = document.getElementById('resSelect') ? document.getElementById('resSelect').value : 'ALL';
    const sortBy = document.getElementById('sortSelect').value;

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
    document.getElementById('channelSelect').value = channelName;
    document.getElementById('searchInput').value = '';
    document.getElementById('explorerSection').scrollIntoView({ behavior: 'smooth' });
    applyFilters();
}

function selectPathway(pathwayKey) {
    document.querySelectorAll('.pathway-chip').forEach(c => c.classList.remove('active'));
    event.currentTarget.classList.add('active');

    const searchInput = document.getElementById('searchInput');
    const channelSelect = document.getElementById('channelSelect');
    const resSelect = document.getElementById('resSelect');

    if (resSelect) resSelect.value = 'ALL';

    if (pathwayKey === 'all') {
        searchInput.value = '';
        channelSelect.value = 'ALL';
    } else if (pathwayKey === '4k') {
        searchInput.value = '';
        channelSelect.value = 'ALL';
        if (resSelect) resSelect.value = '4K';
    } else if (pathwayKey === 'archives') {
        searchInput.value = '';
        channelSelect.value = 'LearnFromMasters';
    } else if (pathwayKey === 'waterlilies') {
        channelSelect.value = 'ALL';
        searchInput.value = 'water lilies';
    } else if (pathwayKey === 'immersion') {
        searchInput.value = 'living';
        channelSelect.value = 'ALL';
    } else if (pathwayKey === 'masters') {
        channelSelect.value = 'K A R O L A';
        searchInput.value = '';
    } else if (pathwayKey === 'romance') {
        channelSelect.value = 'Cupid Studio';
        searchInput.value = '';
    }

    document.getElementById('explorerSection').scrollIntoView({ behavior: 'smooth' });
    applyFilters();
}

function resetFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('channelSelect').value = 'ALL';
    if (document.getElementById('resSelect')) document.getElementById('resSelect').value = 'ALL';
    document.getElementById('sortSelect').value = 'views_desc';
    document.querySelectorAll('.pathway-chip').forEach(c => c.classList.remove('active'));
    document.querySelector('.pathway-chip').classList.add('active');
    applyFilters();
}

function initFiltersAndEvents() {
    document.getElementById('searchInput').addEventListener('input', applyFilters);
    document.getElementById('channelSelect').addEventListener('change', applyFilters);
    if (document.getElementById('resSelect')) {
        document.getElementById('resSelect').addEventListener('change', applyFilters);
    }
    document.getElementById('sortSelect').addEventListener('change', applyFilters);

    // Modal listeners
    document.getElementById('modalOverlay').addEventListener('click', (e) => {
        if (e.target.id === 'modalOverlay') closeVideoModal();
    });

    document.getElementById('wallpaperModalOverlay').addEventListener('click', (e) => {
        if (e.target.id === 'wallpaperModalOverlay') closeWallpaperModal();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeVideoModal();
            closeWallpaperModal();
        }
    });
}

// Modal 1: Video Player
function openVideoModal(videoId, title) {
    const video = ALL_VIDEOS.find(v => v.id === videoId);
    const modal = document.getElementById('modalOverlay');
    const titleEl = document.getElementById('modalTitle');
    const resEl = document.getElementById('modalVideoRes');
    const iframeWrapper = document.getElementById('playerFrameWrapper');
    const directBtn = document.getElementById('modalYtDirectBtn');
    const fallbackLink = document.getElementById('modalYtFallbackLink');

    const ytUrl = `https://www.youtube.com/watch?v=${videoId}`;
    titleEl.textContent = title;
    if (resEl && video) {
        resEl.textContent = `Native Quality: ${video.qualityLabel} (${video.resolution})`;
    }
    if (directBtn) directBtn.href = ytUrl;
    if (fallbackLink) fallbackLink.href = ytUrl;

    const originParam = (window.location.protocol.startsWith('http') && window.location.origin && window.location.origin !== 'null')
        ? `&origin=${encodeURIComponent(window.location.origin)}`
        : '';

    iframeWrapper.innerHTML = `
        <iframe 
            src="https://www.youtube.com/embed/${videoId}?autoplay=1&enablejsapi=1${originParam}" 
            title="${title}" 
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
            referrerpolicy="strict-origin-when-cross-origin"
            allowfullscreen>
        </iframe>
    `;

    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeVideoModal() {
    const modal = document.getElementById('modalOverlay');
    const iframeWrapper = document.getElementById('playerFrameWrapper');
    iframeWrapper.innerHTML = '';
    modal.classList.remove('open');
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

    titleEl.textContent = video.title;
    subTitleEl.textContent = `${video.channel} · Native Quality: ${video.qualityLabel} (${video.resolution})`;

    activeWallpaperList = [];
    if (video.wallpapers && video.wallpapers.length > 0) {
        activeWallpaperList = [...video.wallpapers];
    } else {
        // High-definition YouTube master cover fallback if stream scenes are pending
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
    trayEl.innerHTML = '';

    activeWallpaperList.forEach((wp, idx) => {
        const thumb = document.createElement('img');
        thumb.src = wp.path;
        thumb.className = `wp-tray-thumb ${idx === activeWallpaperIndex ? 'active' : ''}`;
        thumb.title = `Scene at ${wp.timestampFormatted} (${wp.width}×${wp.height})`;
        thumb.onclick = () => selectWallpaperSnapshot(idx);
        trayEl.appendChild(thumb);
    });

    displayActiveWallpaper();
    modal.classList.add('open');
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

    mainImg.src = wp.path;
    const resText = `${wp.qualityLabel || '4K UHD'} · ${wp.width || 3840}×${wp.height || 2160}`;
    const timeText = wp.timestampFormatted ? ` · Scene at ${wp.timestampFormatted}` : '';
    badgeRes.textContent = `${resText}${timeText}`;
    
    downloadBtn.href = wp.path;
    downloadBtn.download = `Impressionism_Wallpaper_${wp.videoId || 'artwork'}_${activeWallpaperIndex + 1}.jpg`;

    const tsParam = wp.timestampSec ? `&t=${wp.timestampSec}s` : '';
    jumpBtn.href = `https://www.youtube.com/watch?v=${wp.videoId}${tsParam}`;
    jumpBtn.textContent = wp.timestampSec ? `Jump to Scene (${wp.timestampFormatted}) ↗` : `Watch Video ↗`;
}

function closeWallpaperModal() {
    const modal = document.getElementById('wallpaperModalOverlay');
    modal.classList.remove('open');
    document.body.style.overflow = '';
}
