import pytest
import allure

from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint

pytestmark = [pytest.mark.backend]

@pytest.mark.parametrize(
    "slug_id, expected_status",
    [
        (None, 400),                  # нет slug
        ("", 400),                    # пустой slug
        ("NOT-EXIST-999999", 400),    # несуществующий
        ("<script>", 400),            # XSS
        ("1 OR 1=1", 400),            # SQLi
        ("A" * 9, 400),            # слишком длинный
    ],
    ids=["no_slug", "empty_slug", "not_found", "xss", "sqli", "too_long"],
)
def test_get_task_wrong_slug(main_space, slug_id, expected_status, owner_client):
    """
        Проверка обработки некорректных значений slug при получении задачи.
        Ожидаем корректные коды ошибок для разных невалидных входных данных.
        """
    allure.dynamic.title(f"Негативные сценарии: Get task с invalid slug | slug={slug_id!r} -> {expected_status}")

    with allure.step("Готовим параметры запроса"):
        endpoint = get_task_endpoint(space_id=main_space, slug_id=slug_id)

    with allure.step(f"Отправляем запрос: slug_id={slug_id}"):
        response = owner_client.post(**endpoint)

    with allure.step(f"Проверяем код ответа == {expected_status}"):
        if isinstance(slug_id, str):
            assert response.status_code == expected_status, f"Ожидался {expected_status}, получено {response.status_code}"

