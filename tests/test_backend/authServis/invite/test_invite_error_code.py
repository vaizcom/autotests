import allure
import pytest

from config import settings
from conftest import main_client, owner_client
from test_backend.data.endpoints.invite.invite_endpoint import (
    invite_to_space_endpoint, deactivate_member_endpoint
)
from test_backend.task_service.utils import get_user_id

pytestmark = [pytest.mark.backend]

#To do: 'IncompleteProfile', 'AcceptOnlyForActiveMember'
# 'CantDepriveAccessCreator',
# 'CantDepriveAccessYourself',
# 'UserAlreadySpaceMember','SelfInvitation'


@allure.parent_suite("Auth Service")
@allure.suite("Invite")
@allure.sub_suite("Invite Error Code")
@allure.title("Ошибка CantDepriveAccessYourself при попытке удалить самого себя")
def test_cant_deprive_access_yourself_error(owner_client, space_with_members):
    expected_status = 400
    expected_error_code = "CantDepriveAccessYourself"
    member_name = 'owner'

    # Получаем ID пользователя, от имени которого делаем запрос
    user_id = get_user_id(owner_client, space_with_members, member_name)

    with allure.step("Пользователь пытается удалить самого себя из пространства"):
        response = owner_client.post(**deactivate_member_endpoint(
            space_id=space_with_members,
            member_id=user_id
        ))

        assert response.status_code == expected_status, f"Ожидалась ошибка {expected_status}, получен статус {response.status_code}"

        error_data = response.json().get("error", {})
        actual_error_code = error_data.get("code")

        assert actual_error_code == expected_error_code, f"Ожидался код ошибки {expected_error_code}, получен {actual_error_code}"


@allure.parent_suite("Auth Service")
@allure.suite("Invite")
@allure.sub_suite("Invite Error Code")
@allure.title("Ошибка CantDepriveAccessCreator при попытке удалить создателя space")
def test_cant_deprive_access_creator_error(main_client, owner_client, space_with_members):
    expected_status = 400
    expected_error_code = "CantDepriveAccessCreator"
    member_name= 'main'
    main_user_id = get_user_id(main_client, space_with_members, member_name)

    with allure.step("Owner пытается удалить создателя пространства"):
        response = owner_client.post(**deactivate_member_endpoint(
            space_id=space_with_members,
            member_id=main_user_id
        ))

        assert response.status_code == expected_status, f"Ожидалась ошибка {expected_status}, получен статус {response.status_code}"

        error_data = response.json().get("error", {})
        actual_error_code = error_data.get("code")

        assert actual_error_code == expected_error_code, f"Ожидался код ошибки {expected_error_code}, получен {actual_error_code}"


@allure.parent_suite("Auth Service")
@allure.suite("Invite")
@allure.sub_suite("Invite Error Code")
@allure.title("Ошибка UserAlreadySpaceMember при попытке пригласить дважды одного пользователя (самого себя)")
def test_already_space_member_error(main_client, space_with_members):
    # Получаем email пользователя, от имени которого выполняем запрос
    main_email = settings.USERS['main']['email']
    expected_status = 400
    expected_error_code = "UserAlreadySpaceMember"

    with allure.step("Пользователь пытается отправить инвайт на свой собственный email"):
        response = main_client.post(**invite_to_space_endpoint(
            space_id=space_with_members,
            email=main_email,
            space_access="Member"
        ))

        assert response.status_code == expected_status, f"Ожидалась ошибка {expected_status}, получен статус {response.status_code}"

        error_data = response.json().get("error", {})
        actual_error_code = error_data.get("code")

        assert actual_error_code == expected_error_code, f"Ожидался код ошибки {expected_error_code}, получен {actual_error_code}"