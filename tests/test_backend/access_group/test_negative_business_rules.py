import allure
import pytest

from config.settings import USERS
from test_backend.data.endpoints.access_group.access_group_endpoints import update_access_group_rights_endpoint
from .helpers import get_self_group_id, get_member_id_by_email

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Negative: бизнес-правила")
@allure.title("Нельзя изменить права своей собственной selfGroup → OwnAccessChangeNotAllowed")
def test_cannot_change_own_rights(main_client, access_space, access_project):
    """
    Кто: main_client (Owner спейса).
    Что: пытается изменить права своей собственной selfGroup на Project.
    Почему не работает: нельзя менять свои собственные права.
                        Бэкенд сверяет, совпадает ли имя группы (`self_${memberId}`)
                        с memberId вызывающего, и бросает OwnAccessChangeNotAllowed.
    Проверяем: статус 400, error.code = OwnAccessChangeNotAllowed.
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]

    with allure.step("Находим member_id и selfGroup main_client в access_space"):
        main_member_id = get_member_id_by_email(main_client, space_id, USERS["main"]["email"])
        own_group_id = get_self_group_id(main_client, space_id, main_member_id)

    with allure.step("main_client пытается изменить свои права на Project"):
        resp = main_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=own_group_id,
            kind="Project", kind_id=project_id, level="Member",
        ))

    with allure.step("Статус ответа 400, error.code = OwnAccessChangeNotAllowed"):
        assert resp.status_code == 400, f"Ожидался 400, получен {resp.status_code}: {resp.text}"
        assert resp.json()["error"]["code"] == "OwnAccessChangeNotAllowed", \
            f"Ожидался OwnAccessChangeNotAllowed: {resp.text}"


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Negative: бизнес-правила")
@allure.title("Нельзя изменить права selfGroup создателя спейса → CreatorAccessChangeNotAllowed")
def test_cannot_change_creator_rights(manager_client, access_manager, main_client, access_space):
    """
    Кто: manager_client (Manager в access_space).
    Что: пытается изменить права selfGroup main_client (создателя спейса) на Space.
    Почему не работает: нельзя менять права создателя спейса на сам спейс.
                        Бэкенд получает creatorId сущности и сравнивает с именем selfGroup —
                        если совпадает, бросает CreatorAccessChangeNotAllowed.
    Проверяем: статус 400, error.code = CreatorAccessChangeNotAllowed.
    """
    space_id = access_space["space_id"]

    with allure.step("Находим selfGroup создателя спейса (main_client)"):
        main_member_id = get_member_id_by_email(main_client, space_id, USERS["main"]["email"])
        creator_group_id = get_self_group_id(main_client, space_id, main_member_id)

    with allure.step("manager_client пытается изменить права создателя на Space"):
        resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=creator_group_id,
            kind="Space", kind_id=space_id, level="Manager",
        ))

    with allure.step("Статус ответа 400, error.code = CreatorAccessChangeNotAllowed"):
        assert resp.status_code == 400, f"Ожидался 400, получен {resp.status_code}: {resp.text}"
        assert resp.json()["error"]["code"] == "CreatorAccessChangeNotAllowed", \
            f"Ожидался CreatorAccessChangeNotAllowed: {resp.text}"


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Negative: бизнес-правила")
@allure.title("Нельзя выдать уровень доступа выше своего (Manager → Owner) → LackAccessChangeNotAllowed")
def test_cannot_grant_higher_than_own_level(manager_client, access_space, access_member_self_group_id):
    """
    Кто: manager_client (Manager в access_space).
    Что: пытается выдать selfGroup мембера уровень Owner на Space.
    Почему не работает: нельзя выдать уровень доступа выше, чем у самого вызывающего.
                        ACCESS_WEIGHT[Manager] < ACCESS_WEIGHT[Owner] →
                        бэкенд бросает LackAccessChangeNotAllowed.
    Проверяем: статус 400, error.code = LackAccessChangeNotAllowed.
    """
    space_id = access_space["space_id"]

    with allure.step("Manager пытается выдать Owner уровень на Space"):
        resp = manager_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=access_member_self_group_id,
            kind="Space", kind_id=space_id, level="Owner",
        ))

    with allure.step("Статус ответа 400, error.code = LackAccessChangeNotAllowed"):
        assert resp.status_code == 400, f"Ожидался 400, получен {resp.status_code}: {resp.text}"
        assert resp.json()["error"]["code"] == "LackAccessChangeNotAllowed", \
            f"Ожидался LackAccessChangeNotAllowed: {resp.text}"


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Negative: бизнес-правила")
@allure.title("NoAccess несовместим с kind=Space → AccessLevelIncompatible")
def test_cannot_set_no_access_on_space(main_client, access_space, access_member_self_group_id):
    """
    Кто: main_client (Owner спейса).
    Что: пытается выставить уровень NoAccess на Space для selfGroup мембера.
    Почему не работает: NoAccess несовместим с kind=Space — удалить участника
                        из спейса можно только через отдельный эндпоинт, не через права.
                        Бэкенд бросает AccessLevelIncompatible.
    Проверяем: статус 400, error.code = AccessLevelIncompatible.
    """
    space_id = access_space["space_id"]

    with allure.step("Пытаемся выставить NoAccess на Space"):
        resp = main_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=access_member_self_group_id,
            kind="Space", kind_id=space_id, level="NoAccess",
        ))

    with allure.step("Статус ответа 400, error.code = AccessLevelIncompatible"):
        assert resp.status_code == 400, f"Ожидался 400, получен {resp.status_code}: {resp.text}"
        assert resp.json()["error"]["code"] == "AccessLevelIncompatible", \
            f"Ожидался AccessLevelIncompatible: {resp.text}"
