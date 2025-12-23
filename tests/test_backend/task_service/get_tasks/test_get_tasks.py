import pytest
import allure

from test_backend.data.endpoints.Project.project_endpoints import get_projects_endpoint
from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

# Базовые smoke-тесты

@allure.parent_suite("Task Service")
@allure.suite("Get Tasks")
@allure.title("GetTasks smoke: базовый смоук — успешный ответ и массив tasks")
@allure.description("Проверка, что эндпоинт возвращает статус 200 и тело с полем tasks (массив).")
def test_get_tasks_minimal(owner_client, board_with_10000_tasks, main_space):
    with allure.step("Выполнить POST /GetTasks без доп. параметров"):
        response = owner_client.post(**get_tasks_endpoint(board=board_with_10000_tasks, space_id=main_space, limit=100))
    with allure.step("Проверить статус и контракт ответа"):
        assert response.status_code == 200
        data = response.json()['payload']
        assert "tasks" in data and isinstance(data["tasks"], list)


@allure.parent_suite("Task Service")
@allure.suite("Get Tasks")
@allure.title("GetTasks: пустой payload")
def test_get_tasks_with_empty_payload(owner_client,main_space):
    """
    Проверяет, что при запросе задач без фильтров возвращаются задачи только из проектов указанного space_id.
    Для этого сверяем projectId каждой задачи со списком проектов пространства.
    """
    with allure.step("Подготовка данных: Запрашиваем список проектов спейса"):
        resp_projects = owner_client.post(**get_projects_endpoint(space_id=main_space))
        resp_projects.raise_for_status()
        projects_payload = resp_projects.json().get("payload") or {}
        projects = projects_payload.get("projects") or []
        allowed_project_ids = {p.get("_id") for p in projects if isinstance(p, dict) and p.get("_id")}
        assert allowed_project_ids, "Список проектов спейса пуст — не с чем сравнивать projectId задач"

    with allure.step("Отправляем запрос get_tasks с пустым payload"):
        resp = owner_client.post(**get_tasks_endpoint(space_id=main_space))
        resp.raise_for_status()
        body = resp.json()

    with allure.step("Проверяем, что задачи принадлежат только указанному спейсу (проверка через projectId этого спейса)"):
        payload = body.get("payload") or {}
        tasks = payload.get("tasks") or []
        assert isinstance(tasks, list), "payload.tasks должен быть списком"
        ids = []
        for t in tasks:
            assert isinstance(t, dict), "Элемент tasks должен быть объектом"
            project_id = t.get("project")
            assert project_id in allowed_project_ids, f"Задача {t.get('_id')} с projectId={project_id!r} не из указанного спейса"
            ids.append(t.get("_id"))
        assert len(ids) == len(set(ids)), f"Найдены дубликаты задач: {ids}"