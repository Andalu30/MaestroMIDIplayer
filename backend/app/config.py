from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dataset_path: Path = Path(__file__).resolve().parent.parent.parent / "MaestroDataset"
    image_cache_dir: Path = Path(__file__).resolve().parent.parent / ".cache" / "composer_images"
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_prefix": "MAESTRO_"}


settings = Settings()
