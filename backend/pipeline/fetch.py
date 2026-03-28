import os
import asyncio 
import httpx
from dotenv import load_dotenv
from datetime import datetime
from app.models import Video, VideoData
from .embed import get_hashtags

load_dotenv()

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
PLAYLIST_ID = os.getenv('PLAYLIST_ID')
REGION_CODE = 'US'
SEM = asyncio.Semaphore(10)


def _populate_categories() -> dict:
    """ 
    Populates categories dictionary for use later using a region code 
    """
    params = {
        'part': 'snippet',
        'regionCode': REGION_CODE,
        'key': YOUTUBE_API_KEY
    }

    endpoint = "https://www.googleapis.com/youtube/v3/videoCategories"

    response = httpx.get(endpoint, params=params)
    data = response.json()
    categories_list = data["items"]
    CATEGORIES = {

    }
    for category in categories_list:
        CATEGORIES[int(category["id"])] = category["snippet"]["title"]

    return CATEGORIES


def get_playlist_videos() -> dict[str, VideoData]:
    """ 
    Retrieves videos from a playlist and adds them to a list with incomplete data 
    """
    RETRIEVED_VIDEOS: dict[str, VideoData] = {

    }
    endpoint = "https://youtube.googleapis.com/youtube/v3/playlistItems"
    params = {
        'part': 'contentDetails, snippet',
        'playlistId': PLAYLIST_ID,
        'key': YOUTUBE_API_KEY,
        'maxResults': 50,
    }

    response = httpx.get(endpoint, params=params)
    data: dict = response.json()
    items = data["items"]
    next_token = data["nextPageToken"]

    while next_token:
        for item in items:
            video_id = item["contentDetails"]["videoId"]
            video_title = item["snippet"]["title"]
            video_channel_name = item["snippet"]["videoOwnerChannelTitle"]
            video_description = item["snippet"]["description"]
            video_published_at = item["contentDetails"]["videoPublishedAt"]
            try:
                # Sometimes the maxres thumbnail links are absent from the API response
                video_thumbnail_link = item["snippet"]["thumbnails"]["maxres"]["url"]
            except KeyError:
                video_thumbnail_link = item["snippet"]["thumbnails"]["high"]["url"]

            current_video_data = VideoData(id=video_id, title=video_title, channel_name=video_channel_name, description=video_description, published_at=video_published_at, thumbnail_link=video_thumbnail_link)

            RETRIEVED_VIDEOS[current_video_data.id] = current_video_data # str maps to VideoData object

        params["pageToken"] = next_token
        new_response = httpx.get(endpoint, params=params)
        data = new_response.json()
        items = data["items"]
        try:
            next_token = data["nextPageToken"]
        except KeyError:
            break

    return RETRIEVED_VIDEOS


async def get_videos_list(fetched_videos: dict[str, VideoData]) -> list[Video]:
    """
    Returns a list of Video objects with correctly populated data from API calls
    """
    endpoint = "https://www.googleapis.com/youtube/v3/videos"
    video_ids_list = list(fetched_videos.keys())

    PARAMS: list[dict] = _get_video_params(video_ids_list)
    VIDEOS_LIST: list[Video] = []
    CATEGORIES = _populate_categories()

    async with httpx.AsyncClient() as client:
        tasks = [get_video_data(client, endpoint, params) for params in PARAMS]
        results = await asyncio.gather(*tasks)
        for result in results:
            items: list[dict] = result['items']
            for item in items:
                video_id: str = item['id']
                video_data: VideoData = fetched_videos[video_id]
                video_data.duration = str(item['contentDetails']['duration'])
                video_data.view_count = int(item['statistics']['viewCount'])
                hashtags = get_hashtags(video_data.description) # extract hashtags if present in description
                # for description_tag in hashtags:
                #         tags.append(description_tag)
                #     video_data.tags = tags
 
                try:
                    # A video may or may not have tags
                    tags = item['snippet']['tags']
                    if hashtags != []:
                        for description_tag in hashtags:
                            tags.append(description_tag)
                    video_data.tags = tags
                except KeyError:
                    video_data.tags = [''] if hashtags == [] else hashtags

                category_id = int(item['snippet']['categoryId'])
                video_data.category = CATEGORIES[category_id]
                converted_datetime_publishedAt = datetime.strptime(video_data.published_at, "%Y-%m-%dT%H:%M:%SZ")

                VIDEOS_LIST.append(Video(id=video_data.id, title=video_data.title, channel_name=video_data.channel_name, duration=video_data.duration, description=video_data.description, published_at=converted_datetime_publishedAt, view_count=video_data.view_count, thumbnail_link=video_data.thumbnail_link, tags=video_data.tags, category=video_data.category))


        return VIDEOS_LIST


def _get_video_params(video_ids: list) -> list[dict]:
    """
    Returns a list of params given list of video ids
    """
    # 2350
    parameters: list[dict] = []
    group_size = 50
    rem: int =  bool(len(video_ids) % group_size) # 0 false, 1 true
    total_groups = (len(video_ids) // group_size) + rem
    start = 0
    end = group_size
    for i in range(total_groups):
        id_string: str = ''
        for index in range(start, end):
            if index < len(video_ids): # out of bounds check
                id_string += f'{video_ids[index]}, '
        params = {
            'part': 'contentDetails, snippet, statistics, topicDetails',
            'id': id_string[:-2].replace(' ', ''), # remove whitespace
            'key': YOUTUBE_API_KEY,
        }
        parameters.append(params)
        start = end
        end = end + group_size

    return parameters


async def get_video_data(client, url, params):
    async with SEM:
        response = await client.get(url, params=params)
    return response.json()


if __name__ == "__main__":
    async def main():
        incomplete_data = get_playlist_videos()
        complete_data = await get_videos_list(incomplete_data)
        print("All done.")
        print(len(complete_data))
    asyncio.run(main())
