import logging
from datetime import datetime
from typing import Set

from openg2p_registry_bg_tasks_models.models import (
    G2PQueBackgroundTask,
    G2PRegistryGovtEmployees,
    G2PRegistryRationCardApplicant,
    G2PRegistryVehicleOwnership,
    TaskStatus,
)
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="ration_card_applicant_worker")
def ration_card_applicant_worker(id: int):
    """
    Worker task to create ration card applicant records from existing vehicle ownership and government employee data.

    This worker combines data from G2PRegistryVehicleOwnership and G2PRegistryGovtEmployees,
    removes Aadhaar duplicates, and creates up to 10,000 records in G2PRegistryRationCardApplicant.

    Args:
        id: The G2PQueBackgroundTask ID to process
    """
    _logger.info(f"Ration Card Applicant Worker processing task id: {id}")

    registry_session_maker = sessionmaker(
        bind=_engine.get("registry"), expire_on_commit=False
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
            max_records = payload.get("max_records", 10000)  # Default to 10,000 records
            application_channel = payload.get("application_channel", "bulk_import")

            _logger.info(f"Creating up to {max_records} ration card applicant records")

            # Process and create ration card applicant records
            records_created = _create_ration_card_applicants(
                registry_session,
                max_records,
                application_channel,
            )

            # Update task status
            task_record.task_status = TaskStatus.COMPLETED
            task_record.number_of_attempts += 1
            task_record.last_attempt_error_code = None
            task_record.last_attempt_datetime = datetime.utcnow()

            # Update payload with processing info
            if task_record.worker_payload is None:
                task_record.worker_payload = {}
            task_record.worker_payload["records_created"] = records_created
            task_record.worker_payload[
                "processing_completed_date"
            ] = datetime.utcnow().isoformat()

            registry_session.commit()
            _logger.info(
                f"Successfully created {records_created} ration card applicant records"
            )

        except Exception as e:
            if task_record:
                task_record.task_status = TaskStatus.FAILED
                task_record.number_of_attempts += 1
                task_record.last_attempt_datetime = datetime.utcnow()
                task_record.last_attempt_error_code = str(e)
                registry_session.commit()
            _logger.error(
                f"Ration card applicant worker task failed for id: {id}, error: {str(e)}",
                exc_info=True,
            )
            raise


def _create_ration_card_applicants(
    registry_session,
    max_records: int,
    application_channel: str,
) -> int:
    """
    Create ration card applicant records from vehicle ownership and government employee data.

    Args:
        registry_session: Registry database session
        max_records: Maximum number of records to create
        application_channel: Application channel value for records

    Returns:
        Number of records created
    """
    records_created = 0
    processed_aadhaar: Set[str] = set()  # Track processed Aadhaar to avoid duplicates
    current_date = datetime.utcnow().date()

    _logger.info("Starting to process vehicle ownership records...")

    # Process vehicle ownership records first
    vehicle_query = (
        registry_session.query(G2PRegistryVehicleOwnership)
        .filter(
            G2PRegistryVehicleOwnership.owner_aadhaar.isnot(None),
            G2PRegistryVehicleOwnership.owner_aadhaar != "",
        )
        .order_by(G2PRegistryVehicleOwnership.owner_aadhaar)
    )

    vehicle_records = vehicle_query.all()
    _logger.info(
        f"Found {len(vehicle_records)} vehicle ownership records with valid Aadhaar"
    )

    for vehicle_record in vehicle_records:
        if records_created >= max_records:
            break

        # Skip if Aadhaar already processed
        if vehicle_record.owner_aadhaar in processed_aadhaar:
            continue

        # Use savepoint for individual record processing
        savepoint = registry_session.begin_nested()
        try:
            # Check if ration card applicant already exists for this Aadhaar
            existing_applicant = (
                registry_session.query(G2PRegistryRationCardApplicant)
                .filter_by(aadhaar_id=vehicle_record.owner_aadhaar)
                .first()
            )

            if not existing_applicant:
                # Create new ration card applicant record
                new_applicant = G2PRegistryRationCardApplicant(
                    aadhaar_id=vehicle_record.owner_aadhaar,
                    application_date=current_date,
                    unique_id=vehicle_record.unique_id,
                    individual_registry_id=vehicle_record.individual_registry_id,
                    individual_unique_id=vehicle_record.individual_unique_id,
                    family_registry_id=vehicle_record.family_registry_id,
                    family_unique_id=vehicle_record.family_unique_id,
                    verified_by=None,  # Not verified initially
                    verification_time_stamp=None,
                    application_channel=application_channel,
                )

                registry_session.add(new_applicant)
                processed_aadhaar.add(vehicle_record.owner_aadhaar)
                records_created += 1

                _logger.debug(
                    f"Created ration card applicant from vehicle record: {vehicle_record.owner_aadhaar}"
                )

            savepoint.commit()

            # Commit in batches
            if records_created % 100 == 0:
                registry_session.commit()
                _logger.info(
                    f"Committed batch, created {records_created} records so far"
                )

        except Exception as e:
            savepoint.rollback()
            _logger.error(
                f"Error processing vehicle record {vehicle_record.owner_aadhaar}: {str(e)}"
            )
            continue

    _logger.info(
        f"Completed vehicle records. Created {records_created} records so far."
    )

    # Process government employee records if we haven't reached the limit
    if records_created < max_records:
        _logger.info("Starting to process government employee records...")

        govt_emp_query = (
            registry_session.query(G2PRegistryGovtEmployees)
            .filter(
                G2PRegistryGovtEmployees.aadhaar.isnot(None),
                G2PRegistryGovtEmployees.aadhaar != "",
            )
            .order_by(G2PRegistryGovtEmployees.aadhaar)
        )

        govt_emp_records = govt_emp_query.all()
        _logger.info(
            f"Found {len(govt_emp_records)} government employee records with valid Aadhaar"
        )

        for govt_emp_record in govt_emp_records:
            if records_created >= max_records:
                break

            # Skip if Aadhaar already processed
            if govt_emp_record.aadhaar in processed_aadhaar:
                continue

            # Use savepoint for individual record processing
            savepoint = registry_session.begin_nested()
            try:
                # Check if ration card applicant already exists for this Aadhaar
                existing_applicant = (
                    registry_session.query(G2PRegistryRationCardApplicant)
                    .filter_by(aadhaar_id=govt_emp_record.aadhaar)
                    .first()
                )

                if not existing_applicant:
                    # Create new ration card applicant record
                    new_applicant = G2PRegistryRationCardApplicant(
                        aadhaar_id=govt_emp_record.aadhaar,
                        application_date=current_date,
                        unique_id=govt_emp_record.unique_id,
                        individual_registry_id=govt_emp_record.individual_registry_id,
                        individual_unique_id=govt_emp_record.individual_unique_id,
                        family_registry_id=govt_emp_record.family_registry_id,
                        family_unique_id=govt_emp_record.family_unique_id,
                        verified_by=None,  # Not verified initially
                        verification_time_stamp=None,
                        application_channel=application_channel,
                    )

                    registry_session.add(new_applicant)
                    processed_aadhaar.add(govt_emp_record.aadhaar)
                    records_created += 1

                    _logger.debug(
                        f"Created ration card applicant from govt employee record: {govt_emp_record.aadhaar}"
                    )

                savepoint.commit()

                # Commit in batches
                if records_created % 100 == 0:
                    registry_session.commit()
                    _logger.info(
                        f"Committed batch, created {records_created} records so far"
                    )

            except Exception as e:
                savepoint.rollback()
                _logger.error(
                    f"Error processing govt employee record {govt_emp_record.aadhaar}: {str(e)}"
                )
                continue

    # Final commit
    registry_session.commit()
    _logger.info(f"Final commit completed. Total records created: {records_created}")
    _logger.info(f"Processed {len(processed_aadhaar)} unique Aadhaar numbers")

    return records_created
