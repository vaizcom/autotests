import pytest
import allure

from config.settings import MAIN_SPACE_ID, BOARD_WITH_TASKS, MILESTONE_2_ID, MILESTONE_1_ID
from tests.test_backend.data.endpoints.milestone.milestones_endpoints import (
    get_milestone_endpoint,
)
from tests.test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

@allure.title("Фильтрация задач по одному milestone")
def test_get_tasks_filtered_by_single_milestone(owner_client):
    """
    Тест проверяет корректность фильтрации задач по одному milestone.

    Цель:
    Убедиться, что API возвращает только те задачи, которые содержат указанный milestone.

    """
    space_id = MAIN_SPACE_ID
    board_id = BOARD_WITH_TASKS
    ms_id = MILESTONE_1_ID

    with allure.step("Подготовка к тесту: Проверяем, что milestone существует и доступен"):
        resp_ms = owner_client.post(**get_milestone_endpoint(ms_id=ms_id, space_id=space_id))
        resp_ms.raise_for_status()
        ms = resp_ms.json()["payload"]["milestone"]
        assert ms["_id"] == ms_id, "Возвращён другой milestone"

    with allure.step("Запрашиваем задачи с фильтром по milestones=[ms_id]"):
        resp_tasks = owner_client.post(**get_tasks_endpoint(space_id=space_id, board_id=board_id, milestones=[ms_id]))
        resp_tasks.raise_for_status()
        payload = resp_tasks.json()["payload"]
        tasks = payload.get("tasks", [])

    with allure.step("Проверяем, что задача содержит указанный milestone"):
        for t in tasks:
            task_ms = t.get("milestones") or t.get("milestone") or []
            if isinstance(task_ms, str):
                task_ms = [task_ms]
            assert ms_id in task_ms, f"Задача {t.get('_id')} не соответствует фильтру по milestone {ms_id}"

@allure.title("Фильтрация задач по нескольким milestones (OR-поведение)")
def test_get_tasks_filtered_by_multiple_milestones(owner_client):
    """
        Тест проверяет фильтрацию задач по нескольким milestone с OR-поведением.

        Цель:
        Убедиться, что каждая возвращённая задача содержит хотя бы один из указанных milestones.

        Ожидаемый результат:
        - Все задачи удовлетворяют условию OR (ms1 или ms2).
        - Ошибки HTTP отсутствуют.
        """
    space_id = MAIN_SPACE_ID
    board_id = BOARD_WITH_TASKS
    ms1 = MILESTONE_1_ID
    ms2 = MILESTONE_2_ID

    with allure.step("Подготовка к тесту: Проверяем наличие обоих milestones в спейсе"):
        for ms_id in (ms1, ms2):
            r = owner_client.post(**get_milestone_endpoint(ms_id=ms_id, space_id=space_id))
            r.raise_for_status()
            assert r.json()["payload"]["milestone"]["_id"] == ms_id

    with allure.step("Запрашиваем задачи по двум milestones"):
        resp = owner_client.post(**get_tasks_endpoint(space_id=space_id, board_id=board_id, milestones=[ms1, ms2]))
        resp.raise_for_status()
        tasks = resp.json()["payload"].get("tasks", [])

    with allure.step("Проверяем, что каждая задача содержит хотя бы один из указанных milestones (OR-поведение)"):
        for t in tasks:
            task_ms = t.get("milestones")
            if isinstance(task_ms, str):
                task_ms = [task_ms]
            assert any(m in task_ms for m in (ms1, ms2)), f"Задача {t.get('_id')} не соответствует фильтру по {ms1}|{ms2}"


@allure.title("Фильтрация с multiselect milestones - задачи с двумя или более milestones присутствует и без дубликатов")
def test_get_tasks_task_contains_both_milestones(owner_client):
    """
        Тест проверяет корректность выборки при multiselect milestones и отсутствие дубликатов.

        Цели:
        - Среди результатов присутствует хотя бы одна задача, у которой отмечены оба milestones.
        - Все найденные задачи с «пересечением» действительно содержат оба milestones.
        - В ответе нет дубликатов задач по _id.

        Ожидаемый результат:
        - Найдена минимум одна задача с обоими milestones.
        - Для каждой такой задачи оба milestones присутствуют.
        - Дубликаты отсутствуют.
        """
    space_id = MAIN_SPACE_ID
    board_id = BOARD_WITH_TASKS
    ms1 = MILESTONE_1_ID
    ms2 = MILESTONE_2_ID

    with allure.step("Подготовка к тесту: Проверяем наличие обоих milestones в спейсе"):
        for ms in (ms1, ms2):
            r = owner_client.post(**get_milestone_endpoint(ms_id=ms, space_id=space_id))
            r.raise_for_status()
            assert r.json()["payload"]["milestone"]["_id"] == ms

    with allure.step("Запрашиваем задачи по двум milestones (OR-фильтр на бэкенде)"):
        resp = owner_client.post(**get_tasks_endpoint(space_id=space_id, board_id=board_id, milestones=[ms1, ms2]))
        resp.raise_for_status()
        tasks = resp.json()["payload"].get("tasks", [])

    with allure.step("Ищем хотя бы одну задачу, содержащую оба milestones (пересечение)"):
        both = []
        for t in tasks:
            task_ms = t.get("milestones")
            if isinstance(task_ms, str):
                task_ms = [task_ms]
            if ms1 in task_ms and ms2 in task_ms:
                both.append(t)

        assert len(both) >= 1, "Не найдено задач, у которых проставлены оба milestone"

    with allure.step("Проверяем корректность у найденных задач, задачи содержат оба milestones"):
        for t in both:
            task_ms = t.get("milestones")
            if isinstance(task_ms, str):
                task_ms = [task_ms]
            assert ms1 in task_ms and ms2 in task_ms, f"Задача {t.get('_id')} не содержит оба milestones"

    with allure.step("Проверяем отсутствие дубликатов в ответе"):
        ids = [t.get("_id") for t in tasks]
        assert len(ids) == len(set(ids)), f"Найдены дубликаты задач: {ids}"


@allure.title("Фильтрация задач: milestone из другой доски не возвращает задачи")
def test_get_tasks_filtered_by_another_board_milestone(owner_client):
    """
        Тест проверяет, что при фильтрации по несуществующему milestone возвращается пустой список задач.
        Покрывает проверку передачи milestone из другого спейса/проекта/борды

        Ожидаемый результат:
        - Пустой список задач (tasks == [] или len(tasks) == 0).
        - Ошибки HTTP отсутствуют.
        """
    space_id = MAIN_SPACE_ID
    board_id = BOARD_WITH_TASKS
    another_ms_id = "68e8fb0f20bb30c7a47df206"

    with allure.step("Запрашиваем задачи с milestone из другой доски"):
        resp = owner_client.post(**get_tasks_endpoint(space_id=space_id, board_id=board_id, milestones=[another_ms_id]))
        resp.raise_for_status()
        tasks = resp.json()["payload"].get("tasks", [])

    with allure.step("Ожидаем пустой список"):
        assert tasks == [] or len(tasks) == 0



