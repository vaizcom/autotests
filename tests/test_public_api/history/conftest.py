import time

import pytest

from test_public_api.data.endpoints.public_history_endpoint import public_history_endpoint

# Тестовые сущности в PUBLIC_SPACE_ID
PROJECT_ID = "6a8d60e54c09ca59fa8e847a"       # Test Project
TASK_ID = "6a8d61164c09ca59fa8ebf96"          # Test Task (TSTPRJCT-1)
MILESTONE_ID = "6a8d63164c09ca59fa913619"     # Test Milestone
DOCUMENT_ID = "6a8d61994c09ca59fa8f848a"      # Test Document


@pytest.fixture(scope="session")
def project_id():
    return PROJECT_ID


@pytest.fixture(scope="session")
def task_id():
    return TASK_ID


@pytest.fixture(scope="session")
def milestone_id():
    return MILESTONE_ID


@pytest.fixture(scope="session")
def document_id():
    return DOCUMENT_ID


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
        **public_history_endpoint(space_id=public_space_id, kind="Project", kind_id=PROJECT_ID)
    )
    assert resp.status_code == 200, f"Не удалось загрузить события проекта: {resp.text}"
    items = resp.json()["items"]
    assert len(items) > 0, "У проекта нет событий — тесты dateRange невозможны"
    dates = sorted(item["createdAt"] for item in items)
    return dates
