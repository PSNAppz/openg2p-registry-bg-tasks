from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import Integer, String, PrimaryKeyConstraint
from sqlalchemy.orm import mapped_column


class RtaRegistration(BaseORMModel):
    __tablename__ = "rta_registration"
    __table_args__ = (
        # Composite primary key using multiple fields to handle duplicates/nulls
        # This ensures we can uniquely identify records for pagination
        PrimaryKeyConstraint('regnno', 'aadhaar', 'issuedate', name='pk_rta_registration'),
        {'schema': 'raw'}
    )

    aname = mapped_column(String, nullable=True)
    dob = mapped_column(String, nullable=True)
    pgname = mapped_column(String, nullable=True)
    # Registration number - may have duplicates and NULLs in external data
    regnno = mapped_column(String, nullable=True)
    officecode = mapped_column(String, nullable=True)
    issuedate = mapped_column(String, nullable=True)
    regn_fromdate = mapped_column(String, nullable=True)
    regn_todate = mapped_column(String, nullable=True)
    cov = mapped_column(String, nullable=True)
    engno = mapped_column(String, nullable=True)
    chsno = mapped_column(String, nullable=True)
    mkrname = mapped_column(String, nullable=True)
    mdldesc = mapped_column(String, nullable=True)
    mkyr = mapped_column(String, nullable=True)
    color = mapped_column(String, nullable=True)
    bodytype = mapped_column(String, nullable=True)
    fuel = mapped_column(String, nullable=True)
    seatcap = mapped_column(String, nullable=True)
    ownerfrom = mapped_column(String, nullable=True)
    ownerto = mapped_column(String, nullable=True)
    trno = mapped_column(String, nullable=True)
    fcvalidity = mapped_column(String, nullable=True)
    permitvalidity = mapped_column(String, nullable=True)
    insvalidity = mapped_column(String, nullable=True)
    taxvalidity = mapped_column(String, nullable=True)
    isfin = mapped_column(String, nullable=True)
    onewflag = mapped_column(String, nullable=True)
    oldregno = mapped_column(String, nullable=True)
    regstatus = mapped_column(String, nullable=True)
    susfrom = mapped_column(String, nullable=True)
    susto = mapped_column(String, nullable=True)
    statecd = mapped_column(String, nullable=True)
    vehcat = mapped_column(String, nullable=True)
    issplace = mapped_column(String, nullable=True)
    insno = mapped_column(String, nullable=True)
    inscmpy = mapped_column(String, nullable=True)
    dist = mapped_column(String, nullable=True)
    pertno = mapped_column(String, nullable=True)
    fcno = mapped_column(String, nullable=True)
    mobileno = mapped_column(String, nullable=True)
    addr = mapped_column(String, nullable=True)
    pincode = mapped_column(String, nullable=True)
    emailid = mapped_column(String, nullable=True)
    apprdt = mapped_column(String, nullable=True)
    ownerpic = mapped_column(String, nullable=True)
    aadhaar = mapped_column(String, nullable=True)
    cln_dob = mapped_column(String, nullable=True)
    cln_fcno = mapped_column(String, nullable=True)
    cln_mobile = mapped_column(String, nullable=True)
    cln_address = mapped_column(String, nullable=True)
    cln_uid = mapped_column(String, nullable=True)
    cln_aname = mapped_column(String, nullable=True)
    cln_pgname = mapped_column(String, nullable=True)
    valid_record = mapped_column(String, nullable=True)
