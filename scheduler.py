import asyncio
from datetime import datetime, timedelta, time
from youtube_api import get_video_stats
from database import save_video, get_monitored_videos
from aiogram import Bot


async def daily_monitoring(bot: Bot):
    monitored = await get_monitored_videos()

    if not monitored:
        return

    chat_ids = set()
    video_ids = set()

    for row in monitored:
        chat_ids.add(row['chat_id'])
        video_ids.add(row['video_id'])

    for video_id in video_ids:
        try:
            stats = get_video_stats(video_id)
            if stats:
                await save_video(
                    video_id, stats['channel_id'], stats['title'],
                    stats['views'], stats['likes'], stats['comments'],
                    stats['published_at']
                )

                text = (
                    f"📊 <b>Ежедневный отчёт</b>\n\n"
                    f"🎬 {stats['title']}\n"
                    f"👀 Просмотры: {stats['views']:,}\n"
                    f"👍 Лайки: {stats['likes']:,}\n"
                    f"💬 Комментарии: {stats['comments']:,}\n"
                    f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )

                for chat_id in chat_ids:
                    try:
                        await bot.send_message(chat_id, text, parse_mode='HTML')
                    except Exception:
                        pass
        except Exception:
            pass


async def start_scheduler(bot: Bot):
    while True:
        now = datetime.now()
        target = datetime.combine(now.date(), time(9, 0))

        if now > target:
            target = datetime.combine(
                now.date() + timedelta(days=1), time(9, 0))

        await asyncio.sleep((target - now).total_seconds())

        try:
            await daily_monitoring(bot)
        except Exception:
            pass
