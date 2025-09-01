from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column


class G2PRegistryFamilies(BaseORMModel):
    __tablename__ = "g2p_registry_families"

    # This is a view, so we define it as read-only
    __table_args__ = {"info": {"is_view": True}}

    id = mapped_column(Integer, primary_key=True)
    unique_id = mapped_column(String, nullable=True)
    hof_individual_id = mapped_column(Integer, nullable=True)
    hof_individual_name = mapped_column(String, nullable=True)
    hof_individual_unique_id = mapped_column(String, nullable=True)
