import aiosqlite
from datetime import datetime

DB_PATH = "youtube_stats.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                channel_id TEXT PRIMARY KEY,
                title TEXT,
                subscribers INTEGER,
                total_views INTEGER,
                video_count INTEGER,
                last_check TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                channel_id TEXT,
                title TEXT,
                views INTEGER,
                likes INTEGER,
                comments INTEGER,
                published_at TEXT,
                last_check TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stats_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                views INTEGER,
                likes INTEGER,
                comments INTEGER,
                checked_at TEXT
            )
        """)
        await db.commit()

async def save_channel(channel_id, title, subscribers, total_views, video_count):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO channels 
            (channel_id, title, subscribers, total_views, video_count, last_check)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (channel_id, title, subscribers, total_views, video_count, datetime.now().isoformat()))
        await db.commit()

async def save_video(video_id, channel_id, title, views, likes, comments, published_at):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO videos 
            (video_id, channel_id, title, views, likes, comments, published_at, last_check)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (video_id, channel_id, title, views, likes, comments, published_at, datetime.now().isoformat()))
        
        await db.execute("""
            INSERT INTO stats_history (video_id, views, likes, comments, checked_at)
            VALUES (?, ?, ?, ?, ?)
        """, (video_id, views, likes, comments, datetime.now().isoformat()))
        await db.commit()

async def get_video_history(video_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT views, likes, comments, checked_at 
            FROM stats_history 
            WHERE video_id = ? 
            ORDER BY checked_at ASC
        """, (video_id,))
        return await cursor.fetchall()

async def get_channel(channel_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM channels WHERE channel_id = ?", (channel_id,))
        return await cursor.fetchone()
