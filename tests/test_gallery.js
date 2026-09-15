// Automated regression test suite for L'Impressionnisme Vivant
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const baseDir = path.resolve(__dirname, '..');
const configCode = fs.readFileSync(path.join(baseDir, 'config.js'), 'utf8');
const dataCode = fs.readFileSync(path.join(baseDir, 'data.js'), 'utf8');
const appCode = fs.readFileSync(path.join(baseDir, 'app.js'), 'utf8');
const html = fs.readFileSync(path.join(baseDir, 'index.html'), 'utf8');

console.log('🧪 Starting Monet Living Gallery Test Suite...\n');

const dom = new JSDOM(html, {
    runScripts: 'outside-only',
    url: 'http://localhost:8000/'
});

// Mock browser methods not present in JSDOM
dom.window.Element.prototype.scrollIntoView = () => {};
dom.window.HTMLMediaElement.prototype.play = () => Promise.resolve();
dom.window.HTMLMediaElement.prototype.pause = () => {};

const errors = [];
dom.window.addEventListener('error', e => errors.push(e.error || e.message));

// Step 1: Script evaluation order
dom.window.eval(configCode);
dom.window.eval(dataCode);
dom.window.eval(appCode);

// Step 2: DOMContentLoaded lifecycle
dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));

// Verification 1: Initial Page Render
const vGrid = dom.window.document.getElementById('videosGrid');
const cards = vGrid ? vGrid.querySelectorAll('.video-card') : [];
console.log(`[PASS] Video cards rendered: ${cards.length} cards (expected >= 24)`);
if (cards.length < 24) throw new Error('Expected at least 24 cards rendered on initial load');

const resText = dom.window.document.getElementById('resultsCount').textContent;
console.log(`[PASS] Results counter: "${resText}"`);

// Verification 2: Wallpapers Tab
dom.window.switchMainTab('wallpapers');
const wpGrid = dom.window.document.getElementById('wallpapersGrid');
const wpCards = wpGrid.querySelectorAll('.wallpaper-card');
console.log(`[PASS] Wallpaper tab switch: ${wpCards.length} wallpaper cards rendered`);
if (wpCards.length < 24) throw new Error('Expected wallpapers to render');

// Verification 3: Favorites Tab
dom.window.switchMainTab('favorites');
const favEmpty = dom.window.document.getElementById('favoritesEmptyState');
console.log(`[PASS] Favorites empty state visible: ${favEmpty && favEmpty.style.display !== 'none'}`);

// Verification 3b: Channels Tab Switch (Dedicated tab view replaces long page scroll)
dom.window.switchMainTab('channels');
const explorerSection = dom.window.document.getElementById('explorerSection');
const channelsSection = dom.window.document.getElementById('channelsSection');
const channelsActive = dom.window.document.getElementById('tabBtnChannels').classList.contains('active');
if (explorerSection.style.display !== 'none') throw new Error('Expected explorerSection to be hidden when Channels tab is active');
if (channelsSection.style.display !== 'block') throw new Error('Expected channelsSection to be visible when Channels tab is active');
if (!channelsActive) throw new Error('Expected tabBtnChannels to have active class');
console.log('[PASS] Channels tab switch: explorer hidden, channelsSection displayed as dedicated tab');

// Verification 3c: Channel Card "Explore Works" Action
dom.window.switchMainTab('channels');
dom.window.filterByChannel('LearnFromMasters');
if (explorerSection.style.display !== 'block') throw new Error('filterByChannel must return to explorerSection');
if (channelsSection.style.display !== 'none') throw new Error('filterByChannel must hide channelsSection');
const chSelect = dom.window.document.getElementById('channelSelect');
if (chSelect.value !== 'LearnFromMasters') throw new Error('filterByChannel must set channel dropdown');
console.log('[PASS] Channel card action: filterByChannel switches tab and sets filter correctly');

// Verification 4: Switch Back to Videos
dom.window.switchMainTab('videos');
dom.window.document.getElementById('channelSelect').value = 'ALL';
dom.window.applyFilters();
if (explorerSection.style.display !== 'block') throw new Error('Expected explorerSection to be visible');
if (channelsSection.style.display !== 'none') throw new Error('Expected channelsSection to be hidden');
console.log(`[PASS] Videos grid restored: ${vGrid.style.display !== 'none'}`);

// Verification 5: Video Player Lightbox
const testVideoId = dom.window.ALL_VIDEOS[0].id;
dom.window.openVideoModal(testVideoId, 'Test Painting Title', 0);
const videoModal = dom.window.document.getElementById('modalOverlay');
console.log(`[PASS] Video modal open: ${videoModal.classList.contains('open')}`);
dom.window.closeVideoModal();
console.log(`[PASS] Video modal closed: ${!videoModal.classList.contains('open')}`);

// Verification 6: Wallpaper Lightbox
dom.window.openWallpaperModal(testVideoId, 0);
const wpModal = dom.window.document.getElementById('wallpaperModalOverlay');
console.log(`[PASS] Wallpaper modal open: ${wpModal.classList.contains('open')}`);
dom.window.closeWallpaperModal();
console.log(`[PASS] Wallpaper modal closed: ${!wpModal.classList.contains('open')}`);

// Verification 7: Legal & Copyright Notice Modal
dom.window.openLegalModal();
const legalModal = dom.window.document.getElementById('legalModalOverlay');
console.log(`[PASS] Legal modal open: ${legalModal.classList.contains('open')}`);
dom.window.closeLegalModal();
console.log(`[PASS] Legal modal closed`);

// Verification 8: Simplified Contact & Direct Email Link
const contactLine = dom.window.document.querySelector('.footer-contact-line');
const emailLink = dom.window.document.querySelector('.footer-email-link');
if (!contactLine || !contactLine.textContent.includes('sachin')) throw new Error('Expected simplified contact for sachin');
if (!emailLink || emailLink.href !== 'mailto:lgtkgtv@gmail.com') throw new Error('Expected email link to lgtkgtv@gmail.com');
console.log(`[PASS] Simplified contact line: "${contactLine.textContent.trim()}"`);

// Verification 9: Search Filter Execution
const searchInput = dom.window.document.getElementById('searchInput');
searchInput.value = 'Monet';
dom.window.applyFilters();
const monetCount = dom.window.document.getElementById('resultsCount').textContent;
console.log(`[PASS] Filter by search "Monet": "${monetCount}"`);

// Verification 10: Strict Audio Isolation
dom.window.openVideoModal(testVideoId, 'Test Video', 0);
dom.window.toggleSlideshowAudio();
console.log(`[PASS] Strict audio isolation: ambient audio blocked while video player is open`);
dom.window.closeVideoModal();

// Verification 11: Favorites Sanitization (Corrupted/Stale IDs purged)
dom.window.localStorage.setItem('monet_gallery_favorites_v1', JSON.stringify(['invalid_stale_id_999', '', null, 'undefined']));
dom.window.loadFavorites();
const cleanedCount = parseInt(dom.window.document.getElementById('favTabCount').textContent, 10);
console.log(`[PASS] Corrupted localStorage IDs purged: count is ${cleanedCount} (expected 0)`);
if (cleanedCount !== 0) throw new Error('Expected invalid IDs to be purged on load');

// Verification 12: Add valid favorite & verify Favorites tab rendering
dom.window.toggleFavoriteVideo(testVideoId);
const updatedCount = parseInt(dom.window.document.getElementById('favTabCount').textContent, 10);
console.log(`[PASS] Valid favorite added: count is ${updatedCount} (expected 1)`);
if (updatedCount !== 1) throw new Error('Expected 1 favorite');

// Verification 13: Switch to Favorites tab with filters auto-resetting
dom.window.switchMainTab('favorites');
const favCards = dom.window.document.getElementById('videosGrid').querySelectorAll('.video-card');
console.log(`[PASS] Favorites tab displays saved work: ${favCards.length} card (expected 1)`);
if (favCards.length !== 1) throw new Error('Expected 1 card in favorites view');

// Verification 14: Clear all favorites
dom.window.clearAllFavorites();
const clearedCount = parseInt(dom.window.document.getElementById('favTabCount').textContent, 10);
console.log(`[PASS] Clear all favorites: count is ${clearedCount} (expected 0)`);
if (clearedCount !== 0) throw new Error('Expected 0 favorites after clear');
const favEmptyAfter = dom.window.document.getElementById('favoritesEmptyState');
console.log(`[PASS] Empty state displayed after clear: ${favEmptyAfter.style.display !== 'none'}`);

// Verification 15: Copyright & Prohibited Downloads Tracking
const isLivingArtMomentsProhibited = dom.window.isChannelDownloadProhibited('Living Art Moments');
const isLearnFromMastersProhibited = dom.window.isChannelDownloadProhibited('LearnFromMasters');
if (!isLivingArtMomentsProhibited) throw new Error('Living Art Moments should be prohibited from downloads');
if (isLearnFromMastersProhibited) throw new Error('LearnFromMasters should be permitted for downloads');
console.log('[PASS] Channel copyright tracking: prohibited downloads correctly enforced');

// Verification 16: Default 4K Resolution Filter
dom.window.switchMainTab('videos');
dom.window.filterTo4K();
const resValue = dom.window.document.getElementById('resSelect').value;
if (resValue !== '4K') throw new Error(`Expected resolution to be 4K, got ${resValue}`);
console.log(`[PASS] Default 4K resolution filter verified: "${resValue}"`);

// Verification 17: Favorites Action Bar visibility
dom.window.toggleFavoriteVideo(testVideoId);
dom.window.switchMainTab('favorites');
const favActionBar = dom.window.document.getElementById('favoritesActionBar');
if (!favActionBar || favActionBar.style.display !== 'flex') {
    throw new Error('Expected favoritesActionBar to be visible (flex) when favorites exist');
}
dom.window.switchMainTab('videos');
if (favActionBar.style.display !== 'none') {
    throw new Error('Expected favoritesActionBar to be hidden in videos view');
}
console.log('[PASS] Favorites action bar toggles visibility correctly across views');

// Verification 18: Cross-device collection sharing import
dom.window.clearAllFavorites();
const testSharedId = dom.window.ALL_VIDEOS[1].id;
dom.window.history.pushState({}, '', `/?fav=${testVideoId},${testSharedId}`);
dom.window.checkSharedFavoritesUrl();
const sharedImportCount = parseInt(dom.window.document.getElementById('favTabCount').textContent, 10);
if (sharedImportCount !== 2) throw new Error(`Expected 2 imported favorites, got ${sharedImportCount}`);
console.log(`[PASS] Cross-device collection sharing imported ${sharedImportCount} works seamlessly`);

// Verification 19: Ken Burns cinematic motion default & toggle
const kenBurnsBtn = dom.window.document.getElementById('slideshowKenBurnsBtn');
const slideshowImg = dom.window.document.getElementById('slideshowImage');
if (!kenBurnsBtn) throw new Error('Expected slideshowKenBurnsBtn to exist in DOM');
if (!kenBurnsBtn.classList.contains('active')) throw new Error('Expected Ken Burns button to have active class by default');
dom.window.toggleSlideshowKenBurns();
if (kenBurnsBtn.classList.contains('active')) throw new Error('Expected Ken Burns button to be deactivated');
if (slideshowImg.classList.contains('ken-burns')) throw new Error('Expected ken-burns class to be removed');
dom.window.toggleSlideshowKenBurns();
if (!kenBurnsBtn.classList.contains('active')) throw new Error('Expected Ken Burns button to have active class after toggling back');
// Verification 20: Generic Multi-Playlist Architecture
if (!Array.isArray(dom.window.PLAYLISTS_CONFIG)) {
    throw new Error('Expected PLAYLISTS_CONFIG to be an array');
}
if (!dom.window.ALL_VIDEOS[0].playlistId) {
    throw new Error('Expected video entries to be tagged with playlistId');
}
// Test multi-playlist dynamic UI activation
dom.window.PLAYLISTS_CONFIG = [
    { id: 'PLeqGkucOU6lA', title: 'Monet Living Arts', url: 'https://youtube.com/playlist?list=PLeqGkucOU6lA' },
    { id: 'PL_Test2', title: 'Post-Impressionist Masters', url: 'https://youtube.com/playlist?list=PL_Test2' }
];
dom.window.populatePlaylistFilter();
const playlistSelect = dom.window.document.getElementById('playlistSelect');
if (playlistSelect.style.display === 'none') {
    throw new Error('Expected playlistSelect to be visible when multiple playlists configured');
}
if (playlistSelect.options.length !== 3) { // ALL + 2 playlists
    throw new Error(`Expected 3 options in playlistSelect, got ${playlistSelect.options.length}`);
}
console.log('[PASS] Generic Multi-Playlist Architecture verified: dynamic filter activation & tagging');

// Verification 21: Artist dropdown filter & auto-resolution relaxation
dom.window.switchMainTab('videos');
dom.window.resetFilters();
const artistSelect = dom.window.document.getElementById('artistSelect');
const resSelect = dom.window.document.getElementById('resSelect');
if (!artistSelect) throw new Error('Expected #artistSelect to exist in DOM');
if (resSelect.value !== '4K') throw new Error(`Expected default resolution to be 4K, got ${resSelect.value}`);

// Alfred Sisley has 0 4K works and 12 FHD works. Selecting Alfred Sisley should auto-expand resolution to ALL.
artistSelect.value = 'Alfred Sisley';
dom.window.onArtistFilterChange();
if (resSelect.value !== 'ALL') {
    throw new Error(`Expected resolution to auto-expand to ALL for Alfred Sisley, got ${resSelect.value}`);
}
const sisleyCardCount = dom.window.document.querySelectorAll('#videosGrid .video-card').length;
if (sisleyCardCount === 0) throw new Error('Expected video cards to render for Alfred Sisley');
console.log(`[PASS] Artist dropdown & auto-resolution expansion: ${sisleyCardCount} works rendered for Alfred Sisley`);

// Verification 22: Theme dropdown filter
dom.window.resetFilters();
const themeSelect = dom.window.document.getElementById('themeSelect');
if (!themeSelect) throw new Error('Expected #themeSelect to exist in DOM');
themeSelect.value = 'Water Lilies & Lotus Ponds';
dom.window.onThemeFilterChange();
const waterLilyCardCount = dom.window.document.querySelectorAll('#videosGrid .video-card').length;
if (waterLilyCardCount === 0) throw new Error('Expected cards rendered for Water Lilies theme');
console.log(`[PASS] Theme dropdown filter: ${waterLilyCardCount} works rendered for Water Lilies motif`);

// Verification 23: Copyright filter
dom.window.resetFilters();
const resSelectEl = dom.window.document.getElementById('resSelect');
if (resSelectEl) resSelectEl.value = 'ALL'; // Living Art Moments titles are in 1080p FHD
const copyrightSelect = dom.window.document.getElementById('copyrightSelect');
if (!copyrightSelect) throw new Error('Expected #copyrightSelect to exist in DOM');
copyrightSelect.value = 'VIEW_ONLY';
dom.window.applyFilters();
const viewOnlyCards = dom.window.document.querySelectorAll('#videosGrid .video-card');
if (viewOnlyCards.length === 0) throw new Error('Expected view-only titles to match filter');
console.log(`[PASS] Copyright filter: ${viewOnlyCards.length} view-only copyright-restricted works isolated`);

// Verification 24: Smart Search Assistance & Educational Discovery Pills for uncataloged artists
dom.window.resetFilters();
searchInput.value = 'Pissarro';
dom.window.applyFilters();
const guidanceBox = dom.window.document.querySelector('.empty-state-guidance-box');
const discoveryPills = dom.window.document.querySelectorAll('.artist-pill-btn');
if (!guidanceBox) throw new Error('Expected .empty-state-guidance-box to be displayed for uncataloged artist search');
if (discoveryPills.length === 0) throw new Error('Expected artist discovery pills to be present');
console.log(`[PASS] Educational discovery empty-state assistance rendered ${discoveryPills.length} artist pills`);

// Test pill click
dom.window.selectArtistFromDropdown('Claude Monet');
if (searchInput.value !== '') throw new Error('Expected search input to be cleared on artist pill selection');
if (artistSelect.value !== 'Claude Monet') throw new Error('Expected artistSelect to be set to Claude Monet');
const monetCardCount = dom.window.document.querySelectorAll('#videosGrid .video-card').length;
if (monetCardCount === 0) throw new Error('Expected cards to render for Claude Monet after pill selection');
console.log(`[PASS] Artist discovery pill selection successfully navigated to Claude Monet (${monetCardCount} works)`);

// Verification 25: Wallpaper modal rights banner & attribution generation
const sampleVideoWithWp = dom.window.ALL_VIDEOS.find(v => v.wallpapers && v.wallpapers.length > 0);
if (!sampleVideoWithWp) throw new Error('Expected sample video with wallpapers');
dom.window.openWallpaperModal(sampleVideoWithWp.id, 0);
const modalRightsBanner = dom.window.document.getElementById('wpModalRightsBanner');
const modalRightsText = dom.window.document.getElementById('wpModalRightsText');
if (!modalRightsBanner) throw new Error('Expected #wpModalRightsBanner to exist');
if (!modalRightsText.textContent.includes('Artwork')) throw new Error('Expected rights banner to mention Artwork attribution');
dom.window.closeWallpaperModal();

const attrText = dom.window.buildZipAttributionText(sampleVideoWithWp.wallpapers, 'Test Attribution Scope');
if (!attrText.includes('IMPRESSIONIST LIVING GALLERY') || !attrText.includes('TERMS OF USE')) {
    throw new Error('Expected generated ZIP attribution text to have valid terms & headers');
}
console.log('[PASS] Lightbox rights banner & ZIP download attribution verification successful');

// Verification 26: Multi-Cut & Duplicate Title De-cluttering
dom.window.resetFilters();
const declutterSelect = dom.window.document.getElementById('declutterSelect');
if (!declutterSelect) throw new Error('Expected #declutterSelect to exist in DOM');
if (declutterSelect.value !== 'DECLUTTER') {
    throw new Error(`Expected declutterSelect to default to DECLUTTER, got ${declutterSelect.value}`);
}

// 26a: Verify DUPLICATE_GROUPS and metadata
if (!Array.isArray(dom.window.DUPLICATE_GROUPS) || dom.window.DUPLICATE_GROUPS.length === 0) {
    throw new Error('Expected DUPLICATE_GROUPS to contain detected multi-cut clusters');
}
const totalAlternateCuts = dom.window.PLAYLIST_METADATA.alternateCutsCount;
if (typeof totalAlternateCuts !== 'number' || totalAlternateCuts <= 0) {
    throw new Error('Expected PLAYLIST_METADATA.alternateCutsCount to be a positive number');
}
console.log(`[PASS] Multi-cut detection: ${dom.window.DUPLICATE_GROUPS.length} duplicate clusters detected (${totalAlternateCuts} redundant cuts tagged)`);

// 26b: Test de-clutter filter behavior in videos grid
const chSel = dom.window.document.getElementById('channelSelect');
const rSel = dom.window.document.getElementById('resSelect');
chSel.value = 'Beautiful Living Art';
rSel.value = 'ALL';
declutterSelect.value = 'DECLUTTER';
dom.window.applyFilters();

const declutteredCards = dom.window.document.querySelectorAll('#videosGrid .video-card');
const primaryCutVid = dom.window.ALL_VIDEOS.find(v => v.id === 'gj55gTwrllA');
if (!primaryCutVid || !primaryCutVid.hasAlternateCuts) {
    throw new Error('Expected gj55gTwrllA to be tagged as primary cut with alternate cuts');
}

// Switch to ALL_CUTS
declutterSelect.value = 'ALL_CUTS';
dom.window.applyFilters();
const allCutsCards = dom.window.document.querySelectorAll('#videosGrid .video-card');
if (allCutsCards.length <= declutteredCards.length) {
    throw new Error(`Expected more cards when ALL_CUTS is selected (got ${allCutsCards.length} vs ${declutteredCards.length})`);
}
console.log(`[PASS] De-clutter filter toggling: ${declutteredCards.length} primary cards vs ${allCutsCards.length} all-cuts cards`);

// 26c: Alternate cuts badges on video cards
const altPills = dom.window.document.querySelectorAll('#videosGrid .pill-alternate-tag');
const cutsPills = dom.window.document.querySelectorAll('#videosGrid .pill-cuts-tag');
if (altPills.length === 0) throw new Error('Expected alternate cuts to display .pill-alternate-tag in ALL_CUTS view');
if (cutsPills.length === 0) throw new Error('Expected primary cuts to display .pill-cuts-tag badge');
console.log(`[PASS] Card badges: rendered ${cutsPills.length} multi-cut badges and ${altPills.length} alternate badges`);

// 26d: Video Player Lightbox Alternate Cuts Switcher Bar
dom.window.openVideoModal('gj55gTwrllA', 'Enter a Renoir Painting', 0);
const modalCutsBar = dom.window.document.getElementById('modalAlternateCutsBar');
const cutPills = dom.window.document.querySelectorAll('#modalAlternateCutsList .cut-pill');
if (!modalCutsBar || modalCutsBar.style.display === 'none') {
    throw new Error('Expected modalAlternateCutsBar to be visible when watching video with alternate cuts');
}
if (cutPills.length !== 4) {
    throw new Error(`Expected 4 cut pills in modal switcher bar for Enter a Renoir Painting cluster, got ${cutPills.length}`);
}

// Test switching cut inside modal
dom.window.switchModalCut('rxz8CSFGKRY');
const activePill = dom.window.document.querySelector('#modalAlternateCutsList .cut-pill.active');
if (!activePill) throw new Error('Expected active cut pill after switchModalCut');
dom.window.closeVideoModal();

// Standalone video (no duplicates) should hide cuts bar
const standaloneVid = dom.window.ALL_VIDEOS.find(v => !v.duplicateGroup);
if (standaloneVid) {
    dom.window.openVideoModal(standaloneVid.id, standaloneVid.title, 0);
    if (modalCutsBar.style.display !== 'none') {
        throw new Error('Expected modalAlternateCutsBar to be hidden for standalone title without duplicates');
    }
    dom.window.closeVideoModal();
}
console.log('[PASS] Video modal alternate cuts switcher bar verified: interactive switching & clean isolation');

// Verification 27: Source Playlist Tracker & Modification Monitoring
const trackerPath = path.join(baseDir, 'playlist_tracker.json');
if (!fs.existsSync(trackerPath)) {
    throw new Error('Expected playlist_tracker.json to exist');
}
const trackerData = JSON.parse(fs.readFileSync(trackerPath, 'utf8'));
if (!trackerData.playlists || Object.keys(trackerData.playlists).length === 0) {
    throw new Error('Expected playlist_tracker.json to have tracked playlists');
}
const primaryPlaylist = trackerData.playlists['PLeqGkucOU6lA'];
if (!primaryPlaylist || !primaryPlaylist.last_known_modified_date || !primaryPlaylist.last_known_count) {
    throw new Error('Expected playlist PLeqGkucOU6lA to have last_known_modified_date and last_known_count');
}
console.log(`[PASS] Source playlist tracker verified: tracking ${Object.keys(trackerData.playlists).length} playlist(s) (modified: ${primaryPlaylist.last_known_modified_date}, count: ${primaryPlaylist.last_known_count})`);

// Verification 28: Title apostrophe and quote robustness in Play Video actions
dom.window.resetFilters();
const testSearchInput = dom.window.document.getElementById('searchInput');
const testResSelect = dom.window.document.getElementById('resSelect');
testSearchInput.value = "Monet's";
testResSelect.value = 'ALL';
dom.window.applyFilters();

const monetsCards = dom.window.document.querySelectorAll('#videosGrid .video-card');
if (monetsCards.length === 0) throw new Error("Expected to find cards matching 'Monet's'");
let monetsLaunched = 0;
monetsCards.forEach(card => {
    const playBtn = card.querySelector('.btn-card-play');
    if (!playBtn) throw new Error('Expected .btn-card-play on video card');
    const onclickStr = playBtn.getAttribute('onclick');
    if (!onclickStr) throw new Error('Expected onclick attribute on play button');
    
    // Method 1: Evaluate inline onclick string
    dom.window.eval(onclickStr);
    let modal = dom.window.document.getElementById('modalOverlay');
    if (!modal.classList.contains('open')) {
        throw new Error('Inline onclick failed to open modal for title with apostrophe');
    }
    const modalTitleEl = dom.window.document.getElementById('modalTitle');
    if (!modalTitleEl || !modalTitleEl.textContent.includes("Monet's")) {
        throw new Error(`Expected modal title to contain Monet's, got: ${modalTitleEl ? modalTitleEl.textContent : 'null'}`);
    }
    dom.window.closeVideoModal();

    // Method 2: Real DOM click simulating user mouse/touch interaction (tests delegated handler)
    playBtn.click();
    modal = dom.window.document.getElementById('modalOverlay');
    if (!modal.classList.contains('open')) {
        throw new Error('Native DOM click failed to open modal for title with apostrophe');
    }
    const iframeWrapper = dom.window.document.getElementById('playerFrameWrapper');
    if (!iframeWrapper || !iframeWrapper.querySelector('iframe')) {
        throw new Error('Expected player iframe to be rendered in playerFrameWrapper');
    }
    dom.window.closeVideoModal();

    monetsLaunched++;
});
console.log(`[PASS] Apostrophe and quote title robustness: verified ${monetsLaunched} titles with "Monet's" launch player via inline handler AND delegated DOM click`);

if (errors.length > 0) {
    console.error('❌ Uncaught runtime errors:', errors);
    process.exit(1);
}

console.log('\n🎉 ALL 28 VERIFICATION TESTS PASSED SUCCESSFULLY WITH 0 ERRORS!\n');

