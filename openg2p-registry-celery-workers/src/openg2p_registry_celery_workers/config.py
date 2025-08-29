from openg2p_fastapi_common.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="registry_celery_workers_", env_file=".env", extra="allow"
    )
    openapi_title: str = "OpenG2P SR Celery Workers"
    openapi_description: str = """
        Celery workers for OpenG2P Social Registry
        ***********************************
        Further details goes here
        ***********************************
        """
    openapi_version: str = __version__

    db_dbname: str = "socialregistrydb"
    db_driver: str = "postgresql"

    db_datasource_pbms: str = (
        "postgresql://postgres:password@localhost:5432/pbmsdb"
    )
    db_external_datasource: str = (
        "postgresql://postgres:password@localhost:5432/externaldb"
    )

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_backend_url: str = "redis://localhost:6379/0"

    mosip_get_uin_url: str = (
        "https://idgenerator.loadtest.openg2p.org/v1/idgenerator/uin"
    )
    mosip_update_uin_url: str = (
        "https://idgenerator.loadtest.openg2p.org/v1/idgenerator/uin"
    )
    status_endpoint_url: str = "status_endpoint_url"

    # Keymanager auth
    sign_key_keymanager_app_id: str = ""
    sign_key_keymanager_ref_id: str = ""
    keymanager_api_base_url: str = "keymanager_api_base_url"
    keymanager_api_timeout: int = 60

    # Authentication parameters
    auth_url: str = "https://idgenerator.loadtest.openg2p.org/v1/idgenerator/token"
    auth_client_id: str = "idgenerator"
    auth_client_secret: str = "idgenerator"
    auth_grant_type: str = "client_credentials"

    worker_type_max_attempts: dict[str, int] = {
        "max_id_generation_request_attempts": 4,
        "max_id_generation_update_attempts": 4,
    }
