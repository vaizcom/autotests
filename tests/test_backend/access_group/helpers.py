import allure

from test_backend.data.endpoints.access_group.access_group_endpoints import (
    create_access_group_endpoint,
    get_access_groups_endpoint,
)
from test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint


def get_self_group_id(client, space_id, member_id):
    """Возвращает _id selfAccessGroup участника по его member_id."""
    resp = client.post(**get_access_groups_endpoint(space_id=space_id))
    assert resp.status_code == 200, f"GetAccessGroups вернул {resp.status_code}: {resp.text}"
    groups = resp.json()["payload"]["accessGroups"]
    self_group = next(
        (g for g in groups if g.get("selfGroup") and member_id in g.get("members", [])),
        None,
    )
    assert self_group is not None, f"selfAccessGroup для member {member_id} не найдена"
    return self_group["_id"]


def get_member_id_by_email(client, space_id, email):
    """Возвращает member_id участника спейса по email."""
    resp = client.post(**get_space_members_endpoint(space_id=space_id))
    assert resp.status_code == 200, f"GetSpaceMembers вернул {resp.status_code}: {resp.text}"
    members = resp.json()["payload"]["members"]
    member = next((m for m in members if m.get("email") == email), None)
    assert member is not None, f"Участник {email} не найден в спейсе"
    return member["_id"]


def create_custom_group(client, space_id, name):
    """
    Создаёт кастомную группу доступа и проверяет начальное состояние.

    Бэкенд принудительно выставляет Guest на Space при создании —
    spaceAccesses[space_id] = Guest, projectAccesses и boardAccesses пустые.
    Параметры прав в запросе игнорируются.

    Возвращает group_id.
    """
    with allure.step(f"Setup: создаём кастомную access group '{name}'"):
        resp = client.post(**create_access_group_endpoint(
            space_id=space_id,
            name=name,
            description="for access group rights tests",
        ))
        assert resp.status_code == 200, f"Setup: не удалось создать access group: {resp.text}"
        group = resp.json()["payload"]["accessGroup"]
        group_id = group["_id"]

    with allure.step("Setup: проверяем начальные права — Space = Guest, Project/Board = NoAccess"):
        space_level = group.get("spaceAccesses", {}).get(space_id)
        assert space_level == "Guest", (
            f"Ожидался Guest на Space при создании группы, получен '{space_level}'. "
            f"Возможно, хардкод в CreateAccessGroup изменился."
        )
        assert group.get("projectAccesses", {}) == {}, \
            f"Ожидался пустой projectAccesses, получен: {group.get('projectAccesses')}"
        assert group.get("boardAccesses", {}) == {}, \
            f"Ожидался пустой boardAccesses, получен: {group.get('boardAccesses')}"

    return group_id
