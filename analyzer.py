import asyncio
from datetime import datetime
from youtube_api import youtube, get_channel_stats, get_video_stats
from database import get_video_history
from spam_analyzer import (
    check_spam_indicators, analyze_channel_age,
    compare_with_recent_videos, check_comment_ratio,
    generate_recommendations
)


def check_youtube_search(video_id, keywords):
    found_positions = []

    for keyword in keywords:
        request = youtube.search().list(
            part='snippet',
            q=keyword,
            type='video',
            maxResults=50,
            order='relevance'
        )
        response = request.execute()

        for idx, item in enumerate(response['items'], 1):
            if item['id']['videoId'] == video_id:
                found_positions.append({
                    'keyword': keyword,
                    'position': idx
                })
                break

    return found_positions


def analyze_view_ratio(video_stats, channel_stats):
    if not channel_stats or channel_stats['subscribers'] == 0:
        return None

    views = video_stats['views']
    subscribers = channel_stats['subscribers']
    ratio = (views / subscribers) * 100

    if ratio < 1:
        status = 'critical'
        message = f'Критически низкое: {ratio:.2f}% (норма 10-100%)'
    elif ratio < 5:
        status = 'warning'
        message = f'Низкое: {ratio:.2f}% (норма 10-100%)'
    elif ratio > 200:
        status = 'viral'
        message = f'Вирусное: {ratio:.2f}%'
    else:
        status = 'normal'
        message = f'Нормальное: {ratio:.2f}%'

    return {
        'ratio': ratio,
        'status': status,
        'message': message
    }


def analyze_view_velocity(video_id):
    async def get_history():
        return await get_video_history(video_id)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        history = loop.run_until_complete(get_history())
    finally:
        loop.close()

    if len(history) < 2:
        return None

    first = history[0]
    last = history[-1]

    first_date = datetime.fromisoformat(first['checked_at'])
    last_date = datetime.fromisoformat(last['checked_at'])

    days_diff = max((last_date - first_date).days, 1)
    views_diff = last['views'] - first['views']
    daily_velocity = views_diff / days_diff

    return {
        'total_growth': views_diff,
        'days': days_diff,
        'daily_velocity': daily_velocity,
        'first_views': first['views'],
        'last_views': last['views']
    }


def comprehensive_shadowban_check(video_id, keywords=None):
    video_stats = get_video_stats(video_id)
    if not video_stats:
        return {'error': 'Видео не найдено'}

    channel_stats = get_channel_stats(video_stats['channel_id'])

    results = {
        'video': video_stats,
        'channel': channel_stats,
        'checks': []
    }

    # 1. Приватность
    if video_stats['privacy_status'] != 'public':
        results['checks'].append({
            'name': 'Приватность',
            'status': 'critical',
            'message': f"Не публичное: {video_stats['privacy_status']}"
        })
    else:
        results['checks'].append({
            'name': 'Приватность',
            'status': 'ok',
            'message': 'Видео публичное'
        })

    # 2. Поиск YouTube
    if keywords:
        search_results = check_youtube_search(video_id, keywords)
        if not search_results:
            results['checks'].append({
                'name': 'Поиск YouTube',
                'status': 'warning',
                'message': 'Не найдено в поиске по ключевым словам'
            })
        else:
            positions = ', '.join(
                [f"{r['keyword']} (#{r['position']})" for r in search_results])
            results['checks'].append({
                'name': 'Поиск YouTube',
                'status': 'ok',
                'message': f'Найдено: {positions}'
            })

    # 3. Соотношение просмотров
    view_ratio = analyze_view_ratio(video_stats, channel_stats)
    if view_ratio:
        results['checks'].append({
            'name': 'Соотношение просмотров',
            'status': view_ratio['status'],
            'message': view_ratio['message']
        })

    # 4. Скорость набора
    velocity = analyze_view_velocity(video_id)
    if velocity:
        if velocity['daily_velocity'] < 10 and velocity['days'] > 3:
            results['checks'].append({
                'name': 'Скорость просмотров',
                'status': 'warning',
                'message': f"{velocity['daily_velocity']:.1f} просмотров/день"
            })
        else:
            results['checks'].append({
                'name': 'Скорость просмотров',
                'status': 'ok',
                'message': f"{velocity['daily_velocity']:.1f} просмотров/день"
            })

    # 5. Для детей
    if video_stats.get('made_for_kids'):
        results['checks'].append({
            'name': 'Контент для детей',
            'status': 'info',
            'message': 'Ограниченные рекомендации'
        })

    # 6. 0 просмотров
    if video_stats['views'] == 0:
        results['checks'].append({
            'name': 'Просмотры',
            'status': 'critical',
            'message': '0 просмотров — не индексируется'
        })

    # 7. Спам-признаки
    spam_check = check_spam_indicators(video_stats)
    if spam_check['warnings']:
        results['checks'].append({
            'name': 'Спам-признаки',
            'status': 'warning' if spam_check['score'] < 5 else 'critical',
            'message': '; '.join(spam_check['warnings'])
        })
    else:
        results['checks'].append({
            'name': 'Спам-признаки',
            'status': 'ok',
            'message': 'Не обнаружено'
        })

    # 8. Возраст канала
    channel_age = analyze_channel_age(channel_stats)
    results['checks'].append({
        'name': 'Возраст канала',
        'status': 'info',
        'message': channel_age['message']
    })

    # 9. Сравнение с другими видео
    try:
        comparison = compare_with_recent_videos(
            video_stats['channel_id'], video_id)
        if comparison:
            results['checks'].append({
                'name': 'Сравнение с видео канала',
                'status': comparison['status'],
                'message': comparison['message']
            })
    except Exception:
        pass

    # 10. Вовлечённость
    comment_ratio = check_comment_ratio(video_stats)
    if comment_ratio:
        results['checks'].append({
            'name': 'Вовлечённость',
            'status': comment_ratio['status'],
            'message': comment_ratio['message']
        })

    # Общая оценка
    critical_count = sum(1 for c in results['checks'] if c['status'] == 'critical')
    warning_count = sum(1 for c in results['checks'] if c['status'] == 'warning')

    if critical_count > 0:
        results['overall'] = 'critical'
        results['overall_message'] = 'Обнаружены серьёзные проблемы'
    elif warning_count > 2:
        results['overall'] = 'warning'
        results['overall_message'] = 'Возможны проблемы с видимостью'
    elif warning_count >= 1:
        results['overall'] = 'caution'
        results['overall_message'] = 'Небольшие проблемы'
    else:
        results['overall'] = 'ok'
        results['overall_message'] = 'Явных признаков проблем не обнаружено'

    results['recommendations'] = generate_recommendations(results)

    return results
