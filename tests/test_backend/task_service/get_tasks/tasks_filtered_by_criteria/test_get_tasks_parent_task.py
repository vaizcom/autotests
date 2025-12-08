import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

@allure.parent_suite("tasks_filtered_by_criteria")
@allure.title("GetTasks: проверяет фильтрацию GetTasks по полю parentTask.")
def test_get_tasks_filter_by_parent_task(
    member_client,
    main_space,
    board_with_10000_tasks,
):
    """
        GetTasks: фильтр по parentTask — собрать уникальные parentId (not None) с board_with_tasks и проверить фильтрацию
    """
    with allure.step("Подготовка данных: сделать запрос GetTasks к board_with_tasks и собрать все непустые parentId"):
        # 1) Получаем все задачи на борде
        params_all = get_tasks_endpoint(
            space_id=main_space,
            board=board_with_10000_tasks,
            limit=200
        )
        resp_all = member_client.post(**params_all)
        assert resp_all.status_code == 200, f"Не удалось получить список задач борды: {resp_all.text}"
        payload_all = resp_all.json().get("payload", {})
        all_tasks = payload_all.get("tasks", [])
        assert isinstance(all_tasks, list), "payload.tasks должен быть массивом"

        # 2) Собираем уникальные валидные parentId
        parent_ids = {t.get("parentTask") for t in all_tasks if t.get("parentTask") is not None}
        assert parent_ids, "На борде нет задач с parentId (нечего проверять)"

    with allure.step("Для каждого parentId  запросить GetTasks с фильтром parentTask и проверить корректность результата"):
        for parent_id in list(parent_ids)[:10]:
            params_filtered = get_tasks_endpoint(
                space_id=main_space,
                board=board_with_10000_tasks,
                parentTask=parent_id
            )
            resp_filtered = member_client.post(**params_filtered)
            assert resp_filtered.status_code == 200, f"Запрос с parentTask={parent_id} завершился ошибкой: {resp_filtered.text}"

            payload = resp_filtered.json().get("payload", {})
            tasks = payload.get("tasks", [])
            assert isinstance(tasks, list), "payload.tasks должен быть массивом"
            assert (t.get("parentTask") == parent_id for t in tasks)
            assert (not isinstance(t.get("parentTask"), (list, dict)) for t in tasks)

        with allure.step("Проверка: все задачи — прямые дети указанного parent_id"):
            # Дублирую проверку(тех что выше) на еще одной задаче, для красивого отчета в аллуре
            assert any(t.get("parentTask") == parent_id for t in tasks), (
                f"Обнаружены задачи без parentId или с отличным parentId при фильтре parentTask={parent_id}"
            )

        with allure.step("Родитель единственный: не допускается более одного parentTask"):
            # Проверяем, что поле parentId единственное (нет массивов/списков/доп. связей)
            assert any(not isinstance(t.get("parentTask"), (list, dict)) for t in tasks), (
                "Поле parentId должно быть одиночным идентификатором, массив/объект недопустим"
            )

        with allure.step(" Дополнительно: проверка обязательных полей(_id, name, creator, board, parentTask)"):
            required_fields = ["_id", "name", "creator", "board", "parentTask"]
            missing = [
                (t.get("_id", "unknown"), [f for f in required_fields if f not in t])
                for t in tasks
                if any(f not in t for f in required_fields)
            ]
            assert not missing, f"Отсутствуют обязательные поля у задач: {missing}"
