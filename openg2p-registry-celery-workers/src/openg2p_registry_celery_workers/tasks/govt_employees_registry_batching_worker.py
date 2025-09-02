import logging
from datetime import datetime
from typing import Optional

from openg2p_registry_bg_tasks_models.models import (
    G2PQueBackgroundTask,
    PosidexGovtEmpsWithAadhaar,
    TaskStatus,
)
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="govt_employees_registry_batching_worker")
def govt_employees_registry_batching_worker(id: int):
    """
    Batching worker that splits large government employees sync jobs into smaller batch tasks.

    This worker analyzes the total records to be processed and creates multiple
    smaller tasks for the govt_employees_registry_worker to process in parallel.

    Args:
        id: The G2PQueBackgroundTask ID to process
    """
    _logger.info(
        f"Government Employees Registry Batching Worker processing task id: {id}"
    )

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

            _logger.info(
                f"Batching Worker Task Payload JSON: {task_record.worker_payload}"
            )

            # Extract parameters from payload
            payload = task_record.worker_payload or {}
            batch_size = payload.get("batch_size", 1000)  # Records per batch
            max_records = payload.get("max_records")  # Optional limit

            _logger.info(
                f"Batching with params - batch_size: {batch_size}, max_records: {max_records}"
            )

            # Count total records to be processed
            total_records = _count_total_records(external_session_maker, max_records)

            if total_records == 0:
                _logger.info("No records found to process")
                task_record.task_status = TaskStatus.COMPLETED
                task_record.worker_payload["total_records"] = 0
                task_record.worker_payload["batches_created"] = 0
                registry_session.commit()
                return

            # Create batch tasks
            batches_created = _create_batch_tasks(
                registry_session,
                batch_size,
                total_records,
                max_records,
                task_record,
            )

            # Update task status
            task_record.task_status = TaskStatus.COMPLETED
            task_record.number_of_attempts += 1
            task_record.last_attempt_error_code = None
            task_record.last_attempt_datetime = datetime.utcnow()

            # Update payload with batching info
            if task_record.worker_payload is None:
                task_record.worker_payload = {}
            task_record.worker_payload.update(
                {
                    "total_records": total_records,
                    "batches_created": batches_created,
                    "batch_size": batch_size,
                    "batching_completed_date": datetime.utcnow().isoformat(),
                }
            )

            registry_session.commit()
            _logger.info(
                f"Successfully created {batches_created} batch tasks for {total_records} total records"
            )

        except Exception as e:
            if task_record:
                task_record.task_status = TaskStatus.FAILED
                task_record.number_of_attempts += 1
                task_record.last_attempt_datetime = datetime.utcnow()
                task_record.last_attempt_error_code = str(e)
                registry_session.commit()
            _logger.error(
                f"Batching worker task failed for id: {id}, error: {str(e)}",
                exc_info=True,
            )
            raise


def _count_total_records(
    external_session_maker,
    max_records: Optional[int] = None,
) -> int:
    """
    Count total records to be processed from external database.

    Args:
        external_session_maker: Session maker for external database
        max_records: Optional limit on total records

    Returns:
        Total number of records to process
    """
    with external_session_maker() as external_session:
        # Build count query - filter out records without aadhaar
        query = external_session.query(PosidexGovtEmpsWithAadhaar).filter(
            PosidexGovtEmpsWithAadhaar.aadhaar_no.isnot(None),
            PosidexGovtEmpsWithAadhaar.aadhaar_no != "",
        )

        # Order by icdb_id for consistent results
        query = query.order_by(PosidexGovtEmpsWithAadhaar.icdb_id)

        # Get total count
        total_count = query.count()

        # Apply max_records limit if specified
        if max_records and total_count > max_records:
            total_count = max_records

        _logger.info(f"Total records to process: {total_count}")
        return total_count


def _create_batch_tasks(
    registry_session,
    batch_size: int,
    total_records: int,
    max_records: Optional[int],
    parent_task: G2PQueBackgroundTask,
) -> int:
    """
    Create multiple batch tasks for processing.

    Args:
        registry_session: Registry database session
        batch_size: Number of records per batch
        total_records: Total records to process
        max_records: Optional limit on total records
        parent_task: The parent batching task

    Returns:
        Number of batch tasks created
    """
    batches_created = 0
    current_offset = 0

    # Calculate how many batches we need
    effective_total = min(total_records, max_records) if max_records else total_records
    total_batches = (effective_total + batch_size - 1) // batch_size  # Ceiling division

    _logger.info(f"Creating {total_batches} batch tasks with batch_size={batch_size}")

    while current_offset < effective_total:
        # Calculate remaining records for this batch
        remaining_records = effective_total - current_offset
        current_batch_size = min(batch_size, remaining_records)

        # Create batch task payload
        batch_payload = {
            "page_size": current_batch_size,
            "page_offset": current_offset,
            "parent_task_id": parent_task.id,
            "batch_number": batches_created + 1,
            "total_batches": total_batches,
        }

        # Create new background task for this batch
        batch_task = G2PQueBackgroundTask(
            worker_type="govt_employees_registry_worker",
            worker_payload=batch_payload,
            task_status=TaskStatus.PENDING,
            queued_datetime=datetime.utcnow(),
            number_of_attempts=0,
        )

        registry_session.add(batch_task)
        batches_created += 1
        current_offset += batch_size

        # Commit in smaller batches to avoid large transactions
        if batches_created % 100 == 0:
            registry_session.commit()
            _logger.info(f"Created {batches_created}/{total_batches} batch tasks")

    # Final commit
    registry_session.commit()
    _logger.info(f"Completed creating {batches_created} batch tasks")

    return batches_created
