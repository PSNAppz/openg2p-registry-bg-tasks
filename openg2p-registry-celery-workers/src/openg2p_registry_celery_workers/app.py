# ruff: noqa: E402

from .config import Settings

_config = Settings.get_config()

from celery import Celery
from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_fastapi_common.exception import BaseExceptionHandler
from sqlalchemy import create_engine

from .helpers import OAuthTokenService


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().init_logger()
        super().init_app()
        BaseExceptionHandler()

        OAuthTokenService()


def get_engine():
    if _config.db_datasource:
        db_engine = create_engine(_config.db_datasource)
        db_engine_pbms = create_engine(_config.db_datasource_pbms)
        db_engine_external = create_engine(_config.db_external_datasource)
        return {
            "registry": db_engine,
            "pbms": db_engine_pbms,
            "external": db_engine_external,
        }


celery_app = Celery(
    "g2p_registry_celery_worker",
    broker=_config.celery_broker_url,
    backend=_config.celery_backend_url,
    include=["openg2p_registry_celery_workers.tasks"],
)

celery_app.conf.timezone = "UTC"
