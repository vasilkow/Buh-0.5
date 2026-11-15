from googleapiclient.discovery import build
from config import YOUTUBE_API_KEY

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_channel_stats(channel_id):
    """Получить статистику канала"""
    request = youtube.channels().list(
        part='snippet,statistics',
        id=channel_id
    )
    response = request.execute()
    
    if not response['items']:
        return None
    
    channel = response['items'][0]
    return {
        'title': channel['snippet']['title'],
        'subscribers': int(channel['statistics'].get('subscriberCount', 0)),
        'total_views': int(channel['statistics'].get('viewCount', 0)),
        'video_count': int(channel['statistics'].get('videoCount', 0)),
        'thumbnail': channel['snippet']['thumbnails']['default']['url']
    }

def get_channel_by_username(username):
    """Найти канал по username"""
    request = youtube.search().list(
        part='snippet',
        q=username,
        type='channel',
        maxResults=1
    )
    response = request.execute()
    
    if not response['items']:
        return None
    
    return response['items'][0]['snippet']['channelId']

def get_video_stats(video_id):
    """Получить статистику видео"""
    request = youtube.videos().list(
        part='snippet,statistics,status',
        id=video_id
    )
    response = request.execute()
    
    if not response['items']:
        return None
    
    video = response['items'][0]
    return {
        'title': video['snippet']['title'],
        'channel_id': video['snippet']['channelId'],
        'views': int(video['statistics'].get('viewCount', 0)),
        'likes': int(video['statistics'].get('likeCount', 0)),
        'comments': int(video['statistics'].get('commentCount', 0)),
        'published_at': video['snippet']['publishedAt'],
        'privacy_status': video['status']['privacyStatus'],
        'made_for_kids': video['status'].get('madeForKids', False),
        'thumbnail': video['snippet']['thumbnails']['default']['url']
    }

def get_channel_videos(channel_id, max_results=10):
    """Получить последние видео канала"""
    request = youtube.search().list(
        part='snippet',
        channelId=channel_id,
        type='video',
        order='date',
        maxResults=max_results
    )
    response = request.execute()
    
    videos = []
    for item in response['items']:
        videos.append({
            'video_id': item['id']['videoId'],
            'title': item['snippet']['title'],
            'published_at': item['snippet']['publishedAt']
        })
    
    return videos

def check_video_in_search(video_id, channel_title):
    """Проверить, находится ли видео в поиске по названию канала"""
    request = youtube.search().list(
        part='snippet',
        q=channel_title,
        type='video',
        maxResults=50
    )
    response = request.execute()
    
    for item in response['items']:
        if item['id']['videoId'] == video_id:
            return True
    return False
