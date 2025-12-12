import allure
import pytest

from test_backend.data.endpoints.Project.assert_project_output_payload import assert_project_payload
from tests.test_backend.data.endpoints.Project.project_endpoints import (
    get_project_endpoint
)

pytestmark = [pytest.mark.backend]

@allure.title('Тест: Проверка получения проекта по ID, payload ответа соответствует ожидаемой структуре')
def test_get_project(owner_client, temp_project, temp_space):
    """
    Этот тест проверяет функциональность получения проекта по его идентификатору и идентификатору пространства.
    Он отправляет POST-запрос на эндпоинт получения проекта, используя предварительно созданные
    temp_project и temp_space.
    Затем тест проверяет:
    - Что HTTP-статус ответа равен 200.
    - Что полезная нагрузка (payload) ответа соответствует ожидаемой структуре с помощью assert_project_payload.
    - Что возвращенные ID проекта и Space ID в ответе точно совпадают с теми, что были использованы в запросе,
      гарантируя корректность полученных данных.
    """
    with allure.step(f"Отправка запроса на получение проекта с ID: {temp_project} и Space ID: {temp_space}"):
        response = owner_client.post(**get_project_endpoint(project_id=temp_project, space_id=temp_space))

    with allure.step("Проверка статуса ответа"):
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"

    with allure.step("Парсинг ответа и проверка полезной нагрузки проекта"):
        payload = response.json()['payload']
        assert_project_payload(payload)
        assert payload['project']['_id'] == temp_project, f"ID проекта в ответе '{payload['id']}' не соответствует ожидаемому '{temp_project}'"
        assert payload['project']['space'] == temp_space, f"ID пространства в ответе '{payload['space_id']}' не соответствует ожидаемому '{temp_space}'"