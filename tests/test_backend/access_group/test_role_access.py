import allure
import pytest

from test_backend.data.endpoints.access_group.access_group_endpoints import (
    get_access_group_endpoint,
    update_access_group_rights_endpoint,
    set_access_group_member_endpoint,
)
from .helpers import create_custom_group

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Доступ по ролям")
@pytest.mark.parametrize("role, client_fixture, access_fixture, expected_status, expected_error", [
    ("Owner (Creator)", "main_client",    "access_owner",      200, None),
    ("Manager",         "manager_client", "access_manager",    200, None),
    ("Member",          "member_client",  "access_member",     403, "AccessDenied"),
    ("Guest",           "guest_client",   "access_guest",      403, "AccessDenied"),
    ("NotInGroup",      "owner_client",   "access_no_project", 403, "AccessDenied"),
], ids=["Owner", "Manager", "Member", "Guest", "NotInGroup"])
def test_update_rights_by_role(
    request, main_client,
    access_space, access_project, access_board,
    role, client_fixture, access_fixture, expected_status, expected_error,
):
    """
    Матрица доступа UpdateAccessGroupRights по ролям.

    Для каждой роли:
      1. Создаём кастомную группу (Owner через main_client).
      2. Добавляем участников с ролями Manager, Member, Guest в группу.
      3. Участник с тестируемой ролью пытается изменить права группы на Project.
      4. Owner/Manager → 200, Member/Guest/NotInGroup → 403 AccessDenied.

    NotInGroup — Manager в спейсе, но без явного доступа к Project через selfGroup.
    Проверяем что роль в спейсе не даёт автоматического доступа к проекту.
    """
    access_data = request.getfixturevalue(access_fixture)
    client = request.getfixturevalue(client_fixture)

    space_id = access_space["space_id"]
    project_id = access_project["project_id"]

    allure.dynamic.title(f"UpdateAccessGroupRights от роли {role} → {expected_status}")

    # ─── Step 1: создаём кастомную группу ────────────────────────────────────

    with allure.step("Создаём кастомную группу"):
        group_id = create_custom_group(main_client, space_id, f"grp_role_{role}")

    # ─── Step 2: добавляем участников в группу ───────────────────────────────

    members_to_add = []
    for member_fixture in ("access_manager", "access_member", "access_guest"):
        member_data = request.getfixturevalue(member_fixture)
        members_to_add.append(member_data)

    for member_data in members_to_add:
        with allure.step(f"Добавляем участника {member_data['email']} в кастомную группу"):
            resp = main_client.post(**set_access_group_member_endpoint(
                space_id=space_id,
                member_id=member_data["member_id"],
                access_group_id=group_id,
            ))
            assert resp.status_code == 200, \
                f"Не удалось добавить {member_data['email']} в группу: {resp.text}"

    # ─── Step 3: проверяем состояние перед тестом ──────────────────────────────

    with allure.step("GetAccessGroup: проверяем состояние перед тестом — Project = NoAccess"):
        before_resp = main_client.post(**get_access_group_endpoint(
            space_id=space_id, group_id=group_id,
        ))
        assert before_resp.status_code == 200, \
            f"GetAccessGroup вернул {before_resp.status_code}: {before_resp.text}"
        before_group = before_resp.json()["payload"]["accessGroup"]
        assert before_group["projectAccesses"].get(project_id) is None, \
            f"Ожидался NoAccess на Project до обновления, получен '{before_group['projectAccesses'].get(project_id)}'"

    # ─── Step 4: тестируемая роль пытается изменить права группы ─────────────

    with allure.step(f"{role} вызывает UpdateAccessGroupRights для кастомной группы на Project (NoAccess → Member)"):
        resp = client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Project", kind_id=project_id, level="Member",
        ))

    # ─── Step 5: проверяем результат ─────────────────────────────────────────

    with allure.step(f"Статус ответа {expected_status}"):
        assert resp.status_code == expected_status, \
            f"Ожидался {expected_status}, получен {resp.status_code}: {resp.text}"

    if expected_error:
        with allure.step(f"error.code = {expected_error}"):
            assert resp.json()["error"]["code"] == expected_error, \
                f"Ожидался {expected_error}: {resp.text}"

    # ─── Step 6: post-condition — проверяем состояние после теста ─────────────

    if expected_status == 200:
        with allure.step("Проверяем ответ: Project = Member"):
            group = resp.json()["payload"]["accessGroup"]
            assert group["projectAccesses"].get(project_id) == "Member", \
                f"Ожидался Member на Project в ответе, получен '{group['projectAccesses'].get(project_id)}'"

        with allure.step("GetAccessGroup подтверждает в БД: Project = Member"):
            after_resp = main_client.post(**get_access_group_endpoint(
                space_id=space_id, group_id=group_id,
            ))
            assert after_resp.status_code == 200, \
                f"GetAccessGroup вернул {after_resp.status_code}: {after_resp.text}"
            after_group = after_resp.json()["payload"]["accessGroup"]
            assert after_group["projectAccesses"].get(project_id) == "Member", \
                f"Ожидался Member на Project в БД, получен '{after_group['projectAccesses'].get(project_id)}'"
    else:
        with allure.step("GetAccessGroup подтверждает: Project остался NoAccess (права не изменились)"):
            after_resp = main_client.post(**get_access_group_endpoint(
                space_id=space_id, group_id=group_id,
            ))
            assert after_resp.status_code == 200, \
                f"GetAccessGroup вернул {after_resp.status_code}: {after_resp.text}"
            after_group = after_resp.json()["payload"]["accessGroup"]
            assert after_group["projectAccesses"].get(project_id) is None, \
                f"Ожидался NoAccess на Project в БД (права не должны были измениться), получен '{after_group['projectAccesses'].get(project_id)}'"
