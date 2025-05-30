import allure
from backend_tests.data.endpoints.Board.board_endpoints import create_board_endpoint
from backend_tests.utils.generators import generate_board_name
from backend_tests.data.endpoints.Board.constants import MAX_BOARD_NAME_LENGTH



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


@allure.title("Создание борды с пустым именем")
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
