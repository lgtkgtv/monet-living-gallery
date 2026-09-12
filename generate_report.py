import json
import csv
from collections import defaultdict

def main():
    with open('playlist_raw.json', 'r', encoding='utf-8') as f:
        entries = json.load(f)

    total_videos = len(entries)
    total_views = sum(v.get('view_count') or 0 for v in entries)
    total_duration_sec = sum(v.get('duration') or 0 for v in entries)
    total_hours = total_duration_sec // 3600
    total_mins = (total_duration_sec % 3600) // 60

    channels = defaultdict(list)
    for e in entries:
        ch = e.get('channel') or e.get('uploader') or 'Unknown'
        channels[ch].append(e)

    for ch in channels:
        channels[ch].sort(key=lambda x: x.get('view_count') or 0, reverse=True)

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
            'top_video': vids[0],
            'videos': vids
        })

    channel_stats.sort(key=lambda x: x['total_views'], reverse=True)
    top_overall = sorted(entries, key=lambda x: x.get('view_count') or 0, reverse=True)[:10]

    lines = []
    lines.append('# YouTube Playlist Analysis: Claude Monet Inspired Visual Arts')
    lines.append('')
    lines.append('**Playlist Link**: [sh_Monet inspired Visual Arts](https://www.youtube.com/playlist?list=PLeqGkucOU6lA)')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 1. Executive Summary & Overview Metrics')
    lines.append('')
    lines.append(f'- **Total Videos**: {total_videos}')
    lines.append(f'- **Total Cumulative Views**: {total_views:,}')
    lines.append(f'- **Total Runtime**: {total_hours} hours, {total_mins} minutes ({total_duration_sec:,} seconds)')
    lines.append(f'- **Average Video Duration**: {int((total_duration_sec / total_videos) // 60)}m {int((total_duration_sec / total_videos) % 60)}s')
    lines.append(f'- **Unique Source Channels**: {len(channel_stats)}')
    lines.append('')
    lines.append('### Key Observations & Insights')
    lines.append('1. **Curator Specialization**: The playlist curates Impressionist visual arts—chiefly Claude Monet, but also related Impressionists and landscape masters (Eugene Boudin, Alfred Sisley, Isaac Levitan, Antonio Parreiras). The visual themes blend museum anthologies with modern AI living paintings, animated ambient art, and classical music pairings (Debussy, Satie, Chopin, Beethoven).')
    lines.append('2. **The Backbone Channel (`Muse Visual Art`)**: **Muse Visual Art** provides **75 videos (37.1% of the entire playlist)**, focusing on 4K living art animations of Monet water lilies, Parisian gardens, and seasonal landscapes.')
    lines.append('3. **Viewership Leader (`LearnFromMasters`)**: Despite having 15 videos (7.4% of total), **LearnFromMasters** generated **6,221,000 views (25.5% of total playlist views)**, featuring the single most popular video in the playlist: *Claude Monet: A collection of 1540 paintings (HD)* with **3,800,000 views**.')
    lines.append('4. **Top 5 Channels by Views**: The top 5 channels by viewership (`LearnFromMasters`, `Lifting Dreams`, `Xander Corvers`, `Extraordinary Visual Art`, `Muse Visual Art`) account for **16,064,700 views (65.8% of total views)**.')
    lines.append('')
    lines.append('```mermaid')
    lines.append('pie title Total Views by Source Channel')
    for ch in channel_stats[:6]:
        ch_title = ch["channel"].replace('"', '')
        lines.append(f'    "{ch_title}" : {ch["total_views"]}')
    other_views = sum(ch["total_views"] for ch in channel_stats[6:])
    lines.append(f'    "Remaining 35 Channels" : {other_views}')
    lines.append('```')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 2. Top 10 Most Popular Videos Overall')
    lines.append('')
    lines.append('| Rank | Video Title | Source Channel | Views | Duration | Link |')
    lines.append('|:---:|:---|:---|:---:|:---:|:---:|')
    for i, v in enumerate(top_overall, 1):
        dur = v.get('duration') or 0
        m, s = divmod(int(dur), 60)
        h, m = divmod(m, 60)
        dur_str = f'{h:d}:{m:02d}:{s:02d}' if h else f'{m:02d}:{s:02d}'
        ch = v.get('channel') or v.get('uploader')
        title_clean = v.get('title', '').replace('|', '-')
        lines.append(f'| {i} | [{title_clean}]({v.get("url")}) | {ch} | {v.get("view_count", 0):,} | {dur_str} | [Watch]({v.get("url")}) |')

    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 3. Channel Breakdown Table (Sorted by Channel Popularity)')
    lines.append('')
    lines.append('| # | Source Channel | Video Count | Total Views | Avg Views/Vid | Top Video Title | Top Video Views |')
    lines.append('|:---:|:---|:---:|:---:|:---:|:---|:---:|')
    for i, ch in enumerate(channel_stats, 1):
        top_v = ch['top_video']
        top_title = top_v.get('title', '').replace('|', '-')
        lines.append(f'| {i} | [{ch["channel"]}]({ch["channel_url"]}) | {ch["count"]} | {ch["total_views"]:,} | {ch["avg_views"]:,} | [{top_title}]({top_v.get("url")}) | {top_v.get("view_count", 0):,} |')

    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 4. Complete Playlist Arranged by Channel & Popularity')
    lines.append('')
    lines.append('> Channels are ordered by total channel popularity. Inside each channel, every video is arranged in descending order of views.')
    lines.append('')

    for i, ch in enumerate(channel_stats, 1):
        lines.append(f'### {i}. [{ch["channel"]}]({ch["channel_url"]})')
        lines.append(f'- **Videos in Playlist**: {ch["count"]} | **Total Views**: {ch["total_views"]:,} | **Average Views**: {ch["avg_views"]:,}')
        lines.append('')
        lines.append('| Rank | Video Title | Views | Duration | Link |')
        lines.append('|:---:|:---|:---:|:---:|:---:|')
        for v_idx, v in enumerate(ch['videos'], 1):
            dur = v.get('duration') or 0
            m, s = divmod(int(dur), 60)
            h, m = divmod(m, 60)
            dur_str = f'{h:d}:{m:02d}:{s:02d}' if h else f'{m:02d}:{s:02d}'
            clean_title = v.get('title', '').replace('|', '-')
            lines.append(f'| {v_idx} | [{clean_title}]({v.get("url")}) | {v.get("view_count", 0):,} | {dur_str} | [Watch]({v.get("url")}) |')
        lines.append('')

    full_md = '\n'.join(lines)
    with open('monet_playlist_catalog.md', 'w', encoding='utf-8') as f:
        f.write(full_md)
    print('monet_playlist_catalog.md written successfully.')

if __name__ == '__main__':
    main()
