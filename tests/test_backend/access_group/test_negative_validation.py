import allure
import pytest

from test_backend.data.endpoints.access_group.access_group_endpoints import update_access_group_rights_endpoint
from .helpers import create_custom_group

pytestmark = [pytest.mark.backend]

_VALID_MONGO_ID = "000000000000000000000001"


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Negative: валидация")
@allure.title("groupId не найден в БД → NotFound")
def test_nonexistent_group_id(main_client, access_space, access_project):
    """
    Кто: main_client (Owner спейса).
    Что: отправляет запрос с валидным по формату ObjectId, которого нет в БД.
    Почему не работает: AccessGroupModel.findByIdOrDie бросает NotFound.
    Проверяем: статус 400, error.code = NotFound.
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]

    with allure.step("Отправляем запрос с несуществующим groupId"):
        resp = main_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=_VALID_MONGO_ID,
            kind="Project", kind_id=project_id, level="Member",
        ))

    with allure.step("Статус ответа 400, error.code = NotFound"):
        assert resp.status_code == 400, f"Ожидался 400, получен {resp.status_code}: {resp.text}"
        assert resp.json()["error"]["code"] == "NotFound", \
            f"Ожидался NotFound: {resp.text}"


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Negative: валидация")
@allure.title("kindId не найден в БД → NotFound или AccessDenied")
def test_nonexistent_kind_id(main_client, access_space):
    """
    Кто: main_client (Owner спейса).
    Что: отправляет запрос с валидным ObjectId в kindId, которого нет в БД.
    Почему не работает: hasAccessLevelOrDie не находит сущность и возвращает
                        NotFound или AccessDenied (зависит от реализации).
    Проверяем: статус 400, error.code = NotFound или AccessDenied.
    """
    space_id = access_space["space_id"]
    with allure.step("Setup: создаём новую кастомную группу"):
        group_id = create_custom_group(main_client, space_id, "grp_validation")

    with allure.step("Отправляем запрос с несуществующим kindId (Project)"):
        resp = main_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id=group_id,
            kind="Project", kind_id=_VALID_MONGO_ID, level="Member",
        ))

    with allure.step("Статус ответа 400 или 403, error.code = NotFound или AccessDenied"):
        assert resp.status_code in (400, 403), f"Ожидался 400 или 403, получен {resp.status_code}: {resp.text}"
        assert resp.json()["error"]["code"] in ("NotFound", "AccessDenied"), \
            f"Ожидался NotFound или AccessDenied: {resp.text}"


@allure.parent_suite("Access Group")
@allure.suite("UpdateAccessGroupRights")
@allure.sub_suite("Negative: валидация")
@allure.title("groupId невалидного формата (не ObjectId) → ValidationErrors")
def test_invalid_group_id_format(main_client, access_space, access_project):
    """
    Кто: main_client (Owner спейса).
    Что: отправляет запрос с groupId невалидного формата (не ObjectId).
    Почему не работает: валидация на входе отклоняет запрос до обращения к БД.
    Проверяем: статус 400, error.code = ValidationErrors.
    """
    space_id = access_space["space_id"]
    project_id = access_project["project_id"]

    with allure.step("Отправляем запрос с невалидным groupId"):
        resp = main_client.post(**update_access_group_rights_endpoint(
            space_id=space_id, group_id="not-an-object-id",
            kind="Project", kind_id=project_id, level="Member",
        ))

    with allure.step("Статус ответа 400, error.code = InvalidForm"):
        assert resp.status_code == 400, f"Ожидался 400, получен {resp.status_code}: {resp.text}"
        assert resp.json()["error"]["code"] == "InvalidForm", \
            f"Ожидался InvalidForm: {resp.text}"
