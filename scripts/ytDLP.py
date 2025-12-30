import asyncio
import re
import os
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import urlparse, parse_qs

def getSongExpiration(url: str) -> int | None:
    parsed = urlparse(url)

    # Case 1: Normal query string (normal video URL)
    if parsed.query:
        params = parse_qs(parsed.query)
        expire = params.get('expire') or params.get('expires')
        if expire:
            return int(expire[0])

    # Case 2: Path-based (stream URL)
    match = re.search(r'/expire/(\d+)', parsed.path)
    if match:
        return int(match.group(1))

    return None

class VideoSearcher():
    def __init__(self):
        root_dir = Path(__file__).resolve().parent.parent
        self.cookies_path = root_dir / "cookies.txt"

    async def getVideoInfoFromURL(self, video_url):
        loop = asyncio.get_running_loop()

        def extract_info():
            yt_dlp_options = {
                'format': 'bestaudio/best',
                'quiet': True,
                'noplaylist': True,
                'cookiefile': str(self.cookies_path),
                'cachedir': False,
            }
            with YoutubeDL(yt_dlp_options) as ytdlp:
                info = ytdlp.extract_info(video_url, download=False)
                return {
                    'title': re.sub(r'[^\w\s\-]', '', info.get('title', '')),
                    'duration': int(info.get('duration') or 0),  # in seconds
                    'thumbnail': info.get('thumbnail'),
                    'link': info.get('url'),
                }

        return await loop.run_in_executor(None, extract_info)
    
    async def getVideoInfoFromQuery(self, video_query):
        loop = asyncio.get_running_loop()

        def extract_info():
            yt_dlp_options = {
                'format': 'bestaudio/best',
                'quiet': True,
                'noplaylist': True,
                'cookiefile': str(self.cookies_path),
                'cachedir': False,
                'default_search': 'ytsearch',
                'max_downloads': 1
            }
            with YoutubeDL(yt_dlp_options) as ytdlp:
                info = ytdlp.extract_info(f"{video_query} lyrics", download=False)
                video = info['entries'][0] if 'entries' in info else info
                return {
                    'title': re.sub(r'[^\w\s\-]', '', video.get('title', '')),
                    'duration': int(video.get('duration') or 0),
                    'thumbnail': video.get('thumbnail'),
                    'link': video.get('url'),
                    'url': video.get('webpage_url')
                }

        return await loop.run_in_executor(None, extract_info)
    
    async def getSearchResults(self, video_query):
        loop = asyncio.get_running_loop()

        def extract_info():
            yt_dlp_options = {
                'format': 'bestaudio/best',
                'quiet': True,
                'noplaylist': True,
                'cookiefile': str(self.cookies_path),
                'cachedir': False,
                'default_search': 'ytsearch10',
                'ignoreerrors': True,
                'extract_flat': 'in_playlist',
            }
            with YoutubeDL(yt_dlp_options) as ytdlp:
                info = ytdlp.extract_info(f"{video_query} lyrics", download=False)
                entries = info['entries'] if 'entries' in info else [info]

                return [
                    {
                        'title': re.sub(r'[^\w\s\-]', '', entry.get('title', '')),
                        'link': entry.get('url'),
                    }
                    for entry in entries
                ]

        return await loop.run_in_executor(None, extract_info)
    
    async def getPlaylistInfo(self, playlist_url):
        loop = asyncio.get_running_loop()

        def extract_info():
            yt_dlp_options = {
                'format': 'bestaudio/best',
                'quiet': False,
                'extract_flat': 'in_playlist',
                'cookiefile': str(self.cookies_path),
                'cachedir': False
            }
            with YoutubeDL(yt_dlp_options) as ytdlp:
                playlist = ytdlp.extract_info(playlist_url, download=False)
                metadata = {
                    'playlist_name': re.sub(r'[^\w\s\-]', '', playlist.get('title', 'Unknown Playlist')),
                    'song_count': len(playlist.get('entries', [])),
                    'thumbnail': playlist.get('thumbnail') or (playlist.get('thumbnails', [{}])[0].get('url') if 'thumbnails' in playlist else None)
                }
                song_urls = [{'url': entry.get('url')} for entry in playlist.get('entries', []) if entry.get('url')]
                return [metadata] + song_urls

        return await loop.run_in_executor(None, extract_info)
    
    async def getVideoInfoFromPlaylist(self, playlist_url):
        loop = asyncio.get_running_loop()

        def extract_info():
            yt_dlp_options = {
                'format': 'bestaudio/best',
                'quiet': False,
                # 'extract_flat': 'in_playlist',
                'cookiefile': str(self.cookies_path),
                'cachedir': False,
                'ignoreerrors': True
            }
            with YoutubeDL(yt_dlp_options) as ytdlp:
                playlist = ytdlp.extract_info(playlist_url, download=False)
                return [{
                    'title': re.sub(r'[^\w\s\-]', '', entry.get('title', '')),
                    'duration': int(entry.get('duration') or 0),
                    'thumbnail': entry.get('thumbnail'),
                    'link': entry.get('url'),
                    'url': entry.get('webpage_url')
                } for entry in playlist.get('entries', [])
                  if entry
                ]
                

        return await loop.run_in_executor(None, extract_info)
