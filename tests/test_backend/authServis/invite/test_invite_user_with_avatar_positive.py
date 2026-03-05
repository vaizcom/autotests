import uuid
import allure
import pytest

from test_backend.data.endpoints.file.upload_avatar_endpoint import get_uploaded_avatar_url, DUMMY_PNG_CONTENT
from test_backend.data.endpoints.invite.invite_endpoint import invite_to_space_endpoint
from tests.test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Auth Service")
@allure.suite("Invite")
@allure.sub_suite("Space Invitations")
@allure.title("Приглашение пользователя с необязательными параметрами (Avatar)")
def test_invite_user_with_avatar_positive(main_client, temp_space):
    """
    Проверка позитивного сценария:
    1. Получение контекста пространства (заголовки).
    2. Загрузка валидного аватара (тип Space) на сервер.
    3. Успешное приглашение нового пользователя в пространство с указанным avatarUrl.
    """

    with allure.step("Получение заголовков с ID пространства для обхода проверок безопасности"):
        space_req = get_space_members_endpoint(space_id=temp_space)
        space_headers = space_req.get("headers", {})

    with allure.step("Загрузка картинки аватара через multipart/form-data"):
        avatar_url = get_uploaded_avatar_url(
            client=main_client,
            kind_id=temp_space,
            kind="Space",  # Говорим серверу, что аватар предназначен для пространства
            file_content=DUMMY_PNG_CONTENT,
            headers=space_headers,
            file_name="test_avatar.png",
            content_type="image/png"
        )

        assert avatar_url is not None, "URL аватара не должен быть None"
        assert len(avatar_url) > 0, "Длина URL аватара должна быть больше 0"

    with allure.step(f"Приглашение нового пользователя с загруженным аватаром ({avatar_url})"):
        # Генерируем уникальный email для каждого запуска
        invite_email = f"new_user_{uuid.uuid4().hex[:8]}@example.com"

        invite_req = invite_to_space_endpoint(
            space_id=temp_space,
            email=invite_email,
            space_access="Member",
            avatar_url=avatar_url
        )

        # Обязательно добавляем заголовки пространства в инвайт
        invite_headers = invite_req.get("headers", {})
        invite_headers.update(space_headers)

        response = main_client.post(
            invite_req["path"],
            json=invite_req.get("json", {}),
            headers=invite_headers
        )

    with allure.step("Проверка статус-кода ответа сервера"):
        if response.status_code != 200:
            print(f"\n[ОШИБКА ИНВАЙТА] Ответ сервера: {response.text}\n")

        assert response.status_code == 200, f"Ошибка приглашения. Ожидался статус 200, получен {response.status_code}. Ответ: {response.text}"