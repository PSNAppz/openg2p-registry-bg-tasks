from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import Integer, String, PrimaryKeyConstraint
from sqlalchemy.orm import mapped_column


class PosidexGovtEmpsWithAadhaar(BaseORMModel):
    __tablename__ = "posidex_govt_emps_with_aadhaar"
    __table_args__ = (
        # Use icdb_id as primary key since it's the unique identifier
        {'schema': 'raw'}
    )

    icdb_id = mapped_column(Integer, primary_key=True)
    identifier1 = mapped_column(String, nullable=True)
    cln_name = mapped_column(String, nullable=True)
    cln_father_name = mapped_column(String, nullable=True)
    cln_address_1 = mapped_column(String, nullable=True)
    cln_phone_1 = mapped_column(String, nullable=True)
    aadhaar_no = mapped_column(String, nullable=True)
    product_flag = mapped_column(String, nullable=True)
    psx_id = mapped_column(String, nullable=True)
    type_of_business = mapped_column(String, nullable=True)
    details = mapped_column(String, nullable=True)
    data = mapped_column(String, nullable=True)
