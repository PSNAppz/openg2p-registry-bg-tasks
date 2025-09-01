import logging
from datetime import datetime
from typing import Optional

from openg2p_registry_bg_tasks_models.models import (
    G2PQueBackgroundTask,
    G2PRegistryVehicleOwnership,
    RtaRegistration,
    TaskStatus,
)
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="vehicle_ownership_registry_worker")
def vehicle_ownership_registry_worker(id: int):
    """
    Worker task to sync vehicle ownership data from external RTA database to internal registry.

    Processes records from RtaRegistration external table
    and creates/updates records in G2PRegistryVehicleOwnership.

    Args:
        id: The G2PQueBackgroundTask ID to process
    """
    _logger.info(f"Vehicle Ownership Registry Worker processing task id: {id}")

    registry_session_maker = sessionmaker(
        bind=_engine.get("registry"), expire_on_commit=False
    )
    external_session_maker = sessionmaker(
        bind=_engine.get("external"), expire_on_commit=False
    )

    with registry_session_maker() as registry_session:
        task_record = None
        try:
            # Get the background task record
            task_record = (
                registry_session.query(G2PQueBackgroundTask).filter_by(id=id).first()
            )
            if not task_record:
                _logger.error(f"Background task with id {id} not found")
                return

            _logger.info(f"Worker Task Payload JSON: {task_record.worker_payload}")

            # Extract parameters from payload
            payload = task_record.worker_payload or {}
            registration_issue_date = payload.get("registration_issue_date")
            page_size = payload.get("page_size", 1000)  # Batch size
            page_offset = payload.get("page_offset", 0)  # Offset for this batch
            parent_task_id = payload.get("parent_task_id")  # ID of batching task
            batch_number = payload.get("batch_number", 1)
            total_batches = payload.get("total_batches", 1)

            _logger.info(
                f"Processing batch {batch_number}/{total_batches} with params - "
                f"issue_date: {registration_issue_date}, page_size: {page_size}, "
                f"page_offset: {page_offset}, parent_task_id: {parent_task_id}"
            )

            # Process single batch of vehicle ownership data
            records_processed = _process_vehicle_ownership_data(
                external_session_maker,
                registry_session,
                registration_issue_date,
                page_size,
                page_offset,
            )

            # Update task status
            task_record.task_status = TaskStatus.COMPLETED
            task_record.number_of_attempts += 1
            task_record.last_attempt_error_code = None
            task_record.last_attempt_datetime = datetime.utcnow()

            # Update payload with processing info
            if task_record.worker_payload is None:
                task_record.worker_payload = {}
            task_record.worker_payload["records_processed"] = records_processed
            task_record.worker_payload[
                "processing_completed_date"
            ] = datetime.utcnow().isoformat()

            registry_session.commit()
            _logger.info(
                f"Successfully processed {records_processed} vehicle ownership records "
                f"for batch {batch_number}/{total_batches} (task {id})"
            )

        except Exception as e:
            if task_record:
                task_record.task_status = TaskStatus.FAILED
                task_record.number_of_attempts += 1
                task_record.last_attempt_datetime = datetime.utcnow()
                task_record.last_attempt_error_code = str(e)
                registry_session.commit()
            _logger.error(
                f"Vehicle ownership worker task failed for id: {id}, error: {str(e)}",
                exc_info=True,
            )
            raise


def _process_vehicle_ownership_data(
    external_session_maker,
    registry_session,
    registration_issue_date: Optional[str] = None,
    page_size: int = 100,
    page_offset: int = 0,
) -> int:
    """
    Process vehicle ownership data from external database and sync to registry.

    Args:
        external_session_maker: Session maker for external database
        registry_session: Registry database session
        registration_issue_date: Filter records greater than this date (YYYY-MM-DD format)
        page_size: Number of records to process in this batch
        page_offset: Offset for pagination

    Returns:
        Number of records processed
    """
    records_processed = 0

    with external_session_maker() as external_session:
        # Build query for RTA registration data
        query = external_session.query(RtaRegistration)

        # Apply date filter if provided
        if registration_issue_date:
            # Convert string date to date format for comparison
            query = query.filter(
                text("rta_registration.issuedate > :issue_date")
            ).params(issue_date=registration_issue_date)

        # Apply ordering for consistent pagination using regnno (unique vehicle registration number)
        query = query.order_by(RtaRegistration.regnno)
        
        # Apply pagination
        query = query.offset(page_offset).limit(page_size)

        _logger.info(
            f"Fetching RTA registration records with offset {page_offset}, limit {page_size}"
        )

        # Execute query and process results
        results = query.all()

        for rta_record in results:
            try:
                # Check if vehicle ownership record already exists
                existing_record = (
                    registry_session.query(G2PRegistryVehicleOwnership)
                    .filter_by(unique_vehicle_id=rta_record.regnno)
                    .first()
                )

                if existing_record:
                    # Update existing record
                    _update_vehicle_ownership_record(existing_record, rta_record)
                    _logger.debug(
                        f"Updated existing vehicle ownership record for vehicle: {rta_record.regnno}"
                    )
                else:
                    # Create new record
                    new_record = _create_vehicle_ownership_record(rta_record)
                    registry_session.add(new_record)
                    _logger.debug(
                        f"Created new vehicle ownership record for vehicle: {rta_record.regnno}"
                    )

                records_processed += 1

                # Commit in batches to avoid large transactions
                if records_processed % 50 == 0:
                    registry_session.commit()
                    _logger.info(
                        f"Committed batch, processed {records_processed} records so far"
                    )

            except Exception as e:
                _logger.error(
                    f"Error processing vehicle record {rta_record.regnno}: {str(e)}"
                )
                # Continue processing other records
                continue

        # Final commit for remaining records
        registry_session.commit()
        _logger.info(f"Final commit completed for {records_processed} records")

    return records_processed


def _create_vehicle_ownership_record(
    rta_record: RtaRegistration,
) -> G2PRegistryVehicleOwnership:
    """
    Create a new G2PRegistryVehicleOwnership record from RTA data.

    Args:
        rta_record: RTA registration record

    Returns:
        New G2PRegistryVehicleOwnership instance
    """
    return G2PRegistryVehicleOwnership(
        unique_vehicle_id=rta_record.regnno or "",
        owner_aadhaar=rta_record.aadhaar,
        unique_id=rta_record.aadhaar,
        class_of_vehicle=rta_record.cov,
        registration_from_date=_parse_date_string(rta_record.regn_fromdate),
        registration_to_date=_parse_date_string(rta_record.regn_todate),
        engine_no=rta_record.engno,
        chassis_no=rta_record.chsno,
        manufacturer=rta_record.mkrname,
        no_of_wheels=G2PRegistryVehicleOwnership.get_wheels_for_cov(rta_record.cov),
    )


def _update_vehicle_ownership_record(
    existing_record: G2PRegistryVehicleOwnership, rta_record: RtaRegistration
) -> None:
    """
    Update an existing G2PRegistryVehicleOwnership record with RTA data.

    Args:
        existing_record: Existing vehicle ownership record
        rta_record: RTA registration record
    """
    existing_record.owner_aadhaar = rta_record.aadhaar
    existing_record.unique_id = rta_record.aadhaar
    existing_record.class_of_vehicle = rta_record.cov
    existing_record.registration_from_date = _parse_date_string(
        rta_record.regn_fromdate
    )
    existing_record.registration_to_date = _parse_date_string(rta_record.regn_todate)
    existing_record.engine_no = rta_record.engno
    existing_record.chassis_no = rta_record.chsno
    existing_record.manufacturer = rta_record.mkrname
    existing_record.no_of_wheels = G2PRegistryVehicleOwnership.get_wheels_for_cov(
        rta_record.cov
    )


def _parse_date_string(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse date string to datetime object.

    Args:
        date_str: Date string in various formats

    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not date_str:
        return None

    # Common date formats to try
    date_formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d-%b-%Y",
        "%d %b %Y",
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue

    _logger.warning(f"Could not parse date string: {date_str}")
    return None
