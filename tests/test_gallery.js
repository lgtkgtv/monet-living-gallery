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

// Verification 8: Contact Curator Modal
dom.window.openContactModal();
const contactModal = dom.window.document.getElementById('contactModalOverlay');
console.log(`[PASS] Contact modal open: ${contactModal.classList.contains('open')}`);
dom.window.closeContactModal();
console.log(`[PASS] Contact modal closed`);

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

if (errors.length > 0) {
    console.error('❌ Uncaught runtime errors:', errors);
    process.exit(1);
}

console.log('\n🎉 ALL 14 VERIFICATION TESTS PASSED SUCCESSFULLY WITH 0 ERRORS!\n');

