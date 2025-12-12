import allure
import pytest

from tests.test_backend.data.endpoints.Project.project_endpoints import (
    get_project_endpoint,
    archive_project_endpoint
)

pytestmark = [pytest.mark.backend]

@allure.title('Тест: Проверка архивации проекта')
def test_archive_project(owner_client, temp_project, temp_space):
    # Получаем данные проекта до архивации
    initial_response = owner_client.post(**get_project_endpoint(project_id=temp_project, space_id=temp_space))
    assert initial_response.status_code == 200
    initial_project_data = initial_response.json()['payload']['project']
    # Убеждаемся, что до архивации поле 'archivedAt' было None
    assert initial_project_data.get('archivedAt') is None

    archive_response = owner_client.post(**archive_project_endpoint(project_id=temp_project, space_id=temp_space))
    assert archive_response.status_code == 200
    project_data = archive_response.json()['payload']['project']
    # Проверяем, что после архивации поле 'archivedAt' имеет значение
    assert project_data.get('archivedAt')

