from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import mapped_column


class G2PRegistryIndividuals(BaseORMModel):
    __tablename__ = "g2p_registry_individuals"
    
    # This is a view, so we define it as read-only
    __table_args__ = {'info': {'is_view': True}}

    id = mapped_column(Integer, primary_key=True)
    unique_id = mapped_column(String, nullable=True)
    family_id = mapped_column(Integer, nullable=True)
    family_unique_id = mapped_column(String, nullable=True)
    aadhaar_id = mapped_column(String, nullable=True)
    ration_card_id = mapped_column(String, nullable=True)
    praja_palana_id = mapped_column(String, nullable=True)
    icdb_id = mapped_column(String, nullable=True)
    name = mapped_column(String, nullable=True)
    family_name = mapped_column(String, nullable=True)
    given_name = mapped_column(String, nullable=True)
    gender = mapped_column(String, nullable=True)
    village = mapped_column(String, nullable=True)
    mandal_string = mapped_column(String, nullable=True)
    district_string = mapped_column(String, nullable=True)
    address = mapped_column(Text, nullable=True)
