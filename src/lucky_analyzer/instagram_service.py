from pathlib import Path

from .config import load_instagram_config
from .database import Database
from .instagram_api import InstagramClient
from .models import InstagramAccountMetrics, InstagramMediaMetrics


class InstagramService:
    def __init__(self, project_root: Path, database: Database):
        self.project_root = project_root
        self.database = database

    def refresh(self) -> tuple[InstagramAccountMetrics, list[InstagramMediaMetrics]]:
        account, media = InstagramClient(load_instagram_config(self.project_root)).fetch()
        self.database.save_instagram_metrics(account, media)
        return account, media
