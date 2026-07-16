import uuid
import allure
import pytest

from test_backend.data.endpoints.file.upload_avatar_endpoint import get_uploaded_avatar_url
from test_backend.data.endpoints.invite.assert_invite_payload import assert_invite_payload
from test_backend.data.endpoints.invite.invite_endpoint import invite_to_space_endpoint
from test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint

pytestmark = [pytest.mark.backend]

# Минимальная валидная картинка 1x1 пиксель
DUMMY_PNG = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'


@allure.parent_suite("Invite Service")
@allure.suite("Space Invitations - Avatar (Positive)")
@allure.title("Приглашение пользователя с аватаром (png)")
def test_invite_user_with_avatar_positive(second_main_client, second_space_id):
    """
    Проверка позитивного сценария:
    1. Загрузка валидного аватара (png) на сервер.
    2. Успешное приглашение нового пользователя в пространство с указанным avatarUrl.
    """
    with allure.step("Получение заголовков с ID пространства для обхода проверок безопасности"):
        space_req = get_space_members_endpoint(space_id=second_space_id)
        space_headers = space_req.get("headers", {})

    with allure.step("Загрузка картинки аватара (png) через multipart/form-data"):
        avatar_url = get_uploaded_avatar_url(
            client=second_main_client,
            kind_id=second_space_id,
            kind="Space",
            file_content=DUMMY_PNG,
            headers=space_headers,
            file_name="test_avatar.png",
            content_type="image/png"
        )

        assert avatar_url is not None, "URL аватара не должен быть None"
        assert len(avatar_url) > 0, "Длина URL аватара должна быть больше 0"

    with allure.step(f"Приглашение нового пользователя с загруженным аватаром ({avatar_url})"):
        invite_email = f"new_user_{uuid.uuid4().hex[:8]}@example.com"

        invite_req = invite_to_space_endpoint(
            space_id=second_space_id,
            email=invite_email,
            space_access="Member",
            avatar_url=avatar_url
        )

        invite_headers = invite_req.get("headers", {})
        invite_headers.update(space_headers)

        response = second_main_client.post(
            invite_req["path"],
            json=invite_req.get("json", {}),
            headers=invite_headers
        )

    with allure.step("Проверка статус-кода ответа сервера 200"):
        if response.status_code != 200:
            print(f"\n[ОШИБКА ИНВАЙТА] Ответ сервера: {response.text}\n")

        assert response.status_code == 200, f"Ошибка приглашения. Ожидался статус 200, получен {response.status_code}. Ответ: {response.text}"

        payload = response.json().get("payload", {}).get("invite", {})


        _id = payload.get("_id")

        assert _id, "В ответе инвайта не вернулся _id"

    with allure.step("Валидация тела ответа InviteToSpace"):
        assert_invite_payload(
            invite=payload,
            space_id=second_space_id,
            email=invite_email
        )

