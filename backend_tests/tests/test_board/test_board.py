import allure
from backend_tests.data.endpoints.Board.board_endpoints import create_board_endpoint
from backend_tests.utils.generators import generate_board_name

@allure.title("Создание борды в существующем проекте")
def test_create_board(owner_client, created_project_id, temp_space):
    name = generate_board_name()
    common_kwargs = {
        "groups": [{"name": "Группа по умолчанию", "description": "Авто-созданная группа"}],
        "typesList": [{"label": "Задача", "color": "blue", "icon": "Dot", "description": ""}],
        "customFields": []
    }
    with allure.step("Отправка запроса на создание борды с валидными данными"):
        response = owner_client.post(**create_board_endpoint(name=name, project_id=created_project_id, space_id=temp_space, **common_kwargs))
    with allure.step("Проверка успешного ответа от API"):
        assert response.status_code == 200, f"Ошибка: {response.text}"
    with allure.step("Проверка корректности имени созданной борды"):
        assert response.json()["payload"]["board"]["name"] == name
