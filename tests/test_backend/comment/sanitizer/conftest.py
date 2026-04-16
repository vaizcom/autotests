import pytest

from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint, get_task_endpoint, delete_task_endpoint


@pytest.fixture(scope="module")
def document_id(owner_client, main_space, main_board):
    """
    Создаёт одну задачу на весь модуль и возвращает ID её документа.
    После прохождения всех тестов модуля задача удаляется.
    """
    create_resp = owner_client.post(
        **create_task_endpoint(
            space_id=main_space,
            board=main_board,
            name="Task for comment sanitizer tests"
        )
    )
    assert create_resp.status_code == 200, f"Ошибка создания задачи: {create_resp.text}"
    task_id = create_resp.json()["payload"]["task"]["_id"]

    task_resp = owner_client.post(**get_task_endpoint(slug_id=task_id, space_id=main_space))
    assert task_resp.status_code == 200
    doc_id = task_resp.json()["payload"]["task"]["document"]

    yield doc_id

    owner_client.post(**delete_task_endpoint(task_id=task_id, space_id=main_space))
