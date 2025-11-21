import pytest
import allure
from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

@allure.title("GetTasks ids: один существующий id -> ровно одна задача")
def test_get_tasks_ids_single(owner_client, main_space, board_with_tasks, task_id_list):
    expected_id = task_id_list[0]

    with allure.step("Выполнить запрос с одним id"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            ids=[expected_id]
        ))

    with allure.step("Проверить успешный ответ и состав"):
        assert response.status_code == 200, f"Ожидался статус 200, получено: {response.status_code}"
        payload = response.json().get("payload", {})
        tasks = payload.get("tasks", [])
        assert isinstance(tasks, list), "payload.tasks должен быть массивом"
        assert len(tasks) == 1, f"Ожидалась ровно одна задача, получено: {len(tasks)}"
        actual_id = tasks[0].get("_id")
        assert actual_id == expected_id, f"ID единственной задачи некорректен: {actual_id} != {expected_id}"
        assert [t.get("_id") for t in tasks] == [expected_id], "Список id в ответе не соответствует ожидаемому"

@allure.title("GetTasks ids: несколько существующих id -> соответствующие задачи в ответе")
def test_get_tasks_ids_multiple(owner_client, main_space, board_with_tasks, task_id_list):
    # Берём первые три id (или столько, сколько есть)
    expected_ids = task_id_list[:3]

    with allure.step(f"Выполнить запрос с несколькими id ({len(expected_ids)})"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            ids=expected_ids
        ))

    with allure.step("Проверить HTTP 200 и состав задач"):
        assert response.status_code == 200, f"Ожидался статус 200, получено: {response.status_code}"
        payload = response.json().get("payload", {})
        tasks = payload.get("tasks", [])
        assert isinstance(tasks, list), "payload.tasks должен быть массивом"
        # Проверяем, что вернулись только запрошенные задачи (порядок может не совпадать)
        returned_ids = [t.get("_id") for t in tasks]
        assert len(tasks) == len(expected_ids), f"Ожидалось {len(expected_ids)} задач, получено: {len(tasks)}"
        assert set(returned_ids) == set(expected_ids), f"Набор id не совпадает: {returned_ids} != {expected_ids}"

@allure.title("GetTasks ids: пустой массив -> 200 и пустой tasks")
def test_get_tasks_ids_empty_array(owner_client, main_space, board_with_tasks):
    with allure.step("Выполнить запрос с ids=[]"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            ids=[]
        ))
    with allure.step("Проверить HTTP 200 и пустой список задач"):
        assert response.status_code == 200
        payload = response.json().get("payload", {})
        tasks = payload.get("tasks", [])
        assert isinstance(tasks, list), "payload.tasks должен быть массивом"
        assert len(tasks) == 0, f"Ожидался пустой список задач, получено: {len(tasks)}"

@allure.title("GetTasks ids: дубликаты во входных ids")
def test_get_tasks_ids_with_duplicates(owner_client, main_space, board_with_tasks, task_id_list):
    # Берём два валидных id (или один, если доступен только один, дублируем его)
    base_ids = task_id_list[:2] if len(task_id_list) >= 2 else [task_id_list[0]]
    duplicated_ids = [base_ids[0]] + base_ids + [base_ids[0]]  # намеренно добавляем дубли

    with allure.step(f"Выполнить запрос с дубликатами ids: {duplicated_ids}"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            ids=duplicated_ids
        ))

    with allure.step("Проверить HTTP 200 и отсутствие дубликатов задач в ответе"):
        assert response.status_code == 200
        tasks = response.json().get("payload", {}).get("tasks", [])
        returned_ids = [t.get("_id") for t in tasks]
        # В большинстве контрактов возвращаются уникальные задачи
        assert len(set(returned_ids)) == len(returned_ids), "В ответе не должно быть дубликатов задач"
        # И набор _id должен совпадать с уникальным множеством входных id
        assert set(returned_ids) == set(duplicated_ids), "Набор _id не совпадает с запрошенными (без дублей)"

@allure.title("GetTasks ids: несуществующие id -> 200 и пустой tasks")
def test_get_tasks_ids_nonexistent(owner_client, main_space, board_with_tasks):
    nonexistent_ids = ["1" * 24, "2" * 24]  # валидные по формату ObjectId, но несуществующие

    with allure.step("Выполнить запрос с несуществующими id"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            ids=nonexistent_ids
        ))

    with allure.step("Проверить HTTP 200 и пустой список задач"):
        assert response.status_code == 200
        tasks = response.json().get("payload", {}).get("tasks", [])
        assert isinstance(tasks, list)
        assert len(tasks) == 0, f"Ожидался пустой список задач, получено: {len(tasks)}"


@allure.title("GetTasks ids: неверный формат id внутри массива -> 400 и корректная ошибка")
def test_get_tasks_ids_invalid_format(owner_client, main_space, board_with_tasks, task_id_list):
    # Формируем массив с одним корректным и несколькими некорректными элементами
    valid_id = task_id_list[0]
    invalid_values = ["CCSS-18137"]  # пример передачи hrid
    ids_with_invalids = [valid_id] + invalid_values

    with allure.step("Выполнить запрос с ids, содержащим элементы неверного формата"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            ids=ids_with_invalids
        ))

    with allure.step("Проверить HTTP 400 и наличие валидационной ошибки по ids"):
        assert response.status_code == 400, f"Ожидался статус 400, получено: {response.status_code}"
        error = response.json().get("error", {})
        assert error.get("code") == "InvalidForm", "Ожидался код ошибки валидации формы"
 