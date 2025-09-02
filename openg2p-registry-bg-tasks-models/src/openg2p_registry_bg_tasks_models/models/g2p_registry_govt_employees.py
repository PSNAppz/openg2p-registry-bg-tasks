from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import BigInteger, Date, Integer, String
from sqlalchemy.orm import mapped_column


class G2PRegistryGovtEmployees(BaseORMModel):
    __tablename__ = "g2p_registry_govt_employees"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    aadhaar = mapped_column(String, nullable=False)
    government_department = mapped_column(String, nullable=True)
    unique_id = mapped_column(String, nullable=True)
    individual_registry_id = mapped_column(BigInteger, nullable=True)
    individual_unique_id = mapped_column(String, nullable=True)
    family_registry_id = mapped_column(BigInteger, nullable=True)
    family_unique_id = mapped_column(String, nullable=True)
    employee_since_date = mapped_column(Date, nullable=True)
    type_of_department = mapped_column(String, nullable=True)
    government_employee_id = mapped_column(String, nullable=True)
