import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import duplicate_task_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Duplicate Task")
@allure.sub_suite("Access Check")
@allure.title("Негативный тест: Попытка сдублировать задачу на доску в другом спейсе (Cross-board/Cross-space)")
def test_duplicate_task_to_forbidden_board(main_client, main_space, temp_task, second_space, second_board, foreign_client):
    """
    Проверяет, что бэкенд пресекает попытку дублирования задачи (DuplicateTask)
    на доску (board_id), к которой у текущего пользователя нет доступа
    (например, доска находится в чужом Space или это приватная доска).
    """
    task_id = temp_task

    with allure.step("1. Пытаемся сдублировать задачу из main_space на доску в another_space"):
        # Пытаемся использовать уязвимость:
        # задача лежит в main_space, а мы подменяем board_id на чужую доску
        resp = main_client.post(
            **duplicate_task_endpoint(
                space_id=main_space,  # Авторизуемся в текущем спейсе
                task_id=task_id,  # Копируем нашу задачу
                board_id="6966448978f899c026adc166"  # Пытаемся положить её на чужую доску, есть в бд
            )
        )

    with allure.step("2. Проверяем, что запрос отклонен из-за прав доступа (403) и возвращает код ошибки 'AccessDenied' "):
        # Бэкенд должен вернуть либо 403 Forbidden (нет прав на целевую доску),
        # либо 400 Bad Request (если он проверяет, что board_id не принадлежит space_id)
        assert resp.status_code == 403, \
            f"УЯЗВИМОСТЬ! Бэкенд разрешил сдублировать задачу на чужую доску. Статус: {resp.status_code}, Ответ: {resp.text}"

        # Убеждаемся, что задача действительно не сдублировалась (ответ содержит ошибку, а не успешный payload)
        response_data = resp.json()
        assert "error" in response_data, "Бэкенд не вернул объект 'error' при запрещенном действии"

        # Если бэкенд возвращает конкретный код ошибки (например, 'AccessDenied')
        error_code = response_data.get("error", {}).get("code")
        assert error_code == "AccessDenied", f"Ожидалась ошибка доступа, получена: {error_code}"


@allure.parent_suite("Task Service")
@allure.suite("Duplicate Task")
@allure.sub_suite("Access Check")
@allure.title("Негативный тест: Попытка сдублировать задачу пользователем без доступа (foreign_client)")
def test_duplicate_task_by_foreign_client(foreign_client, main_space, main_board, temp_task):
    """
    Проверяет, что "чужой" пользователь (foreign_client), не являющийся участником
    main_space, получает ошибку AccessDenied при попытке сдублировать вашу задачу.
    """
    task_id = temp_task

    with allure.step("1. Чужой пользователь пытается сдублировать вашу задачу"):
        # foreign_client подставляет ваш space_id, task_id и board_id в свои заголовки
        resp = foreign_client.post(
            **duplicate_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                board_id=main_board
            )
        )

    with allure.step("2. Проверяем, что запрос отклонен из-за прав доступа (400) и возвращает код ошибки 'MemberDidNotFound'"):
        # Так как клиент "чужой", бэкенд вообще не должен пускать его в спейс
        assert resp.status_code == 400, \
            f"УЯЗВИМОСТЬ! Чужой пользователь смог выполнить DuplicateTask в вашем спейсе. Статус: {resp.status_code}, Ответ: {resp.text}"

        error_data = resp.json()

        # Проверяем структуру ошибки
        assert "error" in error_data, "В ответе отсутствует объект 'error'"

        error_code = error_data.get("error", {}).get("code")
        assert error_code == "MemberDidNotFound", \
            f"Ожидалась ошибка 'MemberDidNotFound', получена: '{error_code}'"