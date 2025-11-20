import allure
import pytest

from tests.test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint, delete_task_endpoint
from test_backend.task_service.utils import get_client, create_task

pytestmark = [pytest.mark.backend]

@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 403),
        ('guest_client', 403),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
@allure.parent_suite("access_task")
@allure.title("Проверка удаления задачи: разрешено владельцу и менеджеру, запрещено мемберу и гостю")
def test_delete_task_access_control(request, main_space, main_board, client_fixture, expected_status, owner_client):
    """
    Быстрая проверка прав на удаление задачи:
      - owner, manager -> 200
      - member, guest  -> 403
    """
    # Создаём задачу владельцем
    payload = create_task_endpoint(space_id=main_space, board=main_board)
    create_resp = create_task(owner_client, payload)
    assert create_resp.status_code == 200, f"Не удалось создать задачу предварительно: {create_resp.text}"
    task_id = create_resp.json()["payload"]["task"]["_id"]

    try:
        client = get_client(request, client_fixture)
        with allure.step(f"Пытаемся удалить задачу под ролью: {client_fixture}"):
            del_resp = client.post(**delete_task_endpoint(space_id=main_space, task_id=task_id))
            assert del_resp.status_code == expected_status, (
                f"Ожидали {expected_status}, получили {del_resp.status_code}: {del_resp.text}"
            )
    finally:
        # Если не удалили в тесте — удаляем владельцем
        check_resp = owner_client.post(**delete_task_endpoint(space_id=main_space, task_id=task_id))
        if expected_status != 200:
            # Для негативных ролей задача должна существовать и удалиться владельцем
            assert check_resp.status_code == 200, f"Финальное удаление владельцем не удалось: {check_resp.text}"
