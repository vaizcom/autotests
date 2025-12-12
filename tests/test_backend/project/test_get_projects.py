import allure
import pytest

from tests.test_backend.data.endpoints.Project.project_endpoints import (
    get_projects_endpoint
)

pytestmark = [pytest.mark.backend]


@allure.title('Тест: Проверка получения списка проектов')
def test_get_projects(owner_client, temp_project, temp_space):
    client = owner_client
    response = client.post(**get_projects_endpoint(space_id=temp_space))
    assert response.status_code == 200
    projects = response.json()['payload']['projects']
    project_ids = [p['_id'] for p in projects]
    assert temp_project in project_ids