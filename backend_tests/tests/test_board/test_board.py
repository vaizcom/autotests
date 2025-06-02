import allure
import pytest

from backend_tests.data.endpoints.Board.board_endpoints import create_board_endpoint, create_board_custom_field_endpoint
from backend_tests.data.endpoints.Board.custom_field_types import CustomFieldType
from backend_tests.utils.generators import generate_board_name
from backend_tests.data.endpoints.Board.constants import (
    MAX_BOARD_NAME_LENGTH,
    BOARD_CUSTOM_FIELD_MAX_DESCRIPTION_LENGTH, DEFAULT_BOARD_GROUP_NAME, BOARD_CUSTOM_FIELD_MAX_TITLE_LENGTH,
    generate_custom_field_title
)


@allure.title("Создание борды в существующем проекте и корректность возвращаемого имени")
def test_create_board(owner_client, temp_project, temp_space):
    # Генерация имени борды
    name = generate_board_name()
    # Отправка запроса и проверка результата
    with allure.step("Отправка запроса на создание борды с валидными данными"):
        response = owner_client.post(**create_board_endpoint(
            name,
            temp_project,
            temp_space,
            [],
            [],
            []))

    # Проверяем статус и возвращаемое имя борды
    with allure.step("Проверка успешного ответа от API"):
        assert response.status_code == 200, f"Ошибка: {response.text}"

    with allure.step("Проверка корректности имени созданной борды"):
        response_data = response.json()
        assert "payload" in response_data, "Ошибка: В ответе отсутствует поле 'payload'"
        assert "board" in response_data["payload"], "Ошибка: В 'payload' отсутствует объект 'board'"
        assert response_data["payload"]["board"]["name"] == name, (
            f"Ожидалось имя борды '{name}', а получено '{response_data['payload']['board']['name']}'"
        )


@allure.title("Ошибка при создание борды с пустым именем")
def test_create_board_empty_name(owner_client, temp_project, temp_space):
    name = ""

    with allure.step("Отправка запроса на создание борды с пустым именем"):
        response = owner_client.post(**create_board_endpoint(
            name,
            temp_project,
            temp_space,
            [],
            [],
            []
        ))

    with allure.step("Проверка, что вернулась ошибка 400 – ошибка валидации"):
        assert response.status_code == 400


@allure.title("Создание нескольких борд с одинаковым именем в одном проекте")
def test_create_board_with_duplicate_name_allowed(owner_client, temp_project, temp_space):
    name = generate_board_name()

    with allure.step("Создание первой борды с именем"):
        response1 = owner_client.post(**create_board_endpoint(
            name, temp_project, temp_space, [], [], []
        ))
        assert response1.status_code == 200

    with allure.step("Повторная попытка создать борду с тем же именем"):
        response2 = owner_client.post(**create_board_endpoint(
            name, temp_project, temp_space, [], [], []
        ))

    with allure.step("Проверка, что API вернул 200"):
        assert response2.status_code == 200


@allure.title("Ошибка при создании борды с именем длиннее допустимого")
def test_create_board_name_too_long(owner_client, temp_project, temp_space):
    long_name = "X" * (MAX_BOARD_NAME_LENGTH+1)

    with allure.step(f"Попытка создать борду с именем из {len(long_name)} символов"):
        response = owner_client.post(**create_board_endpoint(
            long_name, temp_project, temp_space, [], [], []
        ))

    with allure.step("Проверка, что API вернул 400 – ошибка валидации"):
        assert response.status_code == 400

@allure.title("Ошибка при создании борды с None вместо списков в полях groups/typesList/customFields")
def test_create_board_with_none_fields(owner_client, temp_project, temp_space):
    name = generate_board_name()

    with allure.step("Отправка запроса, где списочные поля переданы как None"):
        response = owner_client.post(**create_board_endpoint(
            name,
            temp_project,
            temp_space,
            None,
            None,
            None
        ))

    with allure.step("Проверка, что API вернул 400 – ошибка валидации типов"):
        assert response.status_code == 400

@allure.title("Создание борды с именем максимальной длины (50 символов)")
def test_create_board_with_max_name_length(owner_client, temp_project, temp_space):
    name = "B" * MAX_BOARD_NAME_LENGTH  # Ровно 50 символов

    with allure.step("Отправка запроса на создание борды с максимальной длиной имени"):
        response = owner_client.post(**create_board_endpoint(
            name,
            temp_project,
            temp_space,
            [],
            [],
            []
        ))

    with allure.step("Проверка, что API вернул 200 и борда создана"):
        assert response.status_code == 200
        assert response.json()["payload"]["board"]["name"] == name, (
            f"Ожидалось имя борды '{name}', а получено '{response['payload']['board']['name']}'"
        )

@allure.title("Создание борды с описанием максимальной длины(Поле отсутствует на фронте)")
def test_create_board_with_max_description(owner_client, temp_project, temp_space):
    name = generate_board_name()
    description = "D" * BOARD_CUSTOM_FIELD_MAX_DESCRIPTION_LENGTH

    with allure.step(f"Отправка запроса на создание борды с описанием длиной {BOARD_CUSTOM_FIELD_MAX_DESCRIPTION_LENGTH} символов"):
        response = owner_client.post(**create_board_endpoint(
            name=name,
            temp_project=temp_project,
            space_id=temp_space,
            groups=[],
            typesList=[],
            customFields=[],
            description=description
        ))

    with allure.step("Проверка, что API вернул 200 и описание корректно сохранено"):
        assert response.status_code == 200


@pytest.mark.xfail(reason="Известный баг: длинный заголовок custom field без пробелов не влезает в тултип (APP-2763)")
@allure.label("bug", "APP-2763")
@allure.title("Ошибка при создании борды с заголовком custom field длиннее 25 символов (Баг: до 50 символов - APP-2763 )")
def test_create_board_with_long_custom_field_title(owner_client, temp_project, temp_space):
    name = generate_board_name()

    custom_field = "T" * (BOARD_CUSTOM_FIELD_MAX_TITLE_LENGTH + 1)

    with allure.step(f"Отправка запроса с custom field title длиннее {BOARD_CUSTOM_FIELD_MAX_TITLE_LENGTH} символов"):
        response = owner_client.post(**create_board_endpoint(
            name=name,
            temp_project=temp_project,
            space_id=temp_space,
            groups=[],
            typesList=[],
            customFields=[custom_field]
        ))

    with allure.step("Проверка, что API вернул 400 – ошибка валидации длины заголовка"):
        assert response.status_code == 400


@pytest.mark.parametrize("field_type", CustomFieldType.list())
@allure.title("Создание кастомного поля типа: {field_type}")
def test_create_custom_field_of_each_type(owner_client, temp_board, field_type, temp_space):
    title = generate_custom_field_title()

    with allure.step(f"Создание поля типа '{field_type}' с валидным заголовком"):
        response = owner_client.post(**create_board_custom_field_endpoint(
            board_id=temp_board,
            name=title,
            type=field_type,
            space_id=temp_space
        ))

    with allure.step("Проверка, что API вернул 200"):
        assert response.status_code == 200
        assert response.json()["payload"]["customField"]["name"] == title
        assert response.json()["payload"]["customField"]["type"] == field_type

