import allure
import pytest

from tests.test_backend.data.endpoints.Project.project_endpoints import (
    archive_project_endpoint,
    unarchive_project_endpoint,
)

pytestmark = [pytest.mark.backend]


@allure.title('Тест: Проверка разархивации проекта')
def test_unarchive_project(owner_client, temp_project, temp_space):
    client = owner_client
    client.post(**archive_project_endpoint(project_id=temp_project, space_id=temp_space))
    unarchive_response = client.post(**unarchive_project_endpoint(project_id=temp_project, space_id=temp_space))
    assert unarchive_response.status_code == 200
    assert unarchive_response.json()['payload'].get('itemId') == temp_project