import json
import urllib.request
import urllib.error
from django.core.management.base import BaseCommand
from accounts.models import Video
from decouple import config
from datetime import datetime

class Command(BaseCommand):
    help = 'Fetches latest videos from YouTube channel and updates the database'

    def handle(self, *args, **options):
        api_key = config('YOUTUBE_API_KEY', default='')
        channel_id = config('YOUTUBE_CHANNEL_ID', default='')

        if not api_key or not channel_id:
            self.stderr.write(self.style.ERROR('YOUTUBE_API_KEY or YOUTUBE_CHANNEL_ID is not set in .env'))
            return

        # Determine Uploads Playlist ID
        if channel_id.startswith('UC'):
            playlist_id = 'UU' + channel_id[2:]
        else:
            playlist_id = channel_id

        max_results = 10
        url = f'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults={max_results}&playlistId={playlist_id}&key={api_key}'

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            self.stderr.write(self.style.ERROR(f'YouTube API request failed: {e}\nDetails: {error_body}'))
            return
        except urllib.error.URLError as e:
            self.stderr.write(self.style.ERROR(f'YouTube API request failed: {e}'))
            return

        items = data.get('items', [])
        count = 0
        for item in items:
            snippet = item.get('snippet', {})
            video_id = snippet.get('resourceId', {}).get('videoId')
            if not video_id:
                continue
            
            title = snippet.get('title', '')
            description = snippet.get('description', '')
            published_at = snippet.get('publishedAt')
            
            # Find best thumbnail
            thumbnails = snippet.get('thumbnails', {})
            thumbnail_url = ''
            for res in ['maxres', 'high', 'medium', 'default']:
                if res in thumbnails and 'url' in thumbnails[res]:
                    thumbnail_url = thumbnails[res]['url']
                    break

            video, created = Video.objects.update_or_create(
                id=video_id,
                defaults={
                    'title': title,
                    'description': description,
                    'thumbnail_url': thumbnail_url,
                    'published_at': published_at
                }
            )
            if created:
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Added new video: {title}'))
            else:
                self.stdout.write(f'Updated video: {title}')

        self.stdout.write(self.style.SUCCESS(f'Successfully fetched videos. {count} new videos added.'))
