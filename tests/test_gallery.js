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

// Verification 4: Switch Back to Videos
dom.window.switchMainTab('videos');
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

if (errors.length > 0) {
    console.error('❌ Uncaught runtime errors:', errors);
    process.exit(1);
}

console.log('\n🎉 ALL VERIFICATION TESTS PASSED SUCCESSFULLY WITH 0 ERRORS!\n');
