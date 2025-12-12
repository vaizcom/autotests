import allure
import pytest

from test_backend.data.endpoints.Project.assert_project_output_payload import assert_project_payload
from tests.test_backend.data.endpoints.Project.project_endpoints import (
    get_projects_endpoint
)

pytestmark = [pytest.mark.backend]


@allure.title('Тест: Проверка получения списка проектов, проверка что payload ответа соответствует ожидаемой структуре')
def test_get_projects(owner_client, temp_project, temp_space):
    client = owner_client
    response = client.post(**get_projects_endpoint(space_id=temp_space))
    assert response.status_code == 200
    projects = response.json()['payload']['projects']
    project_ids = [p['_id'] for p in projects]
    assert temp_project in project_ids

    with allure.step("Парсинг ответа и проверка полезной нагрузки списка проектов"):
        payload = response.json()['payload']
        # Предполагаем, что payload содержит ключ 'projects', который является списком
        assert 'projects' in payload, "Ответ не содержит ключ 'projects'"
        assert isinstance(payload['projects'], list), "Значение 'projects' не является списком"

        if len(payload['projects']) > 0:
            for project in payload['projects']:
                with allure.step(f"Проверка структуры проекта с ID: {project.get('_id', 'N/A')}"):
                    assert_project_payload({'project': project}) # Оборачиваем каждый проект в словарь с ключом 'project' для assert_project_payload
        else:
            with allure.step("Список проектов пуст, структура каждого проекта не проверяется"):
                pass