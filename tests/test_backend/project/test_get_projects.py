import allure
import pytest

from test_backend.data.endpoints.Project.assert_project_output_payload import assert_project_payload
from tests.test_backend.data.endpoints.Project.project_endpoints import (
    get_projects_endpoint
)

pytestmark = [pytest.mark.backend]


@allure.title('Тест: Проверка получения списка проектов, проверка что payload ответа соответствует ожидаемой структуре')
def test_get_projects(owner_client, main_project, main_space):
    with allure.step(f"Отправка запроса на получение списка проектов для пространства ID: {main_space}"):
        response = owner_client.post(**get_projects_endpoint(space_id=main_space))

    with allure.step("Проверка статуса ответа и общей структуры ответа"):
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        payload = response.json()['payload']
        assert 'projects' in payload, "Ответ не содержит ключ 'projects'"
        assert isinstance(payload['projects'], list), "Значение 'projects' не является списком"

    projects_list = payload['projects']

    with allure.step("Проверка наличия проекта в списке и того что все проекты в списке принадлежат нужному спейсу."):
        # Убеждаемся, что temp_project присутствует в списке
        assert any(p['_id'] == main_project for p in projects_list), \
            f"Временный проект с ID {main_project} не найден в списке полученных проектов."

        for project in projects_list:
            assert project['space'] == main_space, \
                f"Проект с ID {project['_id']} привязан к пространству '{project['space']}', ожидалось '{main_space}'."

    with allure.step("Пошаговая проверка структуры каждого проекта в списке"):
        if projects_list:
            for project in projects_list:
                with allure.step("Проверка структуры проекта"):
                    # assert_project_payload ожидает полезную нагрузку в формате {'project': {...}}
                    assert_project_payload({'project': project})
        else:
            allure.attach("Список проектов пуст, структура каждого проекта не проверяется.", name="Информация")