import pytest
import allure

from core.waiters import wait_until
from test_backend.data.endpoints.access_group.aaccess_group_endpoints import get_access_groups_endpoint
from test_backend.data.endpoints.invite.assert_invite_payload import assert_invite_payload
from test_backend.data.endpoints.invite.invite_endpoint import invite_to_space_endpoint

pytestmark = [pytest.mark.backend]


# Параметризация для проверки разных ролей
@allure.parent_suite("Invite Service")
@allure.suite("Space Invitations (set role)")
@pytest.mark.parametrize("role", ["Guest", "Member", "Manager", "Owner"])
@allure.title("Приглашение пользователя в Space с ролью {role}")
def test_invite_to_space(second_main_client, space_id_, role):
    """
    Тест проверяет приглашение пользователя в спейс с указанной ролью
    и последующую проверку его прав в списке участников.
    """
    # 1. Генерация уникального email для теста
    email = f"invite_{role.lower()}_{space_id_}@autotest.com"

    # 2. Отправка приглашения
    with allure.step(f"Приглашение пользователя с ролью {role}"):
        response = second_main_client.post(**invite_to_space_endpoint(
            space_id=space_id_,
            email=email,
            space_access=role
        ))
        assert response.status_code == 200, f"Ошибка приглашения: {response.text}"

        payload = response.json().get("payload", {}).get("invite", {})


        _id = payload.get("_id")

        assert _id, "В ответе инвайта не вернулся _id"

    with allure.step("Валидация тела ответа InviteToSpace"):
        assert_invite_payload(
            invite=payload,
            space_id=space_id_,
            email=email
        )

    # 3. Прямой запрос прав доступа по полученному ID с универсальным поллингом
    with allure.step(f"Ожидание появления пользователя в списке групп доступа"):

        def _check_group():
            """Локальная функция-условие для поллинга"""
            group_resp = second_main_client.post(**get_access_groups_endpoint(space_id=space_id_))
            assert group_resp.status_code == 200, f"Ошибка GetAccessGroup: {group_resp.text}"

            groups = group_resp.json().get("payload", {}).get("accessGroups", [])
            # Возвращаем найденную группу или None
            return next((g for g in groups if g.get("members") == [_id]), None)

        try:
            target_id = wait_until(
                condition_func=_check_group,
                timeout=10,
                error_msg=f"Группа с ID {_id} не появилась в списке accessGroups за 10 секунд."
            )
        except TimeoutError as e:
            pytest.fail(str(e))

        # Базовые проверки структуры группы
    with allure.step("Базовые проверки структуры созданной группы"):
        assert target_id.get("space") == space_id_, "ID спейса в группе не совпадает"
        assert isinstance(target_id.get("members"), list), "Поле members должно быть списком"
        assert "createdAt" in target_id, "Отсутствует поле createdAt"
        assert "updatedAt" in target_id, "Отсутствует поле updatedAt"

        # Проверка доступов к проектам и доскам
    with allure.step(f"Проверка доступов к проектам и доскам для роли {role}"):
        if role == "Owner":
            project_accesses = target_id.get("projectAccesses", {})
            board_accesses = target_id.get("boardAccesses", {})
            assert all(val == "Owner" for val in project_accesses.values()), f"Не все права в проектах равны Owner: {project_accesses}"
            assert all(val == "Owner" for val in board_accesses.values()), f"Не все права в досках равны Owner: {board_accesses}"
        else:
            assert target_id.get("projectAccesses") == {}, "Поле projectAccesses должно быть пустым словарем"
            assert target_id.get("boardAccesses") == {}, "Поле boardAccesses должно быть пустым словарем"

        # Проверяем права в spaceAccesses
    with allure.step(f"Проверка соответствия роли {role} в spaceAccesses"):
        space_accesses = target_id.get("spaceAccesses", {})
        actual_role = space_accesses.get(space_id_)

        assert actual_role == role, (
            f"Роль не совпадает!\n"
            f"Ожидалось: {role}\n"
            f"Получено: {actual_role}\n"
            f"Объект spaceAccesses: {space_accesses}"
        )