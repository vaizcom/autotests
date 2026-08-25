import allure
import pytest

from test_backend.data.endpoints.access_group.access_group_endpoints import (
    get_access_group_endpoint,
    update_access_group_rights_endpoint,
)
from .helpers import create_custom_group

pytestmark = [pytest.mark.backend]


# ─── Grant ────────────────────────────────────────────────────────────────────


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Positive")
@allure.title("Manager меняет права кастомной группы на Space (Guest → Member), Project и Board остаются без изменений")
def test_update_custom_group_rights_on_space(manager_client, access_manager, access_space, access_project, access_board):
    """
    Кто: manager_client (Manager в access_space) — минимально необходимая роль.
    Что: меняет уровень кастомной группы на Space с Guest (дефолт при создании) на Member.
    Почему работает:
      - Manager проходит проверку доступа на Space (требуется Manager+)
      - группа — кастомная, не selfGroup: запрет на смену своих прав не применяется
      - группа не принадлежит создателю спейса: запрет CreatorAccessChangeNotAllowed не применяется
      - выдаваемый уровень Member не превышает уровень Manager: запрет LackAccessChangeNotAllowed не применяется
    Проверяем:
      - до: Space = Guest, Project = NoAccess, Board = NoAccess
      - после: Space = Member, Project остался NoAccess, Board остался NoAccess
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]
    board_id = access_board["board_id"]
    with allure.step("Setup: создаём новую кастомную группу"):
        group_id = create_custom_group(manager_client, space_id, "grp_space")

    with allure.step("GetAccessGroup: проверяем состояние перед тестом — Space = Guest, Project = NoAccess, Board = NoAccess"):
        before_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert before_resp.status_code == 200, f"GetAccessGroup вернул {before_resp.status_code}: {before_resp.text}"
        before_group = before_resp.json()["payload"]["accessGroup"]
        assert before_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space до обновления, получен '{before_group['spaceAccesses'].get(space_id)}'"
        assert before_group["projectAccesses"].get(project_id) is None, \
            f"Ожидался NoAccess на Project до обновления, получен '{before_group['projectAccesses'].get(project_id)}'"
        assert before_group["boardAccesses"].get(board_id) is None, \
            f"Ожидался NoAccess на Board до обновления, получен '{before_group['boardAccesses'].get(board_id)}'"

    with allure.step("Меняем уровень кастомной группы на Space с Guest на Member"):
        resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Space", kind_id=space_id, level="Member",
        ))

    with allure.step("Статус ответа 200"):
        assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    with allure.step("Проверяем ответ: Space = Member, Project остался NoAccess, Board остался NoAccess"):
        group = resp.json()["payload"]["accessGroup"]
        assert group["spaceAccesses"].get(space_id) == "Member", \
            f"Ожидался Member на Space, получен '{group['spaceAccesses'].get(space_id)}'"
        assert group["projectAccesses"].get(project_id) is None, \
            f"Ожидался NoAccess на Project (без изменений), получен '{group['projectAccesses'].get(project_id)}'"
        assert group["boardAccesses"].get(board_id) is None, \
            f"Ожидался NoAccess на Board (без изменений), получен '{group['boardAccesses'].get(board_id)}'"

    with allure.step("GetAccessGroup подтверждает в БД: Space = Member, Project = NoAccess, Board = NoAccess"):
        after_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert after_resp.status_code == 200, f"GetAccessGroup вернул {after_resp.status_code}: {after_resp.text}"
        after_group = after_resp.json()["payload"]["accessGroup"]
        assert after_group["spaceAccesses"].get(space_id) == "Member", \
            f"Ожидался Member на Space в БД, получен '{after_group['spaceAccesses'].get(space_id)}'"
        assert after_group["projectAccesses"].get(project_id) is None, \
            f"Ожидался NoAccess на Project в БД (без изменений), получен '{after_group['projectAccesses'].get(project_id)}'"
        assert after_group["boardAccesses"].get(board_id) is None, \
            f"Ожидался NoAccess на Board в БД (без изменений), получен '{after_group['boardAccesses'].get(board_id)}'"


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

    with allure.step("GetAccessGroup: проверяем состояние перед тестом — Space = Guest, Project = NoAccess, Board = NoAccess"):
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

    with allure.step("GetAccessGroup: проверяем состояние перед тестом — Space = Guest, Project = NoAccess, Board = NoAccess"):
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
@allure.title("Выдача Member на Board не эскалирует Project, если у него уже есть доступ (Member)")
def test_board_grant_no_escalation_when_project_has_access(manager_client, access_manager, access_space, access_project, access_board):
    """
    Кто: manager_client (Manager в access_space) — минимально необходимая роль.
    Что: выдаёт кастомной группе Member на Board, когда Project уже в Member.
    Почему важно: эскалация срабатывает только если родитель в NoAccess.
                  Если Project уже Member — эскалация не должна применяться.
    Проверяем:
      - Setup: Project = Member (явно), Board = NoAccess, Space = Guest
      - до: Project = Member, Board = NoAccess
      - после: Board = Member, Project остался Member (эскалация не сработала)
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]
    board_id = access_board["board_id"]
    with allure.step("Setup: создаём новую кастомную группу"):
        group_id = create_custom_group(manager_client, space_id, "grp_board_no_escalation")

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
            f"Ожидался Member на Project до выдачи Board, получен '{before_group['projectAccesses'].get(project_id)}'"
        assert before_group["boardAccesses"].get(board_id) is None, \
            f"Ожидался NoAccess на Board до выдачи, получен '{before_group['boardAccesses'].get(board_id)}'"
        assert before_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space до выдачи, получен '{before_group['spaceAccesses'].get(space_id)}'"

    with allure.step("Выдаём кастомной группе уровень Member на Board"):
        resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Board", kind_id=board_id, level="Member",
        ))

    with allure.step("Статус ответа 200"):
        assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    with allure.step("Проверяем ответ: Board = Member, Project остался Member (эскалация не сработала), Space остался Guest"):
        group = resp.json()["payload"]["accessGroup"]
        assert group["boardAccesses"].get(board_id) == "Member", \
            f"Ожидался Member на Board, получен '{group['boardAccesses'].get(board_id)}'"
        assert group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project (без изменений), получен '{group['projectAccesses'].get(project_id)}'"
        assert group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space (без изменений), получен '{group['spaceAccesses'].get(space_id)}'"

    with allure.step("GetAccessGroup подтверждает в БД: Board = Member, Project = Member, Space = Guest"):
        after_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert after_resp.status_code == 200, f"GetAccessGroup вернул {after_resp.status_code}: {after_resp.text}"
        after_group = after_resp.json()["payload"]["accessGroup"]
        assert after_group["boardAccesses"].get(board_id) == "Member", \
            f"Ожидался Member на Board в БД, получен '{after_group['boardAccesses'].get(board_id)}'"
        assert after_group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project в БД (без изменений), получен '{after_group['projectAccesses'].get(project_id)}'"
        assert after_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space в БД (без изменений), получен '{after_group['spaceAccesses'].get(space_id)}'"


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Positive")
@allure.title("Выдача Member на Board не понижает Project, если у него уже есть более высокий уровень (Manager)")
def test_board_grant_no_escalation_downgrade(manager_client, access_manager, access_space, access_project, access_board):
    """
    Кто: manager_client (Manager в access_space) — минимально необходимая роль.
    Что: выдаёт кастомной группе Member на Board, когда Project уже в Manager.
    Почему важно: эскалация выставляет Member на родителя только если он в NoAccess.
                  Если родитель уже выше Member — эскалация не должна его понижать.
    Проверяем:
      - Setup: Project = Manager, Board = NoAccess, Space = Guest
      - до: Project = Manager, Board = NoAccess
      - после: Board = Member, Project остался Manager (эскалация не понижает)
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]
    board_id = access_board["board_id"]
    with allure.step("Setup: создаём новую кастомную группу"):
        group_id = create_custom_group(manager_client, space_id, "grp_board_no_downgrade")

    with allure.step("Setup: выдаём группе Manager на Project"):
        setup_resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Project", kind_id=project_id, level="Manager",
        ))
        assert setup_resp.status_code == 200, f"Setup: не удалось выдать Manager на Project: {setup_resp.text}"

    with allure.step("GetAccessGroup: проверяем состояние перед тестом — Project = Manager, Board = NoAccess, Space = Guest"):
        before_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert before_resp.status_code == 200, f"GetAccessGroup вернул {before_resp.status_code}: {before_resp.text}"
        before_group = before_resp.json()["payload"]["accessGroup"]
        assert before_group["projectAccesses"].get(project_id) == "Manager", \
            f"Ожидался Manager на Project до выдачи Board, получен '{before_group['projectAccesses'].get(project_id)}'"
        assert before_group["boardAccesses"].get(board_id) is None, \
            f"Ожидался NoAccess на Board до выдачи, получен '{before_group['boardAccesses'].get(board_id)}'"
        assert before_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space до выдачи, получен '{before_group['spaceAccesses'].get(space_id)}'"

    with allure.step("Выдаём кастомной группе уровень Member на Board"):
        resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Board", kind_id=board_id, level="Member",
        ))

    with allure.step("Статус ответа 200"):
        assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    with allure.step("Проверяем ответ: Board = Member, Project остался Manager (эскалация не понижает), Space остался Guest"):
        group = resp.json()["payload"]["accessGroup"]
        assert group["boardAccesses"].get(board_id) == "Member", \
            f"Ожидался Member на Board, получен '{group['boardAccesses'].get(board_id)}'"
        assert group["projectAccesses"].get(project_id) == "Manager", \
            f"Ожидался Manager на Project (без изменений), получен '{group['projectAccesses'].get(project_id)}'"
        assert group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space (без изменений), получен '{group['spaceAccesses'].get(space_id)}'"

    with allure.step("GetAccessGroup подтверждает в БД: Board = Member, Project = Manager, Space = Guest"):
        after_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert after_resp.status_code == 200, f"GetAccessGroup вернул {after_resp.status_code}: {after_resp.text}"
        after_group = after_resp.json()["payload"]["accessGroup"]
        assert after_group["boardAccesses"].get(board_id) == "Member", \
            f"Ожидался Member на Board в БД, получен '{after_group['boardAccesses'].get(board_id)}'"
        assert after_group["projectAccesses"].get(project_id) == "Manager", \
            f"Ожидался Manager на Project в БД (без изменений), получен '{after_group['projectAccesses'].get(project_id)}'"
        assert after_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space в БД (без изменений), получен '{after_group['spaceAccesses'].get(space_id)}'"


# ─── Upgrade ──────────────────────────────────────────────────────────────────


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Positive")
@allure.title("Повышение Project с Member до Manager — Board и Space остаются без изменений")
def test_upgrade_project_member_to_manager(manager_client, access_manager, access_space, access_project, access_board):
    """
    Кто: manager_client (Manager в access_space) — минимально необходимая роль.
    Что: повышает уровень кастомной группы на Project с Member до Manager.
    Почему важно: при изменении уже существующего доступа на Project бэкенд не должен
                  перезаписывать права соседних сущностей (Board) и родителя (Space).
    Проверяем:
      - Setup: Project = Member, Board = Member, Space = Guest
      - до: Project = Member, Board = Member, Space = Guest
      - после: Project = Manager, Board остался Member, Space остался Guest
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]
    board_id = access_board["board_id"]
    with allure.step("Setup: создаём новую кастомную группу"):
        group_id = create_custom_group(manager_client, space_id, "grp_project_upgrade")

    with allure.step("Setup: выдаём группе Member на Project и Member на Board"):
        setup_project = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Project", kind_id=project_id, level="Member",
        ))
        assert setup_project.status_code == 200, f"Setup: не удалось выдать Member на Project: {setup_project.text}"
        setup_board = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Board", kind_id=board_id, level="Member",
        ))
        assert setup_board.status_code == 200, f"Setup: не удалось выдать Member на Board: {setup_board.text}"

    with allure.step("GetAccessGroup: проверяем состояние перед тестом — Project = Member, Board = Member, Space = Guest"):
        before_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert before_resp.status_code == 200, f"GetAccessGroup вернул {before_resp.status_code}: {before_resp.text}"
        before_group = before_resp.json()["payload"]["accessGroup"]
        assert before_group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project до повышения, получен '{before_group['projectAccesses'].get(project_id)}'"
        assert before_group["boardAccesses"].get(board_id) == "Member", \
            f"Ожидался Member на Board до повышения, получен '{before_group['boardAccesses'].get(board_id)}'"
        assert before_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space до повышения, получен '{before_group['spaceAccesses'].get(space_id)}'"

    with allure.step("Повышаем уровень группы на Project с Member до Manager"):
        resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Project", kind_id=project_id, level="Manager",
        ))

    with allure.step("Статус ответа 200"):
        assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    with allure.step("Проверяем ответ: Project = Manager, Board остался Member, Space остался Guest"):
        group = resp.json()["payload"]["accessGroup"]
        assert group["projectAccesses"].get(project_id) == "Manager", \
            f"Ожидался Manager на Project, получен '{group['projectAccesses'].get(project_id)}'"
        assert group["boardAccesses"].get(board_id) == "Member", \
            f"Ожидался Member на Board (без изменений), получен '{group['boardAccesses'].get(board_id)}'"
        assert group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space (без изменений), получен '{group['spaceAccesses'].get(space_id)}'"

    with allure.step("GetAccessGroup подтверждает в БД: Project = Manager, Board = Member, Space = Guest"):
        after_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert after_resp.status_code == 200, f"GetAccessGroup вернул {after_resp.status_code}: {after_resp.text}"
        after_group = after_resp.json()["payload"]["accessGroup"]
        assert after_group["projectAccesses"].get(project_id) == "Manager", \
            f"Ожидался Manager на Project в БД, получен '{after_group['projectAccesses'].get(project_id)}'"
        assert after_group["boardAccesses"].get(board_id) == "Member", \
            f"Ожидался Member на Board в БД (без изменений), получен '{after_group['boardAccesses'].get(board_id)}'"
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


# ─── Revoke ───────────────────────────────────────────────────────────────────


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Positive")
@allure.title("Даунгрейд Space (Member → Guest) не каскадирует вниз — Project и Board остаются без изменений")
def test_revoke_space_rights(manager_client, access_manager, access_space, access_project, access_board):
    """
    Кто: manager_client (Manager в access_space) — минимально необходимая роль.
    Что: понижает уровень кастомной группы на Space с Member до Guest.
    Почему важно: NoAccess на Space несовместим (AccessLevelIncompatible), поэтому
                  минимальный уровень для Space — Guest. Даунгрейд Space не каскадирует
                  вниз — в отличие от отзыва прав на Project, который снимает Board.
    Проверяем:
      - Setup: Space = Member, Project = Member, Board = Member
      - до: Space = Member, Project = Member, Board = Member
      - после: Space = Guest, Project остался Member, Board остался Member
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]
    board_id = access_board["board_id"]
    with allure.step("Setup: создаём новую кастомную группу"):
        group_id = create_custom_group(manager_client, space_id, "grp_revoke_space")

    with allure.step("Setup: повышаем Space до Member, выдаём Member на Project и Board"):
        setup_space = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Space", kind_id=space_id, level="Member",
        ))
        assert setup_space.status_code == 200, f"Setup: не удалось выдать Member на Space: {setup_space.text}"
        setup_project = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Project", kind_id=project_id, level="Member",
        ))
        assert setup_project.status_code == 200, f"Setup: не удалось выдать Member на Project: {setup_project.text}"
        setup_board = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Board", kind_id=board_id, level="Member",
        ))
        assert setup_board.status_code == 200, f"Setup: не удалось выдать Member на Board: {setup_board.text}"

    with allure.step("GetAccessGroup: проверяем состояние перед тестом — Space = Member, Project = Member, Board = Member"):
        before_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert before_resp.status_code == 200, f"GetAccessGroup вернул {before_resp.status_code}: {before_resp.text}"
        before_group = before_resp.json()["payload"]["accessGroup"]
        assert before_group["spaceAccesses"].get(space_id) == "Member", \
            f"Ожидался Member на Space до даунгрейда, получен '{before_group['spaceAccesses'].get(space_id)}'"
        assert before_group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project до даунгрейда, получен '{before_group['projectAccesses'].get(project_id)}'"
        assert before_group["boardAccesses"].get(board_id) == "Member", \
            f"Ожидался Member на Board до даунгрейда, получен '{before_group['boardAccesses'].get(board_id)}'"

    with allure.step("Понижаем уровень группы на Space с Member до Guest"):
        resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Space", kind_id=space_id, level="Guest",
        ))

    with allure.step("Статус ответа 200"):
        assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    with allure.step("Проверяем ответ: Space = Guest, Project остался Member, Board остался Member"):
        group = resp.json()["payload"]["accessGroup"]
        assert group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space, получен '{group['spaceAccesses'].get(space_id)}'"
        assert group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project (без изменений), получен '{group['projectAccesses'].get(project_id)}'"
        assert group["boardAccesses"].get(board_id) == "Member", \
            f"Ожидался Member на Board (без изменений), получен '{group['boardAccesses'].get(board_id)}'"

    with allure.step("GetAccessGroup подтверждает в БД: Space = Guest, Project = Member, Board = Member"):
        after_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert after_resp.status_code == 200, f"GetAccessGroup вернул {after_resp.status_code}: {after_resp.text}"
        after_group = after_resp.json()["payload"]["accessGroup"]
        assert after_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space в БД, получен '{after_group['spaceAccesses'].get(space_id)}'"
        assert after_group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project в БД (без изменений), получен '{after_group['projectAccesses'].get(project_id)}'"
        assert after_group["boardAccesses"].get(board_id) == "Member", \
            f"Ожидался Member на Board в БД (без изменений), получен '{after_group['boardAccesses'].get(board_id)}'"


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Positive")
@allure.title("Отзыв прав на Project (Member → NoAccess) каскадирует вниз на Board, Space остаётся без изменений")
def test_revoke_project_rights(manager_client, access_manager, access_space, access_project, access_board):
    """
    Кто: manager_client (Manager в access_space) — минимально необходимая роль.
    Что: выставляет NoAccess на Project для группы, у которой есть Member на Project и Member на Board.
    Почему важно: NoAccess — это не просто уровень, а удаление ключа из map (.delete(kindId)).
                  Отзыв прав на Project каскадируется вниз: Board-доступ тоже снимается.
                  Это симметрично эскалации вверх при выдаче прав (Board → Project → Space).
    Проверяем:
      - Setup: Project = Member, Board = Member, Space = Guest
      - до: Project = Member, Board = Member
      - после: Project = NoAccess (ключ отсутствует), Board = NoAccess (ключ отсутствует), Space остался Guest
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]
    board_id = access_board["board_id"]
    with allure.step("Setup: создаём новую кастомную группу"):
        group_id = create_custom_group(manager_client, space_id, "grp_revoke_project")

    with allure.step("Setup: выдаём группе Member на Project и Member на Board"):
        setup_project = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Project", kind_id=project_id, level="Member",
        ))
        assert setup_project.status_code == 200, f"Setup: не удалось выдать Member на Project: {setup_project.text}"
        setup_board = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Board", kind_id=board_id, level="Member",
        ))
        assert setup_board.status_code == 200, f"Setup: не удалось выдать Member на Board: {setup_board.text}"

    with allure.step("GetAccessGroup: проверяем состояние перед тестом — Project = Member, Board = Member, Space = Guest"):
        before_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert before_resp.status_code == 200, f"GetAccessGroup вернул {before_resp.status_code}: {before_resp.text}"
        before_group = before_resp.json()["payload"]["accessGroup"]
        assert before_group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project до отзыва, получен '{before_group['projectAccesses'].get(project_id)}'"
        assert before_group["boardAccesses"].get(board_id) == "Member", \
            f"Ожидался Member на Board до отзыва, получен '{before_group['boardAccesses'].get(board_id)}'"
        assert before_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space до отзыва, получен '{before_group['spaceAccesses'].get(space_id)}'"

    with allure.step("Выставляем NoAccess на Project — отзываем права группы на Project"):
        resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Project", kind_id=project_id, level="NoAccess",
        ))

    with allure.step("Статус ответа 200"):
        assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    with allure.step("Проверяем ответ: Project = NoAccess (ключ отсутствует), Board = NoAccess (каскад вниз), Space остался Guest"):
        group = resp.json()["payload"]["accessGroup"]
        assert group["projectAccesses"].get(project_id) is None, \
            f"Ожидался NoAccess (отсутствие ключа) на Project, получен '{group['projectAccesses'].get(project_id)}'"
        assert group["boardAccesses"].get(board_id) is None, \
            f"Ожидался NoAccess (отсутствие ключа) на Board (каскад), получен '{group['boardAccesses'].get(board_id)}'"
        assert group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space (без изменений), получен '{group['spaceAccesses'].get(space_id)}'"

    with allure.step("GetAccessGroup подтверждает в БД: Project = NoAccess, Board = NoAccess, Space = Guest"):
        after_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert after_resp.status_code == 200, f"GetAccessGroup вернул {after_resp.status_code}: {after_resp.text}"
        after_group = after_resp.json()["payload"]["accessGroup"]
        assert after_group["projectAccesses"].get(project_id) is None, \
            f"Ожидался NoAccess (отсутствие ключа) на Project в БД, получен '{after_group['projectAccesses'].get(project_id)}'"
        assert after_group["boardAccesses"].get(board_id) is None, \
            f"Ожидался NoAccess (отсутствие ключа) на Board в БД (каскад), получен '{after_group['boardAccesses'].get(board_id)}'"
        assert after_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space в БД (без изменений), получен '{after_group['spaceAccesses'].get(space_id)}'"


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Positive")
@allure.title("Отзыв прав на Board (Member → NoAccess) не каскадирует вверх на Project, Space остаётся без изменений")
def test_revoke_board_rights(manager_client, access_manager, access_space, access_project, access_board):
    """
    Кто: manager_client (Manager в access_space) — минимально необходимая роль.
    Что: выставляет NoAccess на Board для группы, у которой есть Member на Board и Member на Project.
    Почему важно: проверяем, что отзыв прав на Board не каскадирует вверх на Project —
                  в отличие от отзыва Project, который каскадирует вниз на Board.
    Проверяем:
      - Setup: Board = Member, Project = Member, Space = Guest
      - до: Board = Member, Project = Member
      - после: Board = NoAccess (ключ отсутствует), Project остался Member, Space остался Guest
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]
    board_id = access_board["board_id"]
    with allure.step("Setup: создаём новую кастомную группу"):
        group_id = create_custom_group(manager_client, space_id, "grp_revoke_board")

    with allure.step("Setup: выдаём группе Member на Board (Project эскалирует до Member)"):
        setup_board = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Board", kind_id=board_id, level="Member",
        ))
        assert setup_board.status_code == 200, f"Setup: не удалось выдать Member на Board: {setup_board.text}"

    with allure.step("GetAccessGroup: проверяем состояние перед тестом — Board = Member, Project = Member, Space = Guest"):
        before_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert before_resp.status_code == 200, f"GetAccessGroup вернул {before_resp.status_code}: {before_resp.text}"
        before_group = before_resp.json()["payload"]["accessGroup"]
        assert before_group["boardAccesses"].get(board_id) == "Member", \
            f"Ожидался Member на Board до отзыва, получен '{before_group['boardAccesses'].get(board_id)}'"
        assert before_group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project до отзыва (эскалация), получен '{before_group['projectAccesses'].get(project_id)}'"
        assert before_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space до отзыва, получен '{before_group['spaceAccesses'].get(space_id)}'"

    with allure.step("Выставляем NoAccess на Board — отзываем права группы на Board"):
        resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Board", kind_id=board_id, level="NoAccess",
        ))

    with allure.step("Статус ответа 200"):
        assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    with allure.step("Проверяем ответ: Board = NoAccess (ключ отсутствует), Project остался Member, Space остался Guest"):
        group = resp.json()["payload"]["accessGroup"]
        assert group["boardAccesses"].get(board_id) is None, \
            f"Ожидался NoAccess (отсутствие ключа) на Board, получен '{group['boardAccesses'].get(board_id)}'"
        assert group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project (без изменений), получен '{group['projectAccesses'].get(project_id)}'"
        assert group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space (без изменений), получен '{group['spaceAccesses'].get(space_id)}'"

    with allure.step("GetAccessGroup подтверждает в БД: Board = NoAccess, Project = Member, Space = Guest"):
        after_resp = manager_client.post(**get_access_group_endpoint(space_id=space_id, group_id=group_id))
        assert after_resp.status_code == 200, f"GetAccessGroup вернул {after_resp.status_code}: {after_resp.text}"
        after_group = after_resp.json()["payload"]["accessGroup"]
        assert after_group["boardAccesses"].get(board_id) is None, \
            f"Ожидался NoAccess (отсутствие ключа) на Board в БД, получен '{after_group['boardAccesses'].get(board_id)}'"
        assert after_group["projectAccesses"].get(project_id) == "Member", \
            f"Ожидался Member на Project в БД (без изменений), получен '{after_group['projectAccesses'].get(project_id)}'"
        assert after_group["spaceAccesses"].get(space_id) == "Guest", \
            f"Ожидался Guest на Space в БД (без изменений), получен '{after_group['spaceAccesses'].get(space_id)}'"
