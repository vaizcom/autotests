import allure
import pytest

from test_backend.data.endpoints.multiaction.multiaction_endpoints import multiple_edit_tasks_endpoint
from test_backend.data.endpoints.multiaction.multiaction_asserts import assert_multiaction_response
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint
from test_backend.task_service.utils import get_two_random_types

pytestmark = [pytest.mark.backend]


def _get_task_types(client, space_id, task_id):
    """Получает список types задачи через GetTask."""
    r = client.post(**get_task_endpoint(space_id=space_id, slug_id=task_id))
    assert r.status_code == 200, r.text
    return r.json()["payload"]["task"].get("types", [])


@allure.parent_suite("Multiaction")
@allure.suite("Types")
@allure.sub_suite("Positive")
@allure.title("Add type на задачи без types")
def test_add_type(owner_client, main_space, main_board, make_task_in_main):
    """
    Задачи без types, добавляем один тип.
    Все задачи в success, GetTask подтверждает.
    """
    types = get_two_random_types(owner_client, main_board, main_space)
    type_id = types[0][0]

    with allure.step("Создаём 2 задачи без types"):
        tasks = [make_task_in_main({"name": f"type-add-{i}"}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step(f"Применяем MultipleEditTasks types=[typeId, 'add']"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            types=[type_id, "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids), (
            f"Ожидали success={task_ids}, получили: {payload['success']}"
        )
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"

    with allure.step("Проверяем через GetTask, что type назначен"):
        for tid in task_ids:
            task_types = _get_task_types(owner_client, main_space, tid)
            assert type_id in task_types, (
                f"Задача {tid}: ожидали {type_id} в types, получили: {task_types}"
            )


@allure.parent_suite("Multiaction")
@allure.suite("Types")
@allure.sub_suite("Positive")
@allure.title("Remove type")
def test_remove_type(owner_client, main_space, main_board, make_task_in_main):
    """
    Задачи с типом, убираем его.
    Все в success, GetTask подтверждает.
    """
    types = get_two_random_types(owner_client, main_board, main_space)
    type_id = types[0][0]

    with allure.step("Создаём 2 задачи с типом"):
        tasks = [make_task_in_main({"name": f"type-rm-{i}", "types": [type_id]}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Убираем тип через MultipleEditTasks"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            types=[type_id, "remove"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids), (
            f"Ожидали success={task_ids}, получили: {payload['success']}"
        )
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"

    with allure.step("Проверяем через GetTask, что тип убран"):
        for tid in task_ids:
            task_types = _get_task_types(owner_client, main_space, tid)
            assert type_id not in task_types, (
                f"Задача {tid}: тип не удалён: {task_types}"
            )


@allure.parent_suite("Multiaction")
@allure.suite("Types")
@allure.sub_suite("Positive")
@allure.title("Add type — тип уже есть у всех → все в skipped")
def test_add_type_already_set(owner_client, main_space, main_board, make_task_in_main):
    """
    Все задачи уже с нужным типом.
    Add type → все в skipped.
    """
    types = get_two_random_types(owner_client, main_board, main_space)
    type_id = types[0][0]

    with allure.step("Создаём 2 задачи с типом"):
        tasks = [make_task_in_main({"name": f"type-skip-{i}", "types": [type_id]}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Добавляем тот же тип"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            types=[type_id, "add"],
        ))

    with allure.step("Проверяем, что все в skipped"):
        payload = assert_multiaction_response(resp)
        assert sorted(payload["skipped"]) == sorted(task_ids), (
            f"Ожидали skipped={task_ids}, получили: {payload['skipped']}"
        )
        assert payload["success"] == [], f"success не пуст: {payload['success']}"
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"

    with allure.step("Проверяем через GetTask, что тип по-прежнему на месте"):
        for tid in task_ids:
            task_types = _get_task_types(owner_client, main_space, tid)
            assert type_id in task_types, (
                f"Задача {tid}: тип пропал после skipped: {task_types}"
            )


@allure.parent_suite("Multiaction")
@allure.suite("Types")
@allure.sub_suite("Positive")
@allure.title("Remove type — типа нет ни у одной → все в skipped")
def test_remove_type_not_set(owner_client, main_space, main_board, make_task_in_main):
    """
    Ни у одной задачи нет этого типа.
    Remove type → все в skipped.
    """
    types = get_two_random_types(owner_client, main_board, main_space)
    type_id = types[0][0]

    with allure.step("Создаём 2 задачи без types"):
        tasks = [make_task_in_main({"name": f"type-rm-skip-{i}"}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Убираем тип, которого нет"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            types=[type_id, "remove"],
        ))

    with allure.step("Проверяем, что все в skipped"):
        payload = assert_multiaction_response(resp)
        assert sorted(payload["skipped"]) == sorted(task_ids), (
            f"Ожидали skipped={task_ids}, получили: {payload['skipped']}"
        )
        assert payload["success"] == [], f"success не пуст: {payload['success']}"
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"

    with allure.step("Проверяем через GetTask, что types по-прежнему пуст"):
        for tid in task_ids:
            task_types = _get_task_types(owner_client, main_space, tid)
            assert type_id not in task_types, (
                f"Задача {tid}: тип появился после skipped: {task_types}"
            )


@allure.parent_suite("Multiaction")
@allure.suite("Types")
@allure.sub_suite("Positive")
@allure.title("Add type mixed — часть задач уже с типом")
def test_add_type_mixed_state(owner_client, main_space, main_board, make_task_in_main):
    """
    Часть задач уже с типом, часть без.
    Add type: без типа → success, с типом → skipped.
    """
    types = get_two_random_types(owner_client, main_board, main_space)
    type_id = types[0][0]

    with allure.step("Создаём 2 задачи без типа и 1 с типом"):
        without = [make_task_in_main({"name": f"type-mixed-add-{i}"}) for i in range(2)]
        with_type = [make_task_in_main({"name": "type-mixed-add-existing", "types": [type_id]})]
        without_ids = [t["_id"] for t in without]
        with_ids = [t["_id"] for t in with_type]
        all_ids = without_ids + with_ids

    with allure.step("Добавляем тип через MultipleEditTasks"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=all_ids,
            types=[type_id, "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задачи без типа в success"):
        assert sorted(payload["success"]) == sorted(without_ids), (
            f"Ожидали success={without_ids}, получили: {payload['success']}"
        )

    with allure.step("Проверяем, что задачи с типом в skipped"):
        assert sorted(payload["skipped"]) == sorted(with_ids), (
            f"Ожидали skipped={with_ids}, получили: {payload['skipped']}"
        )

    with allure.step("Проверяем, что failed пуст"):
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"

    with allure.step("Проверяем через GetTask, что у всех задач тип назначен"):
        for tid in all_ids:
            task_types = _get_task_types(owner_client, main_space, tid)
            assert type_id in task_types, (
                f"Задача {tid}: ожидали {type_id} в types, получили: {task_types}"
            )


@allure.parent_suite("Multiaction")
@allure.suite("Types")
@allure.sub_suite("Positive")
@allure.title("Add второй тип — первый сохраняется")
def test_add_second_type_keeps_first(owner_client, main_space, main_board, make_task_in_main):
    """
    Задача уже с типом type_1, добавляем type_2.
    type_2 в success, GetTask подтверждает оба типа.
    """
    types = get_two_random_types(owner_client, main_board, main_space)
    type_1_id = types[0][0]
    type_2_id = types[1][0]

    with allure.step("Создаём задачу с type_1"):
        task = make_task_in_main({"name": "add-second-type", "types": [type_1_id]})
        task_id = task["_id"]

    with allure.step("Добавляем type_2 через MultipleEditTasks"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[task_id],
            types=[type_2_id, "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в success"):
        assert payload["success"] == [task_id], (
            f"Ожидали success=[{task_id}], получили: {payload['success']}"
        )
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"

    with allure.step("Проверяем через GetTask, что оба типа на задаче"):
        task_types = _get_task_types(owner_client, main_space, task_id)
        assert type_1_id in task_types, (
            f"Первый тип пропал: {task_types}"
        )
        assert type_2_id in task_types, (
            f"Второй тип не добавлен: {task_types}"
        )


@allure.parent_suite("Multiaction")
@allure.suite("Types")
@allure.sub_suite("Positive")
@allure.title("Remove один из двух типов — второй остаётся")
def test_remove_one_of_two_types(owner_client, main_space, main_board, make_task_in_main):
    """
    Задача с двумя типами, убираем один.
    Задача в success, GetTask подтверждает что второй тип остался.
    """
    types = get_two_random_types(owner_client, main_board, main_space)
    type_1_id = types[0][0]
    type_2_id = types[1][0]

    with allure.step("Создаём задачу с двумя типами"):
        task = make_task_in_main({"name": "remove-one-of-two", "types": [type_1_id, type_2_id]})
        task_id = task["_id"]

    with allure.step("Убираем type_1 через MultipleEditTasks"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[task_id],
            types=[type_1_id, "remove"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в success"):
        assert payload["success"] == [task_id], (
            f"Ожидали success=[{task_id}], получили: {payload['success']}"
        )
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"

    with allure.step("Проверяем через GetTask, что type_1 убран, type_2 остался"):
        task_types = _get_task_types(owner_client, main_space, task_id)
        assert type_1_id not in task_types, (
            f"type_1 не удалён: {task_types}"
        )
        assert type_2_id in task_types, (
            f"type_2 пропал: {task_types}"
        )


@allure.parent_suite("Multiaction")
@allure.suite("Types")
@allure.sub_suite("Positive")
@allure.title("Remove type mixed — тип есть у части задач")
def test_remove_type_mixed_state(owner_client, main_space, main_board, make_task_in_main):
    """
    Часть задач с типом, часть без.
    Remove type: с типом → success, без типа → skipped.
    """
    types = get_two_random_types(owner_client, main_board, main_space)
    type_id = types[0][0]

    with allure.step("Создаём 1 задачу с типом и 2 без"):
        with_type = [make_task_in_main({"name": "type-mixed-rm-existing", "types": [type_id]})]
        without = [make_task_in_main({"name": f"type-mixed-rm-{i}"}) for i in range(2)]
        with_ids = [t["_id"] for t in with_type]
        without_ids = [t["_id"] for t in without]
        all_ids = with_ids + without_ids

    with allure.step("Убираем тип через MultipleEditTasks"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=all_ids,
            types=[type_id, "remove"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задачи с типом в success"):
        assert sorted(payload["success"]) == sorted(with_ids), (
            f"Ожидали success={with_ids}, получили: {payload['success']}"
        )

    with allure.step("Проверяем, что задачи без типа в skipped"):
        assert sorted(payload["skipped"]) == sorted(without_ids), (
            f"Ожидали skipped={without_ids}, получили: {payload['skipped']}"
        )

    with allure.step("Проверяем, что failed пуст"):
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"

    with allure.step("Проверяем через GetTask, что тип убран у success и не появился у skipped"):
        for tid in with_ids:
            task_types = _get_task_types(owner_client, main_space, tid)
            assert type_id not in task_types, (
                f"Задача {tid}: тип не удалён: {task_types}"
            )
        for tid in without_ids:
            task_types = _get_task_types(owner_client, main_space, tid)
            assert type_id not in task_types, (
                f"Задача {tid}: тип появился после skipped: {task_types}"
            )
