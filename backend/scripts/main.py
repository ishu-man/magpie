import asyncio
from pipeline.fetch import get_playlist_videos, get_videos_list
from app.models import Video
from app.database import insert_videos_to_db, create_db_and_tables

async def get_videos():
    """ Fetches data from YouTube API and inserts that data into the database """
    incomplete_data = get_playlist_videos()
    complete_data = await get_videos_list(incomplete_data)
    return complete_data

if __name__ == "__main__":
    videos_list = asyncio.run(get_videos())
    create_db_and_tables()
    insert_videos_to_db(videos_list)
