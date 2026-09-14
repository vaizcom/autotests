import time

import pytest

from config.settings import PUBLIC_PROJECT_ID, PUBLIC_TASK_ID, PUBLIC_MILESTONE_ID, PUBLIC_DOCUMENT_ID
from api.public.public_history_endpoint import public_history_endpoint


@pytest.fixture(scope="session")
def project_id():
    return PUBLIC_PROJECT_ID


@pytest.fixture(scope="session")
def task_id():
    return PUBLIC_TASK_ID


@pytest.fixture(scope="session")
def milestone_id():
    return PUBLIC_MILESTONE_ID


@pytest.fixture(scope="session")
def document_id():
    return PUBLIC_DOCUMENT_ID


@pytest.fixture(scope="session")
def space_events(public_client, public_space_id):
    """Загружает все события спейса и возвращает отсортированный список createdAt."""
    time.sleep(1)
    resp = public_client.get(
        **public_history_endpoint(space_id=public_space_id, kind="Space", kind_id=public_space_id)
    )
    assert resp.status_code == 200, f"Не удалось загрузить события спейса: {resp.text}"
    items = resp.json()["items"]
    assert len(items) > 0, "У спейса нет событий — тесты dateRange невозможны"
    dates = sorted(item["createdAt"] for item in items)
    return dates


@pytest.fixture(scope="session")
def project_events(public_client, public_space_id):
    """Загружает все события проекта и возвращает отсортированный список createdAt."""
    time.sleep(1)
    resp = public_client.get(
        **public_history_endpoint(space_id=public_space_id, kind="Project", kind_id=PUBLIC_PROJECT_ID)
    )
    assert resp.status_code == 200, f"Не удалось загрузить события проекта: {resp.text}"
    items = resp.json()["items"]
    assert len(items) > 0, "У проекта нет событий — тесты dateRange невозможны"
    dates = sorted(item["createdAt"] for item in items)
    return dates
