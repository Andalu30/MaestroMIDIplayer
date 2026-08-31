from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dataset_path: Path = Path(__file__).resolve().parent.parent.parent / "MaestroDataset"
    auto_download_dataset: bool = True
    # Official MAESTRO v3.0.0 ZIP hosted by Magenta (~60 MB download).
    dataset_download_url: str = (
        "https://storage.googleapis.com/magentadata/datasets/maestro/v3.0.0/maestro-v3.0.0-midi.zip"
    )
    # 30 minutes allows slower home-network pulls of the ~60 MB archive.
    dataset_download_timeout_seconds: int = 10
    image_cache_dir: Path = Path(__file__).resolve().parent.parent / ".cache" / "composer_images"
    prefetch_images: bool = False  # Set to True to warm up image cache at startup
    host: str = "0.0.0.0"
    port: int = 8000
    uid: Optional[int] = None
    gid: Optional[int] = None
    # Set to "production" to disable /docs and /redoc
    env: str = "development"
    # Comma-separated or JSON list of allowed CORS origins.
    cors_origins: list[str] = ["https://midi.andalu30.me", "http://localhost:8000"]

    model_config = {"env_prefix": "MAESTRO_"}


settings = Settings()
