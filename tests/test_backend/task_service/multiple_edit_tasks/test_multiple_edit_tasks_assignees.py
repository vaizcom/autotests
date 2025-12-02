import pytest
import allure

from tests.test_backend.data.endpoints.Task.task_endpoints import (
    get_task_endpoint,
    multiple_edit_tasks_endpoint,
)

pytestmark = [pytest.mark.backend]

@allure.parent_suite("multiple_edit_tasks")
@allure.title("Multiple edit Tasks: назначение assignees задачам в которой уже был установлен assignee и задаче без assignee")
def test_multiple_edit_tasks_set_assignees(owner_client, main_space, main_project, main_board, main_personal, make_task_in_main):
    """
    Создаём 2 задачи в одной борде: у первой уже стоит ассайни, у второй нет.
    Затем применяем multiple_edit_tasks_endpoint и проверяем,
    что у обеих задач установлен только переданный ассайни.
    """
    with allure.step("Определяем целевого ассайни"):
        # Берём один валидный id из фикстуры main_personal по указанной роли
        target_assignee = main_personal["member"][0]

    with allure.step("Создаём задачу №1 c заранее установленным ассайни"):
        task1 = make_task_in_main({
            "name": "Task with assignee",
            "assignees": main_personal["manager"][0],
        })
        task1_id = task1["_id"]

    with allure.step("Создаём задачу №2 без ассайни"):
        task2 = make_task_in_main({
            "name": "Task without assignee",
        })
        task2_id = task2["_id"]

    with allure.step("Применяем multiple_edit_tasks с установленным ассайни у обеих задач"):
        payload = [
            {"taskId": task1_id, "assignees": target_assignee},
            {"taskId": task2_id, "assignees": target_assignee},
        ]
        resp_edit = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks=payload,
        ))
        assert resp_edit.status_code == 200, resp_edit.text

    with allure.step("Проверяем итоговые ассайни у задачи №1"):
        r1 = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task1_id))
        assert r1.status_code == 200, r1.text
        assignees_1 = r1.json()["payload"]["task"].get("assignees", [])
        assert assignees_1 == [target_assignee], f"Ожидался единственный ассайни {target_assignee}, получено {assignees_1}"

    with allure.step("Проверяем итоговые ассайни у задачи №2"):
        r2 = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task2_id))
        assert r2.status_code == 200, r2.text
        assignees_2 = r2.json()["payload"]["task"].get("assignees", [])
        assert assignees_2 == [target_assignee], f"Ожидался единственный ассайни {target_assignee}, получено {assignees_2}"


@allure.parent_suite("multiple_edit_tasks")
@allure.title("Multiple edit Tasks: неверный taskId должен попасть в failed при статусе 200")
def test_multiple_edit_tasks_invalid_id_failed(owner_client, main_space, main_board, make_task_in_main):
    """
    Передаём один валидный taskId и один несуществующий.
    Ожидаем HTTP 200 и что невалидный id попадает в список failed ответа.
    """
    with allure.step("Готовим валидную задачу и невалидный taskId"):
        valid_task = make_task_in_main({"name": "Valid task"})
        valid_id = valid_task["_id"]
        replaced_digit = "0" if valid_id[-1] != "0" else "1"
        invalid_id = valid_id[:-1] + replaced_digit

    with allure.step("Вызываем multiple_edit_tasks с валидным и невалидным taskId"):
        payload = [
            {"taskId": valid_id, "assignees": []},
            {"taskId": invalid_id, "assignees": []},
        ]
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks=payload,
        ))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        payload = body.get("payload", {})


    with allure.step("Проверяем, что невалидный id в списке failed, а валидный в success"):
        failed = payload.get("failed", [])
        success = payload.get("success", [])
        assert  success == [valid_id], f"Ожидали success=[{valid_id}], получили: {success}"
        assert failed == [invalid_id], f"Ожидали failed=[{invalid_id}], получили: {failed}"


@allure.parent_suite("multiple_edit_tasks")
@allure.title("Multiple edit Tasks: установка списка ассайни (мультиселект) для нескольких задач")
def test_multiple_edit_tasks_multiple_assignees(owner_client, main_space, main_board, main_personal, make_task_in_main):
    """
    Передаём список ассайни (мультиселект) и проверяем, что у обеих задач он установлен.
    """
    with allure.step("Определяем список ассайни (минимум два участника)"):
        a1 = main_personal["member"][0]
        a2 = main_personal["owner"][0]
        assignees_list = [a1, a2]

    with allure.step("Создаём две задачи через фикстуру-конструктор"):
        task1 = make_task_in_main({"name": "Task multi A"})
        task2 = make_task_in_main({"name": "Task multi B"})
        task1_id = task1["_id"]
        task2_id = task2["_id"]

    with allure.step("Назначаем список ассайни для обеих задач"):
        payload = [
            {"taskId": task1_id, "assignees": assignees_list},
            {"taskId": task2_id, "assignees": assignees_list},
        ]
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks=payload,
        ))
        assert resp.status_code == 200, resp.text

    with allure.step("Проверяем итоговые ассайни у задач"):
        r1 = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task1_id))
        r2 = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task2_id))
        assert r1.status_code == 200, r1.text
        assert r2.status_code == 200, r2.text
        a1_final = r1.json()["payload"]["task"].get("assignees", [])
        a2_final = r2.json()["payload"]["task"].get("assignees", [])
        assert a1_final == assignees_list, f"Task1: ожидали {assignees_list}, получили {a1_final}"
        assert a2_final == assignees_list, f"Task2: ожидали {assignees_list}, получили {a2_final}"


@allure.parent_suite("multiple_edit_tasks")
@allure.title("Multiple edit Tasks: некорректный assigneeId статус 400")
def test_multiple_edit_tasks_invalid_assignee_id(owner_client, main_space, main_board, main_personal, make_task_in_main):
    """
    Передаём валидный и заведомо некорректный идентификаторы ассайни (у второго последняя цифра заменена на 0).
    Ожидаем HTTP 400 и корректное сообщение об ошибке.
    Баг: CCSS-31512
    """
    with allure.step("Готовим валидные данные и генерируем невалидный assigneeId"):
        valid_assignee = main_personal["member"][0]
        valid_task = make_task_in_main({"name": "Valid task"})
        valid_id = valid_task["_id"]

        invalid_task = make_task_in_main({"name": "InValid task"})
        invalid_id = invalid_task["_id"]
        replaced_digit = "0" if valid_id[-1] != "0" else "1"
        invalid_assignee = valid_assignee[:-1] + replaced_digit

    with allure.step("Вызываем multiple_edit_tasks с валидным и невалидным assigneeId"):
        payload = [
            {"taskId": valid_id, "assignees": [valid_assignee]},
            {"taskId": invalid_id, "assignees": [invalid_assignee]},
        ]
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks=payload,
        ))
        assert resp.status_code == 200, resp.text # CCSS-31512 400


@allure.parent_suite("multiple_edit_tasks")
@allure.title("Multiple edit Tasks: снятие ассайни (передача пустого массива)")
def test_multiple_edit_tasks_clear_assignees(owner_client, main_space, main_board, main_personal, make_task_in_main):
    """
    Снимаем ассайни у задач, передав пустой список assignees.
    Ожидаем HTTP 200 и пустые списки ассайни в задачах.
    """
    with allure.step("Создаём задачи с заранее установленными ассайни"):
        a1 = main_personal["member"][0]
        a2 = main_personal["owner"][0]
        task1 = make_task_in_main({"name": "Task clear A", "assignees": [a1, a2]})
        task2 = make_task_in_main({"name": "Task clear B", "assignees": a1})
        task3 = make_task_in_main({"name": "Task clear C"})
        task1_id, task2_id, task3_id = task1["_id"], task2["_id"], task3["_id"]

    with allure.step("Снимаем ассайни, передав пустой массив"):
        payload = [
            {"taskId": task1_id, "assignees": []},
            {"taskId": task2_id, "assignees": []},
            {"taskId":task3_id, "assignees": []}
        ]
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks=payload,
        ))
        assert resp.status_code == 200, resp.text
        assert resp.json()["payload"]["success"] == [task1_id, task2_id, task3_id]
        assert resp.json()["payload"]["failed"] == []

    with allure.step("Проверяем, что у обеих задач ассайни сняты"):
        r1 = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task1_id))
        r2 = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task2_id))
        r3 = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task3_id))
        assert r1.status_code == 200, r1.text
        assert r2.status_code == 200, r2.text
        assert r3.status_code == 200, r3.text
        assignees_1 = r1.json()["payload"]["task"].get("assignees", [])
        assignees_2 = r2.json()["payload"]["task"].get("assignees", [])
        assignees_3 = r3.json()["payload"]["task"].get("assignees", [])
        assert assignees_1 == [], f"Task1: ожидали пустой список ассайни, получили {assignees_1}"
        assert assignees_2 == [], f"Task2: ожидали пустой список ассайни, получили {assignees_2}"
        assert assignees_3 == [], f"Task3: ожидали пустой список ассайни, получили {assignees_3}"