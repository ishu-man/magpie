from sqlmodel import Session
from database import create_db_and_tables, engine
from models import Video 
from datetime import datetime


def create_videos():
    with Session(engine) as session:
        video_datetime_string = datetime.strptime("2009-10-25T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")

        example_video = Video(id="dQw4w9WgXcQ", title="Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)", channel_name="Rick Astley", duration="3:33", description="The official video for “Never Gonna Give You Up” by Rick Astley.", published_at=video_datetime_string, view_count=1753906894, thumbnail_link="https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg")

        session.add(example_video)
        session.commit()

        session.refresh(example_video)

        print("Created video:", example_video)
        print(example_video.embeddings)

def main():
    create_db_and_tables()
    create_videos()


if __name__ == "__main__":
    main()
