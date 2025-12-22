import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint
from test_backend.task_service.utils import get_client

pytestmark = [pytest.mark.backend]

@allure.title("Тестирование получения задачи(get_task) под разными ролями с валидацией набора полей и типов")
@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 200),
        ('guest_client', 200),
        ('client_with_access_only_in_space', 400),
        ('client_with_access_only_in_project', 400),
        ('foreign_client', 403)
    ],
    ids=['owner', 'manager', 'member', 'guest','no_access_to_project', 'no_access_to_board', 'no_access_to_space'],
)
def test_get_task(request, main_space, board_with_10000_tasks, client_fixture, expected_status, main_project):
    """
    Тест проверки получения задачи под разными ролями с валидацией набора полей и типов.
    """
    allure.dynamic.title(
        f"Get task: клиент={client_fixture}, ожидаемый статус={expected_status}")

    client = get_client(request, client_fixture)
    slug_id = 'CCSS-15042'
    # to do: сделать рандом slug от getTasks
    # to do: сделать по таск Id


    with allure.step("Получение задачи"):
        response = client.post(**get_task_endpoint(space_id=main_space, slug_id=slug_id))

    # Проверяем статус ответа
    with allure.step(f"Проверка статус-кода: ожидаем {expected_status}"):
        assert response.status_code == expected_status, response.text

    # Если запрос успешен, валидируем структуру и типы
    if response.status_code == 200:
        with allure.step("Проверяем содержимое ответа с задачей"):
            body = response.json()

            # Верхний уровень ответа
            assert "payload" in body and isinstance(body["payload"], dict), "Ошибка: отсутствует/некорректен ключ 'payload'"
            assert "task" in body["payload"] and isinstance(body["payload"]["task"], dict), "Ошибка: отсутствует/некорректен ключ 'payload.task'"
            assert "type" in body and isinstance(body["type"], str), "Ошибка: отсутствует/некорректен ключ 'type'"

            task = body["payload"]["task"]

            assert_task_payload(task, board_with_10000_tasks, main_project)

    else:
        task_err = response.json()["error"]
        assert task_err['code'] in ['AccessDenied', 'NotFound']

# To Do: parentTask не равен _id; если есть subtasks — они не содержат _id текущей задачи.

