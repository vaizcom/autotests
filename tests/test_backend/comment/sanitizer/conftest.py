import pytest

from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint


@pytest.fixture
def document_id(owner_client, main_space, make_task_in_main):
    """
    Создаёт задачу и возвращает ID её документа для тестов комментариев.
    """
    task = make_task_in_main({"name": "Task for comment sanitizer test"})
    task_id = task["_id"]

    resp = owner_client.post(**get_task_endpoint(slug_id=task_id, space_id=main_space))
    assert resp.status_code == 200
    return resp.json()["payload"]["task"]["document"]
