import allure
import pytest

from test_backend.data.endpoints.access_group.access_group_endpoints import (
    get_access_group_endpoint,
    update_access_group_rights_endpoint,
)
from .helpers import create_custom_group

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Positive")
@allure.title("Manager меняет права кастомной группы на Space (Guest → Member)")
def test_update_custom_group_rights_on_space(manager_client, access_manager, access_space):
    """
    Кто: manager_client (Manager в access_space) — минимально необходимая роль.
    Что: меняет уровень кастомной группы на Space с Guest (дефолт при создании) на Member.
    Почему работает:
      - Manager проходит проверку доступа на Space (требуется Manager+)
      - группа — кастомная, не selfGroup: запрет на смену своих прав не применяется
      - группа не принадлежит создателю спейса: запрет CreatorAccessChangeNotAllowed не применяется
      - выдаваемый уровень Member не превышает уровень Manager: запрет LackAccessChangeNotAllowed не применяется
    Проверяем: до = Guest, после = Member, изменение подтверждается через GetAccessGroup.
    """
    space_id = access_space["space_id"]
    with allure.step("Setup: создаём новую кастомную группу"):
        group_id = create_custom_group(manager_client, space_id, "grp_space")

    with allure.step("GetAccessGroup: проверяем начальный уровень группы на Space — ожидается Guest (дефолт при создании)"):
        before_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert before_resp.status_code == 200, f"GetAccessGroup вернул {before_resp.status_code}: {before_resp.text}"
        before_level = before_resp.json()["payload"]["accessGroup"]["spaceAccesses"].get(space_id)
        assert before_level == "Guest", f"Ожидался Guest до обновления, получен '{before_level}'"

    with allure.step("Меняем уровень кастомной группы на Space с Guest на Member"):
        resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Space", kind_id=space_id, level="Member",
        ))

    with allure.step("Статус ответа 200"):
        assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    with allure.step("Проверяем ответ: Space = Member"):
        group = resp.json()["payload"]["accessGroup"]
        assert group["spaceAccesses"].get(space_id) == "Member", \
            f"Ожидался Member на Space, получен '{group['spaceAccesses'].get(space_id)}'"

    with allure.step("GetAccessGroup подтверждает что изменение сохранилось в БД"):
        after_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert after_resp.status_code == 200, f"GetAccessGroup вернул {after_resp.status_code}: {after_resp.text}"
        after_level = after_resp.json()["payload"]["accessGroup"]["spaceAccesses"].get(space_id)
        assert after_level == "Member", f"Ожидался Member после обновления, получен '{after_level}'"


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Positive")
@allure.title("Manager меняет права кастомной группы на Project (NoAccess → Member), Board и Space остаются без изменений")
def test_update_custom_group_rights_on_project(manager_client, access_manager, access_space, access_project, access_board):
    """
    Кто: manager_client (Manager в access_space) — минимально необходимая роль.
    Что: выдаёт кастомной группе уровень Member на Project.
    Почему работает:
      - Manager проходит проверку доступа на Project (требуется Manager+)
      - группа — кастомная, не selfGroup: запрет на смену своих прав не применяется
      - группа не принадлежит создателю спейса: запрет CreatorAccessChangeNotAllowed не применяется
      - выдаваемый уровень Member не превышает уровень Manager: запрет LackAccessChangeNotAllowed не применяется
    Проверяем:
      - до: Space = Guest, Project = NoAccess, Board = NoAccess
      - после: Project = Member, Space остался Guest, Board остался NoAccess
      Эскалация идёт только вверх (Board → Project → Space), не вниз.
      Space не меняется, т.к. Guest уже не является NoAccess.
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]
    board_id = access_board["board_id"]
    with allure.step("Setup: создаём новую кастомную группу"):
        group_id = create_custom_group(manager_client, space_id, "grp_project")

    with allure.step("GetAccessGroup: проверяем начальные уровни группы — Space = Guest, Project = NoAccess, Board = NoAccess"):
        before_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert before_resp.status_code == 200, f"GetAccessGroup вернул {before_resp.status_code}: {before_resp.text}"
        before_group = before_resp.json()["payload"]["accessGroup"]
        assert before_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space до обновления, получен '{before_group['spaceAccesses'].get(space_id)}'"
        assert before_group["projectAccesses"].get(project_id) is None, \
            f"Ожидался NoAccess на Project до обновления, получен '{before_group['projectAccesses'].get(project_id)}'"
        assert before_group["boardAccesses"].get(board_id) is None, \
            f"Ожидался NoAccess на Board до обновления, получен '{before_group['boardAccesses'].get(board_id)}'"

    with allure.step("Выдаём кастомной группе уровень Member на Project"):
        resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Project", kind_id=project_id, level="Member",
        ))

    with allure.step("Статус ответа 200"):
        assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    with allure.step("Проверяем ответ: Project = Member, Space остался Guest, Board остался NoAccess"):
        group = resp.json()["payload"]["accessGroup"]
        assert group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project, получен '{group['projectAccesses'].get(project_id)}'"
        assert group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space (без изменений), получен '{group['spaceAccesses'].get(space_id)}'"
        assert group["boardAccesses"].get(board_id) is None, \
            f"Ожидался NoAccess на Board (без изменений), получен '{group['boardAccesses'].get(board_id)}'"

    with allure.step("GetAccessGroup подтверждает в БД: Project = Member, Space = Guest, Board = NoAccess"):
        after_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert after_resp.status_code == 200, f"GetAccessGroup вернул {after_resp.status_code}: {after_resp.text}"
        after_group = after_resp.json()["payload"]["accessGroup"]
        assert after_group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project в БД, получен '{after_group['projectAccesses'].get(project_id)}'"
        assert after_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space в БД (без изменений), получен '{after_group['spaceAccesses'].get(space_id)}'"
        assert after_group["boardAccesses"].get(board_id) is None, \
            f"Ожидался NoAccess на Board в БД (без изменений), получен '{after_group['boardAccesses'].get(board_id)}'"


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Positive")
@allure.title("Выдача Member на Board эскалирует Project до Member, Space (Guest) остаётся без изменений")
def test_update_custom_group_rights_on_board(manager_client, access_manager, access_space, access_project, access_board):
    """
    Кто: manager_client (Manager в access_space) — минимально необходимая роль.
    Что: выдаёт кастомной группе уровень Member на Board.
    Почему важно: при выдаче прав на Board бэкенд автоматически эскалирует доступ
                  к родительским сущностям (Board → Project → Space), если они в NoAccess.
                  Эскалация всегда выставляет Member, независимо от выдаваемого уровня.
    Проверяем:
      - до: Space = Guest, Project = NoAccess, Board = NoAccess
      - после: Board = Member, Project эскалировал до Member,
               Space остался Guest (Guest ≠ NoAccess — эскалация не применяется)
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]
    board_id = access_board["board_id"]
    with allure.step("Setup: создаём новую кастомную группу"):
        group_id = create_custom_group(manager_client, space_id, "grp_board")

    with allure.step("GetAccessGroup: проверяем начальные уровни — Space = Guest, Project = NoAccess, Board = NoAccess"):
        before_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert before_resp.status_code == 200, f"GetAccessGroup вернул {before_resp.status_code}: {before_resp.text}"
        before_group = before_resp.json()["payload"]["accessGroup"]
        assert before_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space до обновления, получен '{before_group['spaceAccesses'].get(space_id)}'"
        assert before_group["projectAccesses"].get(project_id) is None, \
            f"Ожидался NoAccess на Project до обновления, получен '{before_group['projectAccesses'].get(project_id)}'"
        assert before_group["boardAccesses"].get(board_id) is None, \
            f"Ожидался NoAccess на Board до обновления, получен '{before_group['boardAccesses'].get(board_id)}'"

    with allure.step("Выдаём кастомной группе уровень Member на Board"):
        resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Board", kind_id=board_id, level="Member",
        ))

    with allure.step("Статус ответа 200"):
        assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    with allure.step("Проверяем ответ: Board = Member, Project эскалировал до Member, Space остался Guest"):
        group = resp.json()["payload"]["accessGroup"]
        assert group["boardAccesses"].get(board_id) == "Member", \
            f"Ожидался Member на Board, получен '{group['boardAccesses'].get(board_id)}'"
        assert group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project (эскалация с NoAccess), получен '{group['projectAccesses'].get(project_id)}'"
        assert group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space (без изменений), получен '{group['spaceAccesses'].get(space_id)}'"

    with allure.step("GetAccessGroup подтверждает в БД: Board = Member, Project = Member, Space = Guest"):
        after_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert after_resp.status_code == 200, f"GetAccessGroup вернул {after_resp.status_code}: {after_resp.text}"
        after_group = after_resp.json()["payload"]["accessGroup"]
        assert after_group["boardAccesses"].get(board_id) == "Member", \
            f"Ожидался Member на Board в БД, получен '{after_group['boardAccesses'].get(board_id)}'"
        assert after_group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project в БД, получен '{after_group['projectAccesses'].get(project_id)}'"
        assert after_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space в БД (без изменений), получен '{after_group['spaceAccesses'].get(space_id)}'"


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Positive")
@allure.title("Повышение Board с Member до Manager — Project и Space остаются без изменений")
def test_upgrade_board_member_to_manager(manager_client, access_manager, access_space, access_project, access_board):
    """
    Кто: manager_client (Manager в access_space) — минимально необходимая роль.
    Что: повышает уровень кастомной группы на Board с Member до Manager.
    Почему важно: при изменении уже существующего доступа на Board бэкенд не должен
                  перезаписывать права родителей, у которых уже есть не-NoAccess уровень.
    Проверяем:
      - Setup: Board = Member (через апдейт) → Project эскалировал до Member, Space = Guest
      - до: Board = Member, Project = Member, Space = Guest
      - после: Board = Manager, Project остался Member, Space остался Guest
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]
    board_id = access_board["board_id"]
    with allure.step("Setup: создаём новую кастомную группу"):
        group_id = create_custom_group(manager_client, space_id, "grp_board_upgrade")

    with allure.step("Setup: выдаём группе Member на Board (Project эскалирует до Member)"):
        setup_resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Board", kind_id=board_id, level="Member",
        ))
        assert setup_resp.status_code == 200, f"Setup: не удалось выдать Member на Board: {setup_resp.text}"

    with allure.step("GetAccessGroup: проверяем состояние перед тестом — Board = Member, Project = Member, Space = Guest"):
        before_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert before_resp.status_code == 200, f"GetAccessGroup вернул {before_resp.status_code}: {before_resp.text}"
        before_group = before_resp.json()["payload"]["accessGroup"]
        assert before_group["boardAccesses"].get(board_id) == "Member", \
            f"Ожидался Member на Board до повышения, получен '{before_group['boardAccesses'].get(board_id)}'"
        assert before_group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project до повышения, получен '{before_group['projectAccesses'].get(project_id)}'"
        assert before_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space до повышения, получен '{before_group['spaceAccesses'].get(space_id)}'"

    with allure.step("Повышаем уровень группы на Board с Member до Manager"):
        resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Board", kind_id=board_id, level="Manager",
        ))

    with allure.step("Статус ответа 200"):
        assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    with allure.step("Проверяем ответ: Board = Manager, Project остался Member, Space остался Guest"):
        group = resp.json()["payload"]["accessGroup"]
        assert group["boardAccesses"].get(board_id) == "Manager", \
            f"Ожидался Manager на Board, получен '{group['boardAccesses'].get(board_id)}'"
        assert group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project (без изменений), получен '{group['projectAccesses'].get(project_id)}'"
        assert group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space (без изменений), получен '{group['spaceAccesses'].get(space_id)}'"

    with allure.step("GetAccessGroup подтверждает в БД: Board = Manager, Project = Member, Space = Guest"):
        after_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert after_resp.status_code == 200, f"GetAccessGroup вернул {after_resp.status_code}: {after_resp.text}"
        after_group = after_resp.json()["payload"]["accessGroup"]
        assert after_group["boardAccesses"].get(board_id) == "Manager", \
            f"Ожидался Manager на Board в БД, получен '{after_group['boardAccesses'].get(board_id)}'"
        assert after_group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project в БД (без изменений), получен '{after_group['projectAccesses'].get(project_id)}'"
        assert after_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space в БД (без изменений), получен '{after_group['spaceAccesses'].get(space_id)}'"


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Positive")
@allure.title("Отзыв прав на Project (Member → NoAccess) — ключ удаляется из map, Board и Space остаются без изменений")
def test_revoke_project_rights(manager_client, access_manager, access_space, access_project, access_board):
    """
    Кто: manager_client (Manager в access_space) — минимально необходимая роль.
    Что: выставляет NoAccess на Project для группы, у которой уже есть Member на Project.
    Почему важно: NoAccess — это не просто уровень, а удаление ключа из map (.delete(kindId)).
                  Проверяем что после выставления NoAccess ключ в projectAccesses отсутствует,
                  а не равен строке "NoAccess".
    Проверяем:
      - Setup: Project = Member, Board = NoAccess, Space = Guest
      - до: Project = Member
      - после: Project = NoAccess (ключ отсутствует в map), Board и Space без изменений
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]
    board_id = access_board["board_id"]
    with allure.step("Setup: создаём новую кастомную группу"):
        group_id = create_custom_group(manager_client, space_id, "grp_revoke")

    with allure.step("Setup: выдаём группе Member на Project"):
        setup_resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Project", kind_id=project_id, level="Member",
        ))
        assert setup_resp.status_code == 200, f"Setup: не удалось выдать Member на Project: {setup_resp.text}"

    with allure.step("GetAccessGroup: проверяем состояние перед тестом — Project = Member, Board = NoAccess, Space = Guest"):
        before_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert before_resp.status_code == 200, f"GetAccessGroup вернул {before_resp.status_code}: {before_resp.text}"
        before_group = before_resp.json()["payload"]["accessGroup"]
        assert before_group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project до отзыва, получен '{before_group['projectAccesses'].get(project_id)}'"
        assert before_group["boardAccesses"].get(board_id) is None, \
            f"Ожидался NoAccess на Board до отзыва, получен '{before_group['boardAccesses'].get(board_id)}'"
        assert before_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space до отзыва, получен '{before_group['spaceAccesses'].get(space_id)}'"

    with allure.step("Выставляем NoAccess на Project — отзываем права группы"):
        resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Project", kind_id=project_id, level="NoAccess",
        ))

    with allure.step("Статус ответа 200"):
        assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    with allure.step("Проверяем ответ: Project = NoAccess (ключ отсутствует в map), Board и Space без изменений"):
        group = resp.json()["payload"]["accessGroup"]
        assert group["projectAccesses"].get(project_id) is None, \
            f"Ожидался NoAccess (отсутствие ключа) на Project, получен '{group['projectAccesses'].get(project_id)}'"
        assert group["boardAccesses"].get(board_id) is None, \
            f"Ожидался NoAccess на Board (без изменений), получен '{group['boardAccesses'].get(board_id)}'"
        assert group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space (без изменений), получен '{group['spaceAccesses'].get(space_id)}'"

    with allure.step("GetAccessGroup подтверждает в БД: Project = NoAccess, Board = NoAccess, Space = Guest"):
        after_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert after_resp.status_code == 200, f"GetAccessGroup вернул {after_resp.status_code}: {after_resp.text}"
        after_group = after_resp.json()["payload"]["accessGroup"]
        assert after_group["projectAccesses"].get(project_id) is None, \
            f"Ожидался NoAccess (отсутствие ключа) на Project в БД, получен '{after_group['projectAccesses'].get(project_id)}'"
        assert after_group["boardAccesses"].get(board_id) is None, \
            f"Ожидался NoAccess на Board в БД (без изменений), получен '{after_group['boardAccesses'].get(board_id)}'"
        assert after_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space в БД (без изменений), получен '{after_group['spaceAccesses'].get(space_id)}'"
