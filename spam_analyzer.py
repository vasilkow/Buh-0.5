import re


def check_spam_indicators(video_stats, description=None):
    warnings = []
    score = 0

    title = video_stats['title']

    caps_ratio = sum(1 for c in title if c.isupper()) / len(title) if title else 0
    if caps_ratio > 0.7:
        warnings.append("Слишком много ЗАГЛАВНЫХ букв в заголовке")
        score += 2

    if re.search(r'(.)\1{3,}', title):
        warnings.append("Повторяющиеся символы в заголовке")
        score += 1

    spam_words = ['бесплатно', 'hack', 'cheat', 'взлом', '100%',
                  'гарантия', 'срочно', 'шок', 'free', 'money']
    title_lower = title.lower()
    found_spam = [w for w in spam_words if w in title_lower]
    if found_spam:
        warnings.append(f"Спам-слова: {', '.join(found_spam)}")
        score += 2

    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "]+", flags=re.UNICODE
    )
    emojis = emoji_pattern.findall(title)
    if len(emojis) > 5:
        warnings.append(f"Слишком много эмодзи в заголовке ({len(emojis)})")
        score += 1

    if re.search(r'http[s]?://|www\.', title):
        warnings.append("Ссылка в заголовке")
        score += 2

    if description:
        if len(description) < 50:
            warnings.append("Слишком короткое описание")
            score += 1

        words = description.lower().split()
        word_counts = {}
        for word in words:
            if len(word) > 3:
                word_counts[word] = word_counts.get(word, 0) + 1

        repeated = [w for w, c in word_counts.items() if c > 10]
        if repeated:
            warnings.append(f"Повторы в описании: {', '.join(repeated[:3])}")
            score += 2

    return {
        'warnings': warnings,
        'score': score,
        'is_spam': score >= 5
    }


def analyze_channel_age(channel_stats):
    video_count = channel_stats.get('video_count', 0)
    subscribers = channel_stats.get('subscribers', 0)

    if video_count < 10 and subscribers < 100:
        return {
            'age_estimate': 'new',
            'message': 'Канал очень новый (<1 месяца)',
            'restriction_risk': 'high'
        }
    elif video_count < 50 and subscribers < 1000:
        return {
            'age_estimate': 'young',
            'message': 'Канал молодой (1-6 месяцев)',
            'restriction_risk': 'medium'
        }
    else:
        return {
            'age_estimate': 'established',
            'message': 'Канал зрелый (>6 месяцев)',
            'restriction_risk': 'low'
        }


def compare_with_recent_videos(channel_id, current_video_id):
    from youtube_api import get_channel_videos, get_video_stats

    recent_videos = get_channel_videos(channel_id, max_results=10)

    if len(recent_videos) < 3:
        return None

    current_stats = get_video_stats(current_video_id)
    if not current_stats:
        return None

    comparisons = []
    for video in recent_videos:
        if video['video_id'] == current_video_id:
            continue
        stats = get_video_stats(video['video_id'])
        if stats:
            comparisons.append({
                'title': stats['title'],
                'views': stats['views']
            })

    if not comparisons:
        return None

    avg_views = sum(c['views'] for c in comparisons) / len(comparisons)
    current_views = current_stats['views']
    ratio = (current_views / avg_views) if avg_views > 0 else 0

    if ratio < 0.1:
        status = 'critical'
        message = f'В 10+ раз ниже среднего ({current_views:,} vs {avg_views:,.0f})'
    elif ratio < 0.3:
        status = 'warning'
        message = f'Ниже среднего ({current_views:,} vs {avg_views:,.0f})'
    elif ratio > 3:
        status = 'viral'
        message = f'Намного выше среднего ({current_views:,} vs {avg_views:,.0f})'
    else:
        status = 'normal'
        message = f'В пределах нормы ({current_views:,} vs {avg_views:,.0f})'

    return {
        'current_views': current_views,
        'average_views': avg_views,
        'ratio': ratio,
        'status': status,
        'message': message,
        'compared_videos': len(comparisons)
    }


def check_comment_ratio(video_stats):
    views = video_stats['views']
    comments = video_stats['comments']

    if views == 0:
        return None

    ratio = (comments / views) * 100

    if ratio < 0.01:
        status = 'critical'
        message = f'Критически низкое: {ratio:.4f}%'
    elif ratio < 0.05:
        status = 'warning'
        message = f'Низкое: {ratio:.4f}%'
    elif ratio > 2:
        status = 'high_engagement'
        message = f'Высокая вовлечённость: {ratio:.2f}%'
    else:
        status = 'normal'
        message = f'Нормальное: {ratio:.4f}%'

    return {
        'ratio': ratio,
        'status': status,
        'message': message
    }


def generate_recommendations(check_results):
    recommendations = []

    for check in check_results['checks']:
        if check['status'] == 'critical':
            if check['name'] == 'Приватность':
                recommendations.append("🔒 Сделай видео публичным")
            elif check['name'] == 'Просмотры':
                recommendations.append("📢 Поделись видео в соцсетях")
            elif check['name'] == 'Соотношение просмотров':
                recommendations.append("🎯 Улучши превью и заголовок")
        elif check['status'] == 'warning':
            if check['name'] == 'Поиск YouTube':
                recommendations.append("🔍 Добавь релевантные теги")
            elif check['name'] == 'Скорость просмотров':
                recommendations.append("⏰ Публикуй в 18:00-21:00")

    if check_results['channel']['subscribers'] < 1000:
        recommendations.append("📈 Публикуй регулярно (2-3 видео в неделю)")

    if not recommendations:
        recommendations.append("✅ Всё хорошо, продолжай!")

    return recommendations
