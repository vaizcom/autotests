import uuid

import allure
import pytest

from test_backend.data.endpoints.access_group.aaccess_group_endpoints import (
    create_access_group_endpoint,
    update_access_group_endpoint,
    update_access_group_rights_endpoint,
    remove_access_group_endpoint,
)
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


def _create_group(client, space_id: str) -> str:
    """Вспомогательная функция: создаёт группу доступа и возвращает её _id."""
    name = f"test_group_{uuid.uuid4().hex[:6]}"
    resp = client.post(**create_access_group_endpoint(
        space_id=space_id,
        name=name,
        description="history event test group",
    ))
    assert resp.status_code == 200, f"Ошибка создания группы: {resp.text}"
    return resp.json()["payload"]["accessGroup"]["_id"]


@allure.parent_suite("History Service")
@allure.suite("Space History")
@allure.title("ACCESS_GROUP_CREATED event")
def test_access_group_created_event(main_client, space_for_history):
    """
    При создании группы доступа генерируется событие ACCESS_GROUP_CREATED.
    """
    space_id = space_for_history["space_id"]

    with allure.step("Создаём группу доступа"):
        group_id = _create_group(main_client, space_id)

    assert_history_event_exists(
        client=main_client,
        space_id=space_id,
        kind="Space",
        kind_id=space_id,
        expected_event_key="ACCESS_GROUP_CREATED",
    )


ACCESS_GROUP_UPDATE_CASES = [
    pytest.param(
        {"name": f"updated_name_{uuid.uuid4().hex[:6]}"},
        "Обновление имени группы доступа",
        id="update_name",
    ),
    pytest.param(
        {"description": "updated description"},
        "Обновление описания группы доступа",
        id="update_description",
    ),
]


@allure.parent_suite("History Service")
@allure.suite("Space History")
@pytest.mark.parametrize("update_kwargs,title", ACCESS_GROUP_UPDATE_CASES)
def test_access_group_updated_event(main_client, space_for_history, update_kwargs, title):
    """
    При обновлении имени/описания группы доступа генерируется событие ACCESS_GROUP_UPDATED.
    """
    allure.dynamic.title(title)
    space_id = space_for_history["space_id"]

    with allure.step("Создаём группу доступа"):
        group_id = _create_group(main_client, space_id)

    with allure.step(f"Обновляем группу: {list(update_kwargs.keys())}"):
        resp = main_client.post(**update_access_group_endpoint(
            space_id=space_id,
            group_id=group_id,
            **update_kwargs,
        ))
        assert resp.status_code == 200, f"Ошибка обновления группы: {resp.text}"

    assert_history_event_exists(
        client=main_client,
        space_id=space_id,
        kind="Space",
        kind_id=space_id,
        expected_event_key="ACCESS_GROUP_UPDATED",
    )


@allure.parent_suite("History Service")
@allure.suite("Space History")
@allure.title("ACCESS_GROUP_RIGHTS_UPDATED event")
def test_access_group_rights_updated_event(main_client, space_for_history):
    """
    При обновлении прав группы доступа на сущность генерируется событие ACCESS_GROUP_RIGHTS_UPDATED.
    По дефолту группа создается с правами доступа Guest, тест обновляет до уровня доступа Member
    """
    space_id = space_for_history["space_id"]

    with allure.step("Создаём группу доступа"):
        group_id = _create_group(main_client, space_id)

    with allure.step("Обновляем права группы на Space (уровень Member)"):
        resp = main_client.post(**update_access_group_rights_endpoint(
            space_id=space_id,
            group_id=group_id,
            kind="Space",
            kind_id=space_id,
            level="Member",
        ))
        assert resp.status_code == 200, f"Ошибка обновления прав группы: {resp.text}"

    assert_history_event_exists(
        client=main_client,
        space_id=space_id,
        kind="Space",
        kind_id=space_id,
        expected_event_key="ACCESS_GROUP_RIGHTS_UPDATED",
    )


@allure.parent_suite("History Service")
@allure.suite("Space History")
@allure.title("ACCESS_GROUP_REMOVED event")
def test_access_group_removed_event(main_client, space_for_history):
    """
    При удалении группы доступа генерируется событие ACCESS_GROUP_REMOVED.
    """
    space_id = space_for_history["space_id"]

    with allure.step("Создаём группу доступа"):
        group_id = _create_group(main_client, space_id)

    with allure.step("Удаляем группу доступа"):
        resp = main_client.post(**remove_access_group_endpoint(
            space_id=space_id,
            group_id=group_id,
        ))
        assert resp.status_code == 200, f"Ошибка удаления группы: {resp.text}"

    assert_history_event_exists(
        client=main_client,
        space_id=space_id,
        kind="Space",
        kind_id=space_id,
        expected_event_key="ACCESS_GROUP_REMOVED",
    )
