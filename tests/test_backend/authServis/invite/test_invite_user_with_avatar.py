import uuid
import allure
import pytest

from test_backend.data.endpoints.file.upload_avatar_endpoint import get_uploaded_avatar_url, upload_avatar_endpoint
from test_backend.data.endpoints.invite.assert_invite_payload import assert_invite_payload
from test_backend.data.endpoints.invite.invite_endpoint import invite_to_space_endpoint
from tests.test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint

pytestmark = [pytest.mark.backend]

# Минимальные валидные картинки 1x1 пиксель для каждого формата
DUMMY_PNG = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
DUMMY_JPEG = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\xd2\xcf\x20\xff\xd9'
DUMMY_GIF = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
DUMMY_WEBP = b'RIFF\x1a\x00\x00\x00WEBPVP8L\r\x00\x00\x00/\x00\x00\x00\x10\x07\x10\x11\x11\x88\x88\xfe\x07\x00'


@allure.parent_suite("Auth Service")
@allure.suite("Invite")
@allure.sub_suite("Space Invitations - Avatar (Positive)")
@pytest.mark.parametrize(
    "file_ext, mime_type, file_content",
    [
        ("png", "image/png", DUMMY_PNG),
        ("jpg", "image/jpeg", DUMMY_JPEG),
        ("gif", "image/gif", DUMMY_GIF),
        ("webp", "image/webp", DUMMY_WEBP),
    ],
    ids=["png", "jpg", "gif", "webp"]
)
def test_invite_user_with_avatar_positive(second_main_client, space_id_, file_ext, mime_type, file_content):
    """
    Проверка позитивного сценария:
    1. Получение контекста пространства (заголовки).
    2. Загрузка валидного аватара (тип Space) на сервер с проверкой всех доступных форматов.
    3. Успешное приглашение нового пользователя в пространство с указанным avatarUrl.
    """
    allure.dynamic.title(f"(формат: {file_ext}) Приглашение пользователя с необязательными параметрами (Avatar)")

    with allure.step("Получение заголовков с ID пространства для обхода проверок безопасности"):
        space_req = get_space_members_endpoint(space_id=space_id_)
        space_headers = space_req.get("headers", {})

    with allure.step(f"Загрузка картинки аватара ({file_ext}) через multipart/form-data"):
        avatar_url = get_uploaded_avatar_url(
            client=second_main_client,
            kind_id=space_id_,
            kind="Space",
            file_content=file_content,
            headers=space_headers,
            file_name=f"test_avatar.{file_ext}",
            content_type=mime_type
        )

        assert avatar_url is not None, "URL аватара не должен быть None"
        assert len(avatar_url) > 0, "Длина URL аватара должна быть больше 0"

    with allure.step(f"Приглашение нового пользователя с загруженным аватаром ({avatar_url})"):
        invite_email = f"new_user_{uuid.uuid4().hex[:8]}@example.com"

        invite_req = invite_to_space_endpoint(
            space_id=space_id_,
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
            space_id=space_id_,
            email=invite_email
        )


@allure.parent_suite("Auth Service")
@allure.suite("Invite")
@allure.sub_suite("Space Invitations - Avatar (Negative)")
@allure.title("Загрузка аватара с невалидным параметром: {scenario}")
@pytest.mark.parametrize(
    "scenario, kind, file_tuple, expected_status",
    [
        (
                "Невалидный kind (не User и не Space)",
                "Member",
                ("avatar.png", DUMMY_PNG, "image/png"),
                400
        ),
        (
                "Невалидный формат файла (txt вместо картинки)",
                "Space",
                ("fake_image.txt", b"this is not an image", "text/plain"),
                400
        ),
    ]
    , ids=["invalid_kind","invalid_file_format"]
)

def test_upload_avatar_negative(second_main_client, space_id_, scenario, kind, file_tuple, expected_status):
    """
    Негативные сценарии эндпоинта UploadAvatar.
    Ожидаем, что сервер отклонит запрос со статусом 400 Bad Request.
    """
    with allure.step("Подготовка параметров запроса"):
        space_req = get_space_members_endpoint(space_id=space_id_)
        headers = space_req.get("headers", {})

        req = upload_avatar_endpoint(
            file_tuple=file_tuple,
            kind=kind,
            kind_id=space_id_,
        )

    with allure.step(f"Отправка запроса на загрузку аватара ({scenario})"):
        response = second_main_client.post(
            req["path"],
            data=req["data"],
            files=req["files"],
            headers=headers
        )

    with allure.step(f"Проверка, что сервер вернул ошибку {expected_status}"):
        assert response.status_code == expected_status, (
            f"Ожидался статус {expected_status}, но получен {response.status_code}. "
            f"Ответ сервера: {response.text}"
        )


@allure.parent_suite("Auth Service")
@allure.suite("Invite")
@allure.sub_suite("Space Invitations - Avatar (Negative)")
@allure.title("Загрузка аватара, превышающего лимит размера (> 100 МБ)")
def test_upload_avatar_too_large(second_main_client, space_id_):
    """
    Проверка лимита размера загружаемого файла (максимум 100 МБ).
    Генерируем "фейковый" файл размером 101 МБ в памяти и ожидаем ошибку EUploadErrorCode.FileSize.
    """

    with allure.step("Генерация файла размером 101 МБ в памяти"):
        # 101 мегабайт (испол/э
        # ьзуем множитель 1000, как на бэкенде: 101 * 1000 * 1000)
        large_file_size = 101 * 1000 * 1000
        # Создаем строку из нулей нужного размера
        huge_file_content = b"0" * large_file_size

    with allure.step("Подготовка параметров запроса"):
        space_req = get_space_members_endpoint(space_id=space_id_)
        headers = space_req.get("headers", {})
        headers.pop("Content-Type", None)

        req = upload_avatar_endpoint(
            file_tuple=("huge_avatar.png", huge_file_content, "image/png"),
            kind="Space",
            kind_id=space_id_,
        )

    with allure.step("Отправка огромного файла на сервер (может занять несколько секунд)"):
        response = second_main_client.post(
            req["path"],
            data=req["data"],
            files=req["files"],
            headers=headers
        )

    with allure.step("Проверка, что сервер вернул статус 400"):
        # Если защита стоит на уровне Nginx, он может вернуть 413, но если доходит до бэка - будет 400.
        assert response.status_code == 400, (
            f"Сервер пропустил файл размером >100МБ или вернул неверный статус! "
            f"Ожидался статус 400, получен {response.status_code}. "
            f"Ответ сервера: {response.text[:200]}"
        )

    with allure.step("Проверка контракта ошибки (code: FileSize)"):
        response_data = response.json()
        error_info = response_data.get("error", {})

        # Проверяем код ошибки согласно EUploadErrorCode.FileSize
        error_code = error_info.get("code")
        assert error_code == "FileSize", f"Ожидался код ошибки 'FileSize', получен: {error_code}"

        # Проверяем мету лимита
        error_meta_max = error_info.get("meta", {}).get("max")
        assert error_meta_max == "100.00 MB", f"Ожидался лимит '100.00 MB', получен: {error_meta_max}"