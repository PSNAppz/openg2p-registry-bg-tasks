from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import mapped_column


class G2PRegistryGovtEmployees(BaseORMModel):
    __tablename__ = "g2p_registry_govt_employees"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_aadhaar = mapped_column(String, nullable=False)
    is_govt_employee = mapped_column(Boolean, nullable=False)
    unique_id = mapped_column(String, nullable=True)
