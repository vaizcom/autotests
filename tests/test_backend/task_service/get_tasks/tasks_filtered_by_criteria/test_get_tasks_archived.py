import allure
import pytest

from tests.test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Task Service")
@allure.suite("Get Tasks")
@allure.sub_suite("Filtered by criteria")
@allure.title("GetTasks: фильтр по archived=false — возвращаются только неархивные задачи")
def test_get_tasks_archived_false(owner_client, main_space, board_with_10000_tasks):
    """
    Проверяет, что при Archived=false API возвращает только неархивные задачи.

    Ожидаемый результат:
    - Нет архивных задач
    - Все задачи имеют archived/archiver is None.
    """
    with allure.step("Запрашиваем задачи с Archived=false"):
        resp = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            archived=False,
            limit=20,
            board=board_with_10000_tasks))
        resp.raise_for_status()
        tasks = resp.json()["payload"].get("tasks", [])

    if not tasks:
        allure.attach("Пустая выборка", "Нет задач для проверки withArchived=false", allure.attachment_type.TEXT)
        pytest.skip("Нет задач для проверки withArchived=false")

    with allure.step("Проверяем, что отсутствуют архивные задачи (Все задачи имеют archived/archiver is None)"):
        for t in tasks:
            assert t.get("archivedAt") is None, f"Задача {t.get('_id')} помечена как архивная при withArchived=false"
            assert t.get("archiver") is None, f"Задача {t.get('_id')} помечена как архивная при withArchived=false"


@allure.parent_suite("Task Service")
@allure.suite("Get Tasks")
@allure.sub_suite("Filtered by criteria")
@allure.title("GetTasks: фильтр по archived=true — возвращаются only архивные задачи")
def test_get_tasks_archived_true(owner_client, main_space, board_with_10000_tasks):
    """
    Проверяет, что при Archived=true API возвращает архивные задачи, и валидирует поля у архивных.

    Шаги:
    1. Запросить задачи с Archived=true.
    2. Убедиться, что в выборке есть хотя бы одна архивная задача (archivedAt — строка).
       Если архивных нет — скипнуть тест с сообщением.
    3. Для архивных задач проверить:
       - archivedAt — непустая строка (дата/время),
       - archiver — непустая строка (ID пользователя, заархивировавшего задачу).
    4. Убедиться что в выборке отсутствуют неархивные задачи Archived=false
    5. Проверить отсутствие дубликатов по _id.
    """

    with allure.step("Запрашиваем задачи с Archived=true"):
        resp = owner_client.post(**get_tasks_endpoint(space_id=main_space, archived=True, board=board_with_10000_tasks))
        resp.raise_for_status()
        tasks = resp.json()["payload"].get("tasks", [])

    if not tasks:
        allure.attach("Пустая выборка", "Нет задач для проверки Archived=true", allure.attachment_type.TEXT)
        pytest.skip("Нет задач для проверки Archived=true")

        # Сразу отфильтруем архивные задачи
    archived_tasks = [t for t in tasks if isinstance(t.get("archivedAt"), str) and t.get("archivedAt").strip()]

    if not archived_tasks:
        allure.attach("Нет архивных задач", "В выборке отсутствуют задачи с archivedAt как непустой строкой",
                      allure.attachment_type.TEXT)
        pytest.skip("Нет архивных задач для проверки полей archivedAt/archiver при Archived=true")

    with allure.step("Проверяем корректность archivedAt и archiver у архивных задач"):
        for t in archived_tasks[:20]:
            archived_at = t.get("archivedAt")
            archiver = t.get("archiver")
            assert isinstance(archived_at,
                              str) and archived_at.strip(), f"Некорректное archivedAt у задачи {t.get('_id')}: {archived_at!r}"
            assert isinstance(archiver,
                              str) and archiver.strip(), f"У архивной задачи {t.get('_id')} отсутствует/пустой archiver: {archiver!r}"

            # Фильтруем Неархивные задачи (у которых archivedAt не строка -> None)
    with allure.step("Проверяем корректность archivedAt у неархивных задач"):
        non_archived_tasks = [t for t in tasks if not (isinstance(t.get("archivedAt"), str) and t.get("archivedAt").strip())]
        assert non_archived_tasks == []


    with allure.step("Проверяем отсутствие дубликатов среди всех задач ответа"):
        ids = [t.get("_id") for t in tasks]
        assert len(ids) == len(set(ids)), f"Найдены дубликаты задач: {ids}"


@allure.parent_suite("Task Service")
@allure.suite("Get Tasks")
@allure.sub_suite("Filtered by criteria")
@allure.title("Фильтрация задач: Archived некорректного типа — ошибка валидации (400)")
def test_get_tasks_archived_invalid_type(owner_client, main_space, board_with_10000_tasks):
    """
    Проверяет, что при передаче некорректного значения параметра withArchived (не boolean)
    API возвращает 400 и сообщение: 'withArchived must be a boolean value'.
    """
    with allure.step("Отправляем запрос с withArchived=[] (не boolean)"):
        response = owner_client.post(**get_tasks_endpoint(space_id=main_space, archived=[]))

    with allure.step("Проверяем код ответа и структуру ошибки валидации"):
        with allure.step("Проверить HTTP 400 и наличие валидационной ошибки"):
            assert response.status_code == 400, f"Ожидался статус 400, получено: {response.status_code}"
            error = response.json().get("error", {})
            assert error.get("code") == "InvalidForm", "Ожидался код ошибки валидации формы"