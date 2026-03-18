import allure
import pytest

from config.generators import generate_email
from conftest import temp_access_group
from core.waiters import wait_until
from test_backend.data.endpoints.access_group.aaccess_group_endpoints import get_access_groups_endpoint
from test_backend.data.endpoints.invite.assert_invite_payload import assert_invite_payload
from test_backend.data.endpoints.invite.invite_endpoint import invite_to_space_endpoint, remove_invite_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Auth Service")
@allure.suite("Invite")
@allure.sub_suite("Space Invitations - Optional Params (Positive)")
@allure.title("Приглашение пользователя с необязательными параметрами (projectAccesses, boardAccesses, fullName)")
def test_invite_to_space_with_optional_params(main_client, temp_space, temp_project, temp_board):
    """
    Проверка, что при отправке инвайта с дополнительными параметрами
    (права на проекты/доски, имя) они корректно сохраняются и возвращаются в accessGroups.
    Базовая роль в спейсе задается как Member.
    """
    email = generate_email()
    full_name = "Test User Optional"

    project_accesses_payload = [{"id": temp_project, "access": "Manager"}]
    board_accesses_payload = [{"id": temp_board, "access": "Owner"}]

    with allure.step("Отправка приглашения с дополнительными параметрами (микс прав)"):
        response = main_client.post(**invite_to_space_endpoint(
            space_id=temp_space,
            email=email,
            space_access="Member",
            project_accesses=project_accesses_payload,
            board_accesses=board_accesses_payload,
            full_name=full_name,

        ))
        assert response.status_code == 200, f"Ошибка приглашения: {response.text}"

        payload = response.json().get("payload", {}).get("invite", {})
        member_id = payload.get("_id")
        assert member_id, "В ответе инвайта не вернулся _id member"

    with allure.step("Валидация тела ответа InviteToSpace"):
        assert_invite_payload(
            invite=payload,
            space_id=temp_space,
            email=email,
            expected_full_name=full_name
        )

    with allure.step("Ожидание появления пользователя в списке групп доступа"):
        def _check_group():
            group_resp = main_client.post(**get_access_groups_endpoint(space_id=temp_space))
            assert group_resp.status_code == 200, f"Ошибка GetAccessGroup: {group_resp.text}"

            groups = group_resp.json().get("payload", {}).get("accessGroups", [])
            return next((g for g in groups if g.get("members") == [member_id]), None)

        try:
            target_group = wait_until(
                condition_func=_check_group,
                timeout=10,
                error_msg=f"Группа с ID {member_id} не появилась в списке accessGroups за 10 секунд."
            )
        except TimeoutError as e:
            pytest.fail(str(e))

    with allure.step("Проверка сохранения необязательных параметров"):
        project_accesses = target_group.get("projectAccesses", {})
        board_accesses = target_group.get("boardAccesses", {})

        assert project_accesses.get(temp_project) == "Manager", \
            f"Права на проект не сохранились. Ожидалось: Manager, Текущие: {project_accesses.get(temp_project)}"

        assert board_accesses.get(temp_board) == "Owner", \
            f"Права на доску не сохранились. Ожидалось: Guest, Текущие: {board_accesses.get(temp_board)}"

    with allure.step("Удаление инвайта"):
        remove_resp = main_client.post(**remove_invite_endpoint(space_id=temp_space, member_id=member_id))
        assert remove_resp.status_code == 200, f"Ошибка при удалении инвайта: {remove_resp.text}"

#
# @allure.parent_suite("Auth Service")
# @allure.suite("Invite")
# @allure.sub_suite("Space Invitations - Optional Params (Positive)")
# @allure.title("Приглашение пользователя с добавлением в указанную группу доступа (accessGroupId)")
# def test_invite_to_space_with_access_group(main_client, temp_space, temp_access_group):
#     """
#     Проверка, что при отправке инвайта с параметром accessGroupId
#     пользователь успешно добавляется в указанную кастомную группу доступа.
#     """
#     email = generate_email()
#     full_name = "Test User Access Group"
#
#     with allure.step("Отправка приглашения с указанием группы доступа"):
#         response = main_client.post(**invite_to_space_endpoint(
#             space_id=temp_space,
#             email=email,
#             space_access="Member",
#             access_group_id=temp_access_group,
#             full_name=full_name
#         ))
#         assert response.status_code == 200, f"Ошибка приглашения: {response.text}"
#
#         payload = response.json().get("payload", {}).get("invite", {})
#         member_id = payload.get("_id")
#         assert member_id, "В ответе инвайта не вернулся _id"
#
#     with allure.step("Валидация тела ответа InviteToSpace"):
#         assert_invite_payload(
#             invite=payload,
#             space_id=temp_space,
#             email=email,
#             expected_full_name=full_name
#         )
#
#     with allure.step("Ожидание добавления пользователя в целевую группу доступа"):
#         def _check_group():
#             group_resp = main_client.post(**get_access_groups_endpoint(space_id=temp_space))
#             assert group_resp.status_code == 200, f"Ошибка GetAccessGroup: {group_resp.text}"
#
#             groups = group_resp.json().get("payload", {}).get("accessGroups", [])
#
#             # Ищем нашу целевую группу (temp_access_group) и проверяем, есть ли там наш пользователь
#             target_custom_group = next(
#                 (g for g in groups if g.get("_id") == temp_access_group),
#                 None
#             )
#
#             if target_custom_group and member_id in target_custom_group.get("members", []):
#                 return target_custom_group
#             return None
#
#         try:
#             target_group = wait_until(
#                 condition_func=_check_group,
#                 timeout=10,
#                 error_msg=f"Пользователь {member_id} не был добавлен в группу {temp_access_group} за 10 секунд."
#             )
#         except TimeoutError as e:
#             pytest.fail(str(e))
#
#     with allure.step("Проверка добавления в группу"):
#         assert member_id in target_group.get("members", []), \
#             f"Пользователь {member_id} отсутствует в members группы {temp_access_group}"
#
#     with allure.step("Удаление инвайта"):
#         remove_resp = main_client.post(**remove_invite_endpoint(space_id=temp_space, member_id=member_id))
#         assert remove_resp.status_code == 200, f"Ошибка при удалении инвайта: {remove_resp.text}"
#
#
#
# @allure.parent_suite("Auth Service")
# @allure.suite("Invite")
# @allure.sub_suite("Space Invitations - Optional Params (Negative)")
# @allure.title("Инвайт с невалидными доп. параметрами: {scenario}")
# @pytest.mark.parametrize(
#     "scenario, overrides, expected_status",
#     [
#         # --- Проверки прав на проекты (projectAccesses) ---
#         (
#                 "Несуществующая роль в проекте",
#                 {"project_accesses": [{"id": "VALID_PROJECT", "access": "SuperAdminFakeRole"}]},
#                 400
#         ),
#         (
#                 "Невалидный формат ID проекта (не MongoDB ID)",
#                 {"project_accesses": [{"id": "12345-invalid-id", "access": "Manager"}]},
#                 400
#         ),
#         # (
#         #         "Несуществующий (но валидный по формату) accessGroupId",
#         #         {"access_group_id": "5f8d0a6b7b2b3c0017a4b8e9"},  # Рандомный MongoDB ID
#         #         400  # Или 404, зависит от того, как бэкенд обрабатывает Not Found при валидации
#         # ),
#         # (
#         #         "Слишком длинное fullName (> 255 символов)",
#         #         {"full_name": "A" * 1025},
#         #         400  # Сервер должен валидировать длину имени
#         # )
#     ],
#     ids=[
#         "project_role_not_exist",
#         "project_id_invalid_format",
#         # "access_group_id_not_exist",
#         # "full_name_too_long"
#     ]
# )
# def test_invite_optional_params_negative(
#         main_client, temp_space, temp_project, temp_board, scenario, overrides, expected_status
# ):
#     """
#     Негативные сценарии для эндпоинта инвайта с дополнительными параметрами
#     (projectAccesses, boardAccesses, accessGroupId, fullName).
#     Ожидаем, что бэкенд отклонит запрос из-за ошибок валидации.
#     """
#
#     with allure.step("Подготовка тестовых данных и замена плейсхолдеров"):
#         # Так как внутри @pytest.mark.parametrize нельзя напрямую вызывать фикстуры,
#         # мы передаем плейсхолдер "VALID_PROJECT" и заменяем его на реальный ID в самом тесте.
#         if "project_accesses" in overrides:
#             for p in overrides["project_accesses"]:
#                 if p["id"] == "VALID_PROJECT":
#                     p["id"] = temp_project
#
#         if "board_accesses" in overrides:
#             for b in overrides["board_accesses"]:
#                 if b["id"] == "VALID_BOARD":
#                     b["id"] = temp_board
#
#         email = generate_email()
#
#         # Базовые параметры, которые всегда валидны
#         invite_kwargs = {
#             "space_id": temp_space,
#             "email": email,
#             "space_access": "Member"
#         }
#         # Накатываем невалидные параметры поверх базовых
#         invite_kwargs.update(overrides)
#
#     with allure.step(f"Отправка инвайта: {scenario}"):
#         invite_req = invite_to_space_endpoint(**invite_kwargs)
#
#         response = main_client.post(
#             invite_req["path"],
#             json=invite_req.get("json", {}),
#             headers=invite_req.get("headers", {})
#         )
#
#     with allure.step(f"Проверка, что сервер вернул ошибку {expected_status}"):
#         assert response.status_code == expected_status, (
#             f"Уязвимость / Баг валидации! Ожидался статус {expected_status}, "
#             f"но получен {response.status_code}. Ответ сервера: {response.text}"
#         )