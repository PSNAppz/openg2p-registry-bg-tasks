from openg2p_fastapi_common.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="registry_celery_beat_", env_file=".env", extra="allow"
    )
    openapi_title: str = "OpenG2P Registry Celery Tasks"
    openapi_description: str = """
        Celery tasks for OpenG2P Registry
        ***********************************
        Further details goes here
        ***********************************
        """
    openapi_version: str = __version__

    db_dbname: str = "registrydb"
    db_driver: str = "postgresql"

    db_datasource_pbms: str = "postgresql://postgres:password@localhost:5432/pbmsdb"

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_backend_url: str = "redis://localhost:6379/0"

    payment_status_check_interval: int = 2
    producer_frequency: int = 40
    worker_type_max_attempts: dict[str, int] = {
        "max_id_generation_request_attempts": 4,
        "max_id_generation_update_attempts": 4,
    }
    batch_size: int = 10000
