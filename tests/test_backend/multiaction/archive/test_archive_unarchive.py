import allure
import pytest

from test_backend.data.endpoints.multiaction.multiaction_endpoints import (
    multiple_archive_tasks_endpoint,
    multiple_unarchive_tasks_endpoint,
)
from test_backend.data.endpoints.multiaction.multiaction_asserts import assert_multiaction_response
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint
from test_backend.data.endpoints.archive.archive_task_endpoint import archive_task_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Multiaction")
@allure.suite("Archive")
@allure.sub_suite("Positive")
@allure.title("Archive: архивировать несколько задач")
def test_archive_tasks(owner_client, main_space, make_task_in_main):
    with allure.step("Создаём 3 задачи"):
        tasks = [make_task_in_main({"name": f"arch-test-{i}"}) for i in range(3)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Архивируем через MultipleArchiveTasks"):
        resp = owner_client.post(**multiple_archive_tasks_endpoint(
            space_id=main_space, tasks_ids=task_ids,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids)
        assert payload["failed"] == []
        assert payload["skipped"] == []

    with allure.step("Проверяем через GetTask, что задачи архивированы"):
        for tid in task_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            task = r.json()["payload"]["task"]
            assert task.get("archivedAt") is not None, f"Задача {tid} не архивирована"


@allure.parent_suite("Multiaction")
@allure.suite("Archive")
@allure.sub_suite("Positive")
@allure.title("Archive: задача уже в архиве → skipped")
def test_archive_already_archived_skipped(owner_client, main_space, make_task_in_main):
    with allure.step("Создаём задачу и архивируем"):
        task = make_task_in_main({"name": "arch-skip"})
        task_id = task["_id"]
        r = owner_client.post(**archive_task_endpoint(task_id=task_id, space_id=main_space))
        assert r.status_code == 200, r.text

    with allure.step("Пытаемся архивировать повторно"):
        resp = owner_client.post(**multiple_archive_tasks_endpoint(
            space_id=main_space, tasks_ids=[task_id],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert payload["skipped"] == [task_id]
        assert payload["success"] == []


@allure.parent_suite("Multiaction")
@allure.suite("Archive")
@allure.sub_suite("Positive")
@allure.title("Archive: mixed — часть уже в архиве, часть нет")
def test_archive_mixed_state(owner_client, main_space, make_task_in_main):
    with allure.step("Создаём 2 задачи, одну архивируем"):
        task_new = make_task_in_main({"name": "arch-mix-new"})
        task_archived = make_task_in_main({"name": "arch-mix-done"})
        owner_client.post(**archive_task_endpoint(
            task_id=task_archived["_id"], space_id=main_space,
        ))

    with allure.step("Архивируем обе через multiaction"):
        all_ids = [task_new["_id"], task_archived["_id"]]
        resp = owner_client.post(**multiple_archive_tasks_endpoint(
            space_id=main_space, tasks_ids=all_ids,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем: новая в success, уже архивированная в skipped"):
        assert payload["success"] == [task_new["_id"]]
        assert payload["skipped"] == [task_archived["_id"]]
        assert payload["failed"] == []


@allure.parent_suite("Multiaction")
@allure.suite("Archive")
@allure.sub_suite("Positive")
@allure.title("Unarchive: разархивировать несколько задач")
def test_unarchive_tasks(owner_client, main_space, make_task_in_main):
    """Unarchive работает только из Table Task — архивные задачи пропадают с доски и их нельзя выделить."""
    with allure.step("Создаём 3 задачи и архивируем"):
        tasks = [make_task_in_main({"name": f"unarch-test-{i}"}) for i in range(3)]
        task_ids = [t["_id"] for t in tasks]
        for tid in task_ids:
            owner_client.post(**archive_task_endpoint(task_id=tid, space_id=main_space))

    with allure.step("Разархивируем через MultipleUnarchiveTasks"):
        resp = owner_client.post(**multiple_unarchive_tasks_endpoint(
            space_id=main_space, tasks_ids=task_ids,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids)
        assert payload["failed"] == []
        assert payload["skipped"] == []

    with allure.step("Проверяем через GetTask, что задачи разархивированы"):
        for tid in task_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            task = r.json()["payload"]["task"]
            assert task.get("archivedAt") is None, f"Задача {tid} всё ещё в архиве"


@allure.parent_suite("Multiaction")
@allure.suite("Archive")
@allure.sub_suite("Positive")
@allure.title("Unarchive: задача не в архиве → skipped")
def test_unarchive_not_archived_skipped(owner_client, main_space, make_task_in_main):
    with allure.step("Создаём задачу (не архивируем)"):
        task = make_task_in_main({"name": "unarch-skip"})
        task_id = task["_id"]

    with allure.step("Пытаемся разархивировать"):
        resp = owner_client.post(**multiple_unarchive_tasks_endpoint(
            space_id=main_space, tasks_ids=[task_id],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert payload["skipped"] == [task_id]
        assert payload["success"] == []


@allure.parent_suite("Multiaction")
@allure.suite("Archive")
@allure.sub_suite("Positive")
@allure.title("Unarchive: mixed — часть в архиве, часть нет")
def test_unarchive_mixed_state(owner_client, main_space, make_task_in_main):
    with allure.step("Создаём 2 задачи, одну архивируем"):
        task_active = make_task_in_main({"name": "unarch-mix-active"})
        task_archived = make_task_in_main({"name": "unarch-mix-arch"})
        owner_client.post(**archive_task_endpoint(
            task_id=task_archived["_id"], space_id=main_space,
        ))

    with allure.step("Разархивируем обе через multiaction"):
        all_ids = [task_active["_id"], task_archived["_id"]]
        resp = owner_client.post(**multiple_unarchive_tasks_endpoint(
            space_id=main_space, tasks_ids=all_ids,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем: архивированная в success, активная в skipped"):
        assert payload["success"] == [task_archived["_id"]]
        assert payload["skipped"] == [task_active["_id"]]
        assert payload["failed"] == []
