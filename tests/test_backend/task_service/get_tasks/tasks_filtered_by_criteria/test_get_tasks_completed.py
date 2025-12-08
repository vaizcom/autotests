import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

@allure.parent_suite("tasks_filtered_by_criteria")
@allure.title("Фильтрация задач: completed=false — возвращаются только незавершённые задачи")
def test_get_tasks_completed_false(owner_client, main_space, board_with_10000_tasks):
    """
    Проверяет, что при completed=false API возвращает только незавершённые задачи.
    """

    with allure.step("Запрашиваем задачи с completed=false"):
        resp = owner_client.post(**get_tasks_endpoint(space_id=main_space, board=board_with_10000_tasks, completed=False, limit=20))
        resp.raise_for_status()
        tasks = resp.json()["payload"].get("tasks", [])

    if not tasks:
        allure.attach("Пустая выборка", "Нет задач для проверки completed=false", allure.attachment_type.TEXT)
        pytest.skip("Нет задач для проверки completed=false")

    with allure.step("Проверяем, что отсутствуют завершённые задачи"):
        for t in tasks:
            assert t.get("completed") is not True, f"Задача {t.get('_id')} завершена при completed=false"
            assert t.get("completedAt") is None

    with allure.step("Проверяем отсутствие дубликатов"):
        ids = [t.get("_id") for t in tasks]
        assert len(ids) == len(set(ids)), f"Найдены дубликаты задач: {ids}"

@allure.parent_suite("tasks_filtered_by_criteria")
@allure.title("Фильтрация задач: completed=true — возвращаются только завершенные задачи")
def test_get_tasks_completed_true(owner_client, main_space, board_with_10000_tasks):
    """
    Проверяет, что при completed=true выдача включает только завершённые задачи и корректность их completedAt
    Если завершённых задач нет — тест заскипан с сообщением.
    """

    with allure.step("Запрашиваем задачи с completed=true"):
        resp = owner_client.post(**get_tasks_endpoint(space_id=main_space, board=board_with_10000_tasks, completed=True, limit=20))
        resp.raise_for_status()
        tasks = resp.json()["payload"].get("tasks", [])

    if not tasks:
        allure.attach("Пустая выборка", "Нет задач для проверки completed=true", allure.attachment_type.TEXT)
        pytest.skip("Нет задач для проверки completed=true")

    # Отбираем завершённые задачи
    completed_tasks = [t for t in tasks if t.get("completed") is True]
    if not completed_tasks:
        allure.attach("Нет завершённых задач", "В выборке отсутствуют задачи с completed=True", allure.attachment_type.TEXT)
        pytest.skip("Нет завершённых задач для проверки completed=true")

    with allure.step("Проверяем completedAt — непустая строка даты;"):
        for t in completed_tasks:
            # Ожидаем, что completedAt — непустая строка даты;
            completed_at = t.get("completedAt")
            assert isinstance(completed_at, str) and completed_at.strip(), (
                f"Некорректное completedAt у задачи {t.get('_id')}: {completed_at!r}"
            )

    with allure.step("Проверяем отсутствие дубликатов среди всех задач ответа"):
        ids = [t.get("_id") for t in tasks]
        assert len(ids) == len(set(ids)), f"Найдены дубликаты задач: {ids}"

@allure.parent_suite("tasks_filtered_by_criteria")
@allure.title("Фильтрация задач: completed некорректного типа — ошибка валидации (400)")
def test_get_tasks_completed_invalid_type(owner_client, main_space, board_with_10000_tasks):
    """
    Проверяет, что при передаче некорректного значения параметра completed (не boolean)
    API возвращает 400 и сообщение об ошибке валидации для поля completed.
    """

    with allure.step("Отправляем запрос с completed='' (пустая строка, не boolean)"):
        resp = owner_client.post(**get_tasks_endpoint(space_id=main_space, board=main_space, completed=""))
        status = resp.status_code
        body = resp.json()

    with allure.step("Проверяем код ответа и текст ошибки"):
        assert status == 400, f"Ожидался код 400 для ошибки валидации, получено: {status}"
        codes = next(
            (f.get("codes") for f in (body.get("error") or {}).get("fields", []) if f.get("name") == "completed"),
            []
        )
        assert "completed must be a boolean value" in codes, f"Нет ожидаемого сообщения. codes={codes!r}"
