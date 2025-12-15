import allure
import pytest

from test_backend.data.endpoints.Project.assert_project_output_payload import assert_project_payload
from tests.test_backend.data.endpoints.Project.project_endpoints import (
    get_project_endpoint
)

pytestmark = [pytest.mark.backend]


@allure.title('Тест: Проверка получения проекта по ID, payload ответа соответствует ожидаемой структуре')
def test_get_project(owner_client, temp_project, temp_space):
    with allure.step(f"Отправка запроса на получение проекта ID: {temp_project} для пространства ID: {temp_space}"):
        response = owner_client.post(**get_project_endpoint(project_id=temp_project, space_id=temp_space))

    with allure.step("Проверка статуса ответа и общей структуры ответа"):
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        payload = response.json()['payload']
        assert 'project' in payload, "Ответ не содержит ключ 'project'"
        assert isinstance(payload['project'], dict), "Значение 'project' не является словарем"

    project = payload['project']

    with allure.step(f"Проверка, что полученный проект соответствует ожидаемому"):
        assert project['_id'] == temp_project, \
            f"ID проекта в ответе '{project['_id']}' не соответствует ожидаемому '{temp_project}'."
        assert project['space'] == temp_space, \
            f"Проект привязан к пространству '{project['space']}', ожидалось '{temp_space}'."

    with allure.step("Пошаговая проверка структуры полученного проекта"):
        # assert_project_payload ожидает полезную нагрузку в формате {'project': {...}}
        assert_project_payload({'project': project})