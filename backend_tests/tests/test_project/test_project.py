import pytest

from backend_tests.utils.generators import generate_project_name, generate_slug
from backend_tests.data.endpoints.Project.project_endpoints import (
    create_project_endpoint,
    edit_project_endpoint,
    get_project_endpoint,
    get_projects_endpoint,
    archive_project_endpoint,
    unarchive_project_endpoint,
    is_project_slug_unique_endpoint,
    MAX_PROJECT_NAME_LENGTH,
    MAX_PROJECT_DESCRIPTION_LENGTH,
    MAX_PROJECT_SLUG_LENGTH
)


@pytest.fixture(scope="module")
def created_project_id(owner_client, temp_space):
    """Создаёт проект, который используется во всех тестах модуля."""
    name = generate_project_name()
    slug = generate_slug()
    common_kwargs = {
        "color": "blue",
        "icon": "Dot",
        "description": "temporary project",
        "space_id": temp_space
    }
    response = owner_client.post(**create_project_endpoint(
        name=name,
        slug=slug,
        **common_kwargs
    ))
    assert response.status_code == 200
    return response.json()["payload"]["project"]["_id"]


# Тест: Проверка slug: уникальность до создания, неуникальность после создания, и ошибка при дубликате
def test_project_slug_validation(owner_client, temp_space):
    client = owner_client
    slug = generate_slug()
    name = generate_project_name()
    common_kwargs = {
        "color": "blue",
        "icon": "Dot",
        "description": "test slug validation",
        "space_id": temp_space
    }

    # Убедиться, что slug уникален
    check_response_1 = client.post(**is_project_slug_unique_endpoint(slug=slug, space_id=temp_space))
    assert check_response_1.status_code == 200
    assert check_response_1.json()["payload"]["isUnique"]

    # Создать проект с этим slug
    response_1 = client.post(**create_project_endpoint(
        name=name,
        slug=slug,
        **common_kwargs
    ))
    assert response_1.status_code == 200

    # Проверить, что slug стал неуникальным
    check_response_2 = client.post(**is_project_slug_unique_endpoint(slug=slug, space_id=temp_space))
    assert check_response_2.status_code == 200
    assert not check_response_2.json()["payload"]["isUnique"]

    # Попытка создать второй проект с тем же slug
    response_2 = client.post(**create_project_endpoint(
        name=name + "_copy",
        slug=slug,
        **common_kwargs
    ))
    assert response_2.status_code == 400


# Тест: Проверка предельной длины slug
def test_project_slug_length_limit(owner_client, temp_space):
    client = owner_client
    slug = generate_slug(MAX_PROJECT_SLUG_LENGTH + 1, MAX_PROJECT_SLUG_LENGTH + 1)
    name = generate_project_name()
    common_kwargs = {
        "color": "blue",
        "icon": "Dot",
        "description": "too long slug",
        "space_id": temp_space
    }

    response = client.post(**create_project_endpoint(
        name=name,
        slug=slug,
        **common_kwargs
    ))
    assert response.status_code == 400


# Тест: Проверка предельной длины имени проекта
def test_project_name_length_limit(owner_client, temp_space):
    client = owner_client
    name = "P" * (MAX_PROJECT_NAME_LENGTH + 1)
    slug = generate_slug()
    common_kwargs = {
        "color": "blue",
        "icon": "Dot",
        "description": "too long name",
        "space_id": temp_space
    }

    response = client.post(**create_project_endpoint(
        name=name,
        slug=slug,
        **common_kwargs
    ))
    assert response.status_code == 400


# Тест: Проверка предельной длины описания проекта
def test_project_description_length_limit(owner_client, temp_space):
    client = owner_client
    description = "D" * (MAX_PROJECT_DESCRIPTION_LENGTH + 1)
    name = generate_project_name()
    slug = generate_slug()
    common_kwargs = {
        "color": "blue",
        "icon": "Dot",
        "space_id": temp_space
    }

    response = client.post(**create_project_endpoint(
        name=name,
        slug=slug,
        description=description,
        **common_kwargs
    ))
    assert response.status_code == 400


# Тест: Проверка получения проекта по ID
def test_get_project(owner_client, created_project_id, temp_space):
    client = owner_client
    response = client.post(**get_project_endpoint(project_id=created_project_id, space_id=temp_space))
    assert response.status_code == 200
    payload = response.json()["payload"]
    assert "project" in payload


# Тест: Проверка списка проектов
def test_get_projects(owner_client, created_project_id, temp_space):
    client = owner_client
    response = client.post(**get_projects_endpoint(space_id=temp_space))
    assert response.status_code == 200
    projects = response.json()["payload"]["projects"]
    project_ids = [p["_id"] for p in projects]
    assert created_project_id in project_ids


# Тест: Проверка редактирования имени проекта
def test_edit_project_name(owner_client, created_project_id, temp_space):
    client = owner_client
    new_name = generate_project_name()

    edit_response = client.post(**edit_project_endpoint(
        project_id=created_project_id,
        name=new_name,
        space_id=temp_space
    ))
    assert edit_response.status_code == 200
    assert edit_response.json()["payload"]["project"]["name"] == new_name


# Тест: Проверка архивации проекта
def test_archive_project(owner_client, created_project_id, temp_space):
    client = owner_client
    archive_response = client.post(**archive_project_endpoint(
        project_id=created_project_id,
        space_id=temp_space
    ))
    assert archive_response.status_code == 200
    assert archive_response.json()["payload"]["project"].get("archivedAt")


# Тест: Проверка разархивации проекта
def test_unarchive_project(owner_client, created_project_id, temp_space):
    client = owner_client
    client.post(**archive_project_endpoint(project_id=created_project_id, space_id=temp_space))

    unarchive_response = client.post(**unarchive_project_endpoint(
        project_id=created_project_id,
        space_id=temp_space
    ))
    assert unarchive_response.status_code == 200
    assert unarchive_response.json()["payload"].get("itemId") == created_project_id
