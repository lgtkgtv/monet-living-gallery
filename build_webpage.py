import json
import os
import csv
from collections import defaultdict

def main():
    with open('playlist_raw.json', 'r', encoding='utf-8') as f:
        entries = json.load(f)

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
        }
    }

    # Load wallpapers metadata if available
    wallpapers_map = defaultdict(list)
    if os.path.exists('wallpapers/metadata.json'):
        try:
            with open('wallpapers/metadata.json', 'r', encoding='utf-8') as f:
                wp_list = json.load(f)
                for wp in wp_list:
                    wallpapers_map[wp['videoId']].append(wp)
        except Exception as e:
            print('Error loading wallpapers metadata:', e)

    # Build clean video objects
    clean_videos = []
    for idx, e in enumerate(entries, 1):
        vid = e.get('id')
        dur = e.get('duration') or 0
        m, s = divmod(int(dur), 60)
        h, m = divmod(m, 60)
        dur_str = f'{h:d}:{m:02d}:{s:02d}' if h else f'{m:02d}:{s:02d}'
        
        # Associated wallpapers: local extractions + maxres fallback
        video_wallpapers = wallpapers_map.get(vid, [])
        maxres_url = f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"

        clean_videos.append({
            'id': vid,
            'title': e.get('title'),
            'channel': e.get('channel') or e.get('uploader') or 'Unknown',
            'channelUrl': e.get('channel_url') or '',
            'views': e.get('view_count') or 0,
            'durationSec': dur,
            'durationFormatted': dur_str,
            'url': e.get('url'),
            'thumb': f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg',
            'maxresThumb': maxres_url,
            'wallpapers': video_wallpapers,
            'wallpaperCount': len(video_wallpapers)
        })

    # Sort ALL_VIDEOS by views descending by default
    clean_videos.sort(key=lambda x: x['views'], reverse=True)

    data_js = f"""// Generated Data for Monet Playlist Web Guide & Wallpaper Gallery
const PLAYLIST_METADATA = {{
    title: "sh_Monet inspired Visual Arts",
    playlistUrl: "https://www.youtube.com/playlist?list=PLeqGkucOU6lA",
    totalVideos: {len(clean_videos)},
    totalViews: {sum(v['views'] for v in clean_videos)},
    totalDurationSec: {sum(v['durationSec'] for v in clean_videos)},
    channelCount: {len(channels)},
    totalWallpapers: {sum(v['wallpaperCount'] for v in clean_videos)}
}};

const CHANNEL_PROFILES = {json.dumps(channel_profiles, indent=2, ensure_ascii=False)};
const CHANNEL_STATS = {json.dumps(channel_stats, indent=2, ensure_ascii=False)};
const ALL_VIDEOS = {json.dumps(clean_videos, indent=2, ensure_ascii=False)};
"""

    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(data_js)
    print('data.js updated with 199 videos and wallpaper links.')

    # Update CSV
    with open('monet_playlist_by_channel.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Channel Name', 'Channel Total Views', 'Video Rank within Channel', 'Video Title', 'View Count', 'Duration (formatted)', 'Video URL', 'Channel URL'])
        for ch_item in channel_stats:
            for v_rank, v in enumerate(ch_item['videos'], 1):
                dur = v.get('duration') or 0
                m, s = divmod(int(dur), 60)
                h, m = divmod(m, 60)
                dur_str = f'{h:d}:{m:02d}:{s:02d}' if h else f'{m:02d}:{s:02d}'
                writer.writerow([
                    ch_item['channel'],
                    ch_item['total_views'],
                    v_rank,
                    v.get('title'),
                    v.get('view_count') or 0,
                    dur_str,
                    v.get('url'),
                    ch_item['channel_url']
                ])
    print('monet_playlist_by_channel.csv updated.')

if __name__ == '__main__':
    main()
