import re
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from youtube_api import (
    get_channel_stats, get_channel_by_username,
    get_video_stats
)
from database import (
    save_channel, save_video, get_video_history,
    add_monitored_video, remove_monitored_video
)
from analyzer import comprehensive_shadowban_check

router = Router()


def extract_video_id(text):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


@router.message(Command('channel'))
async def cmd_channel(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Укажи username или ID\nПример: /channel @MrBeast")
        return

    username = args[1].strip()

    if username.startswith('@'):
        channel_id = get_channel_by_username(username[1:])
    else:
        channel_id = username

    if not channel_id:
        await message.answer("❌ Канал не найден")
        return

    stats = get_channel_stats(channel_id)
    if not stats:
        await message.answer("❌ Не удалось получить статистику")
        return

    await save_channel(
        channel_id, stats['title'],
        stats['subscribers'], stats['total_views'],
        stats['video_count']
    )

    text = (
        f"📊 <b>{stats['title']}</b>\n\n"
        f"👥 Подписчики: {stats['subscribers']:,}\n"
        f"👀 Всего просмотров: {stats['total_views']:,}\n"
        f"🎬 Видео: {stats['video_count']:,}\n"
        f"🆔 ID: <code>{channel_id}</code>"
    )
    await message.answer(text, parse_mode='HTML')


@router.message(Command('video'))
async def cmd_video(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Укажи ссылку или ID\nПример: /video https://youtube.com/watch?v=...")
        return

    video_id = extract_video_id(args[1])
    if not video_id:
        await message.answer("❌ Не удалось извлечь ID видео")
        return

    stats = get_video_stats(video_id)
    if not stats:
        await message.answer("❌ Видео не найдено или приватное")
        return

    await save_video(
        video_id, stats['channel_id'], stats['title'],
        stats['views'], stats['likes'], stats['comments'],
        stats['published_at']
    )

    text = (
        f"🎬 <b>{stats['title']}</b>\n\n"
        f"👀 Просмотры: {stats['views']:,}\n"
        f"👍 Лайки: {stats['likes']:,}\n"
        f"💬 Комментарии: {stats['comments']:,}\n"
        f"📅 Опубликовано: {stats['published_at'][:10]}\n"
        f"🔒 Статус: {stats['privacy_status']}\n"
        f"🆔 ID: <code>{video_id}</code>"
    )
    await message.answer(text, parse_mode='HTML')


@router.message(Command('history'))
async def cmd_history(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Укажи ID видео\nПример: /history VIDEO_ID")
        return

    video_id = args[1].strip()
    history = await get_video_history(video_id)

    if not history:
        await message.answer(
            "❌ История не найдена. Сначала проверь через /video")
        return

    if len(history) < 2:
        await message.answer(
            "⚠️ Пока одна проверка. Проверь позже для сравнения.")
        return

    first = history[0]
    last = history[-1]

    views_diff = last['views'] - first['views']
    likes_diff = last['likes'] - first['likes']

    text = (
        f"📈 <b>Динамика</b> <code>{video_id}</code>\n\n"
        f"👀 Просмотры: {first['views']:,} → {last['views']:,} "
        f"(<b>+{views_diff:,}</b>)\n"
        f"👍 Лайки: {first['likes']:,} → {last['likes']:,} "
        f"(<b>+{likes_diff:,}</b>)\n"
        f"💬 Комментарии: {first['comments']:,} → {last['comments']:,}\n\n"
        f"📅 Первая проверка: {first['checked_at'][:10]}\n"
        f"📅 Последняя: {last['checked_at'][:10]}"
    )
    await message.answer(text, parse_mode='HTML')


@router.message(Command('check'))
async def cmd_check(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Укажи ID видео\nПример: /check VIDEO_ID")
        return

    video_id = args[1].strip()
    stats = get_video_stats(video_id)

    if not stats:
        await message.answer("❌ Видео не найдено")
        return

    warnings = []

    if stats['privacy_status'] != 'public':
        warnings.append("⚠️ Видео не публичное")
    if stats['views'] == 0:        warnings.append("⚠️ 0 просмотров — возможно, не индексируется")
    if stats.get('made_for_kids'):
        warnings.append("ℹ️ Видео 'для детей' — комментарии отключены")

    if not warnings:
        status = "✅ Явных признаков проблем не обнаружено"
    else:
        status = "⚠️ Возможные проблемы:\n" + "\n".join(warnings)

    text = (
        f"🔍 <b>Быстрая проверка</b>\n\n"
        f"🎬 {stats['title']}\n"
        f"👀 Просмотры: {stats['views']:,}\n\n"
        f"{status}\n\n"
        f"<i>Для полной проверки используй /deepcheck</i>"
    )
    await message.answer(text, parse_mode='HTML')


@router.message(Command('deepcheck'))
async def cmd_deepcheck(message: Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        await message.answer(
            "Укажи ID видео и ключевые слова через запятую\n"
            "Пример: /deepcheck VIDEO_ID ключевое1,ключевое2"
        )
        return

    video_id = args[1].strip()
    keywords = args[2].split(',') if len(args) > 2 else []
    keywords = [k.strip() for k in keywords if k.strip()]

    await message.answer("🔍 Проверяю... (10-20 секунд)")

    results = comprehensive_shadowban_check(
        video_id, keywords if keywords else None)

    if 'error' in results:
        await message.answer(f"❌ {results['error']}")
        return

    status_emoji = {
        'ok': '✅',
        'caution': '⚠️',
        'warning': '⚠️',
        'critical': '❌',
        'info': 'ℹ️',
        'normal': '✅',
        'viral': '🔥',
        'high_engagement': '🔥'
    }

    lines = [
        f"🔍 <b>Комплексная проверка</b>\n",
        f"🎬 {results['video']['title']}\n",
        f"👀 Просмотры: {results['video']['views']:,}\n",
        f"👥 Подписчики: {results['channel']['subscribers']:,}\n"
    ]

    lines.append(f"\n<b>Результаты проверок:</b>\n")

    for check in results['checks']:
        emoji = status_emoji.get(check['status'], '❓')
        lines.append(f"{emoji} <b>{check['name']}:</b> {check['message']}")

    lines.append(
        f"\n<b>Общая оценка:</b> "
        f"{status_emoji[results['overall']]} {results['overall_message']}"
    )

    if results.get('recommendations'):
        lines.append(f"\n<b>Рекомендации:</b>")
        for rec in results['recommendations']:
            lines.append(f"• {rec}")

    lines.append(
        "\n<i>Это косвенные признаки. "
        "YouTube не раскрывает информацию о теневом бане.</i>"
    )

    await message.answer('\n'.join(lines), parse_mode='HTML')


@router.message(Command('compare'))
async def cmd_compare(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Укажи ID видео через запятую\n"
            "Пример: /compare VIDEO_ID1,VIDEO_ID2,VIDEO_ID3"
        )
        return

    video_ids = [v.strip() for v in args[1].split(',')]

    if len(video_ids) < 2:
        await message.answer("Нужно минимум 2 видео для сравнения")
        return

    results = []
    for video_id in video_ids[:5]:
        stats = get_video_stats(video_id)
        if stats:
            results.append(stats)

    if not results:
        await message.answer("❌ Не удалось получить статистику")
        return

    lines = ["📊 <b>Сравнение видео</b>\n"]

    for i, stats in enumerate(results, 1):
        lines.append(
            f"<b>{i}. {stats['title']}</b>\n"
            f"👀 {stats['views']:,} | 👍 {stats['likes']:,} | "
            f"💬 {stats['comments']:,}\n"
        )

    avg_views = sum(r['views'] for r in results) / len(results)
    lines.append(f"\n📈 Среднее: {avg_views:,.0f} просмотров")

    best = max(results, key=lambda x: x['views'])
    lines.append(f"🏆 Лучшее: {best['title']} ({best['views']:,})")

    await message.answer('\n'.join(lines), parse_mode='HTML')


@router.message(Command('monitor'))
async def cmd_monitor(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Укажи ID видео\nПример: /monitor VIDEO_ID")
        return

    video_id = args[1].strip()
    chat_id = message.chat.id

    await add_monitored_video(video_id, chat_id)

    await message.answer(
        f"✅ Видео <code>{video_id}</code> добавлено в мониторинг\n"
        f"Ежедневные отчёты будут приходить в 9:00",
        parse_mode='HTML'
    )


@router.message(Command('unmonitor'))
async def cmd_unmonitor(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Укажи ID видео\nПример: /unmonitor VIDEO_ID")
        return

    video_id = args[1].strip()
    await remove_monitored_video(video_id)

    await message.answer(
        f"✅ Видео <code>{video_id}</code> убрано из мониторинга",
        parse_mode='HTML'
    )
