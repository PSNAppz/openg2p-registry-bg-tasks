import logging
from datetime import datetime
from typing import Optional

from openg2p_registry_bg_tasks_models.models import (
    G2PQueBackgroundTask,
    G2PRegistryFamilies,
    G2PRegistryGovtEmployees,
    G2PRegistryIndividuals,
    PosidexGovtEmpsWithAadhaar,
    TaskStatus,
)
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="govt_employees_registry_worker")
def govt_employees_registry_worker(id: int):
    """
    Worker task to sync government employees data from external Posidex database to internal registry.

    Processes records from PosidexGovtEmpsWithAadhaar external table
    and creates/updates records in G2PRegistryGovtEmployees.

    Args:
        id: The G2PQueBackgroundTask ID to process
    """
    _logger.info(f"Government Employees Registry Worker processing task id: {id}")

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
            page_size = payload.get("page_size", 1000)  # Batch size
            page_offset = payload.get("page_offset", 0)  # Offset for this batch
            parent_task_id = payload.get("parent_task_id")  # ID of batching task
            batch_number = payload.get("batch_number", 1)
            total_batches = payload.get("total_batches", 1)

            _logger.info(
                f"Processing batch {batch_number}/{total_batches} with params - "
                f"page_size: {page_size}, page_offset: {page_offset}, parent_task_id: {parent_task_id}"
            )

            # Process single batch of government employees data
            records_processed = _process_govt_employees_data(
                external_session_maker,
                registry_session,
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
                f"Successfully processed {records_processed} government employee records "
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
                f"Government employees worker task failed for id: {id}, error: {str(e)}",
                exc_info=True,
            )
            raise


def _process_govt_employees_data(
    external_session_maker,
    registry_session,
    page_size: int = 100,
    page_offset: int = 0,
) -> int:
    """
    Process government employees data from external database and sync to registry.

    Args:
        external_session_maker: Session maker for external database
        registry_session: Registry database session
        page_size: Number of records to process in this batch
        page_offset: Offset for pagination

    Returns:
        Number of records processed
    """
    records_processed = 0

    with external_session_maker() as external_session:
        # Build query for government employees data with data quality filters
        query = external_session.query(PosidexGovtEmpsWithAadhaar)

        # Filter out records with poor data quality
        query = query.filter(
            PosidexGovtEmpsWithAadhaar.aadhaar_no.isnot(None),  # Exclude NULL aadhaar
            PosidexGovtEmpsWithAadhaar.aadhaar_no != '',        # Exclude empty aadhaar
        )

        # Apply ordering for consistent pagination
        query = query.order_by(PosidexGovtEmpsWithAadhaar.icdb_id)
        
        # Apply pagination
        query = query.offset(page_offset).limit(page_size)

        _logger.info(
            f"Fetching government employees records with offset {page_offset}, limit {page_size}"
        )

        # Execute query and process results
        results = query.all()

        for govt_emp_record in results:
            # Use a nested transaction for each record to handle errors gracefully
            savepoint = registry_session.begin_nested()
            try:
                # Check if government employee record already exists
                existing_record = (
                    registry_session.query(G2PRegistryGovtEmployees)
                    .filter_by(aadhaar=govt_emp_record.aadhaar_no)
                    .first()
                )

                if existing_record:
                    # Update existing record
                    _update_govt_employee_record(existing_record, govt_emp_record, registry_session)
                    _logger.debug(
                        f"Updated existing government employee record for aadhaar: {govt_emp_record.aadhaar_no}"
                    )
                else:
                    # Create new record
                    new_record = _create_govt_employee_record(govt_emp_record, registry_session)
                    registry_session.add(new_record)
                    _logger.debug(
                        f"Created new government employee record for aadhaar: {govt_emp_record.aadhaar_no}"
                    )

                # Commit the savepoint for this record
                savepoint.commit()
                records_processed += 1

                # Commit in batches to avoid large transactions
                if records_processed % 50 == 0:
                    registry_session.commit()
                    _logger.info(
                        f"Committed batch, processed {records_processed} records so far"
                    )

            except Exception as e:
                # Rollback only this record's changes
                savepoint.rollback()
                _logger.error(
                    f"Error processing government employee record {govt_emp_record.aadhaar_no}: {str(e)}"
                )
                # Continue processing other records
                continue

        # Final commit for remaining records
        registry_session.commit()
        _logger.info(f"Final commit completed for {records_processed} records")

    return records_processed


def _create_govt_employee_record(
    govt_emp_record: PosidexGovtEmpsWithAadhaar,
    registry_session,
) -> G2PRegistryGovtEmployees:
    """
    Create a new G2PRegistryGovtEmployees record from Posidex data.

    Args:
        govt_emp_record: Posidex government employee record
        registry_session: Registry database session for lookups

    Returns:
        New G2PRegistryGovtEmployees instance
    """
    # Look up individual and family data from registry views
    # If lookup fails, continue with basic employee data
    individual_data, family_data = _lookup_registry_data(registry_session, govt_emp_record.aadhaar_no)
    
    return G2PRegistryGovtEmployees(
        aadhaar=govt_emp_record.aadhaar_no,
        government_department=govt_emp_record.type_of_business,  # Can be null
        individual_registry_id=individual_data.get('id') if individual_data else None,
        individual_unique_id=individual_data.get('unique_id') if individual_data else None,
        family_registry_id=family_data.get('id') if family_data else None,
        family_unique_id=family_data.get('unique_id') if family_data else None,
        unique_id=family_data.get('unique_id') if family_data else None,  # Same as family_unique_id
        employee_since_date=None,  # Can be null as specified
        type_of_department=govt_emp_record.type_of_business,  # Can be null
        government_employee_id=govt_emp_record.identifier1,
    )


def _update_govt_employee_record(
    existing_record: G2PRegistryGovtEmployees, 
    govt_emp_record: PosidexGovtEmpsWithAadhaar,
    registry_session,
) -> None:
    """
    Update an existing G2PRegistryGovtEmployees record with Posidex data.

    Args:
        existing_record: Existing government employee record
        govt_emp_record: Posidex government employee record
        registry_session: Registry database session for lookups
    """
    # Look up individual and family data from registry views
    individual_data, family_data = _lookup_registry_data(registry_session, govt_emp_record.aadhaar_no)
    
    # Update employee-specific fields
    existing_record.government_department = govt_emp_record.type_of_business
    existing_record.type_of_department = govt_emp_record.type_of_business
    existing_record.government_employee_id = govt_emp_record.identifier1
    
    # Update registry-related fields
    existing_record.individual_registry_id = individual_data.get('id') if individual_data else None
    existing_record.individual_unique_id = individual_data.get('unique_id') if individual_data else None
    existing_record.family_registry_id = family_data.get('id') if family_data else None
    existing_record.family_unique_id = family_data.get('unique_id') if family_data else None
    existing_record.unique_id = family_data.get('unique_id') if family_data else None


def _lookup_registry_data(registry_session, aadhaar_id: Optional[str]) -> tuple[Optional[dict], Optional[dict]]:
    """
    Look up individual and family data from registry views.
    
    Args:
        registry_session: Registry database session
        aadhaar_id: Aadhaar ID to search for
        
    Returns:
        Tuple of (individual_data, family_data) dictionaries or (None, None) if not found
    """
    if not aadhaar_id:
        return None, None
        
    try:
        # Look up individual by aadhaar_id
        individual = (
            registry_session.query(G2PRegistryIndividuals)
            .filter_by(aadhaar_id=aadhaar_id)
            .first()
        )
        
        if not individual:
            _logger.debug(f"No individual found for Aadhaar: {aadhaar_id}")
            return None, None
            
        # Look up family by family_id
        family = None
        if individual.family_id:
            try:
                family = (
                    registry_session.query(G2PRegistryFamilies)
                    .filter_by(id=individual.family_id)
                    .first()
                )
            except Exception as family_lookup_error:
                _logger.warning(f"Error looking up family {individual.family_id} for Aadhaar {aadhaar_id}: {str(family_lookup_error)}")
                # Continue with individual data only
            
        individual_data = {
            'id': individual.id,
            'unique_id': individual.unique_id,
            'family_id': individual.family_id,
            'family_unique_id': individual.family_unique_id,
        }
        
        family_data = None
        if family:
            family_data = {
                'id': family.id,
                'unique_id': family.unique_id,
            }
        
        return individual_data, family_data
        
    except Exception as e:
        _logger.warning(f"Error looking up individual registry data for Aadhaar {aadhaar_id}: {str(e)}")
        return None, None
