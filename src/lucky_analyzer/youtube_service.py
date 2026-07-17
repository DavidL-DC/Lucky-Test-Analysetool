from pathlib import Path

from .config import load_youtube_config
from .database import Database
from .models import YouTubeChannelMetrics, YouTubeVideoMetrics
from .youtube_api import YouTubeClient


class YouTubeService:
    def __init__(self, project_root: Path, database: Database):
        self.project_root = project_root
        self.database = database

    def refresh(self) -> tuple[YouTubeChannelMetrics, list[YouTubeVideoMetrics]]:
        client = YouTubeClient(load_youtube_config(self.project_root))
        channel, videos = client.fetch()
        self.database.save_youtube_metrics(channel, videos)
        return channel, videos
