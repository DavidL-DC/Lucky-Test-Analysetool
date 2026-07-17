from pathlib import Path

from .config import load_tiktok_config
from .database import Database
from .models import TikTokAccountMetrics, TikTokVideoMetrics
from .tiktok_api import TikTokClient


class TikTokService:
    def __init__(self, project_root: Path, database: Database):
        self.project_root = project_root
        self.database = database

    def refresh(self) -> tuple[TikTokAccountMetrics, list[TikTokVideoMetrics]]:
        account, videos = TikTokClient(load_tiktok_config(self.project_root)).fetch()
        self.database.save_tiktok_metrics(account, videos)
        return account, videos
