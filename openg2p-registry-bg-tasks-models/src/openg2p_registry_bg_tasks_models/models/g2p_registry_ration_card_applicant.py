from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import BigInteger, Date, Integer, String
from sqlalchemy.orm import mapped_column


class G2PRegistryRationCardApplicant(BaseORMModel):
    __tablename__ = "g2p_registry_ration_card_applicant"

    id = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    aadhaar_id = mapped_column(String, nullable=True)
    application_date = mapped_column(Date, nullable=True)
    unique_id = mapped_column(String, nullable=True)
    individual_registry_id = mapped_column(BigInteger, nullable=True)
    individual_unique_id = mapped_column(String, nullable=True)
    family_registry_id = mapped_column(BigInteger, nullable=True)
    family_unique_id = mapped_column(String, nullable=True)
    verified_by = mapped_column(Date, nullable=True)
    verification_time_stamp = mapped_column(String, nullable=True)
    application_channel = mapped_column(String, nullable=True)
