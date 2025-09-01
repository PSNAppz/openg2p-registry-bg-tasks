from unittest.mock import MagicMock

import pytest
from openg2p_registry_bg_tasks_models.models import G2PQueBackgroundTask, TaskStatus
from sqlalchemy.orm import Session


@pytest.fixture
def mock_session(mocker):
    session = MagicMock(spec=Session)
    session_maker = MagicMock()
    session_maker.return_value.__enter__.return_value = session

    mocker.patch("sqlalchemy.orm.sessionmaker", return_value=session_maker)
    return session


def test_example_worker(mock_session):
    from openg2p_registry_celery_workers.tasks.example_worker import (
        example_worker,
    )

    mock_task = G2PQueBackgroundTask(
        id=1,
        worker_type="TEST_WORKER",
        worker_payload={"registrant_id": 1},
        task_status=TaskStatus.PENDING,
        number_of_attempts=0,
    )
    mock_session.query.return_value.filter_by.return_value.first.return_value = (
        mock_task
    )

    example_worker(1)

    mock_session.commit.assert_called()
    assert mock_task.number_of_attempts == 1
    assert mock_task.task_status == TaskStatus.COMPLETED
