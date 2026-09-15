import json
import os
import csv
import re
from collections import defaultdict, Counter
from core.playlist_engine import load_gallery_config

def normalize_exact_title(title):
    if not title:
        return ''
    t = title.strip().lower()
    t = re.sub(r'[\u2018\u2019\u201a\u201b\']', "'", t)
    t = re.sub(r'[\u201c\u201d\u201e\u201f\"]', '"', t)
    t = re.sub(r'\s*\(?(4k|hd|1080p|uhd|60fps)\)?', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def clean_canonical_title(title):
    if not title:
        return ''
    t = normalize_exact_title(title)
    t = re.sub(r'[\'\"`]', '', t)
    t = re.sub(r'\s*\|\s*(monet\s+living\s+art\s+piece|ai\s+living\s+art\s+piece|living\s+art\s+and\s+music|piece|part|episode|vol|volume|#)\s*\d+.*$', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*\|\s*warm\s+relaxing\s+.*$', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*\|\s*monet\s+inspired\s+.*$', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*\|\s*living\s+art\s+.*$', '', t, flags=re.IGNORECASE)
    t = re.sub(r'[\s\|\-]+$', '', t).strip()
    return t

def detect_duplicate_clusters(videos):
    """
    Detect duplicate title clusters and multi-length segment uploads across videos.
    Identifies primary cut (favoring 4K, longest duration, wallpapers, views)
    and tags all videos with declutterPrimary, hasAlternateCuts, and duplicateGroup.
    """
    adj = defaultdict(set)
    for i, v1 in enumerate(videos):
        t1_exact = normalize_exact_title(v1['title'])
        t1_stem = clean_canonical_title(v1['title'])
        ch1 = (v1.get('channel') or '').lower()
        for j in range(i + 1, len(videos)):
            v2 = videos[j]
            t2_exact = normalize_exact_title(v2['title'])
            t2_stem = clean_canonical_title(v2['title'])
            ch2 = (v2.get('channel') or '').lower()

            is_exact_match = (t1_exact == t2_exact and len(t1_exact) > 5)
            is_stem_match = (ch1 == ch2 and t1_stem == t2_stem and len(t1_stem) > 5)
            if is_exact_match or is_stem_match:
                adj[i].add(j)
                adj[j].add(i)

    visited = set()
    clusters = []
    for i in range(len(videos)):
        if i not in visited:
            comp = []
            stack = [i]
            visited.add(i)
            while stack:
                curr = stack.pop()
                comp.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        stack.append(neighbor)
            if len(comp) > 1:
                clusters.append([videos[idx] for idx in comp])

    cluster_summaries = []
    for c_idx, cl in enumerate(clusters, 1):
        # Sort cluster to find primary cut:
        # 1. 4K first (v['is4K'])
        # 2. Longer duration first (v['durationSec'])
        # 3. Has wallpapers first (v['wallpaperCount'])
        # 4. Highest views first (v['views'])
        cl.sort(key=lambda x: (
            1 if x.get('is4K') else 0,
            x.get('durationSec', 0),
            x.get('wallpaperCount', 0),
            x.get('views', 0)
        ), reverse=True)

        primary_cut = cl[0]
        group_id = f"cluster_{primary_cut['id']}"
        canonical_stem = clean_canonical_title(primary_cut['title'])

        cuts_summary = [
            {
                'id': c['id'],
                'title': c['title'],
                'channel': c['channel'],
                'durationSec': c['durationSec'],
                'durationFormatted': c['durationFormatted'],
                'resolution': c['resolution'],
                'qualityLabel': c['qualityLabel'],
                'is4K': c['is4K'],
                'views': c['views'],
                'wallpaperCount': c.get('wallpaperCount', 0),
                'isPrimary': (c['id'] == primary_cut['id'])
            }
            for c in cl
        ]

        cluster_summaries.append({
            'groupId': group_id,
            'canonicalStem': canonical_stem,
            'channel': primary_cut['channel'],
            'primaryVideoId': primary_cut['id'],
            'totalCuts': len(cl),
            'cuts': cuts_summary
        })

        for c in cl:
            is_primary = (c['id'] == primary_cut['id'])
            c['declutterPrimary'] = is_primary
            c['hasAlternateCuts'] = is_primary
            c['duplicateGroup'] = {
                'groupId': group_id,
                'canonicalStem': canonical_stem,
                'isPrimary': is_primary,
                'totalCuts': len(cl),
                'cuts': cuts_summary
            }
            # Update wallpapers for this video
            for wp in c.get('wallpapers', []):
                wp['declutterPrimary'] = is_primary

    # For videos that are standalone (cluster size 1):
    for v in videos:
        if 'declutterPrimary' not in v:
            v['declutterPrimary'] = True
            v['hasAlternateCuts'] = False
            v['duplicateGroup'] = None
            for wp in v.get('wallpapers', []):
                wp['declutterPrimary'] = True

    return cluster_summaries

CATALOG_ARTISTS = [
    {"name": "Claude Monet", "query": "Monet", "icon": "🎨", "era": "French Impressionism"},
    {"name": "Vincent van Gogh", "query": "Van Gogh", "icon": "🌻", "era": "Post-Impressionism"},
    {"name": "Pierre-Auguste Renoir", "query": "Renoir", "icon": "🌸", "era": "French Impressionism"},
    {"name": "Alfred Sisley", "query": "Sisley", "icon": "⛵", "era": "French Impressionism"},
    {"name": "Eugène Boudin", "query": "Boudin", "icon": "🌊", "era": "Plein-Air Pre-Impressionism"},
    {"name": "Isaac Levitan", "query": "Levitan", "icon": "🌲", "era": "Russian Mood Landscape"},
    {"name": "Gustave Loiseau", "query": "Loiseau", "icon": "🍂", "era": "Post-Impressionism"},
    {"name": "Edouard-Léon Cortès", "query": "Cortès", "altQuery": "Cortes", "icon": "🗼", "era": "Parisian Impressionism"},
    {"name": "Victor Bykov", "query": "Bykov", "icon": "🏞️", "era": "Russian Nature Impressionism"},
    {"name": "Carl Spitzweg", "query": "Spitzweg", "icon": "📜", "era": "Biedermeier / Romanticism"},
    {"name": "Charles Leickert", "query": "Leickert", "icon": "⛸️", "era": "Dutch Romantic Landscape"},
    {"name": "Johan Hendrik Weissenbruch", "query": "Weissenbruch", "icon": "🌾", "era": "Hague School"},
    {"name": "Vladimir Orlovsky", "query": "Orlovsky", "icon": "🌾", "era": "Realist / Impressionist Landscape"},
    {"name": "Antonio Parreiras", "query": "Parreiras", "icon": "🌴", "era": "Brazilian Impressionism"},
    {"name": "Walter Moras", "query": "Moras", "icon": "❄️", "era": "German Impressionist Landscape"},
    {"name": "Fritz Thaulow", "query": "Thaulow", "icon": "🌊", "era": "Norwegian Impressionism"},
    {"name": "Ivan Shishkin", "query": "Shishkin", "icon": "🌲", "era": "Russian Landscape"},
    {"name": "Peder Mørk Mønsted", "query": "Mønsted", "altQuery": "Monsted", "icon": "🏡", "era": "Danish Realism"}
]

CATALOG_THEMES = [
    {"name": "Water Lilies & Garden Sanctuaries", "query": "Water Lilies", "icon": "🪷", "synonyms": ["water lilies", "water lily", "garden", "nympheas", "giverny", "pond"]},
    {"name": "Winter & Snowbound Landscapes", "query": "Winter", "icon": "❄️", "synonyms": ["winter", "snow", "magpie", "ice", "frost"]},
    {"name": "Parisian Life & Belle Époque", "query": "Paris", "icon": "🗼", "synonyms": ["paris", "belle époque", "boulevard", "cafe", "street", "opera", "ballet", "can can", "luncheon", "match girl"]},
    {"name": "Venice & Riviera Escapes", "query": "Venice", "icon": "🎭", "synonyms": ["venice", "riviera", "canal", "san giorgio", "gondola"]},
    {"name": "Train Nostalgia & Gare Saint-Lazare", "query": "Train", "icon": "🚂", "synonyms": ["train", "locomotive", "gare", "saint-lazare", "steam", "railway"]},
    {"name": "Coastal Cliffs, Étretat & Ocean Waves", "query": "Étretat", "icon": "🌊", "synonyms": ["étretat", "coast", "ocean", "waves", "cliff", "shore", "sea", "beach", "ship", "ships", "marine"]},
    {"name": "River Seine & Waterways", "query": "Seine", "icon": "⛵", "synonyms": ["seine", "river", "boat", "argenteuil", "grenouillère", "waterside", "cabin", "lake"]},
    {"name": "Sunlit Countryside & Floral Meadows", "query": "Countryside", "icon": "🌻", "synonyms": ["country", "meadow", "floral", "blossom", "sunflower", "field", "poppy", "poppies", "haystacks", "hillside", "rose", "forest", "woodland", "trees"]},
    {"name": "Visual Poems & Living Art Canvases", "query": "Visual Poems", "icon": "🖼️", "synonyms": ["visual poem", "visual poems", "living oil", "living art", "ai impressionism"]},
    {"name": "Masterwork Retrospectives & Anthologies", "query": "Collection", "icon": "🏛️", "synonyms": ["collection of", "screensaver", "slideshow", "retrospective"]}
]

def main():
    config = load_gallery_config()
    prohibited_channels = set(config.get('prohibitedDownloadChannels', ['Living Art Moments']))
    app_meta = config.get('app', {})
    playlists_list = config.get('playlists', [])

    with open('playlist_raw.json', 'r', encoding='utf-8') as f:
        entries = json.load(f)

    # Load resolutions cache
    res_cache = {}
    if os.path.exists('video_resolutions.json'):
        try:
            with open('video_resolutions.json', 'r', encoding='utf-8') as f:
                res_cache = json.load(f)
        except:
            res_cache = {}

    channels = defaultdict(list)
    for e in entries:
        ch = e.get('channel') or e.get('uploader') or 'Unknown'
        channels[ch].append(e)

    for ch in channels:
        channels[ch].sort(key=lambda x: x.get('view_count') or 0, reverse=True)

    # Calculate stats for all channels
    channel_stats = []
    for ch, vids in channels.items():
        tot_views = sum(v.get('view_count') or 0 for v in vids)
        ch_url = vids[0].get('channel_url') or ''
        channel_stats.append({
            'channel': ch,
            'channel_url': ch_url,
            'count': len(vids),
            'total_views': tot_views,
            'avg_views': round(tot_views / len(vids)),
            'videos': vids,
            'top_video': {
                'id': vids[0].get('id'),
                'title': vids[0].get('title'),
                'views': vids[0].get('view_count') or 0,
                'url': vids[0].get('url')
            }
        })

    channel_stats.sort(key=lambda x: x['total_views'], reverse=True)

    channel_profiles = {
        'LearnFromMasters': {
            'name': 'LearnFromMasters',
            'archetype': 'The Academic & Museum Archivist',
            'icon': '🏛️',
            'accent': '#1e3d59',
            'tagline': 'Exhaustive, high-resolution monographic catalogues of master artists',
            'characterization': 'Characterized by methodical, comprehensive titles such as "[Artist Name]: A collection of [N] paintings (HD)". Rather than animating canvases, this channel functions as an open digital art museum. It provides complete, scholarly retrospectives of Claude Monet (1,540 paintings, 3.8M views), Eugène Boudin (1,163 works), Alfred Sisley (419 works), Isaac Levitan (437 works), and Gustave Loiseau (564 works). Each work is credited with title and date over quiet, reverent classical accompaniments.',
            'keyThemes': ['Monographic Catalogues', 'High Resolution Archives', 'Impressionist & Barbizon Masters', 'Complete Oeuvres'],
            'musicalTone': 'Subdued, dignified classical accompaniment designed for contemplation and study.',
            'targetAudience': 'Art history scholars, museum lovers, and collectors wanting definitive visual libraries.'
        },
        'Extraordinary Visual Art': {
            'name': 'Extraordinary Visual Art',
            'archetype': 'The Cinematic Masterpiece Immersionist',
            'icon': '🎬',
            'accent': '#5b2c6f',
            'tagline': 'Stepping inside the brushstrokes of legendary Impressionist canvases in 4K',
            'characterization': 'Characterized by high-concept narrative titles: "Living Inside Monet\'s Woman with a Parasol", "Journey to the Water Lilies", and "Living Inside Impression, Sunrise". Extraordinary Visual Art transforms iconic masterpieces into three-dimensional living environments. Using multi-plane depth modeling and 4K kinetic rendering, the camera glides through Monet’s garden paths, foggy train stations, and Renoir’s flower fields.',
            'keyThemes': ['First-Person Canvas Immersion', 'Iconic Masterpiece Deconstruction', '4K Atmospheric Motion', 'Sensory Storytelling'],
            'musicalTone': 'Expansive, cinematic orchestral and neoclassical arrangements synced with visual reveals.',
            'targetAudience': 'Lovers of high-definition visual storytelling, OLED display users, and Monet devotees.'
        },
        'Muse Visual Art': {
            'name': 'Muse Visual Art',
            'archetype': 'The Impressionist Nature & Atmospheric Sanctuary',
            'icon': '🌿',
            'accent': '#196f3d',
            'tagline': 'Meditative living landscapes celebrating flowers, mist, flowing water, and light',
            'characterization': 'The primary backbone of this playlist (75 videos, 37.7% of all items). Characterized by evocative, poetic nature titles: "Woodland Walk by Floral Scent", "Rain on Blossoms, Deep Greenery", "The Quiet Language of Waves", and "Waterside Cabin, Blooming Shores". The channel focuses on natural serenity—gentle ripples across water lily ponds, breezes through poplars, and drifting mist over French riverbanks.',
            'keyThemes': ['Water Lilies & Garden Sanctuaries', 'Seasonal Transitions', 'Gentle Wind & Water Dynamics', 'Sensory Flora Aesthetics'],
            'musicalTone': 'Gentle piano solos (Debussy & Satie inspired) seamlessly blended with natural rain, birdsong, and breeze.',
            'targetAudience': 'Daily mindfulness practitioners, study/focus sessions, stress relief, and botanical art lovers.'
        },
        'K A R O L A': {
            'name': 'K A R O L A',
            'archetype': 'The Classical Connoisseur of Regional Masters',
            'icon': '🎻',
            'accent': '#b7950b',
            'tagline': 'Curatorial tributes uncovering neglected 19th & 20th-century landscape masters',
            'characterization': 'Characterized by structured curatorial titles: "[Artist Name] ([Years]) ✽ [Country] painter ✽ [Classical Piece]". K A R O L A acts as an art-historical treasure hunter, bringing overlooked landscape masters into focus—such as Brazilian Impressionist Antonio Parreiras (1.2M views), German atmospheric painters Walter Moras and Carl Spitzweg, and Parisian night painter Edouard-Léon Cortès, strictly paired with credited classical recordings (Schumann\'s Träumerei, Ronald Binge\'s Elizabethan Serenade, Mozart).',
            'keyThemes': ['Neglected 19th-C. Masters', 'Brazilian, German, & Russian Impressionism', 'Explicit Classical Pairings', 'Academic Connoisseurship'],
            'musicalTone': 'Historically informed, named classical performances (chamber strings, piano, classical guitar).',
            'targetAudience': 'Classical music purists, European & Latin American art historians, and collectors seeking rare masters.'
        },
        'Painters Dream': {
            'name': 'Painters Dream',
            'archetype': 'The Masterwork Re-enactor & Historical Worldbuilder',
            'icon': '🎨',
            'accent': '#922b21',
            'tagline': 'Dramatic motion animations and historical reconstructions of famous scenes',
            'characterization': 'Characterized by dramatic historical reconstructions: "Arrival of the Normandy Train", "Inside Claude Monet\'s Home: The Luncheon", "The Magpie", and "La Grenouillère". Painters Dream brings the historical context of Impressionist life into motion—steaming locomotives at Gare Saint-Lazare, domestic family breakfasts, and snowbound winter fields, often experimenting with alternate-history artistic premises (e.g. "What if Claude Monet Painted Pride & Prejudice?").',
            'keyThemes': ['Gare Saint-Lazare & Train Nostalgia', 'Domestic Impressionist Life', 'Wildlife & Winter Landscapes', 'Artistic "What If" Vignettes'],
            'musicalTone': 'Evocative neoclassical soundtracks and rich period-authentic ambient sound design.',
            'targetAudience': 'Lovers of French cultural history, train/industrial revolution aesthetics, and creative AI re-imaginings.'
        },
        'Cupid Studio': {
            'name': 'Cupid Studio',
            'archetype': 'The Belle Époque Romantic Storyteller',
            'icon': '💌',
            'accent': '#a569bd',
            'tagline': 'Love stories, ballet, and romantic nostalgia woven through Impressionist canvases',
            'characterization': 'Characterized by romantic French narrative titles: "Claude Monet Painting | Winter Love in France", "Love, Ballet & Music in Paris", "Love, Opera and Can Can in Paris", and "Spring in Venice". Cupid Studio romanticizes the Impressionist era, transforming Monet and Renoir paintings into romantic journey vignettes set against Parisian theaters, Parisian cafes, Venice canals, and the Riviera.',
            'keyThemes': ['Parisian Love Stories', 'Ballet, Opera & Belle Époque Elegance', 'Venice & Riviera Escapes', 'Cozy Romantic Nostalgia'],
            'musicalTone': 'Romantic waltzes, French accordion, passionate strings, and gentle romantic melodies.',
            'targetAudience': 'Romantics, travelers dreaming of vintage Paris and Venice, and fans of cozy nostalgic storytelling.'
        },
        'Beautiful Living Art': {
            'name': 'Beautiful Living Art',
            'archetype': 'The Living Oil Painting & Visual Poet',
            'icon': '🖼️',
            'accent': '#117864',
            'tagline': 'Visual poetry and living Monet & Renoir canvas animations paired with relaxing music',
            'characterization': 'Characterized by poetic series titles: "Visual Poems", "Enter an Impressionist Painting", and "Living Oil Paintings | Dreamy French Art Aesthetic". Beautiful Living Art breathes gentle, atmospheric life into Claude Monet\'s water gardens and Pierre-Auguste Renoir\'s sunlit figures, accompanied by ambient meditative piano.',
            'keyThemes': ['Visual Poetry', 'Claude Monet & Renoir Canvas Living Art', 'Dreamy French Aesthetic', 'Atmospheric AI Motion'],
            'musicalTone': 'Warm, relaxing neoclassical and meditative piano solos.',
            'targetAudience': 'Viewers seeking gentle French Impressionist ambiance, living canvas wall art, and relaxing study accompaniment.',
            'copyrightStatus': 'Educational / Public Domain Impressionism',
            'downloadProhibited': False
        },
        'Art Revived': {
            'name': 'Art Revived',
            'archetype': 'The French Countryside & Coastal Animator',
            'icon': '🌸',
            'accent': '#d97706',
            'tagline': 'Breathtaking 4K living Impressionist journeys across Normandy, Giverny, and the Riviera',
            'characterization': 'Characterized by luminous French journeys: "A Summer in Belle Époque France", "Monet\'s South of France", "Secrets of the Seine", and "French Countryside Summer". Art Revived crafts nostalgic, deeply atmospheric living animations that bring Monet\'s cliffs of Étretat, Parisian bookstalls, and lavender fields into delicate 4K motion.',
            'keyThemes': ['Normandy & Étretat Coasts', 'Belle Époque Summer', 'Lavender & Village Landscapes', 'High-Fidelity 4K Motion'],
            'musicalTone': 'Delicate, nostalgic acoustic arrangements and serene classical melodies.',
            'targetAudience': 'Lovers of French countryside scenery, tranquil coastal motion, and Monet\'s plein-air landscapes.',
            'copyrightStatus': 'Creative Commons & Public Domain Art',
            'downloadProhibited': False
        },
        'Living Art Moments': {
            'name': 'Living Art Moments',
            'archetype': 'The 24/7 Living Stream Broadcast',
            'icon': '🐱',
            'accent': '#8b5cf6',
            'tagline': 'Continuous visual poems and living art broadcasts',
            'characterization': 'Features continuous live streaming and monet-styled visual poems with original music arrangements.',
            'keyThemes': ['Live Art Stream', 'Ambient Music Broadcast', 'Continuous Visual Poems'],
            'musicalTone': 'Continuous original ambient piano and string arrangements.',
            'targetAudience': 'Lovers of 24/7 background ambient relaxation streams.',
            'copyrightStatus': 'Copyright Reserved (View-Only)',
            'downloadProhibited': True
        }
    }

    # Load wallpapers metadata if available
    wallpapers_map = defaultdict(list)
    if os.path.exists('wallpapers/metadata.json'):
        try:
            with open('wallpapers/metadata.json', 'r', encoding='utf-8') as f:
                wp_list = json.load(f)
                for wp in wp_list:
                    if 'formFactor' not in wp:
                        wp['formFactor'] = 'mobile' if wp.get('height', 1080) > wp.get('width', 1920) else 'desktop'
                    wallpapers_map[wp['videoId']].append(wp)
        except Exception as e:
            print('Error loading wallpapers metadata:', e)

    # Sort each video's wallpapers by snapshotIndex
    for vid in wallpapers_map:
        wallpapers_map[vid].sort(key=lambda x: x.get('snapshotIndex', 0))

    # Build clean video objects with rich resolution attributes
    clean_videos = []
    count_4k = 0
    count_fhd = 0

    for idx, e in enumerate(entries, 1):
        vid = e.get('id')
        dur = e.get('duration') or 0
        m, s = divmod(int(dur), 60)
        h, m = divmod(m, 60)
        dur_str = f'{h:d}:{m:02d}:{s:02d}' if h else f'{m:02d}:{s:02d}'
        
        # Get resolution details from cache
        r_info = res_cache.get(vid, {
            'width': 1920,
            'height': 1080,
            'resolution': '1920x1080',
            'qualityLabel': '1080p FHD',
            'is4K': False
        })

        # Overwrite if we have an extracted 4K snapshot
        video_wallpapers = wallpapers_map.get(vid, [])
        if video_wallpapers:
            max_w = max(wp.get('width', 1920) for wp in video_wallpapers)
            max_h = max(wp.get('height', 1080) for wp in video_wallpapers)
            if max_w >= 3840 or max_h >= 2160:
                r_info['is4K'] = True
                r_info['qualityLabel'] = '4K UHD'
                r_info['width'] = max_w
                r_info['height'] = max_h
                r_info['resolution'] = f"{max_w}x{max_h}"

        if r_info.get('is4K'):
            count_4k += 1
        elif r_info.get('height', 1080) >= 1080:
            count_fhd += 1

        maxres_url = f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"

        channel_name = e.get('channel') or e.get('uploader') or 'Unknown'
        thumb_img = f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'
        # Replace Cupid Studio misleading thumbnails with genuine extracted Impressionist scenery
        if channel_name == 'Cupid Studio' and video_wallpapers:
            thumb_img = video_wallpapers[0]['path']

        is_prohibited = channel_name in prohibited_channels
        p_id = e.get('playlistId') or (playlists_list[0]['id'] if playlists_list else 'PLeqGkucOU6lA')
        p_title = e.get('playlistTitle') or (playlists_list[0]['title'] if playlists_list else 'sh_Monet inspired Visual Arts')
        source_pids = e.get('sourcePlaylistIds') or [p_id]

        v_title = e.get('title') or ''
        v_title_lower = v_title.lower()

        # Detect artist
        matched_artist = 'Claude Monet'
        for a in CATALOG_ARTISTS:
            q = a['query'].lower()
            alt_q = a.get('altQuery', '').lower()
            if q in v_title_lower or (alt_q and alt_q in v_title_lower):
                matched_artist = a['name']
                break
        else:
            if 'renoir' in channel_name.lower():
                matched_artist = 'Pierre-Auguste Renoir'
            elif 'van gogh' in channel_name.lower():
                matched_artist = 'Vincent van Gogh'
            elif 'monet' in channel_name.lower():
                matched_artist = 'Claude Monet'
            else:
                matched_artist = 'Impressionist Masters'

        # Detect theme
        matched_theme = 'Visual Poems & Living Art Canvases'
        for t in CATALOG_THEMES:
            if any(syn in v_title_lower for syn in t['synonyms']):
                matched_theme = t['name']
                break

        # Attach copyright and attribution directly to each extracted wallpaper snapshot
        for wp in video_wallpapers:
            wp['channel'] = channel_name
            wp['channelUrl'] = e.get('channel_url') or f"https://www.youtube.com/results?search_query={channel_name}"
            wp['copyrightStatus'] = 'Copyright Reserved (View-Only)' if is_prohibited else 'Public Domain Masterworks'
            wp['downloadProhibited'] = is_prohibited
            wp['artist'] = matched_artist
            wp['theme'] = matched_theme
            wp['videoTitle'] = v_title
            wp['videoUrl'] = e.get('url')

        clean_videos.append({
            'id': vid,
            'title': v_title,
            'channel': channel_name,
            'channelUrl': e.get('channel_url') or '',
            'views': e.get('view_count') or 0,
            'durationSec': dur,
            'durationFormatted': dur_str,
            'url': e.get('url'),
            'thumb': thumb_img,
            'maxresThumb': thumb_img if channel_name == 'Cupid Studio' else maxres_url,
            'width': r_info.get('width', 1920),
            'height': r_info.get('height', 1080),
            'resolution': r_info.get('resolution', '1920x1080'),
            'qualityLabel': r_info.get('qualityLabel', '1080p FHD'),
            'is4K': r_info.get('is4K', False),
            'wallpapers': video_wallpapers,
            'wallpaperCount': len(video_wallpapers),
            'playlistId': p_id,
            'playlistTitle': p_title,
            'sourcePlaylistIds': source_pids,
            'downloadProhibited': is_prohibited,
            'copyrightStatus': 'Copyright Reserved (View-Only)' if is_prohibited else 'Public Domain Masterworks',
            'artist': matched_artist,
            'theme': matched_theme
        })

    # Sort ALL_VIDEOS by views descending by default
    clean_videos.sort(key=lambda x: x['views'], reverse=True)

    # Detect duplicate title clusters and multi-length segment uploads
    duplicate_groups = detect_duplicate_clusters(clean_videos)
    total_duplicate_groups = len(duplicate_groups)
    alternate_cuts_count = sum(len(g['cuts']) - 1 for g in duplicate_groups)
    decluttered_videos_count = len(clean_videos) - alternate_cuts_count

    # Calculate live catalog counts for artists & themes
    computed_artists = []
    for a in CATALOG_ARTISTS:
        q = a['query'].lower()
        alt_q = a.get('altQuery', '').lower()
        matched = [v for v in clean_videos if q in v['title'].lower() or (alt_q and alt_q in v['title'].lower()) or v['artist'] == a['name']]
        computed_artists.append({
            **a,
            'count': len(matched),
            'count4K': sum(1 for v in matched if v['is4K']),
            'countFHD': sum(1 for v in matched if not v['is4K']),
            'wallpapersCount': sum(v['wallpaperCount'] for v in matched)
        })

    computed_themes = []
    for t in CATALOG_THEMES:
        matched = [v for v in clean_videos if any(syn in v['title'].lower() for syn in t['synonyms']) or v['theme'] == t['name']]
        computed_themes.append({
            **t,
            'count': len(matched),
            'count4K': sum(1 for v in matched if v['is4K']),
            'countFHD': sum(1 for v in matched if not v['is4K']),
            'wallpapersCount': sum(v['wallpaperCount'] for v in matched)
        })

    first_playlist_url = playlists_list[0]['url'] if playlists_list else 'https://www.youtube.com/playlist?list=PLeqGkucOU6lA'
    first_playlist_title = playlists_list[0]['title'] if playlists_list else 'sh_Monet inspired Visual Arts'

    # Load source playlist modification tracking metadata
    source_tracker = {}
    if os.path.exists('playlist_tracker.json'):
        try:
            with open('playlist_tracker.json', 'r', encoding='utf-8') as f:
                source_tracker = json.load(f)
        except Exception:
            pass
    first_pid = playlists_list[0]['id'] if playlists_list else 'PLeqGkucOU6lA'
    primary_tracker = source_tracker.get('playlists', {}).get(first_pid, {})
    source_mod_date = primary_tracker.get('last_known_modified_date') or '2026-09-15'
    source_sync_date = (primary_tracker.get('last_synced_at') or '2026-09-15')[:10]

    data_js = f"""// Generated Data for Monet Playlist Web Guide & 4K Wallpaper Archive
const PLAYLIST_METADATA = {{
    title: "{first_playlist_title}",
    playlistUrl: "{first_playlist_url}",
    totalVideos: {len(clean_videos)},
    totalViews: {sum(v['views'] for v in clean_videos)},
    totalDurationSec: {sum(v['durationSec'] for v in clean_videos)},
    channelCount: {len(channels)},
    totalWallpapers: {sum(v['wallpaperCount'] for v in clean_videos)},
    count4K: {count_4k},
    countFHD: {count_fhd},
    playlistCount: {len(playlists_list)},
    totalDuplicateGroups: {total_duplicate_groups},
    alternateCutsCount: {alternate_cuts_count},
    declutteredVideosCount: {decluttered_videos_count},
    sourceModifiedDate: "{source_mod_date}",
    sourceLastSynced: "{source_sync_date}"
}};

const PLAYLISTS_CONFIG = {json.dumps(playlists_list, indent=2, ensure_ascii=False)};
const DUPLICATE_GROUPS = {json.dumps(duplicate_groups, indent=2, ensure_ascii=False)};
const CHANNEL_PROFILES = {json.dumps(channel_profiles, indent=2, ensure_ascii=False)};
const CHANNEL_STATS = {json.dumps(channel_stats, indent=2, ensure_ascii=False)};
const CATALOG_ARTISTS = {json.dumps(computed_artists, indent=2, ensure_ascii=False)};
const CATALOG_THEMES = {json.dumps(computed_themes, indent=2, ensure_ascii=False)};
const ALL_VIDEOS = {json.dumps(clean_videos, indent=2, ensure_ascii=False)};

// Also attach to window for resilient cross-module and global access
if (typeof window !== 'undefined') {{
    window.PLAYLIST_METADATA = PLAYLIST_METADATA;
    window.PLAYLISTS_CONFIG = PLAYLISTS_CONFIG;
    window.DUPLICATE_GROUPS = DUPLICATE_GROUPS;
    window.CHANNEL_PROFILES = CHANNEL_PROFILES;
    window.CHANNEL_STATS = CHANNEL_STATS;
    window.CATALOG_ARTISTS = CATALOG_ARTISTS;
    window.CATALOG_THEMES = CATALOG_THEMES;
    window.ALL_VIDEOS = ALL_VIDEOS;
}}
"""

    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(data_js)

    data_payload = {
        'metadata': {
            'title': first_playlist_title,
            'playlistUrl': first_playlist_url,
            'totalVideos': len(clean_videos),
            'totalViews': sum(v['views'] for v in clean_videos),
            'totalDurationSec': sum(v['durationSec'] for v in clean_videos),
            'channelCount': len(channels),
            'totalWallpapers': sum(v['wallpaperCount'] for v in clean_videos),
            'count4K': count_4k,
            'countFHD': count_fhd,
            'playlistCount': len(playlists_list),
            'totalDuplicateGroups': total_duplicate_groups,
            'alternateCutsCount': alternate_cuts_count,
            'declutteredVideosCount': decluttered_videos_count,
            'sourceModifiedDate': source_mod_date,
            'sourceLastSynced': source_sync_date
        },
        'playlistsConfig': playlists_list,
        'duplicateGroups': duplicate_groups,
        'channelProfiles': channel_profiles,
        'channelStats': channel_stats,
        'artists': computed_artists,
        'themes': computed_themes,
        'videos': clean_videos
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data_payload, f, separators=(',', ':'), ensure_ascii=False)

    print(f'data.js and data.json updated: {len(clean_videos)} videos ({decluttered_videos_count} decluttered, {alternate_cuts_count} alternate cuts across {total_duplicate_groups} clusters), {count_4k} in 4K, {sum(v["wallpaperCount"] for v in clean_videos)} wallpapers.')

    # Update CSV with resolution columns
    with open('monet_playlist_by_channel.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Channel Name', 'Channel Total Views', 'Video Rank within Channel', 'Video Title', 'Resolution', 'Quality', 'View Count', 'Duration', 'Video URL', 'Channel URL'])
        for ch_item in channel_stats:
            for v_rank, v in enumerate(ch_item['videos'], 1):
                vid = v.get('id')
                r_info = res_cache.get(vid, {'resolution': '1920x1080', 'qualityLabel': '1080p FHD'})
                dur = v.get('duration') or 0
                m, s = divmod(int(dur), 60)
                h, m = divmod(m, 60)
                dur_str = f'{h:d}:{m:02d}:{s:02d}' if h else f'{m:02d}:{s:02d}'
                writer.writerow([
                    ch_item['channel'],
                    ch_item['total_views'],
                    v_rank,
                    v.get('title'),
                    r_info.get('resolution', '1920x1080'),
                    r_info.get('qualityLabel', '1080p FHD'),
                    v.get('view_count') or 0,
                    dur_str,
                    v.get('url'),
                    ch_item['channel_url']
                ])
    print('monet_playlist_by_channel.csv updated with resolution columns.')

if __name__ == '__main__':
    main()
